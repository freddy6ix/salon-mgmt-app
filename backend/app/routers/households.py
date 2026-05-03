import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import CurrentUser
from app.models.client import Client, ClientHousehold

router = APIRouter(prefix="/households", tags=["households"])


class HouseholdMemberOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str | None
    cell_phone: str | None


class HouseholdOut(BaseModel):
    id: str
    members: list[HouseholdMemberOut]


def _member_out(c: Client) -> HouseholdMemberOut:
    return HouseholdMemberOut(
        id=str(c.id),
        first_name=c.first_name,
        last_name=c.last_name,
        email=c.email,
        cell_phone=c.cell_phone,
    )


async def _household_out(hh: ClientHousehold, db: AsyncSession, tid: uuid.UUID) -> HouseholdOut:
    members = (await db.execute(
        select(Client).where(
            Client.household_id == hh.id,
            Client.tenant_id == tid,
            Client.is_active == True,  # noqa: E712
        ).order_by(Client.last_name, Client.first_name)
    )).scalars().all()
    return HouseholdOut(id=str(hh.id), members=[_member_out(m) for m in members])


@router.get("", response_model=list[HouseholdOut])
async def list_households(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[HouseholdOut]:
    tid = current_user.tenant_id
    households = (await db.execute(
        select(ClientHousehold).where(ClientHousehold.tenant_id == tid)
        .order_by(ClientHousehold.created_at)
    )).scalars().all()
    return [await _household_out(hh, db, tid) for hh in households]


class HouseholdCreate(BaseModel):
    member_ids: list[str]


@router.post("", response_model=HouseholdOut, status_code=status.HTTP_201_CREATED)
async def create_household(
    body: HouseholdCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HouseholdOut:
    tid = current_user.tenant_id
    if len(body.member_ids) < 2:
        raise HTTPException(status_code=400, detail="A household requires at least 2 members")

    hh = ClientHousehold(tenant_id=tid)
    db.add(hh)
    await db.flush()

    for mid in body.member_ids:
        client = (await db.execute(
            select(Client).where(Client.id == uuid.UUID(mid), Client.tenant_id == tid)
        )).scalar_one_or_none()
        if client:
            client.household_id = hh.id

    await db.commit()
    await db.refresh(hh)
    return await _household_out(hh, db, tid)


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_household(
    household_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    tid = current_user.tenant_id
    hh = (await db.execute(
        select(ClientHousehold).where(
            ClientHousehold.id == uuid.UUID(household_id),
            ClientHousehold.tenant_id == tid,
        )
    )).scalar_one_or_none()
    if not hh:
        raise HTTPException(status_code=404, detail="Household not found")

    # Unlink all members
    await db.execute(
        update(Client)
        .where(Client.household_id == hh.id, Client.tenant_id == tid)
        .values(household_id=None)
    )
    await db.delete(hh)
    await db.commit()
