import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class ProviderSchedule(TenantScopedBase):
    __tablename__ = "provider_schedules"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon … 6=Sun
    block: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1=first, 2=split
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class ProviderScheduleException(TenantScopedBase):
    __tablename__ = "provider_schedule_exceptions"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True
    )
    exception_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class TenantOperatingHours(TenantScopedBase):
    __tablename__ = "tenant_operating_hours"

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon … 6=Sun
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
