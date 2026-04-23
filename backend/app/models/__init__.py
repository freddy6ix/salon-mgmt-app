# Import all models here so Alembic autogenerate can detect them.
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User, PasswordResetToken  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.service import ServiceCategory, Service  # noqa: F401
from app.models.provider import Provider  # noqa: F401
from app.models.schedule import ProviderSchedule, ProviderScheduleException, TenantOperatingHours  # noqa: F401
from app.models.station import Station  # noqa: F401
from app.models.provider_service_price import ProviderServicePrice  # noqa: F401
from app.models.client import ClientHousehold, Client  # noqa: F401
from app.models.appointment import (  # noqa: F401
    AppointmentRequest,
    AppointmentRequestItem,
    Appointment,
    AppointmentItem,
    AppointmentReminder,
)
