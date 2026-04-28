"""
Tenant-defined promotions (P2-10).

GET    /promotions            — list (staff); ?active_only=true to filter
POST   /promotions            — create (admin)
PATCH  /promotions/{id}       — update label/code/value/is_active/sort_order (admin)
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
from app.models.promotion import PromotionKind, TenantPromotion

router = APIRouter(prefix="/promotions", tags=["promotions"])


class PromotionOut(BaseModel):
    id: str
    code: str
    label: str
    kind: str
    value: str
    is_active: bool
    sort_order: int


class PromotionCreate(BaseModel):
    code: str
    label: str
    kind: PromotionKind
    value: Decimal
    sort_order: int = 0


class PromotionUpdate(BaseModel):
    code: str | None = None
    label: str | None = None
    kind: PromotionKind | None = None
    value: Decimal | None = None
    is_active: bool | None = None
    sort_order: int | None = None


def _out(p: TenantPromotion) -> PromotionOut:
    return PromotionOut(
        id=str(p.id),
        code=p.code,
        label=p.label,
        kind=p.kind.value,
        value=str(p.value),
        is_active=p.is_active,
        sort_order=p.sort_order,
    )


@router.get("", response_model=list[PromotionOut])
async def list_promotions(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(False),
) -> list[PromotionOut]:
    q = select(TenantPromotion).where(TenantPromotion.tenant_id == current_user.tenant_id)
    if active_only:
        q = q.where(TenantPromotion.is_active == True)  # noqa: E712
    q = q.order_by(TenantPromotion.sort_order, TenantPromotion.label)
    rows = (await db.execute(q)).scalars().all()
    return [_out(r) for r in rows]


@router.post("", response_model=PromotionOut, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    body: PromotionCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PromotionOut:
    if body.value <= 0:
        raise HTTPException(status_code=400, detail="value must be > 0")
    if body.kind == PromotionKind.percent and body.value > 100:
        raise HTTPException(status_code=400, detail="percent discount cannot exceed 100")
    promo = TenantPromotion(
        tenant_id=current_user.tenant_id,
        code=body.code.strip(),
        label=body.label.strip(),
        kind=body.kind,
        value=body.value,
        sort_order=body.sort_order,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return _out(promo)


@router.patch("/{promotion_id}", response_model=PromotionOut)
async def update_promotion(
    promotion_id: str,
    body: PromotionUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PromotionOut:
    promo = (
        await db.execute(
            select(TenantPromotion).where(
                TenantPromotion.id == uuid.UUID(promotion_id),
                TenantPromotion.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if promo is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    if body.code is not None:
        promo.code = body.code.strip()
    if body.label is not None:
        promo.label = body.label.strip()
    if body.kind is not None:
        promo.kind = body.kind
    if body.value is not None:
        if body.value <= 0:
            raise HTTPException(status_code=400, detail="value must be > 0")
        promo.value = body.value
    if body.is_active is not None:
        promo.is_active = body.is_active
    if body.sort_order is not None:
        promo.sort_order = body.sort_order
    await db.commit()
    await db.refresh(promo)
    return _out(promo)
