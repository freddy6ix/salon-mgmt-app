import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.client import Client, ClientColourNote
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.user import User
from app.models.provider import Provider
from app.models.service import Service

router = APIRouter(prefix="/clients", tags=["clients"])


class ClientOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    pronouns: str | None
    cell_phone: str | None
    email: str | None
    special_instructions: str | None
    no_show_count: int
    late_cancellation_count: int
    is_vip: bool

    model_config = {"from_attributes": True}


def _client_out(c: Client) -> "ClientOut":
    return ClientOut(
        id=str(c.id),
        first_name=c.first_name,
        last_name=c.last_name,
        pronouns=c.pronouns,
        cell_phone=c.cell_phone,
        email=c.email,
        special_instructions=c.special_instructions,
        no_show_count=c.no_show_count,
        late_cancellation_count=c.late_cancellation_count,
        is_vip=c.is_vip,
    )


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
    return [_client_out(c) for c in rows]


@router.get("/check-duplicates", response_model=list[ClientOut])
async def check_duplicates(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: str = Query(""),
    phone: str = Query(""),
) -> list[ClientOut]:
    if not email.strip() and not phone.strip():
        return []
    conditions = []
    if email.strip():
        conditions.append(Client.email == email.strip())
    if phone.strip():
        conditions.append(Client.cell_phone == phone.strip())
    rows = (
        await db.execute(
            select(Client).where(
                Client.tenant_id == current_user.tenant_id,
                Client.is_active == True,  # noqa: E712
                or_(*conditions),
            ).order_by(Client.last_name, Client.first_name)
        )
    ).scalars().all()
    return [_client_out(c) for c in rows]


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
    return _client_out(row)


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
    return _client_out(client)


class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    cell_phone: str | None = None


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: str,
    body: ClientUpdate,
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
    if body.first_name is not None:
        row.first_name = body.first_name.strip()
    if body.last_name is not None:
        row.last_name = body.last_name.strip()
    if body.email is not None:
        row.email = body.email.strip() or None
    if body.cell_phone is not None:
        row.cell_phone = body.cell_phone.strip() or None
    await db.commit()
    await db.refresh(row)
    return _client_out(row)


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
    return _client_out(row)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
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

    upcoming = (
        await db.execute(
            select(Appointment).where(
                Appointment.client_id == row.id,
                Appointment.tenant_id == current_user.tenant_id,
                Appointment.status.in_([AppointmentStatus.confirmed, AppointmentStatus.in_progress]),
                Appointment.appointment_date >= date.today(),
            )
        )
    ).scalars().first()
    if upcoming:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client has upcoming appointments and cannot be deleted",
        )

    row.is_active = False
    if row.user_id:
        linked_user = (
            await db.execute(select(User).where(User.id == row.user_id))
        ).scalar_one_or_none()
        if linked_user:
            linked_user.is_active = False
    await db.commit()


class VisitItem(BaseModel):
    service_name: str
    provider_name: str
    start_time: str  # ISO datetime string
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
            )
            .order_by(desc(Appointment.appointment_date))
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
                    start_time=item.start_time.isoformat(),
                    price=float(item.price),
                )
                for item, svc, prov in items_rows
            ],
        ))
    return visits


# ── Colour notes ──────────────────────────────────────────────────────────────

class ColourNoteOut(BaseModel):
    id: str
    note_date: str
    note_text: str
    created_at: str

    model_config = {"from_attributes": True}


class ColourNoteCreate(BaseModel):
    note_date: date
    note_text: str


async def _get_client_or_404(client_id: str, tenant_id: uuid.UUID, db: AsyncSession) -> Client:
    client = (
        await db.execute(
            select(Client).where(
                Client.id == uuid.UUID(client_id),
                Client.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("/{client_id}/colour-notes", response_model=list[ColourNoteOut])
async def list_colour_notes(
    client_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ColourNoteOut]:
    await _get_client_or_404(client_id, current_user.tenant_id, db)
    rows = (
        await db.execute(
            select(ClientColourNote)
            .where(
                ClientColourNote.client_id == uuid.UUID(client_id),
                ClientColourNote.tenant_id == current_user.tenant_id,
            )
            .order_by(desc(ClientColourNote.note_date), desc(ClientColourNote.created_at))
        )
    ).scalars().all()
    return [
        ColourNoteOut(
            id=str(r.id),
            note_date=r.note_date.strftime("%Y-%m-%d"),
            note_text=r.note_text,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/{client_id}/colour-notes", response_model=ColourNoteOut, status_code=status.HTTP_201_CREATED)
async def create_colour_note(
    client_id: str,
    body: ColourNoteCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ColourNoteOut:
    await _get_client_or_404(client_id, current_user.tenant_id, db)
    note = ClientColourNote(
        tenant_id=current_user.tenant_id,
        client_id=uuid.UUID(client_id),
        created_by_user_id=current_user.id,
        note_date=body.note_date,
        note_text=body.note_text.strip(),
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return ColourNoteOut(
        id=str(note.id),
        note_date=note.note_date.strftime("%Y-%m-%d"),
        note_text=note.note_text,
        created_at=note.created_at.isoformat(),
    )
