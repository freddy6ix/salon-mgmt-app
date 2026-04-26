"""
Services catalog.

GET    /services                   — list (active only) — used by booking forms (existing shape)
GET    /services/all               — list including inactive — used by management page
GET    /services/{id}              — full detail — used by management page
POST   /services                   — create (admin)
PATCH  /services/{id}              — update (admin)
DELETE /services/{id}              — soft delete (admin) — sets is_active=false
"""
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, CurrentUser
from app.models.service import HaircutType, PricingType, Service, ServiceCategory

router = APIRouter(prefix="/services", tags=["services"])


# ── List shape (existing, used by booking pickers) ───────────────────────────

class ServiceOut(BaseModel):
    id: str
    service_code: str
    name: str
    category_name: str
    duration_minutes: int
    default_price: float | None
    is_addon: bool
    pricing_type: str


@router.get("", response_model=list[ServiceOut])
async def list_services(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceOut]:
    rows = (
        await db.execute(
            select(Service, ServiceCategory)
            .join(ServiceCategory, Service.category_id == ServiceCategory.id)
            .where(
                Service.tenant_id == current_user.tenant_id,
                Service.is_active == True,  # noqa: E712
            )
            .order_by(ServiceCategory.display_order, Service.display_order, Service.name)
        )
    ).all()

    return [
        ServiceOut(
            id=str(svc.id),
            service_code=svc.service_code,
            name=svc.name,
            category_name=cat.name,
            duration_minutes=svc.duration_minutes,
            default_price=float(svc.default_price) if svc.default_price is not None else None,
            is_addon=svc.is_addon,
            pricing_type=svc.pricing_type.value,
        )
        for svc, cat in rows
    ]


# ── Full detail shape (used by management page) ──────────────────────────────

class ServiceDetailOut(BaseModel):
    id: str
    category_id: str
    category_name: str
    service_code: str
    name: str
    description: str | None
    haircut_type: str | None
    pricing_type: str
    default_price: str | None
    default_cost: str | None
    duration_minutes: int
    processing_offset_minutes: int
    processing_duration_minutes: int
    is_addon: bool
    requires_prior_consultation: bool
    is_gst_exempt: bool
    is_pst_exempt: bool
    suggestions: str | None
    is_active: bool
    display_order: int


def _to_detail(svc: Service, cat: ServiceCategory) -> ServiceDetailOut:
    return ServiceDetailOut(
        id=str(svc.id),
        category_id=str(svc.category_id),
        category_name=cat.name,
        service_code=svc.service_code,
        name=svc.name,
        description=svc.description,
        haircut_type=svc.haircut_type.value if svc.haircut_type else None,
        pricing_type=svc.pricing_type.value,
        default_price=str(svc.default_price) if svc.default_price is not None else None,
        default_cost=str(svc.default_cost) if svc.default_cost is not None else None,
        duration_minutes=svc.duration_minutes,
        processing_offset_minutes=svc.processing_offset_minutes,
        processing_duration_minutes=svc.processing_duration_minutes,
        is_addon=svc.is_addon,
        requires_prior_consultation=svc.requires_prior_consultation,
        is_gst_exempt=svc.is_gst_exempt,
        is_pst_exempt=svc.is_pst_exempt,
        suggestions=svc.suggestions,
        is_active=svc.is_active,
        display_order=svc.display_order,
    )


@router.get("/all", response_model=list[ServiceDetailOut])
async def list_services_full(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceDetailOut]:
    rows = (
        await db.execute(
            select(Service, ServiceCategory)
            .join(ServiceCategory, Service.category_id == ServiceCategory.id)
            .where(Service.tenant_id == current_user.tenant_id)
            .order_by(ServiceCategory.display_order, Service.display_order, Service.name)
        )
    ).all()
    return [_to_detail(svc, cat) for svc, cat in rows]


async def _load_with_category(
    service_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession
) -> tuple[Service, ServiceCategory]:
    row = (
        await db.execute(
            select(Service, ServiceCategory)
            .join(ServiceCategory, Service.category_id == ServiceCategory.id)
            .where(Service.id == service_id, Service.tenant_id == tenant_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return row[0], row[1]


@router.get("/{service_id}", response_model=ServiceDetailOut)
async def get_service(
    service_id: str,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceDetailOut:
    svc, cat = await _load_with_category(uuid.UUID(service_id), current_user.tenant_id, db)
    return _to_detail(svc, cat)


# ── Create / update / delete ─────────────────────────────────────────────────

class ServiceIn(BaseModel):
    category_id: str
    service_code: str | None = Field(default=None, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    haircut_type: HaircutType | None = None
    pricing_type: PricingType = PricingType.fixed
    default_price: float | None = None
    default_cost: float | None = None
    duration_minutes: int = Field(default=60, ge=5)
    processing_offset_minutes: int = 0
    processing_duration_minutes: int = 0
    is_addon: bool = False
    requires_prior_consultation: bool = False
    is_gst_exempt: bool = False
    is_pst_exempt: bool = False
    suggestions: str | None = None
    is_active: bool = True
    display_order: int = 0


class ServicePatch(BaseModel):
    category_id: str | None = None
    service_code: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    haircut_type: HaircutType | None = None
    pricing_type: PricingType | None = None
    default_price: float | None = None
    default_cost: float | None = None
    duration_minutes: int | None = Field(default=None, ge=5)
    processing_offset_minutes: int | None = None
    processing_duration_minutes: int | None = None
    is_addon: bool | None = None
    requires_prior_consultation: bool | None = None
    is_gst_exempt: bool | None = None
    is_pst_exempt: bool | None = None
    suggestions: str | None = None
    is_active: bool | None = None
    display_order: int | None = None


def _slugify_code(name: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    return s[:50] or 'service'


@router.post("", response_model=ServiceDetailOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceDetailOut:
    tid = current_user.tenant_id

    cat = (
        await db.execute(
            select(ServiceCategory).where(
                ServiceCategory.id == uuid.UUID(body.category_id),
                ServiceCategory.tenant_id == tid,
            )
        )
    ).scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid category_id")

    svc = Service(
        tenant_id=tid,
        category_id=cat.id,
        service_code=body.service_code or _slugify_code(body.name),
        name=body.name,
        description=body.description,
        haircut_type=body.haircut_type,
        pricing_type=body.pricing_type,
        default_price=body.default_price,
        default_cost=body.default_cost,
        duration_minutes=body.duration_minutes,
        processing_offset_minutes=body.processing_offset_minutes,
        processing_duration_minutes=body.processing_duration_minutes,
        is_addon=body.is_addon,
        requires_prior_consultation=body.requires_prior_consultation,
        is_gst_exempt=body.is_gst_exempt,
        is_pst_exempt=body.is_pst_exempt,
        suggestions=body.suggestions,
        is_active=body.is_active,
        display_order=body.display_order,
    )
    db.add(svc)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A service with that code already exists")
    await db.refresh(svc)
    return _to_detail(svc, cat)


@router.patch("/{service_id}", response_model=ServiceDetailOut)
async def update_service(
    service_id: str,
    body: ServicePatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceDetailOut:
    tid = current_user.tenant_id
    svc, _ = await _load_with_category(uuid.UUID(service_id), tid, db)

    for field in body.model_fields_set:
        value = getattr(body, field)
        if field == 'category_id' and value is not None:
            cat = (
                await db.execute(
                    select(ServiceCategory).where(
                        ServiceCategory.id == uuid.UUID(value),
                        ServiceCategory.tenant_id == tid,
                    )
                )
            ).scalar_one_or_none()
            if cat is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid category_id")
            svc.category_id = cat.id
        else:
            setattr(svc, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A service with that code already exists")
    await db.refresh(svc)
    cat = (
        await db.execute(select(ServiceCategory).where(ServiceCategory.id == svc.category_id))
    ).scalar_one()
    return _to_detail(svc, cat)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_service(
    service_id: str,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc, _ = await _load_with_category(uuid.UUID(service_id), current_user.tenant_id, db)
    svc.is_active = False
    await db.commit()
