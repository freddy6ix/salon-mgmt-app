import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.client import Client
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.provider import Provider
from app.models.service import Service

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    cell_phone: str | None
    email: str | None
    special_instructions: str | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ClientOut])
async def search_clients(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query("", description="Search by name, phone, or email"),
    limit: int = Query(20, le=100),
) -> list[ClientOut]:
    stmt = select(Client).where(
        Client.tenant_id == current_user.tenant_id,
        Client.is_active == True,  # noqa: E712
    )
    if q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Client.first_name.ilike(term),
                Client.last_name.ilike(term),
                Client.cell_phone.ilike(term),
                Client.email.ilike(term),
            )
        )
    stmt = stmt.order_by(Client.last_name, Client.first_name).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        ClientOut(
            id=str(c.id),
            first_name=c.first_name,
            last_name=c.last_name,
            cell_phone=c.cell_phone,
            email=c.email,
            special_instructions=c.special_instructions,
        )
        for c in rows
    ]


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientOut:
    row = (
        await db.execute(
            select(Client).where(
                Client.id == uuid.UUID(client_id),
                Client.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return ClientOut(
        id=str(row.id),
        first_name=row.first_name,
        last_name=row.last_name,
        cell_phone=row.cell_phone,
        email=row.email,
        special_instructions=row.special_instructions,
    )


class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    cell_phone: str | None = None
    email: str | None = None
    special_instructions: str | None = None


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientOut:
    tid = current_user.tenant_id
    # Generate a simple sequential-style code
    count = (await db.execute(
        select(Client).where(Client.tenant_id == tid)
    )).scalars()
    client_code = f"C{str(uuid.uuid4())[:8].upper()}"

    client = Client(
        tenant_id=tid,
        client_code=client_code,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        cell_phone=body.cell_phone,
        email=body.email,
        special_instructions=body.special_instructions,
        country="CA",
        is_vip=False,
        is_active=True,
        no_show_count=0,
        late_cancellation_count=0,
        account_balance=0,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return ClientOut(
        id=str(client.id),
        first_name=client.first_name,
        last_name=client.last_name,
        cell_phone=client.cell_phone,
        email=client.email,
        special_instructions=client.special_instructions,
    )


class ClientNotesUpdate(BaseModel):
    special_instructions: str | None


@router.patch("/{client_id}/notes", response_model=ClientOut)
async def update_client_notes(
    client_id: str,
    body: ClientNotesUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClientOut:
    row = (
        await db.execute(
            select(Client).where(
                Client.id == uuid.UUID(client_id),
                Client.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    row.special_instructions = body.special_instructions
    await db.commit()
    await db.refresh(row)
    return ClientOut(
        id=str(row.id),
        first_name=row.first_name,
        last_name=row.last_name,
        cell_phone=row.cell_phone,
        email=row.email,
        special_instructions=row.special_instructions,
    )


class VisitItem(BaseModel):
    service_name: str
    provider_name: str
    price: float


class VisitOut(BaseModel):
    appointment_id: str
    date: str
    status: str
    items: list[VisitItem]


@router.get("/{client_id}/history", response_model=list[VisitOut])
async def client_history(
    client_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, le=50),
) -> list[VisitOut]:
    client = (
        await db.execute(
            select(Client).where(
                Client.id == uuid.UUID(client_id),
                Client.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    appts = (
        await db.execute(
            select(Appointment)
            .where(
                Appointment.client_id == client.id,
                Appointment.tenant_id == current_user.tenant_id,
                Appointment.status != AppointmentStatus.no_show,
            )
            .order_by(desc(Appointment.appointment_date))
            .limit(limit)
        )
    ).scalars().all()

    visits: list[VisitOut] = []
    for appt in appts:
        items_rows = (
            await db.execute(
                select(AppointmentItem, Service, Provider)
                .join(Service, AppointmentItem.service_id == Service.id)
                .join(Provider, AppointmentItem.provider_id == Provider.id)
                .where(AppointmentItem.appointment_id == appt.id)
                .order_by(AppointmentItem.sequence)
            )
        ).all()

        visits.append(VisitOut(
            appointment_id=str(appt.id),
            date=appt.appointment_date.strftime("%Y-%m-%d"),
            status=appt.status.value,
            items=[
                VisitItem(
                    service_name=svc.name,
                    provider_name=prov.display_name,
                    price=float(item.price),
                )
                for item, svc, prov in items_rows
            ],
        ))
    return visits
