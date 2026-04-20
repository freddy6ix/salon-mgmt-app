from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.provider import Provider

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderOut(BaseModel):
    id: str
    display_name: str
    provider_type: str
    booking_order: int
    has_appointments: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ProviderOut])
async def list_providers(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProviderOut]:
    result = await db.execute(
        select(Provider)
        .where(
            Provider.tenant_id == current_user.tenant_id,
            Provider.is_active == True,  # noqa: E712
        )
        .order_by(Provider.booking_order)
    )
    providers = result.scalars().all()
    return [
        ProviderOut(
            id=str(p.id),
            display_name=p.display_name,
            provider_type=p.provider_type.value,
            booking_order=p.booking_order,
            has_appointments=p.has_appointments,
        )
        for p in providers
    ]
