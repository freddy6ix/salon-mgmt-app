import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import StaffUser
from app.models.tenant import Tenant

router = APIRouter(prefix="/settings", tags=["settings"])


VALID_SLOT_MINUTES = {10, 15, 20, 30}


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
    from fastapi import HTTPException, status as http_status
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
