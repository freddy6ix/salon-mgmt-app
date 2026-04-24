"""
Provider schedules — weekly hours + per-date exceptions.

GET  /schedules?date=YYYY-MM-DD        — all active providers with is_working + hours for that date
POST /schedules                        — upsert per-date is_working exception
GET  /schedules/weekly                 — all active providers' weekly hours
PUT  /schedules/weekly/{provider_id}   — upsert a provider's weekly schedule (all 7 days)
"""
import uuid
from datetime import date, time as dtime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.provider import Provider
from app.models.schedule import ProviderSchedule, ProviderScheduleException, TenantOperatingHours

router = APIRouter(prefix="/schedules", tags=["schedules"])


# ── Response models ──────────────────────────────────────────────────────────

class ProviderWorkStatus(BaseModel):
    provider_id: str
    display_name: str
    booking_order: int
    is_working: bool
    start_time: str | None  # "HH:MM"
    end_time: str | None


class WorkStatusUpdate(BaseModel):
    provider_id: str
    date: date
    is_working: bool


class DayHours(BaseModel):
    day_of_week: int  # 0=Mon … 6=Sun
    is_working: bool
    start_time: str | None  # "HH:MM"
    end_time: str | None


class ProviderWeeklyHours(BaseModel):
    provider_id: str
    display_name: str
    booking_order: int
    days: list[DayHours]


class WeeklyHoursUpdate(BaseModel):
    days: list[DayHours]
    effective_from: date | None = None  # defaults to today


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt(t: dtime | None) -> str | None:
    return t.strftime("%H:%M") if t else None


# ── GET /schedules?date= ─────────────────────────────────────────────────────

@router.get("", response_model=list[ProviderWorkStatus])
async def get_schedule(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    date: date = Query(...),
) -> list[ProviderWorkStatus]:
    tid = current_user.tenant_id
    dow = date.weekday()  # 0=Mon … 6=Sun

    providers = (
        await db.execute(
            select(Provider)
            .where(Provider.tenant_id == tid, Provider.is_active == True, Provider.has_appointments == True)  # noqa: E712
            .order_by(Provider.booking_order)
        )
    ).scalars().all()

    # Weekly schedules for this day of week
    weekly = (
        await db.execute(
            select(ProviderSchedule).where(
                ProviderSchedule.tenant_id == tid,
                ProviderSchedule.day_of_week == dow,
                ProviderSchedule.effective_from <= date,
            )
        )
    ).scalars().all()
    # Most recent effective_from wins
    weekly_map: dict[str, ProviderSchedule] = {}
    for w in sorted(weekly, key=lambda x: x.effective_from):
        weekly_map[str(w.provider_id)] = w

    # Per-date exceptions override weekly
    exceptions = (
        await db.execute(
            select(ProviderScheduleException).where(
                ProviderScheduleException.tenant_id == tid,
                ProviderScheduleException.exception_date == date,
            )
        )
    ).scalars().all()
    exc_map = {str(e.provider_id): e for e in exceptions}

    result = []
    for p in providers:
        pid = str(p.id)
        exc = exc_map.get(pid)
        weekly_row = weekly_map.get(pid)

        if exc is not None:
            is_working = exc.is_working
            start = _fmt(exc.start_time or (weekly_row.start_time if weekly_row else None))
            end = _fmt(exc.end_time or (weekly_row.end_time if weekly_row else None))
        elif weekly_row is not None:
            is_working = weekly_row.is_working
            start = _fmt(weekly_row.start_time)
            end = _fmt(weekly_row.end_time)
        else:
            is_working = True
            start = None
            end = None

        result.append(ProviderWorkStatus(
            provider_id=pid,
            display_name=p.display_name,
            booking_order=p.booking_order,
            is_working=is_working,
            start_time=start,
            end_time=end,
        ))
    return result


# ── POST /schedules — per-date exception ─────────────────────────────────────

@router.post("", response_model=ProviderWorkStatus)
async def set_working_status(
    body: WorkStatusUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProviderWorkStatus:
    tid = current_user.tenant_id
    provider_id = uuid.UUID(body.provider_id)

    if body.date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a past date's schedule",
        )

    provider = (
        await db.execute(
            select(Provider).where(Provider.id == provider_id, Provider.tenant_id == tid)
        )
    ).scalar_one_or_none()

    existing = (
        await db.execute(
            select(ProviderScheduleException).where(
                ProviderScheduleException.tenant_id == tid,
                ProviderScheduleException.provider_id == provider_id,
                ProviderScheduleException.exception_date == body.date,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.is_working = body.is_working
    else:
        db.add(ProviderScheduleException(
            tenant_id=tid,
            provider_id=provider_id,
            exception_date=body.date,
            is_working=body.is_working,
        ))

    await db.commit()
    return ProviderWorkStatus(
        provider_id=str(provider.id),
        display_name=provider.display_name,
        booking_order=provider.booking_order,
        is_working=body.is_working,
        start_time=None,
        end_time=None,
    )


# ── GET /schedules/weekly ────────────────────────────────────────────────────

@router.get("/weekly", response_model=list[ProviderWeeklyHours])
async def get_weekly(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProviderWeeklyHours]:
    tid = current_user.tenant_id

    providers = (
        await db.execute(
            select(Provider)
            .where(Provider.tenant_id == tid, Provider.is_active == True, Provider.has_appointments == True)  # noqa: E712
            .order_by(Provider.booking_order)
        )
    ).scalars().all()

    today = date.today()
    all_rows = (
        await db.execute(
            select(ProviderSchedule).where(
                ProviderSchedule.tenant_id == tid,
                ProviderSchedule.effective_from <= today,
            )
        )
    ).scalars().all()

    # Build map: provider_id → dow → most recent active row
    sched_map: dict[str, dict[int, ProviderSchedule]] = {}
    for row in sorted(all_rows, key=lambda x: x.effective_from):
        pid = str(row.provider_id)
        if pid not in sched_map:
            sched_map[pid] = {}
        sched_map[pid][row.day_of_week] = row

    result = []
    for p in providers:
        pid = str(p.id)
        days = []
        for dow in range(7):
            row = sched_map.get(pid, {}).get(dow)
            days.append(DayHours(
                day_of_week=dow,
                is_working=row.is_working if row else False,
                start_time=_fmt(row.start_time) if row else None,
                end_time=_fmt(row.end_time) if row else None,
            ))
        result.append(ProviderWeeklyHours(
            provider_id=pid,
            display_name=p.display_name,
            booking_order=p.booking_order,
            days=days,
        ))
    return result


# ── PUT /schedules/weekly/{provider_id} ─────────────────────────────────────

@router.put("/weekly/{provider_id}", response_model=ProviderWeeklyHours)
async def set_weekly(
    provider_id: str,
    body: WeeklyHoursUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProviderWeeklyHours:
    tid = current_user.tenant_id
    pid = uuid.UUID(provider_id)

    provider = (
        await db.execute(
            select(Provider).where(Provider.id == pid, Provider.tenant_id == tid)
        )
    ).scalar_one_or_none()

    today = date.today()
    effective_from = body.effective_from or today

    if effective_from < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="effective_from cannot be in the past — historical schedules are locked",
        )

    def _parse(t: str | None) -> dtime | None:
        return dtime.fromisoformat(t) if t else None

    # Re-saving on the same effective_from date is idempotent; older rows are immutable history.
    await db.execute(
        delete(ProviderSchedule).where(
            ProviderSchedule.tenant_id == tid,
            ProviderSchedule.provider_id == pid,
            ProviderSchedule.effective_from == effective_from,
        )
    )

    for day in body.days:
        db.add(ProviderSchedule(
            tenant_id=tid,
            provider_id=pid,
            day_of_week=day.day_of_week,
            block=1,
            is_working=day.is_working,
            start_time=_parse(day.start_time),
            end_time=_parse(day.end_time),
            effective_from=effective_from,
            effective_to=None,
        ))

    await db.commit()

    days = [
        DayHours(
            day_of_week=d.day_of_week,
            is_working=d.is_working,
            start_time=d.start_time,
            end_time=d.end_time,
        )
        for d in body.days
    ]
    return ProviderWeeklyHours(
        provider_id=str(provider.id),
        display_name=provider.display_name,
        booking_order=provider.booking_order,
        days=days,
    )
