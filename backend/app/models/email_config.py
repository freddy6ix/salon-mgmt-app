from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class TenantEmailConfig(TenantScopedBase):
    __tablename__ = "tenant_email_configs"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_tenant_email_config"),)

    send_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="smtp")

    # Resend HTTP API fields
    resend_api_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # SMTP fields (nullable — only required when send_mode = 'smtp')
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
