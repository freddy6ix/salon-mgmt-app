"""Orchestrates a full briefing run: synthesize → deliver."""

from briefing_engine import config as cfg
from briefing_engine.delivery import file as file_delivery
from briefing_engine.synthesizer import synthesize


async def run(
    briefing_id: str,
    api_key: str,
    base_dir: str = "",
    gcs_bucket: str = "",
    email_to: str = "",
    email_from: str = "",
    resend_api_key: str = "",
) -> dict:
    briefing = cfg.get(briefing_id)
    if briefing is None:
        raise ValueError(f"Unknown briefing_id: {briefing_id!r}")
    if not briefing.active:
        return {"briefing_id": briefing_id, "status": "inactive"}

    content = await synthesize(briefing, api_key)

    delivered: list[str] = []
    for channel in briefing.delivery_channels:
        if channel == "file" and base_dir and briefing.output_path:
            resolved = await file_delivery.deliver(content, briefing.output_path, base_dir)
            delivered.append(resolved)
        elif channel == "gcs" and gcs_bucket and briefing.output_path:
            from briefing_engine.delivery import gcs as gcs_delivery
            resolved = await gcs_delivery.deliver(content, gcs_bucket, briefing.output_path)
            delivered.append(resolved)
        elif channel == "email" and email_to and email_from and resend_api_key:
            from briefing_engine.delivery import email as email_delivery
            from datetime import date
            subject = f"SalonOS Market Intelligence — {date.today().strftime('%B %d, %Y')}"
            resolved = await email_delivery.deliver(content, resend_api_key, email_from, email_to, subject)
            delivered.append(resolved)

    return {
        "briefing_id": briefing_id,
        "status": "delivered",
        "channels": delivered,
        "chars": len(content),
    }
