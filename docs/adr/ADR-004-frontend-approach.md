# ADR-004: Frontend Approach — API-First with React Admin UI

**Date:** 2026-04-20
**Status:** Accepted
**Deciders:** Frederick Ferguson

---

## Context

Phase 1 requires a staff-facing UI for:
- Appointment book (the central feature — visual calendar grid, multi-provider columns)
- Client management
- Booking request queue (review and convert incoming requests)
- Provider schedule management

The owner is a solo developer with Python/backend experience, less familiar with the frontend side of this repo. The UI must be functional and usable for real salon operations, but does not need to be polished for a general SaaS audience in Phase 1.

Options considered:
1. **Headless API only** — no UI in Phase 1; staff continue using Milano until Phase 2
2. **Server-rendered HTML** — FastAPI + Jinja2 templates + HTMX
3. **React SPA** — decoupled frontend calling the FastAPI backend
4. **Low-code admin tool** — e.g., Retool, AdminJS, or FastAPI's auto-admin

---

## Decision

**React SPA (TypeScript) calling the FastAPI backend, with a component library to minimise custom CSS.**

Recommended stack: **Vite + React + TypeScript + Tailwind CSS + shadcn/ui components.**

The appointment book calendar grid is the one component that requires custom work regardless of stack — no off-the-shelf admin component handles multi-provider time columns well enough. Everything else (client list, request queue, schedule management) can be assembled from standard table/form components.

---

## Rationale

| Option | Pro | Con |
|--------|-----|-----|
| Headless only | No frontend work | Salon cannot switch off Milano; no Phase 1 value |
| Jinja2 + HTMX | Single codebase, Python-native | Poor fit for the appointment book's interactive grid; limited component ecosystem |
| React SPA | Full control over calendar grid; large ecosystem; Claude Code can generate components effectively | Context switch for backend-focused developer; build tooling overhead |
| Low-code admin | Fast for CRUD screens | Cannot implement the appointment book grid; vendor lock-in |

The appointment book is the core of the system. It requires:
- A time-ruler grid with provider columns (similar to Google Calendar's day view, but multi-column)
- Drag-and-drop appointment item placement
- Visual representation of processing time windows
- Real-time updates when other staff book simultaneously (Phase 2)

This level of interactivity is only practical in a modern frontend framework. React has the largest ecosystem of calendar/scheduler primitives to build on.

**Component library choice — shadcn/ui:** Unstyled-by-default components with Tailwind. Avoids fighting an opinionated design system; easy to customise for the appointment book aesthetic.

**Third-party calendar consideration:** Libraries like `react-big-calendar` or `@fullcalendar/react` can accelerate the appointment book grid. Evaluate at implementation time — if a library handles multi-resource day view well, use it; otherwise build a custom grid.

---

## Consequences

- **Positive:** Clean API/UI separation; the FastAPI backend can serve future mobile clients or third-party integrations without changes.
- **Positive:** TypeScript + Pydantic schemas = type safety end-to-end; OpenAPI-generated TypeScript client keeps API contract in sync automatically.
- **Positive:** React's component model is well-suited to the appointment book's column-per-provider layout.
- **Negative:** Two build systems to maintain (Python backend + Node frontend). Mitigated by keeping them in the same repo under `frontend/`.
- **Negative:** Solo developer must context-switch between Python and TypeScript. Mitigated by Claude Code handling most frontend scaffolding.
- **Neutral:** Frontend served as static build from object storage (GCS or Azure Blob) behind a CDN in staging/production. FastAPI serves only the API, not static assets.

---

## Phase 1 UI Scope

Minimum viable screens for Phase 1 launch:

| Screen | Priority |
|--------|---------|
| Login | P0 |
| Appointment book (day/week view, multi-provider columns) | P0 |
| Booking request queue | P0 |
| Client list + client detail | P0 |
| New appointment (create from request or direct) | P0 |
| Provider schedule management | P1 |
| Service list (read-only in Phase 1) | P1 |

POS, reporting, and CRM screens are Phase 2.
