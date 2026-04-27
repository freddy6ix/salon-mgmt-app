import uuid
from datetime import time as dtime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, StaffUser
from app.models.schedule import TenantOperatingHours
from app.models.tenant import Tenant

router = APIRouter(prefix="/settings", tags=["settings"])


VALID_SLOT_MINUTES = {5, 10, 15, 20, 30}


class BrandingOut(BaseModel):
    salon_name: str
    logo_url: str | None
    brand_color: str | None
    slot_minutes: int


class BrandingPatch(BaseModel):
    logo_url: str | None = None
    brand_color: str | None = None
    slot_minutes: int | None = None


async def _get_tenant(tenant_id: uuid.UUID, db: AsyncSession) -> Tenant:
    return (
        await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one()


@router.get("/branding", response_model=BrandingOut)
async def get_branding(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrandingOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    return BrandingOut(
        salon_name=tenant.name,
        logo_url=tenant.logo_url,
        brand_color=tenant.brand_color,
        slot_minutes=tenant.slot_minutes,
    )


@router.patch("/branding", response_model=BrandingOut)
async def update_branding(
    body: BrandingPatch,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BrandingOut:
    tenant = await _get_tenant(current_user.tenant_id, db)
    for field in body.model_fields_set:
        value = getattr(body, field)
        if field == 'slot_minutes':
            if value not in VALID_SLOT_MINUTES:
                raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"slot_minutes must be one of {sorted(VALID_SLOT_MINUTES)}")
            tenant.slot_minutes = value
        else:
            setattr(tenant, field, value or None)
    await db.commit()
    await db.refresh(tenant)
    return BrandingOut(
        salon_name=tenant.name,
        logo_url=tenant.logo_url,
        brand_color=tenant.brand_color,
        slot_minutes=tenant.slot_minutes,
    )


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
