"""
Synthesizes a briefing document for a given audience using the Claude API.
For audiences with topic_domains that require web search, the web_search_20250305
server-side tool is used — Anthropic handles search execution automatically.
"""

from datetime import date

import anthropic

from briefing_engine.config import BriefingConfig

# ── System prompts by audience ────────────────────────────────────────────────

_SYSTEM: dict[str, str] = {
    "developer": """\
You are a market intelligence analyst briefing Freddy Ferguson — founder of SalonOS, \
a cloud-native salon management platform he is building to replace Milano Software \
(Canadian, on-premises) at Salon Lyol in Toronto, eventually going multi-tenant SaaS.

About SalonOS:
- Stack: Python/FastAPI · PostgreSQL · React/TypeScript · GCP
- Target: Mid-market salons. Salon Lyol first, then multi-tenant SaaS.
- P1 ✓  Appointment book, client management, provider scheduling
- P2 ✓  POS/checkout, inventory, reporting, email confirmations, reminders, data import
- P3    Multi-tenancy, beta salon onboarding
- P4    Voice AI receptionist, AI briefings to stylists/owners, full SaaS

Output rules:
- Markdown, one screenful (~500 words max)
- Lead with the single most actionable or newsworthy item
- Use ## headers per topic area; skip sections with nothing significant
- Be direct and specific: what happened, who shipped it, what it means for SalonOS
- Flag feature gaps: "X has it, SalonOS doesn't yet"
- End with a single "**Bottom line:**" sentence
- Never fabricate — only report what you actually find via search
""",
    "claude_code": """\
You are a market intelligence analyst briefing Claude Code — an AI coding assistant \
building SalonOS, a cloud-native salon management platform replacing Milano Software \
(Canadian, on-premises, est. 1990).

About SalonOS:
- Stack: Python/FastAPI · PostgreSQL · React/TypeScript · GCP
- Target: Mid-market salons. Salon Lyol (Toronto) first, then multi-tenant SaaS.
- P1 ✓  Appointment book, client management, provider scheduling
- P2 ✓  POS/checkout, inventory, reporting, email confirmations, reminders, data import
- P3    Multi-tenancy, beta salon onboarding
- P4    Voice AI receptionist, AI briefings to stylists/owners, full SaaS

Key differentiators being built: correct multi-provider appointment sequencing, \
Briefing Engine, AI-first CRM. No competitor currently offers this combination.

Output rules:
- Markdown, one screenful (~500 words max)
- Lead with the single most actionable item
- Use ## headers per topic area; skip sections with nothing significant
- For each finding: what happened, which competitor/vendor, and whether it affects \
  the SalonOS roadmap (which phase, what specifically)
- Flag anything a competitor ships that SalonOS does not yet have
- End with a single "**Bottom line:**" sentence
- Never fabricate — only report what you actually find via search
""",
}

# ── User prompts by audience ──────────────────────────────────────────────────

_USER: dict[str, str] = """\
Today is {date}. Search for developments in the past 7 days on these topics:

1. **Competitor moves** — new features, pricing changes, or announcements from: \
Zenoti, Boulevard, Mangomint, Phorest, Vagaro, Fresha, Mindbody, Meevo, Shortcuts, GlossGenius
2. **AI in salon/beauty tech** — voice receptionists, missed-call recovery, scheduling AI, \
rebooking automation, churn prediction, marketing AI, chatbots
3. **Industry news** — acquisitions, funding rounds, market moves affecting salon software in North America
4. **Regulation** — anything affecting Canadian salons, payment processing, or small business software

Synthesize your findings into a briefing for Claude Code. \
Skip any topic area with no significant news. Focus only on items that should influence the SalonOS build.
"""

_USER_DEVELOPER = """\
Today is {date}. Search for developments in the past 7 days on these topics:

1. **Competitor moves** — new features, pricing changes, or announcements from: \
Zenoti, Boulevard, Mangomint, Phorest, Vagaro, Fresha, Mindbody, Meevo, Shortcuts, GlossGenius
2. **AI in salon/beauty tech** — voice receptionists, missed-call recovery, scheduling AI, \
rebooking automation, churn prediction, marketing AI, chatbots
3. **Industry news** — acquisitions, funding rounds, market moves affecting salon software in North America
4. **Regulation** — anything affecting Canadian salons, payment processing, or small business software

Synthesize your findings into a briefing for Freddy. \
Skip any topic area with no significant news. Be direct about what matters for the SalonOS build.
"""

# Storing as plain string, keyed in synthesize() by audience
_USER_PROMPTS: dict[str, str] = {
    "developer": _USER_DEVELOPER,
    "claude_code": _USER,
}


async def synthesize(config: BriefingConfig, api_key: str) -> str:
    system = _SYSTEM.get(config.audience)
    user_template = _USER_PROMPTS.get(config.audience)
    if not system or not user_template:
        raise ValueError(f"No prompt defined for audience: {config.audience!r}")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    today = date.today().strftime("%B %d, %Y")

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": user_template.format(date=today)}],
    )

    text_parts = [b.text for b in response.content if hasattr(b, "text") and b.text]
    if not text_parts:
        raise RuntimeError("Synthesizer returned no text — check API key and web_search tool availability")

    header = f"<!-- Generated {today} · model: claude-sonnet-4-6 · audience: {config.audience} -->\n\n"
    return header + "\n\n".join(text_parts)
