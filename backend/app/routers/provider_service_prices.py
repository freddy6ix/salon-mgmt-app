"""
Provider-service capability + price/duration override matrix.

A row indicates "this provider offers this service" and carries optional
per-provider price overrides. Absence of a row means the provider does
not offer that service.

GET    /provider-service-prices?service_id=...    — list (admin) — by service or provider
POST   /provider-service-prices                   — create (admin)
PATCH  /provider-service-prices/{id}              — update (admin)
DELETE /provider-service-prices/{id}              — delete (admin) — removes capability
"""
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser
from app.models.provider import Provider
from app.models.provider_service_price import ProviderServicePrice
from app.models.service import Service

router = APIRouter(prefix="/provider-service-prices", tags=["provider-service-prices"])


class PSPOut(BaseModel):
    id: str
    provider_id: str
    provider_name: str
    service_id: str
    service_name: str
    price: str
    duration_minutes: int | None
    processing_offset_minutes: int | None
    processing_duration_minutes: int | None
    cost: str | None
    cost_is_percentage: bool
    effective_from: date
    effective_to: date | None
    is_active: bool


class PSPIn(BaseModel):
    provider_id: str
    service_id: str
    price: float
    duration_minutes: int | None = None
    processing_offset_minutes: int | None = None
    processing_duration_minutes: int | None = None
    cost: float | None = None
    cost_is_percentage: bool = False
    effective_from: date | None = None  # defaults to today
    effective_to: date | None = None
    is_active: bool = True


class PSPPatch(BaseModel):
    price: float | None = None
    duration_minutes: int | None = None
    processing_offset_minutes: int | None = None
    processing_duration_minutes: int | None = None
    cost: float | None = None
    cost_is_percentage: bool | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    is_active: bool | None = None


def _serialize(p: ProviderServicePrice, provider_name: str, service_name: str) -> PSPOut:
    return PSPOut(
        id=str(p.id),
        provider_id=str(p.provider_id),
        provider_name=provider_name,
        service_id=str(p.service_id),
        service_name=service_name,
        price=str(p.price),
        duration_minutes=p.duration_minutes,
        processing_offset_minutes=p.processing_offset_minutes,
        processing_duration_minutes=p.processing_duration_minutes,
        cost=str(p.cost) if p.cost is not None else None,
        cost_is_percentage=p.cost_is_percentage,
        effective_from=p.effective_from,
        effective_to=p.effective_to,
        is_active=p.is_active,
    )


@router.get("", response_model=list[PSPOut])
async def list_psps(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    service_id: Annotated[str | None, Query()] = None,
    provider_id: Annotated[str | None, Query()] = None,
) -> list[PSPOut]:
    q = (
        select(ProviderServicePrice, Provider, Service)
        .join(Provider, ProviderServicePrice.provider_id == Provider.id)
        .join(Service, ProviderServicePrice.service_id == Service.id)
        .where(ProviderServicePrice.tenant_id == current_user.tenant_id)
    )
    if service_id:
        q = q.where(ProviderServicePrice.service_id == uuid.UUID(service_id))
    if provider_id:
        q = q.where(ProviderServicePrice.provider_id == uuid.UUID(provider_id))
    q = q.order_by(Provider.display_name, Service.name)

    rows = (await db.execute(q)).all()
    return [_serialize(p, prov.display_name, svc.name) for p, prov, svc in rows]


async def _validate_provider_and_service(
    provider_id: uuid.UUID, service_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> tuple[Provider, Service]:
    prov = (
        await db.execute(
            select(Provider).where(Provider.id == provider_id, Provider.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if prov is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid provider_id")
    svc = (
        await db.execute(
            select(Service).where(Service.id == service_id, Service.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if svc is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid service_id")
    return prov, svc


@router.post("", response_model=PSPOut, status_code=status.HTTP_201_CREATED)
async def create_psp(
    body: PSPIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PSPOut:
    tid = current_user.tenant_id
    prov, svc = await _validate_provider_and_service(
        uuid.UUID(body.provider_id), uuid.UUID(body.service_id), tid, db,
    )
    existing = (
        await db.execute(
            select(ProviderServicePrice).where(
                ProviderServicePrice.tenant_id == tid,
                ProviderServicePrice.provider_id == prov.id,
                ProviderServicePrice.service_id == svc.id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That provider already has a price for this service",
        )

    psp = ProviderServicePrice(
        tenant_id=tid,
        provider_id=prov.id,
        service_id=svc.id,
        price=body.price,
        duration_minutes=body.duration_minutes,
        processing_offset_minutes=body.processing_offset_minutes,
        processing_duration_minutes=body.processing_duration_minutes,
        cost=body.cost,
        cost_is_percentage=body.cost_is_percentage,
        effective_from=body.effective_from or date.today(),
        effective_to=body.effective_to,
        is_active=body.is_active,
    )
    db.add(psp)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That provider already has a price for this service",
        )
    await db.refresh(psp)
    return _serialize(psp, prov.display_name, svc.name)


@router.patch("/{psp_id}", response_model=PSPOut)
async def update_psp(
    psp_id: str,
    body: PSPPatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PSPOut:
    tid = current_user.tenant_id
    row = (
        await db.execute(
            select(ProviderServicePrice, Provider, Service)
            .join(Provider, ProviderServicePrice.provider_id == Provider.id)
            .join(Service, ProviderServicePrice.service_id == Service.id)
            .where(
                ProviderServicePrice.id == uuid.UUID(psp_id),
                ProviderServicePrice.tenant_id == tid,
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider-service price not found")
    psp, prov, svc = row

    for field in body.model_fields_set:
        setattr(psp, field, getattr(body, field))

    await db.commit()
    await db.refresh(psp)
    return _serialize(psp, prov.display_name, svc.name)


@router.delete("/{psp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_psp(
    psp_id: str,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    psp = (
        await db.execute(
            select(ProviderServicePrice).where(
                ProviderServicePrice.id == uuid.UUID(psp_id),
                ProviderServicePrice.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if psp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider-service price not found")
    await db.delete(psp)
    await db.commit()
