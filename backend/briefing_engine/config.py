from dataclasses import dataclass, field


@dataclass
class BriefingConfig:
    briefing_id: str
    tenant_id: str
    audience: str               # developer | stylist | salon_owner | client | claude_code
    topic_domains: list[str]    # market | clients | competitors | ai_features | industry | regulation
    cadence: str                # daily | weekly | event_triggered
    delivery_channels: list[str]  # email | in_app | sms | voice | file
    output_format: str          # markdown | html | voice_script
    recipient_ids: list[str]
    schedule_cron: str          # e.g. "0 7 * * *"
    output_path: str | None     # relative to base_dir, for file delivery
    active: bool


_REGISTRY: dict[str, BriefingConfig] = {}


def _reg(cfg: BriefingConfig) -> BriefingConfig:
    _REGISTRY[cfg.briefing_id] = cfg
    return cfg


def get(briefing_id: str) -> BriefingConfig | None:
    return _REGISTRY.get(briefing_id)


def all_configs() -> list[BriefingConfig]:
    return list(_REGISTRY.values())


# ── Registered configs ────────────────────────────────────────────────────────

CLAUDE_CODE_BRIEFING = _reg(BriefingConfig(
    briefing_id="claude-code-market-daily",
    tenant_id="salon-lyol",
    audience="claude_code",
    topic_domains=["market", "ai_features", "industry", "regulation"],
    cadence="daily",
    delivery_channels=["file"],
    output_format="markdown",
    recipient_ids=[],
    schedule_cron="0 7 * * *",
    output_path=".claude/rules/market-intelligence.md",
    active=True,
))
