import uuid
from datetime import time as dtime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, StaffUser
from app.i18n import SUPPORTED_LANGUAGES
from app.models.schedule import TenantOperatingHours
from app.models.tenant import Tenant

router = APIRouter(prefix="/settings", tags=["settings"])


VALID_SLOT_MINUTES = {5, 10, 15, 20, 30}
VALID_TIME_FORMATS = {"12h", "24h"}


CONTACT_FIELDS = (
    "address_line1", "address_line2", "city", "region",
    "postal_code", "country", "phone", "hours_summary",
)


class BrandingOut(BaseModel):
    salon_name: str
    logo_url: str | None
    brand_color: str | None
    slot_minutes: int
    time_format: str
    default_language: str
    supported_languages: list[str]
    address_line1: str | None
    address_line2: str | None
    city: str | None
    region: str | None
    postal_code: str | None
    country: str | None
    phone: str | None
    hours_summary: str | None


class BrandingPatch(BaseModel):
    salon_name: str | None = None
    logo_url: str | None = None
    brand_color: str | None = None
    slot_minutes: int | None = None
    time_format: str | None = None
    default_language: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    hours_summary: str | None = None


async def _get_tenant(tenant_id: uuid.UUID, db: AsyncSession) -> Tenant:
    return (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one()


def _branding_out(tenant: Tenant) -> BrandingOut:
    return BrandingOut(
        salon_name=tenant.name,
        logo_url=tenant.logo_url,
        brand_color=tenant.brand_color,
        slot_minutes=tenant.slot_minutes,
        time_format=tenant.time_format,
        default_language=tenant.default_language,
        supported_languages=SUPPORTED_LANGUAGES,
        address_line1=tenant.address_line1,
        address_line2=tenant.address_line2,
        city=tenant.city,
        region=tenant.region,
        postal_code=tenant.postal_code,
        country=tenant.country,
        phone=tenant.phone,
        hours_summary=tenant.hours_summary,
    )


@router.get("/branding", response_model=BrandingOut)
async def get_branding(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrandingOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    return _branding_out(tenant)


@router.patch("/branding", response_model=BrandingOut)
async def update_branding(
    body: BrandingPatch,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrandingOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    for field in body.model_fields_set:
        value = getattr(body, field)
        if field == 'salon_name':
            if not value or not value.strip():
                raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="Salon name cannot be blank")
            tenant.name = value.strip()
        elif field == 'slot_minutes':
            if value not in VALID_SLOT_MINUTES:
                raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"slot_minutes must be one of {sorted(VALID_SLOT_MINUTES)}")
            tenant.slot_minutes = value
        elif field == 'time_format':
            if value not in VALID_TIME_FORMATS:
                raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="time_format must be '12h' or '24h'")
            tenant.time_format = value
        elif field == 'default_language':
            if value not in SUPPORTED_LANGUAGES:
                raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"default_language must be one of {SUPPORTED_LANGUAGES}")
            tenant.default_language = value
        elif field in CONTACT_FIELDS:
            cleaned = value.strip() if isinstance(value, str) else value
            setattr(tenant, field, cleaned or None)
        else:
            setattr(tenant, field, value or None)
    await db.commit()
    await db.refresh(tenant)
    return _branding_out(tenant)


# ── Operating hours ──────────────────────────────────────────────────────────


class OperatingHoursDay(BaseModel):
    day_of_week: int  # 0=Mon … 6=Sun
    is_open: bool
    open_time: str | None  # "HH:MM"
    close_time: str | None

    @field_validator("day_of_week")
    @classmethod
    def _dow_in_range(cls, v: int) -> int:
        if v < 0 or v > 6:
            raise ValueError("day_of_week must be 0..6")
        return v


class OperatingHoursUpdate(BaseModel):
    days: list[OperatingHoursDay]


def _fmt_time(t: dtime | None) -> str | None:
    return t.strftime("%H:%M") if t else None


def _parse_time(v: str | None) -> dtime | None:
    return dtime.fromisoformat(v) if v else None


@router.get("/operating-hours", response_model=list[OperatingHoursDay])
async def get_operating_hours(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OperatingHoursDay]:
    tid = current_user.tenant_id
    rows = (
        await db.execute(
            select(TenantOperatingHours).where(TenantOperatingHours.tenant_id == tid)
        )
    ).scalars().all()
    by_dow = {r.day_of_week: r for r in rows}
    return [
        OperatingHoursDay(
            day_of_week=dow,
            is_open=by_dow[dow].is_open if dow in by_dow else False,
            open_time=_fmt_time(by_dow[dow].open_time) if dow in by_dow else None,
            close_time=_fmt_time(by_dow[dow].close_time) if dow in by_dow else None,
        )
        for dow in range(7)
    ]


@router.put("/operating-hours", response_model=list[OperatingHoursDay])
async def set_operating_hours(
    body: OperatingHoursUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OperatingHoursDay]:
    tid = current_user.tenant_id

    seen: set[int] = set()
    for d in body.days:
        if d.day_of_week in seen:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"duplicate day_of_week {d.day_of_week}",
            )
        seen.add(d.day_of_week)
        if d.is_open:
            if not d.open_time or not d.close_time:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"open_time and close_time required when day {d.day_of_week} is open",
                )
            if _parse_time(d.open_time) >= _parse_time(d.close_time):
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"open_time must be before close_time on day {d.day_of_week}",
                )

    existing = (
        await db.execute(
            select(TenantOperatingHours).where(TenantOperatingHours.tenant_id == tid)
        )
    ).scalars().all()
    by_dow = {r.day_of_week: r for r in existing}

    for d in body.days:
        rec = by_dow.get(d.day_of_week)
        if rec is None:
            rec = TenantOperatingHours(tenant_id=tid, day_of_week=d.day_of_week)
            db.add(rec)
        rec.is_open = d.is_open
        rec.open_time = _parse_time(d.open_time) if d.is_open else None
        rec.close_time = _parse_time(d.close_time) if d.is_open else None

    await db.commit()
    return await get_operating_hours(current_user, db)


# ── Request notifications ────────────────────────────────────────────────────


class RequestNotificationsOut(BaseModel):
    enabled: bool
    recipients: list[str]
    reminder_enabled: bool
    reminder_lead_hours: int


class RequestNotificationsPatch(BaseModel):
    enabled: bool | None = None
    recipients: list[str] | None = None
    reminder_enabled: bool | None = None
    reminder_lead_hours: int | None = None


def _split_recipients(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [r.strip() for r in raw.split(",") if r.strip()]


def _join_recipients(items: list[str]) -> str | None:
    cleaned = [r.strip() for r in items if r and r.strip()]
    return ",".join(cleaned) if cleaned else None


@router.get("/notifications", response_model=RequestNotificationsOut)
async def get_request_notifications(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RequestNotificationsOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    return RequestNotificationsOut(
        enabled=tenant.request_notifications_enabled,
        recipients=_split_recipients(tenant.request_notification_recipients),
        reminder_enabled=tenant.reminder_enabled,
        reminder_lead_hours=tenant.reminder_lead_hours,
    )


@router.patch("/notifications", response_model=RequestNotificationsOut)
async def update_request_notifications(
    body: RequestNotificationsPatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RequestNotificationsOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    if body.enabled is not None:
        tenant.request_notifications_enabled = body.enabled
    if body.recipients is not None:
        # Light shape validation — anything containing "@" is acceptable here;
        # real address validation happens at the SMTP layer.
        for r in body.recipients:
            if "@" not in r:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"'{r}' doesn't look like an email address",
                )
        tenant.request_notification_recipients = _join_recipients(body.recipients)
    if body.reminder_enabled is not None:
        tenant.reminder_enabled = body.reminder_enabled
    if body.reminder_lead_hours is not None:
        if body.reminder_lead_hours < 1:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reminder_lead_hours must be at least 1",
            )
        tenant.reminder_lead_hours = body.reminder_lead_hours
    await db.commit()
    await db.refresh(tenant)
    return RequestNotificationsOut(
        enabled=tenant.request_notifications_enabled,
        recipients=_split_recipients(tenant.request_notification_recipients),
        reminder_enabled=tenant.reminder_enabled,
        reminder_lead_hours=tenant.reminder_lead_hours,
    )
