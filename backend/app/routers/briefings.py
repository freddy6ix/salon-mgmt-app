from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/internal", tags=["briefings"])

# Two levels up from routers/ → backend/, three → salon-mgmt-app/
_FALLBACK_BASE_DIR = str(Path(__file__).resolve().parents[3])


def _require_secret(x_internal_secret: str | None = Header(None)) -> None:
    if not settings.internal_secret or x_internal_secret != settings.internal_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


class TriggerRequest(BaseModel):
    briefing_id: str


@router.post("/run-briefing")
async def run_briefing(
    body: TriggerRequest,
    _: None = Depends(_require_secret),
) -> dict:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    base_dir = settings.briefing_base_dir or _FALLBACK_BASE_DIR

    from briefing_engine.runner import run
    return await run(body.briefing_id, settings.anthropic_api_key, base_dir)
