"""
Cash reconciliation — end-of-day till management.

See docs/specs/P2-8-cash-reconciliation.md for rules and acceptance tests.

GET    /cash-reconciliation/current          — current open period (404 if none)
POST   /cash-reconciliation                  — open a new period
GET    /cash-reconciliation                  — list recent periods (last 30 days)
GET    /cash-reconciliation/{date}           — specific date (YYYY-MM-DD)
POST   /cash-reconciliation/{date}/close     — close a period
POST   /cash-reconciliation/{date}/petty-cash       — add petty cash entry
DELETE /cash-reconciliation/{date}/petty-cash/{id}  — remove entry (open periods only)
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import StaffUser, AdminUser
from app.models.cash_reconciliation import (
    CashReconciliation, PettyCashEntry, ReconciliationStatus,
)
from app.models.payment_method import PaymentMethodKind, TenantPaymentMethod
from app.models.sale import Payment, Sale, SaleStatus

router = APIRouter(prefix="/cash-reconciliation", tags=["cash-reconciliation"])

BUSINESS_TZ = "America/Toronto"


def _money(v: Decimal | float | int | str) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ── Response models ──────────────────────────────────────────────────────────

class PettyCashEntryOut(BaseModel):
    id: str
    amount: str
    description: str
    created_at: datetime


class ReconciliationOut(BaseModel):
    id: str
    business_date: date
    opening_balance: str
    cash_in: str           # computed
    petty_cash_net: str    # computed
    expected_balance: str  # computed
    counted_balance: str | None
    deposit_amount: str
    closing_balance: str | None
    variance: str | None
    variance_note: str | None
    status: str
    closed_at: datetime | None
    petty_cash_entries: list[PettyCashEntryOut]


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _compute_cash_in(biz_date: date, tenant_id: uuid.UUID, db: AsyncSession) -> Decimal:
    """Sum of completed cash sale payments (net cashback) on the given business date."""
    # Identify cash payment method IDs for this tenant
    cash_pm_ids = (
        await db.execute(
            select(TenantPaymentMethod.id).where(
                TenantPaymentMethod.tenant_id == tenant_id,
                TenantPaymentMethod.kind == PaymentMethodKind.cash,
            )
        )
    ).scalars().all()

    if not cash_pm_ids:
        return Decimal("0")

    # Sum (amount - cashback) for completed sales on that business date
    # Using DATE(completed_at AT TIME ZONE tz) for Toronto business dates
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(Payment.amount - Payment.cashback_amount),
                Decimal("0"),
            )
        )
        .join(Sale, Sale.id == Payment.sale_id)
        .where(
            Sale.tenant_id == tenant_id,
            Sale.status == SaleStatus.completed,
            Payment.payment_method_id.in_(cash_pm_ids),
            func.date(
                func.timezone(BUSINESS_TZ, Sale.completed_at)
            ) == biz_date,
        )
    )
    return _money(result.scalar() or Decimal("0"))


async def _load_recon(biz_date: date, tenant_id: uuid.UUID, db: AsyncSession) -> CashReconciliation:
    row = (
        await db.execute(
            select(CashReconciliation).where(
                CashReconciliation.tenant_id == tenant_id,
                CashReconciliation.business_date == biz_date,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reconciliation for this date")
    return row


async def _serialize(recon: CashReconciliation, tenant_id: uuid.UUID, db: AsyncSession) -> ReconciliationOut:
    cash_in = await _compute_cash_in(recon.business_date, tenant_id, db)

    entries = (
        await db.execute(
            select(PettyCashEntry)
            .where(PettyCashEntry.reconciliation_id == recon.id)
            .order_by(PettyCashEntry.created_at)
        )
    ).scalars().all()

    petty_net = _money(sum(e.amount for e in entries))
    expected = _money(recon.opening_balance + cash_in + petty_net)

    return ReconciliationOut(
        id=str(recon.id),
        business_date=recon.business_date,
        opening_balance=str(recon.opening_balance),
        cash_in=str(cash_in),
        petty_cash_net=str(petty_net),
        expected_balance=str(expected),
        counted_balance=str(recon.counted_balance) if recon.counted_balance is not None else None,
        deposit_amount=str(recon.deposit_amount),
        closing_balance=str(recon.closing_balance) if recon.closing_balance is not None else None,
        variance=str(recon.variance) if recon.variance is not None else None,
        variance_note=recon.variance_note,
        status=recon.status.value,
        closed_at=recon.closed_at,
        petty_cash_entries=[
            PettyCashEntryOut(
                id=str(e.id),
                amount=str(e.amount),
                description=e.description,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )


# ── GET /current ─────────────────────────────────────────────────────────────

@router.get("/current", response_model=ReconciliationOut)
async def get_current(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    row = (
        await db.execute(
            select(CashReconciliation)
            .where(
                CashReconciliation.tenant_id == current_user.tenant_id,
                CashReconciliation.status == ReconciliationStatus.open,
            )
            .order_by(CashReconciliation.business_date.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open reconciliation period")
    return await _serialize(row, current_user.tenant_id, db)


# ── GET / (list) ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[ReconciliationOut])
async def list_reconciliations(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReconciliationOut]:
    cutoff = date.today() - timedelta(days=30)
    rows = (
        await db.execute(
            select(CashReconciliation)
            .where(
                CashReconciliation.tenant_id == current_user.tenant_id,
                CashReconciliation.business_date >= cutoff,
            )
            .order_by(CashReconciliation.business_date.desc())
        )
    ).scalars().all()
    return [await _serialize(r, current_user.tenant_id, db) for r in rows]


# ── POST / (open a new period) ────────────────────────────────────────────────

class OpenPeriodIn(BaseModel):
    business_date: date
    opening_balance: Decimal | None = None


@router.post("", response_model=ReconciliationOut, status_code=status.HTTP_201_CREATED)
async def open_period(
    body: OpenPeriodIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    tid = current_user.tenant_id

    # R1 — uniqueness
    existing = (
        await db.execute(
            select(CashReconciliation).where(
                CashReconciliation.tenant_id == tid,
                CashReconciliation.business_date == body.business_date,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A reconciliation for this date already exists")

    # R8 — opening balance from previous close, or provided override
    if body.opening_balance is not None:
        opening = _money(body.opening_balance)
    else:
        prev = (
            await db.execute(
                select(CashReconciliation)
                .where(
                    CashReconciliation.tenant_id == tid,
                    CashReconciliation.status == ReconciliationStatus.closed,
                    CashReconciliation.business_date < body.business_date,
                )
                .order_by(CashReconciliation.business_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        opening = _money(prev.closing_balance) if prev and prev.closing_balance is not None else Decimal("0")

    recon = CashReconciliation(
        tenant_id=tid,
        business_date=body.business_date,
        opening_balance=opening,
        status=ReconciliationStatus.open,
    )
    db.add(recon)
    await db.commit()
    await db.refresh(recon)
    return await _serialize(recon, tid, db)


# ── GET /{date} ───────────────────────────────────────────────────────────────

@router.get("/{biz_date}", response_model=ReconciliationOut)
async def get_reconciliation(
    biz_date: date,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    recon = await _load_recon(biz_date, current_user.tenant_id, db)
    return await _serialize(recon, current_user.tenant_id, db)


# ── POST /{date}/close ────────────────────────────────────────────────────────

class CloseIn(BaseModel):
    counted_balance: Decimal
    deposit_amount: Decimal = Decimal("0")
    variance_note: str = ""


@router.post("/{biz_date}/close", response_model=ReconciliationOut)
async def close_period(
    biz_date: date,
    body: CloseIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    tid = current_user.tenant_id
    recon = await _load_recon(biz_date, tid, db)

    if recon.status == ReconciliationStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period is already closed")

    cash_in = await _compute_cash_in(biz_date, tid, db)
    entries = (await db.execute(
        select(PettyCashEntry).where(PettyCashEntry.reconciliation_id == recon.id)
    )).scalars().all()
    petty_net = _money(sum(e.amount for e in entries))
    expected = _money(recon.opening_balance + cash_in + petty_net)

    counted = _money(body.counted_balance)
    deposit = _money(body.deposit_amount)
    variance = _money(counted - expected)

    # R5 — variance note required when variance ≠ 0
    if variance != Decimal("0") and not body.variance_note.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="variance_note is required when counted balance differs from expected",
        )

    recon.counted_balance = counted
    recon.deposit_amount = deposit
    recon.closing_balance = _money(counted - deposit)
    recon.variance = variance
    recon.variance_note = body.variance_note.strip() or None
    recon.status = ReconciliationStatus.closed
    recon.closed_by_user_id = current_user.id
    recon.closed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(recon)
    return await _serialize(recon, tid, db)


# ── POST /{date}/petty-cash ───────────────────────────────────────────────────

class PettyCashIn(BaseModel):
    amount: Decimal
    description: str


@router.post("/{biz_date}/petty-cash", response_model=ReconciliationOut, status_code=status.HTTP_201_CREATED)
async def add_petty_cash(
    biz_date: date,
    body: PettyCashIn,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    tid = current_user.tenant_id
    recon = await _load_recon(biz_date, tid, db)

    if recon.status == ReconciliationStatus.closed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Cannot add entries to a closed period")

    if not body.description.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="description is required")

    db.add(PettyCashEntry(
        tenant_id=tid,
        reconciliation_id=recon.id,
        amount=_money(body.amount),
        description=body.description.strip(),
        created_by_user_id=current_user.id,
    ))
    await db.commit()
    await db.refresh(recon)
    return await _serialize(recon, tid, db)


# ── DELETE /{date}/petty-cash/{id} ───────────────────────────────────────────

@router.delete("/{biz_date}/petty-cash/{entry_id}", response_model=ReconciliationOut)
async def delete_petty_cash(
    biz_date: date,
    entry_id: str,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationOut:
    tid = current_user.tenant_id
    recon = await _load_recon(biz_date, tid, db)

    if recon.status == ReconciliationStatus.closed:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Cannot modify a closed period")

    entry = (
        await db.execute(
            select(PettyCashEntry).where(
                PettyCashEntry.id == uuid.UUID(entry_id),
                PettyCashEntry.reconciliation_id == recon.id,
            )
        )
    ).scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    await db.delete(entry)
    await db.commit()
    await db.refresh(recon)
    return await _serialize(recon, tid, db)
