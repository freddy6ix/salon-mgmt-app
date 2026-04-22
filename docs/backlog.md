# Product Backlog

> Prioritized list of work items. Phase 1 items are in scope now; Phase 2 items are next after the core appointment book is production-ready.

---

## Phase 1 — Core Appointment Book

### P1-0 · App shell and home dashboard

Replace the current pattern (login → straight to appointment book) with a proper app shell that persists across all staff pages.

**Shell layout:**
- Collapsible left sidebar (or persistent top nav on mobile) with nav links
- Nav items: Appointment Book · Clients · Requests · Staff · Reports · Settings
- Active route highlighted; salon name / logo in header
- "Sign out" moved into the shell (removed from individual pages)

**Home dashboard (`/home` or `/`):**
After login, staff land on a simple dashboard showing:
- Today's appointment count (per provider)
- Pending booking requests (count + quick link)
- Quick-action buttons: "+ New Appointment", "View today's book"

**What changes:**
- New `AppShell` layout component wrapping all staff routes
- New `DashboardPage` as the post-login landing
- `App.tsx`: staff root redirects to `/home` (dashboard); appointment book moves to `/appointments`; requests to `/requests`; staff settings to `/settings/staff`
- Remove the header + sign-out button from `AppointmentBookPage` (shell handles it)
- `RequireStaff` wraps the shell, not individual routes

### P1-1 · Convert request → appointment
Staff review an incoming booking request and convert it into a confirmed appointment, mapping each requested service/provider to real catalog entries and setting the confirmed time slot.

- Backend: `POST /appointment-requests/{id}/convert` — creates `Client` (or links existing), creates `Appointment` + `AppointmentItem`(s), marks request as `converted`
- Frontend: "Convert to appointment" action in `RequestsPage` — dialog to map items to real services/providers and pick a time; navigates to appointment book on success

### P1-2 · Provider schedule versioning and historical locking

Default weekly schedules already exist in the data model, but the current implementation overwrites history when a schedule changes. This item makes the schedule system behave correctly.

**Desired behaviour:**
- Each provider has a default schedule per weekday (working/off, start time, end time)
- Changing the default schedule applies from a specified future date (default: today) forward — past dates are unaffected
- Staff can still override any individual future date via a per-date exception (already implemented via `ProviderScheduleException`)
- Past schedules and past exceptions are read-only — no editing historical records

**What needs to change:**

Backend:
- `PUT /schedules/weekly/{provider_id}`: accept an optional `effective_from` date (default: today). Instead of deleting and reinserting EPOCH rows, close the current active schedule rows (`effective_to = effective_from - 1 day`) and insert new rows with the given `effective_from`. Historical EPOCH rows are preserved.
- `POST /schedules` (per-date exception): reject requests where `exception_date` is in the past

Frontend (`StaffSchedulePage`):
- Add an "Effective from" date picker (default: today) that travels with the Save button
- Show a note: "Changes apply from [date] · historical schedules are locked"
- The per-date override on the appointment book grid already blocks past dates (the WhoIsWorking toggle) — add the same guard

No schema migration required — `ProviderSchedule.effective_from` and `effective_to` already exist.

### P1-3 · Client card

View a client's full profile directly from the appointment book — without leaving the grid.

- Contact information (name, email, phone, pronouns)
- Upcoming appointments
- Past appointments (with services, providers, prices)
- Colour formula / service notes (free-text, per-client, versioned by date)
- No-show and cancellation history (count + dates)
- General notes (free-text, staff-visible)

Accessible by clicking the client name on any appointment block on the grid. Opens as a slide-over panel (not a full page navigation).

### P1-4 · Add / remove services on an appointment
From the appointment book, staff can add new `AppointmentItem`(s) to an existing appointment, or remove items that are no longer happening — without having to delete and recreate the whole appointment.

- Add: opens the booking form pre-scoped to the existing appointment's client and date
- Remove: confirmation prompt then soft-delete (status → `cancelled`) on the item

### P1-5 · Creative login / landing page
Replace the plain login page with a branded, visually engaging entry point appropriate for a premium Toronto salon. Should work well as the public-facing first impression for guests arriving to submit a booking request.

### P1-7 · Delete client

Staff can soft-delete (deactivate) a client record from the Clients page. A deleted client's history is preserved for reporting but they no longer appear in search results or the client list.

- Backend: `DELETE /clients/{id}` — sets `is_active = False` on the `Client` record (soft delete); returns 204
- Frontend: "Delete client" action in the client detail panel; confirmation dialog before proceeding; removes client from the list on success
- Guard: prevent deletion if the client has any upcoming (confirmed / in-progress) appointments — return a 409 with a clear message

### P1-6 · Branding configuration
Salon owners can upload a logo and set basic brand colours. Logo appears in the app header, on the login/landing page, and in outbound emails.

- `TenantSettings` entity (or extend `Tenant`): `logo_url`, `primary_colour`, `salon_name_display`
- Logo stored in Cloud Storage
- Settings page (staff/admin only)

---

## Phase 2 — POS, Notifications, and Reporting

### P2-1 · Checkout and payment
Staff check out a client at the end of their visit and record payment.

- `Sale` + `SaleItem` entities (per the ERM in `docs/reports/reports-annotations.md`)
- Payment types: AMEX, CASH, DEBIT, E-TRANSFER, MASTERCARD, VISA
- Split payment across multiple types
- Discounts (manual override or promotion code)
- GST and PST tracked per sale (Ontario: 5% + 8%)
- Checkout initiated from the appointment block on the grid or from client card

### P2-2 · Appointment confirmation notification
When a booking request is converted to a confirmed appointment, automatically send the client a confirmation via email and/or SMS.

- Message includes: date, time, provider(s), services, salon address, cancellation policy
- Channel (email / SMS / both) configurable per tenant
- Triggered by the convert endpoint (P1-1)

### P2-3 · Appointment reminder notifications
Send the client a reminder before their appointment. Lead time is configurable (e.g., 24 h, 48 h, or a custom number of hours before the appointment start).

- `AppointmentReminder` entity already exists in the schema
- Background job (Cloud Run Job or Cloud Tasks) to evaluate and dispatch pending reminders
- Channel (email / SMS / both) configurable per tenant
- Per-appointment opt-out

### P2-4 · New booking request notification to salon
When a guest submits a booking request via the public form, notify the salon staff by email.

- Notification email includes: guest name, requested date/time, services requested, special notes
- On/off toggle in tenant settings (default: on)
- Recipient address(es) configurable in tenant settings

### P2-5 · Monthly sales report
Reproduces the "Daily Sales Report" from Milano for any configurable date range (daily, weekly, monthly).

Full spec in `docs/reports/reports-annotations.md`. Key sections:

| Section | Content |
|---------|---------|
| Revenue | Service Sales gross, Less Discounts / Returns / Voids, Total Service Sales; same for Retail |
| Gift Certificates & Series | Separate revenue lines |
| Taxes | GST and PST independently aggregated |
| On Account | Charges vs. payments, net position |
| Payment reconciliation | Breakdown by payment type (AMEX, CASH, DEBIT, E-TRANSFER, MASTERCARD, VISA) |
| Petty Cash | Reconciled into Grand Total |

- Exportable as PDF
- Key management metric: **Payroll % of Net Sales** (target: visible on report)
