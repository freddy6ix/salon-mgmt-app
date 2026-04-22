import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, Numeric, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class ReferralSource(str, enum.Enum):
    client_referral = "client_referral"
    google = "google"
    instagram = "instagram"
    walk_by = "walk_by"
    other = "other"


class ClientHousehold(TenantScopedBase):
    __tablename__ = "client_households"

    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Client(TenantScopedBase):
    __tablename__ = "clients"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_households.id"), nullable=True, index=True
    )
    preferred_provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True
    )
    referred_by_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True
    )
    client_code: Mapped[str] = mapped_column(String(20), nullable=False)
    milano_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pronouns: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    home_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    work_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cell_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="CA")
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referral_source: Mapped[ReferralSource | None] = mapped_column(
        Enum(ReferralSource), nullable=True
    )
    no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_cancellation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    account_balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    waiver_acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_policy_acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClientColourNote(TenantScopedBase):
    __tablename__ = "client_colour_notes"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    note_date: Mapped[date] = mapped_column(Date, nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
