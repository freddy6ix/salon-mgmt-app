from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class TenantPayrollConfig(TenantScopedBase):
    __tablename__ = "tenant_payroll_configs"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_payroll_config"),)

    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    signature: Mapped[str | None] = mapped_column(String(100), nullable=True)
    footer: Mapped[str | None] = mapped_column(Text, nullable=True)
