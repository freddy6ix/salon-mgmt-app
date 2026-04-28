import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.models.base import TenantScopedBase


class ReconciliationStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class CashReconciliation(TenantScopedBase):
    __tablename__ = "cash_reconciliations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "business_date", name="uq_cash_reconciliation_date"),
    )

    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    # cash_in, petty_cash_net, expected_balance are computed on read — not stored
    counted_balance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    closing_balance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    variance_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReconciliationStatus] = mapped_column(
        SQLEnum(ReconciliationStatus, name="reconciliation_status"),
        nullable=False,
        default=ReconciliationStatus.open,
    )
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PettyCashEntry(TenantScopedBase):
    __tablename__ = "petty_cash_entries"

    reconciliation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_reconciliations.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
