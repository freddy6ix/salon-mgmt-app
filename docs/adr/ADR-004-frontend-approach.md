# ADR-004: Frontend Approach — Two Distinct Clients

**Date:** 2026-04-20
**Status:** Accepted (mobile platform decision deferred)
**Deciders:** Frederick Ferguson

---

## Context

The system serves two distinct user groups with fundamentally different needs:

**Reception / Owner (desktop):**
- Full appointment book — multi-provider columns, drag-and-drop scheduling
- Converting booking requests across channels (form, email, phone, walk-in)
- Administrative functions: reporting, inventory, payroll, schedule management

**Individual staff (mobile):**
- Their own schedule for today
- Current client: notes, services booked, colour formula
- Check in a client when they arrive
- Check out a client and accept payment

These are different enough in scope, interaction model, and device constraints that they warrant separate client applications, not a single responsive UI. A mobile-optimised appointment book showing all 8 provider columns is not a viable UX on a phone screen.

---

## Decision

**Two separate frontend clients sharing one FastAPI backend:**

1. **Desktop web app** — React + TypeScript + Vite + Tailwind CSS + shadcn/ui. Served as a static build from Cloud Storage + CDN.

2. **Staff mobile app** — native iOS/Android. **Platform decision (React Native vs. Flutter vs. native Swift/Kotlin) is deferred.** The FastAPI backend is designed from day one to serve both clients — no mobile-specific API changes will be needed later.

The mobile app is **Phase 2**. Phase 1 delivers the desktop web app only. Staff use desktop during Phase 1.

---

## Desktop Web App

### Why React SPA over other options

| Option | Pro | Con |
|--------|-----|-----|
| Headless only | No frontend work | No staff-facing UI; no Phase 1 value |
| Jinja2 + HTMX | Single codebase, Python-native | Poor fit for the appointment book's interactive grid |
| React SPA | Full control over calendar grid; large ecosystem | Context switch for backend-focused developer |
| Low-code admin | Fast for CRUD screens | Cannot implement the appointment book grid; vendor lock-in |

The appointment book requires:
- A time-ruler grid with one column per provider (similar to Google Calendar day view, multi-column)
- Drag-and-drop appointment item placement
- Visual representation of processing time windows (provider-free windows shown differently from booked time)
- Real-time updates when multiple staff book simultaneously (Phase 2 WebSocket)

This level of interactivity is only practical in a modern frontend framework.

**shadcn/ui** — unstyled-by-default components with Tailwind. Avoids fighting an opinionated design system while providing accessible, composable primitives for forms, tables, and modals.

**Third-party calendar:** Libraries like `@fullcalendar/react` (resource timeline view) may handle the multi-provider grid. Evaluate at implementation — if a library handles multi-resource day view well enough, use it; otherwise build a custom grid component.

---

## Mobile App (Deferred to Phase 2)

### Use cases

| Action | Notes |
|--------|-------|
| View today's personal schedule | Own appointments only — not the full book |
| Client check-in | Mark client as arrived |
| View client notes + service details | Special instructions, colour formula, service sequence |
| Client check-out | Accept payment (card via terminal integration, or cash) |

### Deferred platform decision

Native iOS/Android is preferred over a PWA or responsive web for the mobile experience (better camera access for client photos, push notifications for schedule changes, smoother payment terminal integration). The specific framework — React Native, Flutter, or native — is deferred until Phase 2 planning.

**API design implication (not deferred):** The FastAPI backend must expose mobile-friendly endpoints from Phase 1:
- `GET /providers/{id}/schedule/today` — single provider's day view
- `GET /appointments/{id}` — full appointment detail including client notes and service sequence
- `POST /appointments/{id}/checkin` — mark arrived
- `POST /appointments/{id}/checkout` — initiate payment

These endpoints should be designed and implemented in Phase 1 even though the mobile app consuming them is built in Phase 2. This avoids retrofitting the API later.

---

## Consequences

- **Positive:** Desktop and mobile UX are each optimised for their context — no compromises from a single responsive design.
- **Positive:** Clean API separation means the mobile app can be built in Phase 2 against an already-stable backend contract.
- **Positive:** TypeScript + Pydantic/OpenAPI = type-safe API contract shared between backend and both frontends.
- **Negative:** Two separate frontend codebases to maintain eventually. Mitigated by deferred mobile build.
- **Negative:** Solo developer must context-switch between Python and TypeScript for the desktop app. Mitigated by Claude Code handling frontend scaffolding.
- **Neutral:** Desktop frontend served as static build from Cloud Storage + CDN (ADR-001). FastAPI serves only the API, not static assets.

---

## Phase 1 Desktop UI Scope

| Screen | Priority |
|--------|---------|
| Login | P0 |
| Appointment book — day view, multi-provider columns | P0 |
| Booking request queue | P0 |
| Client list + client detail | P0 |
| New appointment (from request or direct) | P0 |
| Provider schedule management | P1 |
| Service list (read-only) | P1 |

POS, reporting, inventory, and CRM screens are Phase 2 desktop. Mobile app is Phase 2.
