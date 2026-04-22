import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import CurrentUser, StaffUser
from app.models.appointment import (
    Appointment,
    AppointmentItem,
    AppointmentItemStatus,
    AppointmentRequest,
    AppointmentRequestItem,
    AppointmentRequestStatus,
    AppointmentSource,
    AppointmentStatus,
)
from app.models.client import Client
from app.models.provider import Provider
from app.models.service import Service
from app.models.user import UserRole

router = APIRouter(prefix="/appointment-requests", tags=["appointment-requests"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class RequestItemIn(BaseModel):
    service_name: str
    preferred_provider_name: str
    sequence: int = 1


class AppointmentRequestIn(BaseModel):
    desired_date: str  # YYYY-MM-DD
    desired_time_note: str | None = None
    special_note: str | None = None
    items: list[RequestItemIn]


class RequestItemOut(BaseModel):
    id: str
    sequence: int
    service_name: str
    preferred_provider_name: str


class AppointmentRequestOut(BaseModel):
    id: str
    status: str
    desired_date: str
    desired_time_note: str | None
    special_note: str | None
    submitted_at: str
    staff_notes: str | None
    items: list[RequestItemOut]
    first_name: str
    last_name: str
    email: str
    phone: str | None
    client_id: str | None


class RequestReview(BaseModel):
    status: AppointmentRequestStatus
    staff_notes: str | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _load_request_out(req: AppointmentRequest, db: AsyncSession) -> AppointmentRequestOut:
    items = (
        await db.execute(
            select(AppointmentRequestItem)
            .where(AppointmentRequestItem.request_id == req.id)
            .order_by(AppointmentRequestItem.sequence)
        )
    ).scalars().all()

    client_id: str | None = None
    if req.submitted_by_user_id:
        linked_client = (
            await db.execute(
                select(Client).where(
                    Client.user_id == req.submitted_by_user_id,
                    Client.tenant_id == req.tenant_id,
                    Client.is_active == True,  # noqa: E712
                )
            )
        ).scalar_one_or_none()
        if linked_client:
            client_id = str(linked_client.id)

    return AppointmentRequestOut(
        id=str(req.id),
        status=req.status.value,
        desired_date=req.desired_date.strftime("%Y-%m-%d"),
        desired_time_note=req.desired_time_note,
        special_note=req.special_note,
        submitted_at=req.submitted_at.isoformat(),
        staff_notes=req.staff_notes,
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        phone=req.phone or None,
        client_id=client_id,
        items=[
            RequestItemOut(
                id=str(i.id),
                sequence=i.sequence,
                service_name=i.service_name,
                preferred_provider_name=i.preferred_provider_name,
            )
            for i in items
        ],
    )


async def _get_guest_client(user_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> Client:
    client = (
        await db.execute(
            select(Client).where(
                Client.user_id == user_id,
                Client.tenant_id == tenant_id,
                Client.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No client profile found for this account")
    return client


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", response_model=AppointmentRequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    body: AppointmentRequestIn,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRequestOut:
    if current_user.role not in (UserRole.guest,):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only guest accounts can submit appointment requests",
        )

    if not body.items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one service required")

    client = await _get_guest_client(current_user.id, current_user.tenant_id, db)

    desired_date = datetime.strptime(body.desired_date, "%Y-%m-%d")

    req = AppointmentRequest(
        tenant_id=current_user.tenant_id,
        submitted_by_user_id=current_user.id,
        first_name=client.first_name,
        last_name=client.last_name,
        email=client.email or current_user.email,
        phone=client.cell_phone or "",
        desired_date=desired_date,
        desired_time_note=body.desired_time_note,
        source=AppointmentSource.online_form,
        special_note=body.special_note,
        waiver_acknowledged=False,
        cancellation_policy_acknowledged=False,
        status=AppointmentRequestStatus.new,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(req)
    await db.flush()

    for item_in in body.items:
        db.add(AppointmentRequestItem(
            tenant_id=current_user.tenant_id,
            request_id=req.id,
            sequence=item_in.sequence,
            service_name=item_in.service_name,
            preferred_provider_name=item_in.preferred_provider_name,
        ))

    await db.commit()
    await db.refresh(req)
    return await _load_request_out(req, db)


@router.get("", response_model=list[AppointmentRequestOut])
async def list_requests(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    request_status: str | None = Query(None, alias="status"),
) -> list[AppointmentRequestOut]:
    q = select(AppointmentRequest).where(
        AppointmentRequest.tenant_id == current_user.tenant_id
    )

    if current_user.role == UserRole.guest:
        # Guests only see their own requests
        q = q.where(AppointmentRequest.submitted_by_user_id == current_user.id)
    elif current_user.role not in (UserRole.staff, UserRole.tenant_admin, UserRole.super_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    if request_status:
        try:
            q = q.where(AppointmentRequest.status == AppointmentRequestStatus(request_status))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid status: {request_status}")

    q = q.order_by(AppointmentRequest.submitted_at.desc())
    requests = (await db.execute(q)).scalars().all()
    return [await _load_request_out(r, db) for r in requests]


class ConvertItemIn(BaseModel):
    request_item_id: str
    service_id: str
    provider_id: str
    second_provider_id: str | None = None
    sequence: int = 1
    start_time: datetime
    duration_minutes: int
    price: float
    notes: str | None = None


class ConvertRequestIn(BaseModel):
    client_id: str | None = None  # None = create new client from request data
    appointment_date: str  # YYYY-MM-DD
    notes: str | None = None
    items: list[ConvertItemIn]


class ConvertOut(BaseModel):
    appointment_id: str
    appointment_date: str


@router.post("/{request_id}/convert", response_model=ConvertOut, status_code=status.HTTP_201_CREATED)
async def convert_request(
    request_id: str,
    body: ConvertRequestIn,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConvertOut:
    tid = current_user.tenant_id

    req = (
        await db.execute(
            select(AppointmentRequest).where(
                AppointmentRequest.id == uuid.UUID(request_id),
                AppointmentRequest.tenant_id == tid,
            )
        )
    ).scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if req.status == AppointmentRequestStatus.converted:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Request already converted")
    if req.status == AppointmentRequestStatus.declined:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot convert a declined request")
    if not body.items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one item required")

    if body.client_id:
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
    else:
        client_code = f"C{str(uuid.uuid4())[:8].upper()}"
        client = Client(
            tenant_id=tid,
            client_code=client_code,
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email,
            cell_phone=req.phone or None,
            country="CA",
            is_vip=False,
            is_active=True,
            no_show_count=0,
            late_cancellation_count=0,
            account_balance=0,
        )
        db.add(client)
        await db.flush()

    appt_date = datetime.strptime(body.appointment_date, "%Y-%m-%d")

    appt = Appointment(
        tenant_id=tid,
        client_id=client.id,
        request_id=req.id,
        created_by_user_id=current_user.id,
        appointment_date=appt_date,
        source=AppointmentSource.online_form,
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
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Second provider not found")
            second_provider_id = sp.id

        start_time = item_in.start_time.replace(tzinfo=None)

        appt_item = AppointmentItem(
            tenant_id=tid,
            appointment_id=appt.id,
            service_id=service.id,
            provider_id=provider.id,
            second_provider_id=second_provider_id,
            sequence=item_in.sequence,
            start_time=start_time,
            duration_minutes=item_in.duration_minutes,
            price=item_in.price,
            price_is_locked=True,
            status=AppointmentItemStatus.pending,
            notes=item_in.notes,
        )
        db.add(appt_item)
        await db.flush()

        req_item = (
            await db.execute(
                select(AppointmentRequestItem).where(
                    AppointmentRequestItem.id == uuid.UUID(item_in.request_item_id),
                    AppointmentRequestItem.request_id == req.id,
                )
            )
        ).scalar_one_or_none()
        if req_item:
            req_item.converted_to_item_id = appt_item.id

    req.status = AppointmentRequestStatus.converted
    req.converted_to_appointment_id = appt.id
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    await db.commit()

    return ConvertOut(
        appointment_id=str(appt.id),
        appointment_date=body.appointment_date,
    )


@router.patch("/{request_id}", response_model=AppointmentRequestOut)
async def review_request(
    request_id: str,
    body: RequestReview,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRequestOut:
    req = (
        await db.execute(
            select(AppointmentRequest).where(
                AppointmentRequest.id == uuid.UUID(request_id),
                AppointmentRequest.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    req.status = body.status
    if body.staff_notes is not None:
        req.staff_notes = body.staff_notes
    req.reviewed_by_user_id = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(req)
    return await _load_request_out(req, db)
