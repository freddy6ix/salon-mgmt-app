"""
Retail item catalog + inventory (P2-12, P2-13).

GET    /retail-items                        — list with on_hand count (staff)
POST   /retail-items                        — create (admin)
PATCH  /retail-items/{id}                   — update (admin)
GET    /retail-items/{id}/stock             — on_hand + movement history (staff)
POST   /retail-items/{id}/stock/receive     — receive shipment (admin)
POST   /retail-items/{id}/stock/adjust      — adjust to counted quantity (admin)
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import AdminUser, StaffUser
from app.models.retail import RetailItem, RetailStockMovement, StockMovementKind

router = APIRouter(prefix="/retail-items", tags=["retail-items"])


# ── Response models ───────────────────────────────────────────────────────────

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
    on_hand: int


class StockMovementOut(BaseModel):
    id: str
    kind: str
    quantity: int
    unit_cost: str | None
    note: str | None
    created_at: datetime


class StockOut(BaseModel):
    on_hand: int
    movements: list[StockMovementOut]


# ── Request models ────────────────────────────────────────────────────────────

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


class ReceiveIn(BaseModel):
    quantity: int        # units received; must be > 0
    unit_cost: Decimal | None = None
    note: str | None = None


class AdjustIn(BaseModel):
    counted: int         # physically counted on-hand; delta is computed
    note: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _on_hand(item_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(RetailStockMovement.quantity), 0))
        .where(RetailStockMovement.retail_item_id == item_id)
    )
    return int(result.scalar() or 0)


def _out(r: RetailItem, on_hand: int = 0) -> RetailItemOut:
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
        on_hand=on_hand,
    )


async def _load_item(item_id: str, tenant_id: uuid.UUID, db: AsyncSession) -> RetailItem:
    item = (
        await db.execute(
            select(RetailItem).where(
                RetailItem.id == uuid.UUID(item_id),
                RetailItem.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Retail item not found")
    return item


# ── Catalog CRUD ──────────────────────────────────────────────────────────────

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

    # Batch-compute on_hand for all items in one query
    if rows:
        item_ids = [r.id for r in rows]
        counts = (
            await db.execute(
                select(
                    RetailStockMovement.retail_item_id,
                    func.coalesce(func.sum(RetailStockMovement.quantity), 0).label("total"),
                )
                .where(RetailStockMovement.retail_item_id.in_(item_ids))
                .group_by(RetailStockMovement.retail_item_id)
            )
        ).all()
        on_hand_map = {str(row.retail_item_id): int(row.total) for row in counts}
    else:
        on_hand_map = {}

    return [_out(r, on_hand_map.get(str(r.id), 0)) for r in rows]


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
    return _out(item, 0)


@router.patch("/{item_id}", response_model=RetailItemOut)
async def update_retail_item(
    item_id: str,
    body: RetailItemUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RetailItemOut:
    item = await _load_item(item_id, current_user.tenant_id, db)
    for field in body.model_fields_set:
        setattr(item, field, getattr(body, field))
    await db.commit()
    await db.refresh(item)
    on_hand = await _on_hand(item.id, db)
    return _out(item, on_hand)


# ── Stock endpoints ───────────────────────────────────────────────────────────

@router.get("/{item_id}/stock", response_model=StockOut)
async def get_item_stock(
    item_id: str,
    current_user: StaffUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StockOut:
    item = await _load_item(item_id, current_user.tenant_id, db)
    on_hand = await _on_hand(item.id, db)
    movements = (
        await db.execute(
            select(RetailStockMovement)
            .where(RetailStockMovement.retail_item_id == item.id)
            .order_by(RetailStockMovement.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return StockOut(
        on_hand=on_hand,
        movements=[
            StockMovementOut(
                id=str(m.id),
                kind=m.kind.value,
                quantity=m.quantity,
                unit_cost=str(m.unit_cost) if m.unit_cost is not None else None,
                note=m.note,
                created_at=m.created_at,
            )
            for m in movements
        ],
    )


@router.post("/{item_id}/stock/receive", response_model=StockOut, status_code=status.HTTP_201_CREATED)
async def receive_stock(
    item_id: str,
    body: ReceiveIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StockOut:
    if body.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="quantity must be > 0")
    item = await _load_item(item_id, current_user.tenant_id, db)
    db.add(RetailStockMovement(
        tenant_id=current_user.tenant_id,
        retail_item_id=item.id,
        kind=StockMovementKind.receive,
        quantity=body.quantity,
        unit_cost=body.unit_cost,
        note=body.note,
        created_by_user_id=current_user.id,
    ))
    await db.commit()
    return await get_item_stock(item_id, current_user, db)


@router.post("/{item_id}/stock/adjust", response_model=StockOut, status_code=status.HTTP_201_CREATED)
async def adjust_stock(
    item_id: str,
    body: AdjustIn,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StockOut:
    if not body.note.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="note is required for adjustments")
    item = await _load_item(item_id, current_user.tenant_id, db)
    current = await _on_hand(item.id, db)
    delta = body.counted - current
    if delta == 0:
        return await get_item_stock(item_id, current_user, db)
    db.add(RetailStockMovement(
        tenant_id=current_user.tenant_id,
        retail_item_id=item.id,
        kind=StockMovementKind.adjust,
        quantity=delta,
        note=body.note.strip(),
        created_by_user_id=current_user.id,
    ))
    await db.commit()
    return await get_item_stock(item_id, current_user, db)
