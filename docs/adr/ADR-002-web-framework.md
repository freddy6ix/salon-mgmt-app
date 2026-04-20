# ADR-002: Web Framework — FastAPI

**Date:** 2026-04-20
**Status:** Accepted
**Deciders:** Frederick Ferguson

---

## Context

The backend service requires a Python web framework. The system will expose a REST API consumed by the frontend (Phase 1) and eventually by the AI CRM and voice integrations (Phase 2+). Key requirements:

- Strong async support — appointment scheduling and CRM integrations involve concurrent I/O
- First-class OpenAPI/JSON Schema generation — the API will be consumed by a frontend and eventually third-party integrations
- SQLAlchemy compatibility — the chosen ORM (ADR-003) integrates best with frameworks that support async sessions
- Developer familiarity — owner has a Python background

Alternatives considered: Django REST Framework, Flask + extensions, Litestar.

---

## Decision

**FastAPI.**

---

## Rationale

| Criterion | FastAPI | Django REST Framework | Flask |
|-----------|---------|----------------------|-------|
| Async-first | ✓ native | limited (sync-first) | ✓ with extensions |
| Auto OpenAPI docs | ✓ built-in | requires drf-spectacular | requires flask-smorest |
| Type-driven validation | ✓ Pydantic v2 | serializers (verbose) | manual |
| SQLAlchemy async | ✓ clean | possible but awkward | ✓ |
| Startup overhead | low | high (ORM, admin, sessions baked in) | low |
| Community / ecosystem | large, active | largest | large |

FastAPI's automatic OpenAPI generation means the API is self-documenting from day one — useful for a solo developer iterating quickly. Pydantic models serve as both request/response validation and the API contract, reducing boilerplate. Django's batteries (admin, auth, ORM) are not needed since we're using Alembic for migrations and building custom auth.

---

## Consequences

- **Positive:** Fast iteration, auto-generated docs at `/docs`, clean async SQLAlchemy integration, type safety at API boundaries.
- **Positive:** Pydantic schemas can be reused as the basis for AI prompt schemas in Phase 2 CRM work.
- **Negative:** No built-in admin UI — Phase 1 staff UI must be built separately (see ADR-004).
- **Negative:** FastAPI's async model requires discipline around blocking calls (database queries must use `async` sessions; CPU-bound work needs a thread pool).
- **Neutral:** Authentication must be implemented explicitly (JWT + middleware). This is by design — no framework-imposed auth model to work around in Phase 3 multi-tenancy.
