from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.deps import CurrentUser
from app.models.service import Service, ServiceCategory

router = APIRouter(prefix="/services", tags=["services"])


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
