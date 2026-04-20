import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class StationType(str, enum.Enum):
    styling = "styling"
    colour_application = "colour_application"
    multi_purpose = "multi_purpose"


class Station(TenantScopedBase):
    __tablename__ = "stations"

    default_provider_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    station_type: Mapped[StationType] = mapped_column(Enum(StationType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
