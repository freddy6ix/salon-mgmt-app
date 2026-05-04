from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/internal", tags=["briefings"])


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

    from briefing_engine.runner import run
    return await run(
        body.briefing_id,
        settings.anthropic_api_key,
        settings.briefing_base_dir,
        settings.briefing_gcs_bucket,
        settings.briefing_email_to,
        settings.briefing_from_address,
        settings.briefing_resend_api_key,
    )
