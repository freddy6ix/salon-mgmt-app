"""
Tenant-configurable payment methods.

GET    /payment-methods                — list (staff)
POST   /payment-methods                — create (admin)
PATCH  /payment-methods/{id}           — update (admin)
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
from app.models.payment_method import PaymentMethodKind, TenantPaymentMethod

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


class PaymentMethodOut(BaseModel):
    id: str
    code: str
    label: str
    kind: str
    is_active: bool
    sort_order: int


class PaymentMethodIn(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r'^[a-z0-9_]+$')
    label: str = Field(min_length=1, max_length=80)
    kind: PaymentMethodKind
    is_active: bool = True
    sort_order: int = 0


class PaymentMethodPatch(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40, pattern=r'^[a-z0-9_]+$')
    label: str | None = Field(default=None, min_length=1, max_length=80)
    kind: PaymentMethodKind | None = None
    is_active: bool | None = None
    sort_order: int | None = None


def _serialize(m: TenantPaymentMethod) -> PaymentMethodOut:
    return PaymentMethodOut(
        id=str(m.id),
        code=m.code,
        label=m.label,
        kind=m.kind.value,
        is_active=m.is_active,
        sort_order=m.sort_order,
    )


@router.get("", response_model=list[PaymentMethodOut])
async def list_payment_methods(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = False,
) -> list[PaymentMethodOut]:
    q = select(TenantPaymentMethod).where(
        TenantPaymentMethod.tenant_id == current_user.tenant_id,
    ).order_by(TenantPaymentMethod.sort_order, TenantPaymentMethod.label)
    if active_only:
        q = q.where(TenantPaymentMethod.is_active.is_(True))
    rows = (await db.execute(q)).scalars().all()
    return [_serialize(m) for m in rows]


@router.post("", response_model=PaymentMethodOut, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    body: PaymentMethodIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentMethodOut:
    method = TenantPaymentMethod(
        tenant_id=current_user.tenant_id,
        code=body.code,
        label=body.label,
        kind=body.kind,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(method)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A payment method with code '{body.code}' already exists",
        )
    await db.refresh(method)
    return _serialize(method)


@router.patch("/{method_id}", response_model=PaymentMethodOut)
async def update_payment_method(
    method_id: str,
    body: PaymentMethodPatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentMethodOut:
    method = (
        await db.execute(
            select(TenantPaymentMethod).where(
                TenantPaymentMethod.id == uuid.UUID(method_id),
                TenantPaymentMethod.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if method is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")

    for field in body.model_fields_set:
        setattr(method, field, getattr(body, field))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A payment method with that code already exists",
        )
    await db.refresh(method)
    return _serialize(method)
