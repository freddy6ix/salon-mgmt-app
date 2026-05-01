"""Orchestrates a full briefing run: synthesize → deliver."""

from briefing_engine import config as cfg
from briefing_engine.delivery import file as file_delivery
from briefing_engine.synthesizer import synthesize


async def run(briefing_id: str, api_key: str, base_dir: str) -> dict:
    briefing = cfg.get(briefing_id)
    if briefing is None:
        raise ValueError(f"Unknown briefing_id: {briefing_id!r}")
    if not briefing.active:
        return {"briefing_id": briefing_id, "status": "inactive"}

    content = await synthesize(briefing, api_key)

    delivered: list[str] = []
    for channel in briefing.delivery_channels:
        if channel == "file" and briefing.output_path:
            resolved = await file_delivery.deliver(content, briefing.output_path, base_dir)
            delivered.append(resolved)

    return {
        "briefing_id": briefing_id,
        "status": "delivered",
        "channels": delivered,
        "chars": len(content),
    }
