import uuid
from calendar import monthrange
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import StaffUser
from app.models.payment_method import TenantPaymentMethod
from app.models.provider import Provider
from app.models.sale import Payment, Sale, SaleItem, SaleItemKind, SaleStatus

router = APIRouter(prefix="/reports", tags=["reports"])


def _d(val: Decimal | None) -> str:
    return str(val or Decimal("0"))


# ── GET /reports/monthly ──────────────────────────────────────────────────────

class ProviderRow(BaseModel):
    provider_name: str
    total: str
    sale_count: int


class PaymentMethodRow(BaseModel):
    label: str
    gross: str
    cashback: str
    net: str


class DayRow(BaseModel):
    date: str        # "YYYY-MM-DD"
    sale_count: int
    total: str


class MonthlyReport(BaseModel):
    year: int
    month: int
    sale_count: int
    subtotal: str
    discount_total: str
    gst_amount: str
    pst_amount: str
    total: str
    service_total: str
    retail_total: str
    by_provider: list[ProviderRow]
    by_payment_method: list[PaymentMethodRow]
    by_day: list[DayRow]


@router.get("/monthly", response_model=MonthlyReport)
async def monthly_report(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> MonthlyReport:
    tid = current_user.tenant_id
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    _, last_day = monthrange(year, month)
    end_month = month + 1 if month < 12 else 1
    end_year = year if month < 12 else year + 1
    end = datetime(end_year, end_month, 1, tzinfo=timezone.utc)

    completed = (
        Sale.tenant_id == tid,
        Sale.status == SaleStatus.completed,
        Sale.completed_at >= start,
        Sale.completed_at < end,
    )

    # ── Overall totals ────────────────────────────────────────────────────────
    totals_row = (
        await db.execute(
            select(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.subtotal), 0),
                func.coalesce(func.sum(Sale.discount_total), 0),
                func.coalesce(func.sum(Sale.gst_amount), 0),
                func.coalesce(func.sum(Sale.pst_amount), 0),
                func.coalesce(func.sum(Sale.total), 0),
            ).where(*completed)
        )
    ).one()
    sale_count, subtotal, discount_total, gst, pst, total = totals_row

    # ── Service vs retail split ───────────────────────────────────────────────
    kind_rows = (
        await db.execute(
            select(SaleItem.kind, func.coalesce(func.sum(SaleItem.line_total), 0))
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(*completed)
            .group_by(SaleItem.kind)
        )
    ).all()
    service_total = Decimal("0")
    retail_total = Decimal("0")
    for kind, amt in kind_rows:
        if kind == SaleItemKind.service:
            service_total = Decimal(str(amt))
        else:
            retail_total = Decimal(str(amt))

    # ── By provider (service items only) ─────────────────────────────────────
    provider_rows = (
        await db.execute(
            select(
                Provider.display_name,
                func.coalesce(func.sum(SaleItem.line_total), 0),
                func.count(func.distinct(Sale.id)),
            )
            .join(Sale, Sale.id == SaleItem.sale_id)
            .join(Provider, Provider.id == SaleItem.provider_id)
            .where(*completed, SaleItem.kind == SaleItemKind.service)
            .group_by(Provider.id, Provider.display_name)
            .order_by(func.sum(SaleItem.line_total).desc())
        )
    ).all()

    # ── By payment method ─────────────────────────────────────────────────────
    payment_rows = (
        await db.execute(
            select(
                TenantPaymentMethod.label,
                func.coalesce(func.sum(Payment.amount), 0),
                func.coalesce(func.sum(Payment.cashback_amount), 0),
            )
            .join(Sale, Sale.id == Payment.sale_id)
            .join(TenantPaymentMethod, TenantPaymentMethod.id == Payment.payment_method_id)
            .where(*completed)
            .group_by(TenantPaymentMethod.id, TenantPaymentMethod.label)
            .order_by(func.sum(Payment.amount).desc())
        )
    ).all()

    # ── By day ────────────────────────────────────────────────────────────────
    day_rows = (
        await db.execute(
            select(
                func.date(Sale.completed_at).label("day"),
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.total), 0),
            )
            .where(*completed)
            .group_by(func.date(Sale.completed_at))
            .order_by(func.date(Sale.completed_at))
        )
    ).all()

    return MonthlyReport(
        year=year,
        month=month,
        sale_count=sale_count,
        subtotal=_d(subtotal),
        discount_total=_d(discount_total),
        gst_amount=_d(gst),
        pst_amount=_d(pst),
        total=_d(total),
        service_total=_d(service_total),
        retail_total=_d(retail_total),
        by_provider=[
            ProviderRow(provider_name=name, total=_d(amt), sale_count=cnt)
            for name, amt, cnt in provider_rows
        ],
        by_payment_method=[
            PaymentMethodRow(
                label=label,
                gross=_d(gross),
                cashback=_d(cb),
                net=_d(Decimal(str(gross)) - Decimal(str(cb))),
            )
            for label, gross, cb in payment_rows
        ],
        by_day=[
            DayRow(date=str(day), sale_count=cnt, total=_d(amt))
            for day, cnt, amt in day_rows
        ],
    )
