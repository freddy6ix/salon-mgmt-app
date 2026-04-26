"""
Provider time blocks (non-bookable spans on a provider's column).

GET    /time-blocks?date=YYYY-MM-DD   — list for a date (staff)
POST   /time-blocks                   — create (staff)
PATCH  /time-blocks/{id}              — update (staff)
DELETE /time-blocks/{id}              — delete (staff)
"""
import uuid
from datetime import date as date_type, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import StaffUser
from app.models.provider import Provider
from app.models.time_block import TimeBlock

router = APIRouter(prefix="/time-blocks", tags=["time-blocks"])


class TimeBlockOut(BaseModel):
    id: str
    provider_id: str
    start_time: datetime
    duration_minutes: int
    note: str | None


class TimeBlockIn(BaseModel):
    provider_id: str
    start_time: datetime
    duration_minutes: int = Field(ge=5)
    note: str | None = None


class TimeBlockPatch(BaseModel):
    provider_id: str | None = None
    start_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5)
    note: str | None = None


def _serialize(b: TimeBlock) -> TimeBlockOut:
    return TimeBlockOut(
        id=str(b.id),
        provider_id=str(b.provider_id),
        start_time=b.start_time,
        duration_minutes=b.duration_minutes,
        note=b.note,
    )


@router.get("", response_model=list[TimeBlockOut])
async def list_time_blocks(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    date: Annotated[date_type, Query()],
) -> list[TimeBlockOut]:
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())
    rows = (
        await db.execute(
            select(TimeBlock).where(
                and_(
                    TimeBlock.tenant_id == current_user.tenant_id,
                    TimeBlock.start_time >= day_start,
                    TimeBlock.start_time <= day_end,
                )
            ).order_by(TimeBlock.start_time)
        )
    ).scalars().all()
    return [_serialize(b) for b in rows]


async def _validate_provider(provider_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> Provider:
    prov = (
        await db.execute(
            select(Provider).where(Provider.id == provider_id, Provider.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if prov is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid provider_id")
    return prov


@router.post("", response_model=TimeBlockOut, status_code=status.HTTP_201_CREATED)
async def create_time_block(
    body: TimeBlockIn,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimeBlockOut:
    tid = current_user.tenant_id
    await _validate_provider(uuid.UUID(body.provider_id), tid, db)
    block = TimeBlock(
        tenant_id=tid,
        provider_id=uuid.UUID(body.provider_id),
        start_time=body.start_time,
        duration_minutes=body.duration_minutes,
        note=body.note,
        created_by_user_id=current_user.id,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return _serialize(block)


@router.patch("/{block_id}", response_model=TimeBlockOut)
async def update_time_block(
    block_id: str,
    body: TimeBlockPatch,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimeBlockOut:
    block = (
        await db.execute(
            select(TimeBlock).where(
                TimeBlock.id == uuid.UUID(block_id),
                TimeBlock.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time block not found")

    for field in body.model_fields_set:
        value = getattr(body, field)
        if field == 'provider_id' and value is not None:
            await _validate_provider(uuid.UUID(value), current_user.tenant_id, db)
            block.provider_id = uuid.UUID(value)
        else:
            setattr(block, field, value)

    await db.commit()
    await db.refresh(block)
    return _serialize(block)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_block(
    block_id: str,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    block = (
        await db.execute(
            select(TimeBlock).where(
                TimeBlock.id == uuid.UUID(block_id),
                TimeBlock.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time block not found")
    await db.delete(block)
    await db.commit()
