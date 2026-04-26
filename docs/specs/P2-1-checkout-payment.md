# P2-1 — Checkout and Payment

> Status: in development. This spec is the source of truth for v1. Behavior changes require updating this document first.

## Goal

Staff check out a client at the end of their visit, record what was sold, apply a tip, and split the payment across one or more payment types. Completing checkout finalizes the appointment and creates the records needed for the Daily Sales Report (P2-5).

## Scope (v1)

In scope:
- Checkout from an `in_progress` appointment
- Service items pulled from the appointment, with editable price + per-line discount
- Tip as a single sale-level amount
- GST 5% + PST 8% on the discounted subtotal (services taxable)
- Multi-type payment split (cash, debit, credit cards, e-transfer)
- On submit: appointment → `completed`, Sale + SaleItems + Payments persisted

Out of scope (deferred):
- Walk-in retail (no appointment)
- Gift certificate / series sale or redemption
- On-account charges
- Voids / refunds
- Tip allocation per provider
- Promotion codes / manager overrides
- Card processor integration (Stripe Terminal, Square, etc.) — payment is recorded manually
- Tenant-configurable tax rates
- Print receipts (on-screen confirmation only)

## Data model

```
Sale
├── id, tenant_id
├── appointment_id           FK → appointments.id, UNIQUE (one Sale per Appointment)
├── client_id                FK → clients.id (denormalized for reporting)
├── subtotal                 NUMERIC(10,2)   sum of line totals before tax/tip
├── discount_total           NUMERIC(10,2)   sum of per-line discounts (informational)
├── gst_amount               NUMERIC(10,2)   subtotal × 0.05
├── pst_amount               NUMERIC(10,2)   subtotal × 0.08
├── tip_amount               NUMERIC(10,2)   sale-level tip (default 0)
├── total                    NUMERIC(10,2)   subtotal + gst + pst + tip
├── status                   ENUM (pending, completed)
├── completed_at             TIMESTAMPTZ
├── completed_by_user_id     FK → users.id
├── notes                    TEXT NULL
└── created_at, updated_at

SaleItem
├── id, tenant_id, sale_id   FK → sales.id
├── appointment_item_id      FK → appointment_items.id, NULL (for v2 retail)
├── description              TEXT (snapshot of service name)
├── provider_id              FK → providers.id (snapshot for tip/payroll attribution)
├── sequence                 INT
├── unit_price               NUMERIC(10,2)
├── discount_amount          NUMERIC(10,2) DEFAULT 0
├── line_total               NUMERIC(10,2)  = unit_price - discount_amount
└── created_at

Payment
├── id, tenant_id, sale_id   FK → sales.id
├── payment_type             ENUM (amex, cash, debit, e_transfer, mastercard, visa)
├── amount                   NUMERIC(10,2)
└── created_at
```

**Snapshot strategy:** `description` and `provider_id` on `SaleItem` are intentionally denormalized snapshots — service names, provider display names, and prices may change later, but the historical record of what was sold must be stable.

## Rules

Each rule is a candidate test case.

### Sale lifecycle
- **R1** — A Sale can only be created for an appointment in status `in_progress`. Other statuses → 422.
- **R2** — At most one `completed` Sale per Appointment. Attempting a second → 409.
- **R3** — Submitting a Sale transitions the Appointment to `completed` atomically (single transaction).
- **R4** — A Sale row is created in `completed` status — there's no draft persistence in v1.
- **R5** — Past-date guard does **not** apply to checkout. Same-day appointments that ran late and need to be checked out the next morning must still be checkoutable. (Past-date guard applies to *editing* the appointment, not finalizing it.)

### Items
- **R6** — A Sale must have at least one SaleItem.
- **R7** — Each SaleItem corresponds to exactly one AppointmentItem in v1 (`appointment_item_id` non-null).
- **R8** — All AppointmentItems on the Appointment must be represented in the Sale (no skipping).
- **R9** — `unit_price` may be edited from the AppointmentItem's price at checkout (e.g., manager discretion).
- **R10** — `discount_amount` ≥ 0 and ≤ `unit_price`. Zero is the default.
- **R11** — `line_total` = `unit_price` - `discount_amount`. Computed server-side; client-supplied values ignored.

### Tax + tip
- **R12** — `gst_amount` = round(`subtotal` × 0.05, 2). Banker's rounding not required; use standard half-up.
- **R13** — `pst_amount` = round(`subtotal` × 0.08, 2).
- **R14** — Tip is **post-tax** and not taxed. (Standard Canadian salon practice.)
- **R15** — `tip_amount` ≥ 0. No upper bound.
- **R16** — `total` = `subtotal` + `gst_amount` + `pst_amount` + `tip_amount`.

### Payment
- **R17** — A Sale must have at least one Payment row.
- **R18** — Sum of Payment.amount must equal Sale.total exactly. Mismatch → 422.
- **R19** — Each Payment.amount > 0.
- **R20** — Multiple Payments with the same `payment_type` are allowed (e.g., two cash payments) but discouraged in UI — the form merges them.

### Reporting (forward-looking)
- **R21** — All amounts persist as `NUMERIC(10,2)` (postgres `Decimal`), never `FLOAT`.
- **R22** — `completed_at` is the timestamp used for daily reports. Sales created on day D but completed at 12:01 AM on D+1 belong to D+1.

## API

### POST /sales

Create and complete a Sale for an appointment in one call (no draft state in v1).

```json
{
  "appointment_id": "uuid",
  "tip_amount": "0.00",
  "notes": "string | null",
  "items": [
    {
      "appointment_item_id": "uuid",
      "unit_price": "65.00",
      "discount_amount": "0.00"
    }
  ],
  "payments": [
    { "payment_type": "visa", "amount": "73.45" }
  ]
}
```

Response: full Sale with computed totals.

Errors:
- 422 if appointment not `in_progress` (R1)
- 409 if a completed Sale already exists for the appointment (R2)
- 422 if items missing or partial (R6, R8)
- 422 if payments don't sum to total (R18)

### GET /sales/by-appointment/{appointment_id}

Returns existing completed Sale for an appointment, or 404. Used by the UI to show a read-only receipt view if checkout already happened.

## UX

### Trigger
The "Check out" button on `in_progress` appointments in the right-side `AppointmentDetail` panel opens the **Checkout panel** — a separate right-side panel that overlays on top of the AppointmentDetail (similar pattern to the Convert Request panel over the appointment book).

### Checkout panel layout (top-to-bottom)

1. **Header**: Client name + appointment date, close X
2. **Items list** — one row per AppointmentItem:
   - Service name + provider (read-only)
   - Editable `unit_price` (text input, decimal)
   - Editable `discount_amount` (text input, decimal, default 0)
   - Computed `line_total` (read-only)
3. **Tip** — single decimal input, default 0
4. **Totals breakdown** (read-only, live-computed):
   - Subtotal
   - Discount total (if > 0)
   - GST (5%)
   - PST (8%)
   - Tip (if > 0)
   - **Total** (bold)
5. **Payments** — list of `(payment_type, amount)` rows; "+ Add payment" button to add another row. Default v1: one row, type `cash`, amount = total.
6. **Remaining** indicator: "$0.00 remaining" or "$X.XX over/under" — Submit disabled until 0.
7. **Notes** — optional text area
8. **Submit** — "Complete checkout" button. On success, closes both panels and updates the appointment block on the grid.

### Validation surfaces in the UI
- Per-line: discount > price → red border + inline message
- Totals: payments don't match total → red "Remaining: $X" message
- Submit error from server: red banner at bottom of panel

## Open questions / future

- **Q1** — Should we let staff edit a Sale after submission (correct a mis-typed amount within N hours)? Today: no. Future: a small admin-only edit window or void-and-redo flow.
- **Q2** — Do we need a "no-charge" flow (free service for friends/family)? Today: discount each line to 0, complete with a $0 cash payment.
- **Q3** — Should the AppointmentDetail show "Sale: $X.XX, Cash $Y / Visa $Z" on completed appointments? Yes, eventually — out of scope for the first cut but easy follow-up using the GET endpoint.

## Acceptance test list

For backend (informal — would be pytest cases when test infrastructure is set up):

- T1: POST /sales for confirmed appointment → 422
- T2: POST /sales for completed appointment → 409
- T3: POST /sales with subset of items → 422
- T4: POST /sales with payments < total → 422
- T5: POST /sales with payments > total → 422
- T6: POST /sales happy path → 201, sale + items + payments persisted, appointment status = completed
- T7: GST/PST computed correctly: $100 subtotal → $5.00 GST, $8.00 PST
- T8: Tip is excluded from tax base
- T9: Discount reduces line total and subtotal
- T10: Second POST /sales for same appointment → 409
