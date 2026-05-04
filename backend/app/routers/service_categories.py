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
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, ResolvedLanguage, StaffUser
from app.models.i18n import ServiceCategoryTranslation
from app.models.service import ServiceCategory

router = APIRouter(prefix="/service-categories", tags=["service-categories"])


class ServiceCategoryTranslationData(BaseModel):
    name: str | None = None


class ServiceCategoryOut(BaseModel):
    id: str
    name: str
    display_order: int
    is_active: bool
    translations: dict[str, ServiceCategoryTranslationData] = {}


class ServiceCategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_order: int = 0
    is_active: bool = True
    translations: dict[str, ServiceCategoryTranslationData] | None = None


class ServiceCategoryPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    display_order: int | None = None
    is_active: bool | None = None
    translations: dict[str, ServiceCategoryTranslationData] | None = None


async def _load_translations(
    category_id: uuid.UUID, db: AsyncSession
) -> dict[str, ServiceCategoryTranslationData]:
    rows = (
        await db.execute(
            select(ServiceCategoryTranslation).where(
                ServiceCategoryTranslation.category_id == category_id
            )
        )
    ).scalars().all()
    return {row.language: ServiceCategoryTranslationData(name=row.name) for row in rows}


async def _upsert_translation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID,
    language: str,
    name: str,
) -> None:
    existing = (
        await db.execute(
            select(ServiceCategoryTranslation).where(
                ServiceCategoryTranslation.category_id == category_id,
                ServiceCategoryTranslation.language == language,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(ServiceCategoryTranslation(
            tenant_id=tenant_id, category_id=category_id, language=language, name=name,
        ))
    else:
        existing.name = name


def _serialize(c: ServiceCategory, name: str, translations: dict) -> ServiceCategoryOut:
    return ServiceCategoryOut(
        id=str(c.id),
        name=name,
        display_order=c.display_order,
        is_active=c.is_active,
        translations=translations,
    )


@router.get("/{category_id}", response_model=ServiceCategoryOut)
async def get_category(
    category_id: str,
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
    all_tr = await _load_translations(cat.id, db)
    return _serialize(cat, cat.name, all_tr)


@router.get("", response_model=list[ServiceCategoryOut])
async def list_categories(
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    language: ResolvedLanguage,
) -> list[ServiceCategoryOut]:
    rows = (
        await db.execute(
            select(ServiceCategory, ServiceCategoryTranslation)
            .outerjoin(ServiceCategoryTranslation, and_(
                ServiceCategoryTranslation.category_id == ServiceCategory.id,
                ServiceCategoryTranslation.language == language,
            ))
            .where(ServiceCategory.tenant_id == current_user.tenant_id)
            .order_by(ServiceCategory.display_order, ServiceCategory.name)
        )
    ).all()
    return [
        _serialize(cat, tr.name if tr else cat.name, {})
        for cat, tr in rows
    ]


@router.post("", response_model=ServiceCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: ServiceCategoryIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceCategoryOut:
    tid = current_user.tenant_id
    cat = ServiceCategory(
        tenant_id=tid,
        name=body.name,
        display_order=body.display_order,
        is_active=body.is_active,
    )
    db.add(cat)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")

    # Seed English translation
    en_name = (body.translations or {}).get("en", ServiceCategoryTranslationData()).name or body.name
    await _upsert_translation(db, tid, cat.id, "en", en_name)
    for lang, tr_data in (body.translations or {}).items():
        if lang != "en" and tr_data.name:
            await _upsert_translation(db, tid, cat.id, lang, tr_data.name)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")

    await db.refresh(cat)
    all_tr = await _load_translations(cat.id, db)
    return _serialize(cat, cat.name, all_tr)


@router.patch("/{category_id}", response_model=ServiceCategoryOut)
async def update_category(
    category_id: str,
    body: ServiceCategoryPatch,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ServiceCategoryOut:
    tid = current_user.tenant_id
    cat = (
        await db.execute(
            select(ServiceCategory).where(
                ServiceCategory.id == uuid.UUID(category_id),
                ServiceCategory.tenant_id == tid,
            )
        )
    ).scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    for field in body.model_fields_set - {"translations"}:
        setattr(cat, field, getattr(body, field))

    if "name" in body.model_fields_set and body.name:
        await _upsert_translation(db, tid, cat.id, "en", body.name)

    for lang, tr_data in (body.translations or {}).items():
        if tr_data.name:
            await _upsert_translation(db, tid, cat.id, lang, tr_data.name)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")

    await db.refresh(cat)
    all_tr = await _load_translations(cat.id, db)
    return _serialize(cat, cat.name, all_tr)
