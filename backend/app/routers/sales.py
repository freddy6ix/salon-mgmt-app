"""
Sales — checkout / payment.

POST /sales                              — create + complete a Sale for an in_progress appointment
GET  /sales/by-appointment/{appt_id}     — get the completed Sale for an appointment (404 if none)

See docs/specs/P2-1-checkout-payment.md for the rule list and acceptance tests.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import StaffUser
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.payment_method import TenantPaymentMethod
from app.models.sale import Payment, Sale, SaleItem, SaleStatus
from app.models.service import Service

router = APIRouter(prefix="/sales", tags=["sales"])

GST_RATE = Decimal("0.05")
PST_RATE = Decimal("0.08")


def _money(value: Decimal | float | int | str) -> Decimal:
    """Normalise to 2-decimal Decimal with half-up rounding."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ── Request/response models ──────────────────────────────────────────────────

class SaleItemIn(BaseModel):
    appointment_item_id: str
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")


class PaymentIn(BaseModel):
    payment_method_id: str
    amount: Decimal


class SaleIn(BaseModel):
    appointment_id: str
    tip_amount: Decimal = Decimal("0")
    notes: str | None = None
    items: list[SaleItemIn] = Field(min_length=1)
    payments: list[PaymentIn] = Field(min_length=1)


class SaleItemOut(BaseModel):
    id: str
    description: str
    provider_id: str
    sequence: int
    unit_price: str
    discount_amount: str
    line_total: str


class PaymentOut(BaseModel):
    id: str
    payment_method_id: str
    payment_method_code: str
    payment_method_label: str
    amount: str


class SaleOut(BaseModel):
    id: str
    appointment_id: str
    client_id: str
    subtotal: str
    discount_total: str
    gst_amount: str
    pst_amount: str
    tip_amount: str
    total: str
    status: str
    completed_at: datetime | None
    notes: str | None
    items: list[SaleItemOut]
    payments: list[PaymentOut]


def _serialize(
    sale: Sale,
    items: list[SaleItem],
    payments: list[Payment],
    methods_by_id: dict[uuid.UUID, TenantPaymentMethod],
) -> SaleOut:
    return SaleOut(
        id=str(sale.id),
        appointment_id=str(sale.appointment_id),
        client_id=str(sale.client_id),
        subtotal=str(sale.subtotal),
        discount_total=str(sale.discount_total),
        gst_amount=str(sale.gst_amount),
        pst_amount=str(sale.pst_amount),
        tip_amount=str(sale.tip_amount),
        total=str(sale.total),
        status=sale.status.value,
        completed_at=sale.completed_at,
        notes=sale.notes,
        items=[
            SaleItemOut(
                id=str(it.id),
                description=it.description,
                provider_id=str(it.provider_id),
                sequence=it.sequence,
                unit_price=str(it.unit_price),
                discount_amount=str(it.discount_amount),
                line_total=str(it.line_total),
            )
            for it in items
        ],
        payments=[
            PaymentOut(
                id=str(p.id),
                payment_method_id=str(p.payment_method_id),
                payment_method_code=methods_by_id[p.payment_method_id].code,
                payment_method_label=methods_by_id[p.payment_method_id].label,
                amount=str(p.amount),
            )
            for p in payments
        ],
    )


# ── POST /sales ──────────────────────────────────────────────────────────────

@router.post("", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
async def create_sale(
    body: SaleIn,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SaleOut:
    tid = current_user.tenant_id
    appt_uuid = uuid.UUID(body.appointment_id)

    # Load appointment
    appt = (
        await db.execute(
            select(Appointment).where(
                Appointment.id == appt_uuid,
                Appointment.tenant_id == tid,
            )
        )
    ).scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # R1 — only in_progress appointments can be checked out
    if appt.status != AppointmentStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only appointments that are in progress can be checked out",
        )

    # R2 — at most one completed Sale per Appointment
    existing = (
        await db.execute(
            select(Sale).where(
                Sale.tenant_id == tid,
                Sale.appointment_id == appt_uuid,
                Sale.status == SaleStatus.completed,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This appointment already has a completed sale")

    # Load all appointment items, validate item set
    appt_items = (
        await db.execute(
            select(AppointmentItem).where(
                AppointmentItem.appointment_id == appt.id,
                AppointmentItem.tenant_id == tid,
            )
        )
    ).scalars().all()
    appt_item_map = {str(ai.id): ai for ai in appt_items}

    body_item_ids = [it.appointment_item_id for it in body.items]
    if set(body_item_ids) != set(appt_item_map.keys()):  # R8
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Sale must include exactly the appointment's items (no missing or extra)",
        )

    # Validate per-line discount and price
    for in_item in body.items:
        if in_item.unit_price < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unit_price must be ≥ 0")
        if in_item.discount_amount < 0 or in_item.discount_amount > in_item.unit_price:  # R10
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="discount_amount must be between 0 and unit_price",
            )

    if body.tip_amount < 0:  # R15
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="tip_amount must be ≥ 0")

    # Compute totals server-side (R11–R16)
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    line_records: list[tuple[SaleItemIn, Decimal]] = []  # (input, line_total)
    for in_item in body.items:
        unit = _money(in_item.unit_price)
        disc = _money(in_item.discount_amount)
        line_total = _money(unit - disc)
        subtotal += line_total
        discount_total += disc
        line_records.append((in_item, line_total))

    subtotal = _money(subtotal)
    discount_total = _money(discount_total)
    gst = _money(subtotal * GST_RATE)
    pst = _money(subtotal * PST_RATE)
    tip = _money(body.tip_amount)
    total = _money(subtotal + gst + pst + tip)

    # R18 — payments must sum to total exactly
    payments_total = _money(sum((p.amount for p in body.payments), Decimal("0")))
    if payments_total != total:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Payments total ({payments_total}) must equal sale total ({total})",
        )
    for p in body.payments:
        if p.amount <= 0:  # R19
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each payment amount must be > 0",
            )

    # Validate payment methods belong to this tenant and are active.
    method_uuids = {uuid.UUID(p.payment_method_id) for p in body.payments}
    methods = (
        await db.execute(
            select(TenantPaymentMethod).where(
                TenantPaymentMethod.tenant_id == tid,
                TenantPaymentMethod.id.in_(method_uuids),
            )
        )
    ).scalars().all()
    methods_by_id = {m.id: m for m in methods}
    if len(methods_by_id) != len(method_uuids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more payment_method_id values are invalid for this tenant",
        )
    inactive = [m.label for m in methods if not m.is_active]
    if inactive:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inactive payment method(s): {', '.join(inactive)}",
        )

    # Persist (R3 — atomic with appointment status)
    sale = Sale(
        tenant_id=tid,
        appointment_id=appt.id,
        client_id=appt.client_id,
        subtotal=subtotal,
        discount_total=discount_total,
        gst_amount=gst,
        pst_amount=pst,
        tip_amount=tip,
        total=total,
        status=SaleStatus.completed,
        completed_at=datetime.now(timezone.utc),
        completed_by_user_id=current_user.id,
        notes=body.notes,
    )
    db.add(sale)
    await db.flush()

    # Lookup service names for description snapshot
    service_ids = {ai.service_id for ai in appt_items}
    services = (
        await db.execute(select(Service).where(Service.id.in_(service_ids)))
    ).scalars().all()
    service_names = {s.id: s.name for s in services}

    sale_items: list[SaleItem] = []
    for in_item, line_total in line_records:
        ai = appt_item_map[in_item.appointment_item_id]
        si = SaleItem(
            tenant_id=tid,
            sale_id=sale.id,
            appointment_item_id=ai.id,
            description=service_names.get(ai.service_id, "Service"),
            provider_id=ai.provider_id,
            sequence=ai.sequence,
            unit_price=_money(in_item.unit_price),
            discount_amount=_money(in_item.discount_amount),
            line_total=line_total,
        )
        db.add(si)
        sale_items.append(si)

    sale_payments: list[Payment] = []
    for in_pay in body.payments:
        sp = Payment(
            tenant_id=tid,
            sale_id=sale.id,
            payment_method_id=uuid.UUID(in_pay.payment_method_id),
            amount=_money(in_pay.amount),
        )
        db.add(sp)
        sale_payments.append(sp)

    appt.status = AppointmentStatus.completed

    await db.commit()
    await db.refresh(sale)
    return _serialize(sale, sale_items, sale_payments, methods_by_id)


# ── GET /sales/by-appointment/{appointment_id} ────────────────────────────────

@router.get("/by-appointment/{appointment_id}", response_model=SaleOut)
async def get_sale_by_appointment(
    appointment_id: str,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SaleOut:
    sale = (
        await db.execute(
            select(Sale).where(
                Sale.tenant_id == current_user.tenant_id,
                Sale.appointment_id == uuid.UUID(appointment_id),
                Sale.status == SaleStatus.completed,
            )
        )
    ).scalar_one_or_none()
    if sale is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sale for this appointment")

    items = (await db.execute(select(SaleItem).where(SaleItem.sale_id == sale.id).order_by(SaleItem.sequence))).scalars().all()
    payments = (await db.execute(select(Payment).where(Payment.sale_id == sale.id))).scalars().all()
    method_ids = {p.payment_method_id for p in payments}
    methods = (
        await db.execute(
            select(TenantPaymentMethod).where(TenantPaymentMethod.id.in_(method_ids))
        )
    ).scalars().all() if method_ids else []
    methods_by_id = {m.id: m for m in methods}
    return _serialize(sale, list(items), list(payments), methods_by_id)
