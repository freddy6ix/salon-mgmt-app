from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class RetailItem(TenantScopedBase):
    __tablename__ = "retail_items"

    sku: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    default_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_gst_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pst_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
