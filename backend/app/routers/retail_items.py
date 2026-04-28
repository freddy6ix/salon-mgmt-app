"""
Retail item catalog (P2-12).

GET    /retail-items            — list (staff); ?active_only=true
POST   /retail-items            — create (admin)
PATCH  /retail-items/{id}       — update (admin)
"""
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, StaffUser
from app.models.retail import RetailItem

router = APIRouter(prefix="/retail-items", tags=["retail-items"])


class RetailItemOut(BaseModel):
    id: str
    sku: str | None
    name: str
    description: str | None
    default_price: str
    default_cost: str | None
    is_gst_exempt: bool
    is_pst_exempt: bool
    is_active: bool


class RetailItemCreate(BaseModel):
    sku: str | None = None
    name: str
    description: str | None = None
    default_price: Decimal
    default_cost: Decimal | None = None
    is_gst_exempt: bool = False
    is_pst_exempt: bool = False


class RetailItemUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None
    default_price: Decimal | None = None
    default_cost: Decimal | None = None
    is_gst_exempt: bool | None = None
    is_pst_exempt: bool | None = None
    is_active: bool | None = None


def _out(r: RetailItem) -> RetailItemOut:
    return RetailItemOut(
        id=str(r.id),
        sku=r.sku,
        name=r.name,
        description=r.description,
        default_price=str(r.default_price),
        default_cost=str(r.default_cost) if r.default_cost is not None else None,
        is_gst_exempt=r.is_gst_exempt,
        is_pst_exempt=r.is_pst_exempt,
        is_active=r.is_active,
    )


@router.get("", response_model=list[RetailItemOut])
async def list_retail_items(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(False),
) -> list[RetailItemOut]:
    q = select(RetailItem).where(RetailItem.tenant_id == current_user.tenant_id)
    if active_only:
        q = q.where(RetailItem.is_active == True)  # noqa: E712
    q = q.order_by(RetailItem.name)
    rows = (await db.execute(q)).scalars().all()
    return [_out(r) for r in rows]


@router.post("", response_model=RetailItemOut, status_code=status.HTTP_201_CREATED)
async def create_retail_item(
    body: RetailItemCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RetailItemOut:
    item = RetailItem(
        tenant_id=current_user.tenant_id,
        sku=body.sku.strip() if body.sku else None,
        name=body.name.strip(),
        description=body.description.strip() if body.description else None,
        default_price=body.default_price,
        default_cost=body.default_cost,
        is_gst_exempt=body.is_gst_exempt,
        is_pst_exempt=body.is_pst_exempt,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _out(item)


@router.patch("/{item_id}", response_model=RetailItemOut)
async def update_retail_item(
    item_id: str,
    body: RetailItemUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RetailItemOut:
    item = (
        await db.execute(
            select(RetailItem).where(
                RetailItem.id == uuid.UUID(item_id),
                RetailItem.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Retail item not found")
    for field in body.model_fields_set:
        setattr(item, field, getattr(body, field))
    await db.commit()
    await db.refresh(item)
    return _out(item)
