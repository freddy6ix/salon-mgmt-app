import uuid
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from fastapi import Depends

from app.database import get_db
from app.deps import CurrentUser
from app.models.appointment import (
    Appointment,
    AppointmentItem,
    AppointmentItemStatus,
    AppointmentSource,
    AppointmentStatus,
)
from app.models.client import Client
from app.models.provider import Provider
from app.models.service import Service

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ── Response schemas ────────────────────────────────────────────────────────


class ServiceSummary(BaseModel):
    id: str
    service_code: str
    name: str
    duration_minutes: int
    processing_offset_minutes: int
    processing_duration_minutes: int

    model_config = {"from_attributes": True}


class ProviderSummary(BaseModel):
    id: str
    display_name: str
    provider_type: str

    model_config = {"from_attributes": True}


class ClientSummary(BaseModel):
    id: str
    first_name: str
    last_name: str
    cell_phone: str | None
    special_instructions: str | None

    model_config = {"from_attributes": True}


class AppointmentItemOut(BaseModel):
    id: str
    service: ServiceSummary
    provider: ProviderSummary
    second_provider: ProviderSummary | None
    sequence: int
    start_time: datetime
    duration_minutes: int
    duration_override_minutes: int | None
    price: float
    status: str
    notes: str | None


class AppointmentOut(BaseModel):
    id: str
    appointment_date: datetime
    status: str
    source: str
    notes: str | None
    client: ClientSummary
    items: list[AppointmentItemOut]


# ── Create schemas ───────────────────────────────────────────────────────────


class AppointmentItemIn(BaseModel):
    service_id: str
    provider_id: str
    second_provider_id: str | None = None
    sequence: int = 1
    start_time: datetime
    duration_minutes: int
    duration_override_minutes: int | None = None
    price: float
    notes: str | None = None


class AppointmentIn(BaseModel):
    client_id: str
    appointment_date: date
    source: AppointmentSource = AppointmentSource.staff_entered
    notes: str | None = None
    items: list[AppointmentItemIn]


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _load_appointment_out(appt: Appointment, db: AsyncSession) -> AppointmentOut:
    client = (await db.execute(select(Client).where(Client.id == appt.client_id))).scalar_one()

    items_rows = (
        await db.execute(
            select(AppointmentItem)
            .where(AppointmentItem.appointment_id == appt.id)
            .order_by(AppointmentItem.sequence, AppointmentItem.start_time)
        )
    ).scalars().all()

    service_ids = {i.service_id for i in items_rows}
    provider_ids = {i.provider_id for i in items_rows} | {
        i.second_provider_id for i in items_rows if i.second_provider_id
    }

    services = {
        r.id: r
        for r in (
            await db.execute(select(Service).where(Service.id.in_(service_ids)))
        ).scalars().all()
    }
    providers = {
        r.id: r
        for r in (
            await db.execute(select(Provider).where(Provider.id.in_(provider_ids)))
        ).scalars().all()
    }

    items_out = []
    for item in items_rows:
        svc = services[item.service_id]
        prov = providers[item.provider_id]
        sec = providers.get(item.second_provider_id) if item.second_provider_id else None

        items_out.append(
            AppointmentItemOut(
                id=str(item.id),
                service=ServiceSummary(
                    id=str(svc.id),
                    service_code=svc.service_code,
                    name=svc.name,
                    duration_minutes=svc.duration_minutes,
                    processing_offset_minutes=svc.processing_offset_minutes,
                    processing_duration_minutes=svc.processing_duration_minutes,
                ),
                provider=ProviderSummary(
                    id=str(prov.id),
                    display_name=prov.display_name,
                    provider_type=prov.provider_type.value,
                ),
                second_provider=ProviderSummary(
                    id=str(sec.id),
                    display_name=sec.display_name,
                    provider_type=sec.provider_type.value,
                ) if sec else None,
                sequence=item.sequence,
                start_time=item.start_time,
                duration_minutes=item.duration_minutes,
                duration_override_minutes=item.duration_override_minutes,
                price=float(item.price),
                status=item.status.value,
                notes=item.notes,
            )
        )

    return AppointmentOut(
        id=str(appt.id),
        appointment_date=appt.appointment_date,
        status=appt.status.value,
        source=appt.source.value,
        notes=appt.notes,
        client=ClientSummary(
            id=str(client.id),
            first_name=client.first_name,
            last_name=client.last_name,
            cell_phone=client.cell_phone,
            special_instructions=client.special_instructions,
        ),
        items=items_out,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    date: date = Query(..., description="Date to fetch appointments for (YYYY-MM-DD)"),
) -> list[AppointmentOut]:
    day_start = datetime.combine(date, time.min)
    day_end = datetime.combine(date, time.max)

    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.tenant_id == current_user.tenant_id,
                Appointment.appointment_date >= day_start,
                Appointment.appointment_date <= day_end,
                Appointment.status != AppointmentStatus.no_show,
            )
        )
        .order_by(Appointment.appointment_date)
    )
    appointments = result.scalars().all()

    return [await _load_appointment_out(a, db) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentOut:
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == uuid.UUID(appointment_id),
            Appointment.tenant_id == current_user.tenant_id,
        )
    )
    appt = result.scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return await _load_appointment_out(appt, db)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentIn,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentOut:
    tid = current_user.tenant_id

    # Validate client belongs to tenant
    client = (
        await db.execute(
            select(Client).where(
                Client.id == uuid.UUID(body.client_id),
                Client.tenant_id == tid,
                Client.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if not body.items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one item required")

    appt = Appointment(
        tenant_id=tid,
        client_id=client.id,
        created_by_user_id=current_user.id,
        appointment_date=datetime.combine(body.appointment_date, time.min),
        source=body.source,
        status=AppointmentStatus.confirmed,
        notes=body.notes,
    )
    db.add(appt)
    await db.flush()

    for item_in in body.items:
        provider = (
            await db.execute(
                select(Provider).where(
                    Provider.id == uuid.UUID(item_in.provider_id),
                    Provider.tenant_id == tid,
                )
            )
        ).scalar_one_or_none()
        if provider is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider {item_in.provider_id} not found")

        service = (
            await db.execute(
                select(Service).where(
                    Service.id == uuid.UUID(item_in.service_id),
                    Service.tenant_id == tid,
                )
            )
        ).scalar_one_or_none()
        if service is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service {item_in.service_id} not found")

        second_provider_id = None
        if item_in.second_provider_id:
            sp = (
                await db.execute(
                    select(Provider).where(
                        Provider.id == uuid.UUID(item_in.second_provider_id),
                        Provider.tenant_id == tid,
                    )
                )
            ).scalar_one_or_none()
            if sp is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Second provider {item_in.second_provider_id} not found")
            second_provider_id = sp.id

        appt_item = AppointmentItem(
            tenant_id=tid,
            appointment_id=appt.id,
            service_id=service.id,
            provider_id=provider.id,
            second_provider_id=second_provider_id,
            sequence=item_in.sequence,
            start_time=item_in.start_time,
            duration_minutes=item_in.duration_minutes,
            duration_override_minutes=item_in.duration_override_minutes,
            price=item_in.price,
            price_is_locked=True,
            status=AppointmentItemStatus.pending,
            notes=item_in.notes,
        )
        db.add(appt_item)

    await db.commit()
    await db.refresh(appt)
    return await _load_appointment_out(appt, db)


# ── Item update (drag-to-move / resize) ──────────────────────────────────────

class AppointmentItemPatch(BaseModel):
    start_time: datetime | None = None
    provider_id: str | None = None
    duration_override_minutes: int | None = None


@router.patch("/{appointment_id}/items/{item_id}", response_model=AppointmentOut)
async def patch_appointment_item(
    appointment_id: str,
    item_id: str,
    body: AppointmentItemPatch,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentOut:
    appt = (
        await db.execute(
            select(Appointment).where(
                Appointment.id == uuid.UUID(appointment_id),
                Appointment.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appt.status in (AppointmentStatus.completed, AppointmentStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot modify a completed or cancelled appointment",
        )

    item = (
        await db.execute(
            select(AppointmentItem).where(
                AppointmentItem.id == uuid.UUID(item_id),
                AppointmentItem.appointment_id == appt.id,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if body.start_time is not None:
        item.start_time = body.start_time
    if body.provider_id is not None:
        provider = (
            await db.execute(
                select(Provider).where(
                    Provider.id == uuid.UUID(body.provider_id),
                    Provider.tenant_id == current_user.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if provider is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
        item.provider_id = provider.id
    if body.duration_override_minutes is not None:
        item.duration_override_minutes = body.duration_override_minutes

    await db.commit()
    await db.refresh(appt)
    return await _load_appointment_out(appt, db)


# ── Status transitions ────────────────────────────────────────────────────────

VALID_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.confirmed: {AppointmentStatus.in_progress, AppointmentStatus.cancelled, AppointmentStatus.no_show},
    AppointmentStatus.in_progress: {AppointmentStatus.completed, AppointmentStatus.cancelled},
    AppointmentStatus.completed: set(),
    AppointmentStatus.cancelled: set(),
    AppointmentStatus.no_show: set(),
}

ITEM_STATUS_FOR_APPT: dict[AppointmentStatus, AppointmentItemStatus] = {
    AppointmentStatus.in_progress: AppointmentItemStatus.in_progress,
    AppointmentStatus.completed: AppointmentItemStatus.completed,
    AppointmentStatus.cancelled: AppointmentItemStatus.cancelled,
}


class StatusUpdate(BaseModel):
    status: AppointmentStatus


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appointment_id: str,
    body: StatusUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentOut:
    appt = (
        await db.execute(
            select(Appointment).where(
                Appointment.id == uuid.UUID(appointment_id),
                Appointment.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if body.status not in VALID_TRANSITIONS[appt.status]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from {appt.status.value} to {body.status.value}",
        )

    appt.status = body.status

    # Cascade to items if applicable
    if body.status in ITEM_STATUS_FOR_APPT:
        item_status = ITEM_STATUS_FOR_APPT[body.status]
        items = (
            await db.execute(
                select(AppointmentItem).where(AppointmentItem.appointment_id == appt.id)
            )
        ).scalars().all()
        for item in items:
            if item.status not in (AppointmentItemStatus.cancelled, AppointmentItemStatus.completed):
                item.status = item_status

    await db.commit()
    await db.refresh(appt)
    return await _load_appointment_out(appt, db)
