<p align="center">
  <img src="frontend/public/salon-lyol-logo.png" alt="Salon Lyol" height="64">
</p>

<h1 align="center">Salon Management System</h1>

<p align="center">
  Cloud-native salon management software — replacing legacy desktop tools with a modern,<br>
  AI-ready platform built for the way premium salons actually work.
</p>

<p align="center">
  <a href="https://github.com/freddy6ix/salon-mgmt-app/actions/workflows/deploy.yml">
    <img src="https://github.com/freddy6ix/salon-mgmt-app/actions/workflows/deploy.yml/badge.svg" alt="Deploy to Staging">
  </a>
  &nbsp;
  <img src="https://img.shields.io/badge/phase-2%20nearly%20complete-blue" alt="Phase 2 nearly complete">
  &nbsp;
  <img src="https://img.shields.io/badge/deployed-GCP%20Cloud%20Run-4285F4?logo=googlecloud&logoColor=white" alt="Deployed on GCP">
</p>

---

## The Problem

Legacy salon software (Milano, Vagaro, Mindbody) was designed for a different era — desktop-first, rigid pricing models, and no path to customization. For a high-end independent salon like [Salon Lyol](https://salonlyol.ca) in Toronto, the appointment book *is* the business: multi-service, multi-provider bookings where colour-development gaps and idle-time optimization are daily concerns. No off-the-shelf tool models this correctly.

This project replaces Salon Lyol's current system with purpose-built cloud software, and is being designed from day one as a multi-tenant SaaS platform for other premium salons.

---

## Screenshots

<table>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/landing.png" alt="Landing page">
      <p align="center"><sub>Branded landing page & guest booking request form</sub></p>
    </td>
    <td width="50%">
      <img src="docs/screenshots/home-dashboard.png" alt="Home dashboard">
      <p align="center"><sub>Staff dashboard — today's book & pending requests</sub></p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/appointment-book.png" alt="Appointment book">
      <p align="center"><sub>Appointment book — drag-and-drop, multi-provider grid</sub></p>
    </td>
    <td width="50%">
      <img src="docs/screenshots/appointment-detail.png" alt="Appointment detail">
      <p align="center"><sub>Appointment detail — services, confirmation email, status flow</sub></p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/appointment-checkout.png" alt="POS checkout">
      <p align="center"><sub>POS checkout — split payment, GST/PST, cashback flow</sub></p>
    </td>
    <td width="50%">
      <img src="docs/screenshots/till.png" alt="Cash till">
      <p align="center"><sub>Cash till — running position, end-of-day reconciliation</sub></p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/clients.png" alt="Client CRM">
      <p align="center"><sub>Client CRM — history, colour notes, upcoming appointments</sub></p>
    </td>
    <td width="50%">
      <img src="docs/screenshots/services-detail.png" alt="Services catalog">
      <p align="center"><sub>Services catalog — per-provider pricing & processing times</sub></p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/booking-requests.png" alt="Booking requests">
      <p align="center"><sub>Booking requests — guest-submitted, staff-confirmed</sub></p>
    </td>
    <td width="50%">
      <img src="docs/screenshots/settings.png" alt="Settings">
      <p align="center"><sub>Settings — branding, operating hours, payment methods, email</sub></p>
    </td>
  </tr>
</table>

---

## What's Built

### Appointment Book
- Interactive drag-and-drop grid with multi-provider columns
- Multi-service appointments (appointment = container, items = individual services per provider)
- Colour-development gap rendering — processing time appears as free blocks on the grid so providers can take other clients
- Scheduled time blocks (lunch, training, closures) — moveable and resizable
- Full status flow: requested → confirmed → in-progress → completed / cancelled
- Conflict detection across all providers

### Guest Booking & Staff Workflow
- Public booking request form on salonlyol.ca — no account required for guests
- Staff review, adjust, and confirm requests; clients do not self-book (deliberate quality control)
- Branded confirmation emails — staff-authored, never automatic
- Instant email notification to staff when a new request arrives

### POS & Checkout
- Checkout panel on any in-progress appointment
- Group checkout — multiple same-day appointments in a single transaction (common for families)
- Tenant-configured payment methods (cash, card, e-transfer, and others)
- Split payment across multiple methods in a single transaction
- Ontario GST (5%) + PST (8%) tracked per sale, with per-item tax flags for retail
- Cashback flow: tips are returned to the client as change and never touch salon revenue — correct for how the salon actually operates, and required for honest cash reconciliation
- Tenant-defined promotions — percent or fixed-amount discounts applied per line at checkout
- Sale summary on completed appointments with payment breakdown
- Edit completed sale payments (same-day correction with full audit log)

### Retail & Inventory
- Retail product catalog (SKU, price, cost, tax flags) with full CRUD
- Retail items available at checkout alongside services
- Stock ledger: receive, sell, adjust, and return movements per item
- On-hand count displayed in the catalog; sold at checkout automatically decremented
- Adjustment flow: staff enters a physical count and the delta is computed and recorded with a reason

### Sales Reporting & Cash Reconciliation
- Monthly sales report covering revenue, discounts, taxes, and payment-type breakdown (similar to the legacy Milano report)
- End-of-day cash till: open/close periods, petty cash entries, expected vs. counted variance, 30-day history

### Client CRM
- Full client profile: contact details, pronouns, colour formulas, service notes, general notes
- Complete appointment history with start times, providers, and prices
- No-show and late-cancellation counts
- Slide-over panel accessible directly from any appointment on the grid — no page navigation

### Service Catalog
- Full CRUD for categories, services, per-provider pricing, and duration overrides
- Processing-offset and processing-duration fields drive the grid's gap rendering
- Gender-free haircut classification (Type 1 / Type 2 / Type 2+) — pricing based on effort and expertise, not client gender

### Notifications & Email
- Staff-authored appointment confirmation emails with branded layout
- Appointment reminder emails — configurable lead time (2 h to 3 days), dispatched via Cloud Scheduler
- New booking request notifications to configurable salon recipients
- Rich-text WYSIWYG body editor for confirmation emails (Tiptap)
- Fully branded email layout: salon logo, brand colour, address, and footer on all outbound email

### Multi-Provider Staff Management
- Provider types: Stylist, Colourist, Dualist (can deliver both)
- Default weekly schedules with versioned effective dates — past schedules are locked
- Per-date exceptions for individual days
- Tenant-configurable salon operating hours (drives the appointment grid)

### Settings & Branding
- Tenant logo, brand colour, address, phone — applied to the app header and all outbound emails
- Configurable appointment slot granularity and operating hours
- User management: add, edit role, deactivate, and hard-delete staff and guest accounts
- Email settings: SMTP or Resend API, new-request notifications, appointment reminders

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **1** | Appointment book · Client management · Guest booking · Staff schedules | ✅ Complete |
| **2** | POS & checkout · Notifications · Sales reporting · Retail catalog · Inventory · Data import | 🔄 Nearly complete |
| **3** | Multi-tenancy hardening · Beta salon onboarding | Planned |
| **4** | AI-integrated CRM (email, chat, voice) · Advanced analytics | Planned |

**Phase 2 remaining:** bulk data import from Milano (clients, appointments, services, staff).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API** | Python · FastAPI · SQLAlchemy 2 (async) · Alembic |
| **Database** | PostgreSQL 16 |
| **Frontend** | TypeScript · React · Vite · Tailwind CSS · shadcn/ui |
| **Cloud** | GCP Cloud Run · Cloud SQL · Cloud Storage · Secret Manager · Artifact Registry |
| **Infrastructure** | Terraform |
| **CI/CD** | GitHub Actions — build, push, and deploy to Cloud Run on every push to `main` |
| **Auth** | JWT with refresh tokens · bcrypt |

---

## Architecture

Two Cloud Run services (API + frontend) backed by Cloud SQL PostgreSQL. Secrets are injected via Secret Manager — no plaintext in containers or environment files. The API runs Alembic migrations automatically on startup, so every deploy is schema-current.

```
Guest (salonlyol.ca)          Staff browser
         │                          │
         └──────────┬───────────────┘
                    ▼
             Cloud Run
          salon-frontend (Nginx + React SPA)
                    │
                    ▼
             Cloud Run
          salon-api (FastAPI / uvicorn)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    Cloud SQL   Cloud        Secret
    Postgres   Storage      Manager
```

The frontend is a single-page app served from Nginx; all data flows through the FastAPI backend. The public booking form and staff application share the same API — access is scoped by JWT role.

---

## How This Is Built: Spec-Driven Development with Claude Code

Every feature starts as a written specification — not a ticket, a *spec*: the data model, API contract, business rules, and UX behaviour are fully described in [`docs/backlog.md`](docs/backlog.md) and [`docs/specs/`](docs/specs/) before a line of code is written.

Architecture decisions are recorded as [ADRs](docs/adr/) — short documents capturing the context, decision, and trade-offs for each major choice (cloud target, web framework, database/ORM, frontend approach).

[`CLAUDE.md`](CLAUDE.md) is the project's persistent brain — domain model, design principles, current state, and working agreements in one place. Claude Code reads it at the start of every session and operates on the codebase from that grounded context.

This workflow enables a solo developer to build at a pace and quality level that would normally require a team: the specification *is* the implementation plan, and the AI partner executes against it with full context and no re-explanation between sessions.

---

## Local Development

**Prerequisites:** Docker, Python 3.12+, Node 20+, [`uv`](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/freddy6ix/salon-mgmt-app.git
cd salon-mgmt-app

# Start local PostgreSQL
docker-compose up -d

# Backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# API at http://localhost:8000  (OpenAPI docs at /docs)

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

---

## Beta Access

Salon Lyol is the first production user. If you run a salon and are interested in early access, or you're an investor, reach out:

**freddy@meshentics.com** · **[salonlyol.ca](https://salonlyol.ca)**

---

*Built with [Claude Code](https://claude.ai/code)*
