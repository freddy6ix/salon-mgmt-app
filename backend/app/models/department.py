from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class Department(TenantScopedBase):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    can_be_cashier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    makes_appointments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_appointments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
