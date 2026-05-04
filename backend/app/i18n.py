"""
Language resolution for SalonOS.

Priority for every request:
  1. Accept-Language header (session override — set by frontend toggle)
  2. current_user.language_preference
  3. tenant.default_language
  4. "en" (system fallback)
"""

SUPPORTED_LANGUAGES: list[str] = ["en", "fr"]
_DEFAULT = "en"


def resolve_language(
    accept_language: str | None,
    user_preference: str,
    tenant_default: str,
) -> str:
    if accept_language:
        lang = _best_match(accept_language)
        if lang:
            return lang
    if user_preference in SUPPORTED_LANGUAGES:
        return user_preference
    if tenant_default in SUPPORTED_LANGUAGES:
        return tenant_default
    return _DEFAULT


def _best_match(accept_language: str) -> str | None:
    """
    Parse Accept-Language header and return the best supported language.
    Handles weighted lists like "fr-CA,fr;q=0.9,en;q=0.8".
    """
    candidates: list[tuple[str, float]] = []
    for item in accept_language.split(","):
        item = item.strip()
        if not item or item == "*":
            continue
        if ";q=" in item:
            lang_tag, q_str = item.split(";q=", 1)
            try:
                weight = float(q_str.strip())
            except ValueError:
                weight = 1.0
        else:
            lang_tag = item
            weight = 1.0
        # Use only the primary language subtag (e.g. "fr" from "fr-CA")
        primary = lang_tag.strip().split("-")[0].lower()
        candidates.append((primary, weight))

    candidates.sort(key=lambda x: -x[1])
    for lang, _ in candidates:
        if lang in SUPPORTED_LANGUAGES:
            return lang
    return None
