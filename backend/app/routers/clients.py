import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.client import Client

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
