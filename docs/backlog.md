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

### P1-8 · Show service times in client Appointments tab

The Appointments tab on the client profile (Clients page) shows each service with the date but not the specific start time. Add the start time to each service line so staff can see exactly when each service is/was scheduled.

- Frontend only: update `VisitHistory` in `ClientsPage.tsx` to include the `start_time` from each visit item
- Requires the backend `/clients/{id}/history` endpoint to return `start_time` per item (currently only returns `service_name`, `provider_name`, `price`)
- Backend: add `start_time: str` to the `VisitItem` model in `clients.py` and populate it from `AppointmentItem.start_time`
- Frontend: display formatted time (e.g. "9:00 AM") alongside service name and provider on each item row

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

### P2-6 · Show sale summary on completed appointment

Follow-up to P2-1 (deferred Q3 from `docs/specs/P2-1-checkout-payment.md`). When viewing a completed appointment in `AppointmentDetail`, show the recorded sale: totals (subtotal, GST, PST, tip, total) and the payment breakdown (e.g., "Cash $40 · Visa $33.45").

- Frontend only (backend `GET /sales/by-appointment/{id}` already exists)
- Fetch the sale when the appointment status is `completed`; render under the existing "Checked out" indicator
- Read-only view in v1 (editing/voiding deferred — see P2-1 spec Q1)

### P2-7 · Edit a completed sale (correct payment methods / splits)

Staff sometimes record the wrong payment method or a bad split (e.g., charged $50 to Visa when it was actually Mastercard). They need to correct the receipt without voiding and re-creating the sale.

- Scope of editable fields in v1: payment lines only — `payment_method`, `amount`, add/remove split lines. Total, items, prices, taxes are **not** editable here (those are voids/refunds, separate concern).
- Server-side rule: edited payments must still sum to the existing sale total (no change to totals).
- Audit trail: every edit writes a `SalePaymentEdit` record (who, when, before → after JSON snapshot). Original is preserved for reporting integrity.
- Constraint: editable while the sale is on the same business day; older sales become read-only and require a void+redo (see future void/refund work). Tenant-configurable cutoff acceptable in v2.
- Backend: `PATCH /sales/{id}/payments` — accepts the new payment list, validates total, writes edit log, replaces payment rows in a transaction.
- Frontend: "Edit payments" action on the sale summary (P2-6); reuses payment selector from CheckoutPanel.

### P2-8 · End-of-day cash reconciliation

Cash is the one payment method that has to physically match a count at the end of the day. Staff need a flow that tracks the running cash position and supports a daily till count with variance.

**Core model:**
- A `CashReconciliation` record per tenant per business day, with: `opening_balance` (from previous close), `expected_cash`, `counted_cash`, `variance`, `deposit_amount`, `notes`, `closed_by_user_id`, `closed_at`.
- "Expected cash" = previous closing balance + (cash payments since) − (cash refunds since) − (deposits since) ± (petty cash adjustments).
- Petty cash entries (small in/out, e.g. coffee for staff, tip-out) recorded as `PettyCashEntry` rows tagged with the active reconciliation period.

**Flow:**
1. Staff opens the reconciliation page; app shows previous closing balance and cash movements since.
2. Staff records actual counted cash + any deposit going to the bank.
3. App computes variance and prompts for a note if non-zero.
4. Closing the reconciliation locks all cash payments and petty-cash entries in that period — they can no longer be edited (protects audit trail).
5. The closing balance becomes the next day's opening.

**Why this matters:** without this, the P2-5 sales report can compute "cash sales" but no one can confirm the till matches. This is the linchpin of cash control and Milano had it.

**Depends on:**
- P2-5 (monthly sales report) — shares the reconciliation period model and petty cash semantics.
- "Cash" payment method needs to be identifiable across tenant-defined payment methods (use `kind = 'cash'` on the `TenantPaymentMethod` row).

### P2-9 · Tip-as-cashback flow (tips are not salon revenue)

P2-1 currently models tip as part of the sale (`Sale.tip_amount`, included in `total`, payments must cover it). That's the conventional POS model but it's **wrong for Salon Lyol's actual workflow**:

- Client owes the bill amount (subtotal + tax). They tender extra cash.
- Cashier returns the overage as **cashback to the client**.
- The client physically hands that cash to the staff member as a tip.
- The tip **never touches the salon's books** — not counted as revenue, not in the cash drawer's net intake.

**What needs to change:**

1. **Sale model:** drop `tip_amount` from the sale record (or keep as a non-revenue informational field flagged "not revenue"). Sale total = subtotal − discount + GST + PST. No tip.
2. **CheckoutPanel UI:** replace the "Tip ($)" input with an **"Amount tendered" → "Change due"** pattern, like a real till. Cashier types what the client handed over (cash); UI computes change. The change goes back to the client (who may or may not pass it to staff — none of the salon's business). For card payments, this whole concept doesn't apply — card runs for bill amount only.
3. **Cash drawer math:** for a cash sale, drawer goes up by the **bill amount**, not the tendered amount. The recorded `Payment.amount` stays equal to the bill, which keeps the till tally (P2-8) honest.
4. **Tip tracking for staff:** if the salon ever wants to track tips per stylist (for tax/reporting reasons stylists might need), that's a separate side ledger keyed by appointment_item but explicitly outside the sale total. Out of scope for v1; flag for later.

**Why this matters:** treating tips as sale revenue inflates GST/PST liability (since taxes are computed on `subtotal`, but if tips were ever rolled into total they'd distort cash totals), distorts payroll-to-revenue ratios, and breaks cash reconciliation (P2-8). Get the model right before more code piles on top.

**Depends on:** revisits P2-1 (`Sale.tip_amount`, `CheckoutPanel`, `POST /sales` total computation). Should land before P2-8 since reconciliation math assumes recorded cash payments equal the cash actually retained.

### P2-10 · Tenant-defined promotions (per-service discount)

Salons run their own promotions — "Senior Tuesday", "First-time colour", "Stylist's birthday week". Promotions are configured by an admin and applied at checkout to **individual service lines**, not to the sale as a whole.

**Promotion types (v1):**
- **Percent** — e.g., 10% off the line's `unit_price`.
- **Fixed amount** — e.g., $5 off the line, regardless of price.

**Data model:**
- `TenantPromotion` table per tenant: `code`, `label`, `kind` (`percent` | `amount`), `value` (numeric — interpreted as percent or dollars based on `kind`), `is_active`, `sort_order`. Optional fields for v2: `start_date`/`end_date` for time-bounded campaigns, `service_filter` to restrict eligibility.
- `SaleItem` already has `discount_amount`; add a nullable `promotion_id` FK so reporting (P2-5 "Less Discounts" line) can attribute the discount source.

**Checkout UX:**
- Each item line gets a "Apply promotion" picker showing active promotions.
- Selecting one populates `discount_amount` server-side based on the promotion's `kind` and `value`. Staff can still type a manual discount instead — promotion picker and manual entry are alternatives, not stacked.
- The line shows the promotion label next to the discount amount so it's auditable later.

**Settings UX:** "Promotions" tab (admin), parallel to "Payment methods". Same row pattern: label, code, kind, value, active toggle.

**Out of scope for v1:** stacking multiple promotions, customer-facing codes for guest entry, threshold-based promos ("$10 off any service over $100"), per-service eligibility filters.

### P2-11 · Pay for multiple appointments together (group checkout)

Common case: a parent/guardian arrives with one or more children, each booked into separate appointments (different providers, different services, different times). The parent expects one transaction at the end, not three.

**What needs to change:**

The current model assumes one sale per appointment (`uq_sale_appointment` constraint on `sales.appointment_id`). That has to give. Cleanest approach: replace `Sale.appointment_id` with a `sale_appointments` junction (`sale_id`, `appointment_id`, unique on `(tenant_id, appointment_id)` so each appointment still has at most one sale).

Sale items already reference `appointment_item_id` — they naturally span multiple appointments under a junction model. Reporting still attributes each item to its own provider; nothing changes downstream.

**Eligibility rules (v1):**
- All grouped appointments must be **same tenant, same business day, status `in_progress`**.
- No restriction on payer identity — staff judgment, no enforced "same family" linkage. (If the salon ever wants to track household for marketing, that's `ClientHousehold` work, separate.)

**Checkout UX:**
1. Staff initiates checkout from any one of the appointments.
2. The CheckoutPanel shows a "+ Add appointment to this sale" affordance listing other in-progress same-day appointments.
3. Staff picks which to include; line items merge into one cart.
4. Single payment covers everything; on success, **all** linked appointments transition to `completed` atomically (preserves the P2-1 R3 atomicity rule, just over a set instead of one).

**Reporting impact:** P2-5 needs to count each appointment-item once (not multiply across grouped appointments). The junction model makes this natural — items are already 1:1 with appointment_items.

**Depends on:** revisits P2-1 (the `appointment_id` FK on `Sale` and the unique constraint). Pre-UAT lifecycle means we drop the column and add the junction in a single migration with no backfill drama.

### P2-12 · Retail items (catalog + checkout integration)

Salons sell product (shampoo, styling product, tools) alongside services. Today the system has no concept of retail. Adds the retail catalog and lets staff add retail lines to a sale at checkout.

**Data model:**
- `RetailItem` (per tenant): `sku` (optional), `name`, `description`, `category_id` (nullable, links to a new `RetailCategory` table), `default_price`, `default_cost`, `is_gst_exempt`, `is_pst_exempt`, `is_active`. Stock fields live in P2-13, not here — keep this entity catalog-only.
- `SaleItem` needs a kind discriminator (`service` | `retail`) and a nullable `retail_item_id` alongside the existing `appointment_item_id`. Exactly one of the two FKs is set per row. The existing `description`/`unit_price`/`discount_amount`/`line_total` columns work for both kinds.

**UX:**
- Top-level "Retail" nav entry — admin-managed list + edit (matches the data/config pattern: this is data, not settings).
- CheckoutPanel: a "+ Add retail item" affordance (separate from service items) opens a picker; selecting one creates a SaleItem with kind=retail, defaults from the catalog, editable price/discount inline.

**Tax handling:** retail typically has different tax treatment than services (e.g. PST applies to retail in Ontario but not to most services). The per-item `is_gst_exempt`/`is_pst_exempt` flags carry over to checkout — sale total computation uses each line's flags rather than a flat tenant rate.

### P2-13 · Inventory management

Stock tracking on retail items so staff know what's on hand and the till deducts on sale. Builds on P2-12.

**Data model:**
- `RetailStockMovement`: per-tenant ledger keyed by `retail_item_id`. Each row has `kind` (`receive` | `sell` | `adjust` | `return`), `quantity` (positive integer), `unit_cost` (nullable, populated on receive/adjust), `sale_item_id` (nullable, set when kind=sell or return), `note`, `created_by_user_id`, `created_at`.
- Current stock = sum of signed quantities (receive +, sell −, adjust ±, return +). Compute on read; no denormalised "on_hand" column in v1 (avoid drift).

**Hooks:**
- Checkout completion: on a successful sale containing retail lines, write `kind=sell` movements atomically with the sale.
- Edit/void of a retail sale (P2-7 territory): inverse movement so stock stays consistent.
- Manual receive/adjust UI: simple form on the retail item detail page — receive a shipment (qty + unit cost), adjust to a counted number with a reason.

**Out of scope for v1:** reorder points, low-stock alerts, supplier records, purchase orders. Those are v2 once the basic ledger is trusted.

### P2-14 · Services management (top-level page)

Backend already has `Service`, `ServiceCategory`, and `ProviderServicePrice` — including processing-offset and processing-duration columns for colour-development gap time. What's missing is the staff UI: today only `GET /services` exists, so adding/editing a service requires a developer to touch the database. Blocks salon self-sufficiency before UAT.

**Backend additions:**
- `POST /services`, `PATCH /services/{id}`, `DELETE /services/{id}` (soft via `is_active=false`).
- `POST /service-categories`, `PATCH /service-categories/{id}`, `DELETE /service-categories/{id}`.
- `GET/POST/PATCH/DELETE /provider-service-prices` for the capability + per-provider override matrix. (May exist partially — verify.)

**Frontend (top-level "Services" nav entry):**
- Service catalog grouped by category: list view with name, default price, default duration, active toggle.
- Edit form covering all the fields the data model exposes: code, name, description, category, default price/cost, duration, processing offset + duration, haircut type (when relevant), pricing type (fixed/hourly), tax flags, addon flag, suggestions/notes.
- Inside the service edit view: provider matrix — which providers offer this service, with optional per-provider price + duration overrides. Adds rows to `ProviderServicePrice`.

**Out of scope for v1:** tier-based pricing across providers, time-bounded `effective_from`/`effective_to` on prices (column exists; UI defers it), service photos, online booking eligibility flags.

**Why this is the natural next step:** services are the catalogue the entire appointment book operates on. Without staff CRUD, every catalogue change is a developer task. P2-12 (Retail) reuses the same UI conventions, so building Services first establishes the pattern.

### P2-15 · Tenant time format (12h / 24h)

Each tenant chooses whether the app displays times in 12-hour (`6:00 PM`) or 24-hour (`18:00`) format. Affects every place a time is rendered: appointment book grid, appointment detail, sale summary, requests, settings, staff schedules, etc. Inputs (`<input type="time">`) honour the same setting where the browser allows it.

- `tenants.time_format`: `"12h" | "24h"`, default `"12h"`.
- Backend: expose on `GET /settings/branding` and accept on `PATCH /settings/branding`.
- Frontend: shared `formatTime(hhmm: string)` helper reading the tenant setting; replace ad-hoc `HH:mm` formatting throughout.
- Setting lives under Settings → Scheduling alongside slot granularity and operating hours.
- Display rule when 12h is active: drop leading zeros on the hour (e.g. `6:00 PM`, not `06:00 PM`).

### P2-16 · Branded email layout

All outbound emails (confirmations, welcome, password reset, future reminders) currently render as plain HTML with no consistent chrome. Wrap them in a tenant-branded layout that uses the same logo and brand colour set under Settings → Branding (P1-6).

**Shared layout (a single `app/email_layout.py` helper):**
- Header: tenant logo (`tenant.logo_url`) on a brand-coloured band, with the salon name as alt text fallback when no logo is set.
- Body slot: rendered content (existing template HTML).
- Footer: salon name + address + a small "If you weren't expecting this email…" line.
- Inline CSS only (Gmail/Outlook compatibility); brass/brand colour pulled from `tenant.brand_color`; web-safe fallback fonts; readable text colour computed from brand colour luminance (white text on dark brands, near-black on light).
- Fixed max-width container (~600px) with light cream background, mirroring the in-app aesthetic.

**Wire-up:**
- `email.py` gains a `wrap_branded(html, tenant)` helper. `send_email` callers pass the tenant (or a small `BrandingContext`) so the wrapper can inject the chrome.
- Confirmation, welcome, and password-reset templates collapse to the inner body only; the outer chrome lives in the layout.
- Settings → Email tab gains a "Send sample" button (in addition to the existing test) that previews the branded layout with a placeholder body.

**Out of scope for v1:** custom email header images per tenant, per-email-type logo overrides, dark-mode-aware emails, plain-text alternative parts (we already only send HTML).

**Depends on:** P1-6 branding (already shipped — logo URL + brand colour live on `tenants`).

### P2-17 · Rich-text email body editor

The P2-2 confirmation dialog (and any future tenant-facing email composer) currently shows the body as a read-only rendered preview. Staff don't write HTML — they need a WYSIWYG that produces email-safe HTML they can edit comfortably.

**Scope:**
- A small WYSIWYG component (Tiptap or Lexical) with a minimal toolbar: bold, italic, underline, link, bullet list, paragraph break. No headings, no images in v1 — kept tight on purpose so output stays email-client-safe.
- Output sanitized to a constrained allowlist of inline tags + attributes before persisting (`<p>`, `<strong>`, `<em>`, `<u>`, `<a href>`, `<ul>`, `<ol>`, `<li>`, `<br>`).
- Replaces the preview block in `ConfirmationDialog`; subject input stays as-is.
- Initial value comes from the existing default template (or saved draft).
- Save / Send still post the resulting HTML to the existing endpoints — no schema change.

**Out of scope for v1:** images, inline styles, custom fonts, source-HTML toggle, merge-tag insertion (e.g. `{{client.first_name}}`). Those land alongside tenant-customizable templates if/when that feature ships.

**Depends on:** P2-2 (already shipped — endpoints accept arbitrary HTML body).

### P2-18 · Tenant contact details (address, phone, hours)

`tenants` currently has `name`, `logo_url`, `brand_color`. It's missing the contact info needed to render a real footer on emails (P2-16 omits address for v1) and a public-facing "how to reach us" section on the landing page (which currently hardcodes "1452 Yonge Street").

**Schema additions on `tenants`:**
- `address_line1`, `address_line2`, `city`, `region`, `postal_code`, `country` — stored as discrete fields, not a free-text blob, so we can format per locale and link to maps.
- `phone` (E.164 string).
- `hours_summary` — a short human string like "Tue–Sat · 9–6", because per-day hours already live on `TenantOperatingHours` and don't need a second source of truth. Just a display caption.

**Wire-up:**
- Settings → Branding form gets a "Contact" section (address fields + phone + hours summary).
- Landing page reads from the tenant API (no more hardcoded address).
- Email footer (P2-16 layout) gains an address line + phone when set; falls back to name-only when blank.

**Out of scope for v1:** geo-coding, multiple locations per tenant, opening-hours overrides for holidays.
