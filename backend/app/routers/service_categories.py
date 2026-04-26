"""
Service categories — used to group services in the catalog UI.

GET    /service-categories          — list (staff)
POST   /service-categories          — create (admin)
PATCH  /service-categories/{id}     — update (admin)
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, StaffUser
from app.models.service import ServiceCategory

router = APIRouter(prefix="/service-categories", tags=["service-categories"])


class ServiceCategoryOut(BaseModel):
    id: str
    name: str
    display_order: int
    is_active: bool


class ServiceCategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_order: int = 0
    is_active: bool = True


class ServiceCategoryPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    display_order: int | None = None
    is_active: bool | None = None


def _serialize(c: ServiceCategory) -> ServiceCategoryOut:
    return ServiceCategoryOut(
        id=str(c.id),
        name=c.name,
        display_order=c.display_order,
        is_active=c.is_active,
    )


@router.get("", response_model=list[ServiceCategoryOut])
async def list_categories(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceCategoryOut]:
    rows = (
        await db.execute(
            select(ServiceCategory)
            .where(ServiceCategory.tenant_id == current_user.tenant_id)
            .order_by(ServiceCategory.display_order, ServiceCategory.name)
        )
    ).scalars().all()
    return [_serialize(c) for c in rows]


@router.post("", response_model=ServiceCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: ServiceCategoryIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceCategoryOut:
    cat = ServiceCategory(
        tenant_id=current_user.tenant_id,
        name=body.name,
        display_order=body.display_order,
        is_active=body.is_active,
    )
    db.add(cat)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
    await db.refresh(cat)
    return _serialize(cat)


@router.patch("/{category_id}", response_model=ServiceCategoryOut)
async def update_category(
    category_id: str,
    body: ServiceCategoryPatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceCategoryOut:
    cat = (
        await db.execute(
            select(ServiceCategory).where(
                ServiceCategory.id == uuid.UUID(category_id),
                ServiceCategory.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for field in body.model_fields_set:
        setattr(cat, field, getattr(body, field))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")
    await db.refresh(cat)
    return _serialize(cat)
