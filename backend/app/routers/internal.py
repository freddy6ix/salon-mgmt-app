"""Internal endpoints called by Cloud Scheduler (not exposed to the public).

Protected by X-Internal-Secret header matching the INTERNAL_SECRET env var.
If INTERNAL_SECRET is empty the endpoint is disabled (returns 403).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.reminder_dispatcher import dispatch_due_reminders

router = APIRouter(prefix="/internal", tags=["internal"])


def _require_secret(x_internal_secret: Annotated[str | None, Header()] = None) -> None:
    if not settings.internal_secret or x_internal_secret != settings.internal_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/dispatch-reminders")
async def dispatch_reminders(
    _: Annotated[None, Depends(_require_secret)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await dispatch_due_reminders(db)
