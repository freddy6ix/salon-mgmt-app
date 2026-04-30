# Reports Reference — Daily Sales & Petty Cash

Source: Reports exported from Salon Lyol's previous salon management system.
Period covered: March 1–31, 2026.
Captured: 2026-04-20.

---

## 1. Daily Sales Report

**File:** `Daily Sales Report4.pdf`

This is the primary end-of-period financial reconciliation report. Run monthly here (could also be run daily or weekly). It is the single document that reconciles all revenue, taxes, adjustments, and payment methods for a period.

### Report Structure

#### Revenue Section

| Line | March 2026 |
|------|-----------|
| Service Sales (gross) | $58,125.00 |
| Less Discounts | -$546.25 |
| Less Returns | $0.00 |
| Less Voids | $0.00 |
| **Total Service Sales** | **$57,578.75** |
| Retail Sales (gross) | $3,555.18 |
| Less Discounts | -$727.05 |
| Less Returns | -$57.00 |
| Less Voids | $0.00 |
| **Total Retail Sales** | **$2,771.13** |
| **Total Sales Before Taxes** | **$60,349.88** |

**Note:** Discounts, Returns, and Voids are tracked separately for both Service and Retail streams. These are NOT collapsed into a single net figure — they appear as distinct adjustment lines. This means the system must record them as distinct transaction types, not just price overrides.

#### Tax Section

| Tax | Amount |
|-----|--------|
| GST | $3,017.51 |
| PST | $4,828.03 |
| **Total Taxes Collected** | **$7,845.54** |

Two separate Canadian tax types (GST = federal 5%, PST = provincial 8% in Ontario). Both are tracked and reported independently.

#### Gift Certificates & Series

| | G/C | Series |
|-|-----|--------|
| Sales | $400.00 | $0.00 |
| Less Discounts | $0.00 | $0.00 |
| Less Returns | $0.00 | $0.00 |
| Less Voids | $0.00 | $0.00 |
| **Total** | **$400.00** | **$0.00** |

Gift Certificates and Series are tracked as separate revenue categories (not counted in service or retail sales above). This confirms they are distinct financial instruments.

#### On Account

| Line | Amount |
|------|--------|
| Less On Account Sales | -$158.75 |
| Plus On Account Payments | $0.00 |

"On Account" = client charges services/retail to their account (accounts receivable), paying later. Net -$158.75 means $158.75 was charged to client accounts this period with no repayments recorded.

#### Grand Total: $68,436.67

#### Payment Type Reconciliation

| Payment Type | Amount |
|-------------|--------|
| AMEX | $5,402.83 |
| CASH | **-$12,228.99** |
| DEBIT | $12,322.86 |
| E-TRANSFER | $100.00 |
| MASTERCARD | $9,607.50 |
| VISA | $50,394.79 |
| **Sub Total** | **$65,598.99** |
| **Plus Petty Cash** | **$2,837.68** |
| **Grand Total** | **$68,436.67** |

**CASH is negative** (-$12,228.99): Cash was taken out of the register (likely for payroll, which is paid in cash to stylists — confirmed by payroll report context). The Petty Cash figure ($2,837.68) is a separate line added back because petty cash disbursements are tracked independently through the Petty Cash Report.

Reconciliation: Sub Total ($65,598.99) + Petty Cash ($2,837.68) = Grand Total ($68,436.67).

Payment types confirmed: **AMEX, CASH, DEBIT, E-TRANSFER, MASTERCARD, VISA** — these are the `PaymentType` lookup values.

---

## 2. Petty Cash Report

**File:** `Petty Cash Report4.pdf`

Tracks cash disbursements from the till for operating expenses. Each entry has a category, date, cashier, GST, PST, and a free-text comment.

### Report Structure

| Category | Date | Amount | GST | PST | Cashier | Comment |
|----------|------|--------|-----|-----|---------|---------|
| Food Expenses | 03/07/2026 | $18.08 | $0.00 | $0.00 | JJ | |
| Miscellaneous Expenses | 03/31/2026 | $2,819.60 | $0.00 | $0.00 | JJ | PROFESSIONAL PRODUCT |
| **Grand Total** | | **$2,837.68** | **$0.00** | **$0.00** | | |

**Categories seen:** Food Expenses, Miscellaneous Expenses. Additional categories likely exist (office supplies, etc.) — category is a configurable lookup.

**PROFESSIONAL PRODUCT** ($2,819.60): Colour and styling product purchased for the salon. This is the dominant petty cash item most months (professional product is a major COGS).

**Cashier field:** Records which staff member handled the disbursement. Maps to `Provider`.

**GST/PST columns:** Both are $0.00 here — either these particular purchases were tax-exempt, or taxes are tracked separately for petty cash. Column structure indicates taxes CAN be recorded per entry.

---

## 3. ERM Implications

### 3.1 PettyCashEntry Entity (Phase 2)

```
PettyCashEntry
├── id
├── tenant_id
├── category_id         (FK → PettyCashCategory)
├── entry_date
├── amount
├── gst_amount          (nullable — may be 0)
├── pst_amount          (nullable — may be 0)
├── cashier_id          (FK → Provider)
└── comment             (free text, optional)
```

```
PettyCashCategory
├── id
├── tenant_id
└── name                (e.g., "Food Expenses", "Miscellaneous Expenses")
```

### 3.2 Tax Tracking on Sale (Phase 2)

The Daily Sales Report shows GST and PST as independently reported totals. The `Sale` entity needs to store tax amounts per transaction:

```
Sale additions:
├── gst_collected
└── pst_collected
```

Or, a `SaleTax` detail line per sale (more flexible for multi-tax jurisdictions). For Phase 2, per-sale GST/PST columns on Sale are sufficient.

### 3.3 Adjustment Types on SaleItem (Phase 2)

The report tracks **Discounts**, **Returns**, and **Voids** as separate line items — not collapsed into net price. This means:

- **Discount**: price reduction applied at time of sale — tracked as a separate `discount_amount` on SaleItem (or via a `Promotion` link)
- **Return**: post-sale reversal of a retail item — a separate `SaleReturn` record referencing the original SaleItem
- **Void**: same-session cancellation before finalizing — `SaleItem.is_voided` boolean

The split between Service and Retail streams in the report means these adjustments must be query-able by sale type.

### 3.4 On Account Sales (Phase 2)

Clients can charge services/retail to their "account" — a form of in-house credit/receivable.

```
OnAccountTransaction
├── id
├── tenant_id
├── client_id           (FK → Client)
├── sale_id             (FK → Sale, nullable — may be a payment not tied to a specific sale)
├── transaction_date
├── amount              (positive = charge, negative = payment)
├── transaction_type    (enum: charge, payment)
└── notes
```

`Client` needs a derived or cached `account_balance` (sum of OnAccountTransaction.amount).

### 3.5 Gift Certificates vs. Series — Separate Revenue Lines

G/C and Series appear as distinct categories in the report (not under Service Sales or Retail Sales). When a G/C or Series is sold it creates its own revenue event, and when redeemed it reduces the sale total. Both already modeled as Phase 2 skeletons; this confirms they need distinct sale categorization.

### 3.6 Payment Types Confirmed

Lookup table `PaymentType` values confirmed from this report:
`AMEX`, `CASH`, `DEBIT`, `E-TRANSFER`, `MASTERCARD`, `VISA`

### 3.7 Reporting Requirements Summary

The Daily Sales Report drives the following reporting dimensions required in Phase 2:

| Dimension | Requirement |
|-----------|-------------|
| Revenue stream | Service Sales vs. Retail Sales vs. G/C vs. Series |
| Adjustment type | Gross → Less Discounts → Less Returns → Less Voids → Net |
| Tax | GST and PST independently aggregated |
| Period | Flexible date range (daily, monthly, custom) |
| Payment method | Breakdown by payment type |
| Petty cash | Reconciled into Grand Total |
| On Account | Net position (charges minus payments) included in Grand Total |

---

## 4. Google Sheet (Finance Tracker)

URL: https://docs.google.com/spreadsheets/d/1h70PrzlAneeaU9jAI39GvD8DpwKIv-PoGJH47W07CGQ

This is a manually maintained financial management workbook running alongside the previous POS system. Its primary purpose is cash flow tracking, payroll calculation, and reconciliation between the POS system and the external accounting journal. It is **not** replaced by our system — it informs what reports our system must produce.

### Sheets

| Sheet | Purpose |
|-------|---------|
| **Daily** | Date-level sales summary manually populated from the previous POS |
| **Transactions** | Individual service/retail transactions exported from the previous POS |
| **Monthly** | Monthly rollup: Total Sales, Payroll, Ending Balance, Payroll % |
| **Performance** | Multi-year reconciliation: POS vs. Journal, HST tracking |
| **Journal** | External accounting journal entries |
| **Expense Ledger** | Vendor-level expense tracking (L'Oreal, utilities, Paytrak, etc.) |
| **Expense Categories** | Category lookup for expenses |
| **Vendor Lookup** | Vendor master list |
| **Merchant** | Merchant account / payment processor data |
| **Loans** | Loan tracking |
| **Weekday** | Weekday distribution analysis |
| **Overview** | Summary dashboard |
| **Claude Cache** | Appears to be AI-assisted analysis cache |

### Daily Sheet (key columns)

```
Date | Expense | Net Sales | Services | Retail | GST | PST | Total Sales |
Clients | Rev/Client | Items | Open? | Rev. Day? | Weekday |
7-Day Avg Net Sales | 7-Day Avg Clients
```

- **Expense**: Cash disbursed from the till that day (payroll, petty cash) — negative value
- **Services / Retail**: Revenue split by type
- **Clients**: Count of clients served
- **Rev/Client**: Average revenue per client (calculated)
- **Items**: Count of service/retail items sold
- **Open? / Rev. Day?**: Boolean flags (Y/N)
- **7-Day Avg**: Rolling averages (calculated)

This sheet is populated **manually** from the previous system's daily report. In our system, this data is directly queryable from the `Sale` + `SaleItem` tables — no manual export required.

### Transactions Sheet (key columns)

```
Receipt | Date | Description | Client | Staff | Quantity | Amount | GST | PST |
Staff2 | Comstaff1 | Comstaff2 | TillCode
```

- **Receipt**: receipt/sale number — maps to `Sale.receipt_number`
- **Description**: Service or product name (free text from the previous POS)
- **Client**: legacy client code, format `LASTNAME3_FIRSTNAME2_SEQ` (e.g. `ZIMJ01`)
- **Staff / Staff2**: Primary and secondary provider codes
- **Comstaff1 / Comstaff2**: Commission amounts for each provider — confirms split commission model
- **TillCode**: Payment type code (VISA, CASH, DEBIT, etc.) or till identifier

Multiple rows share the same Receipt number = multi-item sale (confirmed appointment model).
Negative Amount rows = adjustments, reversals, or consultation entries.

**Client code format `ZIMJ01`:** 3 chars last name + 2 chars first name + sequence. Legacy system's generated code format. Our system uses UUIDs; a `Client.legacy_id` migration field preserves lookup during cutover.

### Monthly Sheet

```
MO | End Date | Total Sales | Payroll | Ending Balance | Avg Balance |
Max Balance | Net Sales | Payroll % Blended Net Sales
```

**Payroll % of Net Sales** is the key management metric — March 2026 was 57.95%. This is the ratio the owner monitors most closely month-over-month.

**Ending / Avg / Max Balance** = cash balance in the salon bank account. The sheet tracks the business's real-time cash position.

### Performance Sheet

Monthly reconciliation between the **previous POS system** (source of truth) and the **Journal** (accounting system — likely Wave or similar). A person named **Christina** does monthly reconciliation. Tracks:
- Total Merchant Sales (from payment processor)
- Net Sales, HST Collected (POS figures)
- HST Inputs (claimable tax on expenses)
- HST Net (remittance amount = HST collected − HST inputs)
- Cash Float variance

**HST vs. GST+PST:** Ontario charges HST at 13% (= 5% federal GST + 8% provincial component). The previous system recorded them split; the Google Sheet reconciles them combined as HST. Both representations are correct; our reports need to support both.

### Expense Ledger

Tracks payments to individual vendors: L'Oreal, beauty supply distributors, Toronto Hydro, Enbridge, Bell Canada, Staples, Paytrak (payroll processor), insurance, legal counsel. Categories include: professional product, utilities, payroll processing, CRA remittances, office/cleaning, food & beverage, professional services.

---

## 5. Consolidated ERM Implications (Reports + Google Sheet)

### 5.1 PettyCashEntry Entity (Phase 2)

```
PettyCashEntry
├── id
├── tenant_id
├── category_id         (FK → PettyCashCategory)
├── entry_date
├── amount
├── gst_amount
├── pst_amount
├── cashier_id          (FK → Provider)
└── comment
```

```
PettyCashCategory
├── id
├── tenant_id
└── name
```

### 5.2 Sale Entity additions (Phase 2)

```
Sale additions:
├── receipt_number      (receipt number for display)
├── gst_collected
└── pst_collected
```

### 5.3 SaleItem adjustments (Phase 2)

- `discount_amount` (from Promotion or manual override)
- `is_voided` (boolean — same-session cancellation)
- Returns are separate `SaleReturn` records

### 5.4 OnAccountTransaction (Phase 2)

Clients can charge to their in-house account. Net position appears on the Daily Sales Report.

```
OnAccountTransaction
├── id
├── tenant_id
├── client_id
├── sale_id             (nullable)
├── transaction_date
├── amount              (positive = charge, negative = payment)
├── transaction_type    (enum: charge, payment)
└── notes
```

### 5.5 Client Migration Field

```
Client addition:
└── legacy_id         (nullable text — e.g. "ZIMJ01", for cutover lookup)
```

### 5.6 Reporting Requirements (Phase 2 targets)

The Google Sheet and legacy reports define the reporting surface our system must replace:

| Report | Granularity | Key Outputs |
|--------|-------------|-------------|
| Daily Sales Report | Configurable date range | Service/Retail gross, Discounts/Returns/Voids, GST/PST, G/C & Series, On Account, Payment type breakdown, Petty Cash reconciliation |
| Petty Cash Report | Configurable date range | By category, with cashier and GST/PST per entry |
| Daily Operations Dashboard | Per day | Clients served, Revenue, Items, Services vs. Retail split, 7-day rolling avg |
| Provider Performance | Per provider, per period | Revenue, commission, client count, items per client |
| Payroll Report | Monthly | Per-provider: hours, revenue, commission tiers, gross pay — Payroll % of Net Sales |
| Tax Summary | Monthly | GST collected, PST collected, HST net (for remittance) |

**The Payroll % of Net Sales ratio is the primary KPI the owner tracks.** This drives the payroll report as a first-class Phase 2 requirement.
