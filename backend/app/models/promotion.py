import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum as SQLEnum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class PromotionKind(str, enum.Enum):
    percent = "percent"   # value = percentage off (e.g. 10 = 10%)
    amount = "amount"     # value = fixed dollar amount off


class TenantPromotion(TenantScopedBase):
    __tablename__ = "tenant_promotions"

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[PromotionKind] = mapped_column(
        SQLEnum(PromotionKind, name="promotion_kind"), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
