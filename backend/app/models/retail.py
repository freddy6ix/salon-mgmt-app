import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
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


class StockMovementKind(str, enum.Enum):
    receive = "receive"   # incoming shipment — positive qty
    sell = "sell"         # sold at checkout — negative qty (written automatically)
    adjust = "adjust"     # manual count correction — signed qty (delta from counted)
    ret = "return"        # item returned — positive qty


class RetailStockMovement(TenantScopedBase):
    __tablename__ = "retail_stock_movements"

    retail_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retail_items.id"), nullable=False, index=True
    )
    kind: Mapped[StockMovementKind] = mapped_column(
        SQLEnum(StockMovementKind, name="stock_movement_kind"), nullable=False
    )
    # Signed quantity: positive = stock in, negative = stock out
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    sale_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sale_items.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
