# P2-8 — End-of-day Cash Reconciliation

> Status: in development.

## Goal

Track the physical cash position of the till and close it each business day with a count. Staff can see exactly how much cash should be in the drawer, count what's actually there, record a bank deposit, and flag any variance. Once closed, the period is locked — no edits to cash payments or petty-cash entries.

## Scope (v1)

In scope:
- One reconciliation per tenant per business day (`business_date`)
- Cash in = sum of completed sale payments where `payment_method.kind = 'cash'`, net of cashback
- Petty cash entries (in or out) attached to the open period
- Staff counts the till, records deposit, closes the period
- Closing locks entries and carries the closing balance forward as the next day's opening
- History view: past closed reconciliations (read-only)

Out of scope (deferred):
- Multiple tills / cash drawers
- Automated bank feed reconciliation
- Petty cash categories / chart of accounts (backlog entry in reports-annotations.md)
- Mid-day partial closes

## Data model

```
CashReconciliation
├── id, tenant_id
├── business_date             DATE, unique per tenant
├── opening_balance           NUMERIC(10,2)  — previous close's closing_balance (0 on first day)
├── cash_in                   NUMERIC(10,2)  — computed on read; never stored
├── petty_cash_net            NUMERIC(10,2)  — computed on read; sum of PettyCashEntry.amount
├── expected_balance          NUMERIC(10,2)  — opening + cash_in + petty_cash_net (computed on read)
├── counted_balance           NUMERIC(10,2) NULL  — entered by staff at close
├── deposit_amount            NUMERIC(10,2)  default 0
├── closing_balance           NUMERIC(10,2) NULL  — counted - deposit (set on close)
├── variance                  NUMERIC(10,2) NULL  — counted - expected (set on close)
├── variance_note             TEXT NULL
├── status                    ENUM (open, closed)
├── closed_by_user_id         FK → users NULL
├── closed_at                 TIMESTAMPTZ NULL
└── created_at, updated_at

PettyCashEntry
├── id, tenant_id
├── reconciliation_id         FK → cash_reconciliations.id
├── amount                    NUMERIC(10,2)  positive = into till, negative = out of till
├── description               TEXT
├── created_by_user_id        FK → users
└── created_at
```

## Rules

### Period lifecycle
- **R1** — At most one reconciliation per (tenant_id, business_date). Attempting to open a second → 409.
- **R2** — A reconciliation starts in `open` status. Only one `open` period should exist at a time per tenant.
- **R3** — Closing sets: `counted_balance` (from request), `deposit_amount` (from request), `closing_balance = counted - deposit`, `variance = counted - expected`, `closed_at`, `closed_by_user_id`, status → `closed`.
- **R4** — A closed reconciliation is fully read-only — no further changes to the record or its petty cash entries.
- **R5** — `variance_note` is required when `|variance| > 0` at close time. Backend enforces this.

### Cash in computation
- **R6** — `cash_in` = `SUM(sp.amount - sp.cashback_amount)` across `sale_payments sp` joined to `sales s` and `tenant_payment_methods pm` where `pm.kind = 'cash'`, `s.status = 'completed'`, `DATE(s.completed_at AT TIME ZONE 'America/Toronto') = business_date`, `s.tenant_id = tenant_id`.
- **R7** — Cash in is always recomputed on read — never persisted. Adding a sale after opening a period correctly reflects in the expected balance.

### Opening balance
- **R8** — When creating a new period, opening balance = previous closed period's `closing_balance`. If no prior closed period exists, opening balance defaults to 0 and staff can override on creation.

### Petty cash entries
- **R9** — Entries may only be added/deleted while the period is `open`.
- **R10** — `amount` may be positive (cash added to till, e.g. change fund) or negative (cash removed, e.g. staff supplies purchase).
- **R11** — `description` is required, non-empty.

## API

```
GET    /cash-reconciliation/current          — get today's open period, or most recent open; 404 if none
POST   /cash-reconciliation                  — open a new period for a given business_date
GET    /cash-reconciliation/{date}           — get a specific date's reconciliation (YYYY-MM-DD)
GET    /cash-reconciliation                  — list recent periods (last 30 days), admin only
POST   /cash-reconciliation/{date}/close     — close the period; sets counted/deposit/variance
POST   /cash-reconciliation/{date}/petty-cash       — add entry to open period
DELETE /cash-reconciliation/{date}/petty-cash/{id}  — delete entry from open period
```

### POST /cash-reconciliation (open a period)
```json
{ "business_date": "YYYY-MM-DD", "opening_balance": "0.00" }
```
`opening_balance` optional — if omitted, defaults to previous close's `closing_balance`.

### POST /cash-reconciliation/{date}/close
```json
{ "counted_balance": "543.25", "deposit_amount": "500.00", "variance_note": "" }
```
`variance_note` required when variance ≠ 0.

### Response shape (CashReconciliationOut)
```json
{
  "id": "uuid",
  "business_date": "2026-04-29",
  "opening_balance": "50.00",
  "cash_in": "643.25",        // computed
  "petty_cash_net": "-20.00", // computed
  "expected_balance": "673.25",
  "counted_balance": null,
  "deposit_amount": "0.00",
  "closing_balance": null,
  "variance": null,
  "variance_note": null,
  "status": "open",
  "closed_at": null,
  "petty_cash_entries": [
    { "id": "uuid", "amount": "-20.00", "description": "Coffee supplies", "created_at": "..." }
  ]
}
```

## UX — Till page (/till)

Visible to admins and staff. Appears in the nav between Reports and Settings.

### Open period view
- Header: "Till — [business_date]" + status badge (Open / Closed)
- **Cash summary card**:
  - Opening balance
  - + Cash in today (from sales, live-computed)
  - + Petty cash net (from entries below)
  - = **Expected balance** (bold)
- **Petty cash entries** — inline list + "Add entry" form (description + amount, + for in / − for out)
- **Close till** section (only for admins):
  - Counted balance input
  - Deposit amount input
  - Live variance preview = counted − expected
  - Variance note (required when variance ≠ 0)
  - "Close" button — opens confirmation, then locks the period

### History view
- List of past closed periods: date, expected, counted, variance, deposit
- Click any row to expand: full summary + petty cash entries (read-only)

### No open period
- "Open today's till" button — creates a new period with the computed opening balance; staff can override

## Acceptance tests

- T1: POST /cash-reconciliation with existing open period → 409
- T2: Cash in reflects sales completed on that business_date only (not yesterday)
- T3: Cash in uses `amount - cashback_amount` (not raw amount)
- T4: Close with counted ≠ expected and no variance_note → 422
- T5: Close with counted = expected and no variance_note → 201 (note not required)
- T6: Adding petty-cash entry to closed period → 422
- T7: Opening balance defaults to previous close's closing_balance
- T8: Closing balance = counted - deposit; variance = counted - expected
