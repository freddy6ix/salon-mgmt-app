# Milano Reference — Data Control Module

Screenshots from the Milano Data Control module, captured from the Salon Lyol installation on 2026-04-20. Covers the full menu structure and key sub-screens.

---

## 1. Data Control Menu Structure

**File:** `Screenshot 2026-04-20 at 12.53.52 PM.png`

Top-level menu items:

| Menu Item | Submenus | Phase relevance |
|-----------|----------|-----------------|
| **Staff Relations** | Staff Profile, Schedules, Departments, Security Groups, Program SmartCards | Phase 1 |
| **Service Control** | Services, Series | Phase 1 (Services); Series likely legacy bundles |
| **Inventory Control** | Retail, Professional, Packages, Brands, Physical Count, Bulk Sale Pricing, Transfers | Phase 2 |
| **Supplier Mngmt** | Suppliers, Purchase Orders, Labels | Phase 2 |
| **Categories** | Service, Product, Petty Cash, Payment Type, Campaign, Other | Phase 1/2 |
| **Promotions** | *(flat screen)* | Phase 2 |
| **Gift Certs** | *(flat screen)* | Phase 2 |
| **Payments** | Payment Types, Payment Type Order | Phase 2 |
| **Province** | *(flat screen — reference lookup)* | Phase 1 reference data |
| **User Defined** | User 9, 10, 11, 12 | Not modelled |

---

## 2. Staff Relations → Staff Profile

Five tabs: **General Info, Pay Structure, Goals, Security, Bookings**. Staff member ANTONELLA shown throughout.

Staff list visible: ADMIN, ANTONELLA, ASAMI, BECKY, GUMI, HOUSE, JJ, JOANNE, MAYUMI, OLGA, RYAN, SARAH, SEAN

**Note on HOUSE:** A system/virtual staff entry — likely used for house charges, internal bookings, or non-provider transactions. Not a real service provider.

### 2.1 General Info Tab

**File:** `data-control-staff-relations-profile-general-tab-Screenshot 2026-04-20 at 1.04.25 PM.png`

| Field | Value (Antonella) | Notes |
|-------|-------------------|-------|
| Code | ANTONELLA | Staff code — unique identifier |
| Active | checkbox | Controls whether staff appears in system |
| First Name | Antonella | |
| Last Name | (visible) | |
| Address 1 | 530 Lawrence ave west | Personal home address |
| City | Toronto | |
| Province | ON | |
| Postal Code | m6ao6 | |
| Email | antonellacumbo88@outlook.com | Personal email — may differ from login email |
| Home Phone | (blank) | |
| Cell Phone | 416 803-5764 | |
| Other Phone | (blank) | |
| Long Distance | checkboxes per phone | |
| Note 1 | 4169224145 Teresa (mom) | Emergency contact |
| Note 2 | Cumbo | Additional notes |
| Birthday | 02-06-1988 | |
| Photo | NO PHOTO | |

**Domain notes:**
- Provider entity needs personal contact fields distinct from login credentials (personal email ≠ system login email).
- `birthday` field — used for staff management / HR; not client-facing.
- Two free-text Note fields → `Provider.notes` (text).
- Photo → `Provider.photo_url` (object storage).
- Emergency contact is embedded in Note 1 — no structured emergency contact entity needed in Phase 1.

---

### 2.2 Pay Structure Tab

**File:** `data-control-staff-relations-profile-pay-structure-tab-Screenshot 2026-04-20 at 1.04.34 PM.png`

| Field | Value (Antonella) | Notes |
|-------|-------------------|-------|
| S.I.N. | 533748297 | Social Insurance Number — **sensitive PII** |
| Pay Amount | 20.00 | Base pay rate |
| Pay Type | Hourly | Dropdown: Hourly / Salary |
| Automatic time in/out with security | checkbox | Links schedule to security login |

**Service commission tiers (retroactive):**

| From | To | Percentage |
|------|----|------------|
| 0.00 | 999,999.999 | 50.00 |
| 0.00 | 0.00 | 0.00 |
| ... | ... | 0.00 |

**Retail commission tiers (retroactive):**

| From | To | Percentage |
|------|----|------------|
| 801.00 | 999,999.999 | 20.00 |
| 0.00 | 800.00 | 10.00 |
| ... | ... | 0.00 |

**Quota Factor:** 0.00

**Domain notes:**
- **S.I.N. must be stored encrypted at rest** — not plain text. Access restricted to OWNER/MANAGER security groups only. Consider a separate `ProviderSensitiveInfo` table with stricter access controls and auditing.
- **Tiered commission structure** — a single commission percentage is insufficient. Service and retail commissions are tier-based (revenue bracket → percentage). Requires a `ProviderCommissionTier` entity.
- "Retroactive" flag on tiers — when a provider hits a higher tier, the higher percentage applies retroactively to the entire period, not just future sales. This affects commission calculation logic.
- `pay_type` enum: `hourly`, `salary`.
- `quota_factor` — a multiplier applied to goals; 0.00 = no quota in use.

---

### 2.3 Goals Tab

**File:** `data-control-staff-relations-profile-goals-tab-Screenshot 2026-04-20 at 1.04.44 PM.png`

| Field | Notes |
|-------|-------|
| Year | 2026 |
| Don't show on login | Hides goal progress from login screen |
| Service Goal | Target service revenue |
| Retail Goal | Target retail revenue |
| Annual earning breakdown (%) | % of annual goal expected per month (JAN–DEC) |
| Weekly earning breakdown (%) | % expected per day of week |

**Domain notes:**
- `ProviderGoal` entity: `provider_id`, `year`, `service_goal`, `retail_goal`, per-month and per-day distribution percentages.
- Phase 2 reporting will use this to track actual vs. goal performance.
- "Don't show on login" → `ProviderGoal.hide_on_login` boolean.

---

### 2.4 Security Tab

**File:** `data-control-staff-relations-profile-security-tab-Screenshot 2026-04-20 at 1.04.52 PM.png`

| Field | Value (Antonella) | Notes |
|-------|-------------------|-------|
| Password | (masked) | Staff login password |
| Security Group | STAFF | Inherited permission set |

**Permission modules:** Bookings, CRM, Reports, Data Control, Sys Mngt, Cash, Other

**Partial permissions visible:**

| Permission | Allow |
|------------|-------|
| Add to/Change Waiting List | ✓ |
| Arrive an Appointment | ☐ |
| Auto Dial Appointment Phone | ☐ |
| Cancel an Appointment | ☐ |
| Client Status 1 | ✓ |
| Client Status 2 | (varies) |
| Copy a Block | ☐ |
| Create/Change a Block | ☐ |
| Create/Change an Appointment | ✓ |
| Create/Change Standing Appointment | ☐ |
| Create a Standing Block | ☐ |

**Domain notes:**
- Milano uses a two-layer permission model: **Security Group** (inherited baseline) + **individual overrides** per staff member.
- This is more sophisticated than our current `User.role` enum. We need:
  - `SecurityGroup` entity (MANAGER, OWNER, RECEPTION, STAFF) with a permission set
  - `Provider.security_group_id` FK
  - Individual permission overrides on Provider (or a `ProviderPermission` table)
- For Phase 1, a simplified approach: use `User.role` enum mapping to security groups, deferring granular per-permission overrides to Phase 2.

---

### 2.5 Bookings Tab

**File:** `data-control-staff-relations-profiles-bookings-tab-Screenshot 2026-04-20 at 1.05.01 PM.png`

| Field | Value (Antonella) | Notes |
|-------|-------------------|-------|
| Department | STYLING | Which department this provider belongs to |
| Can be a cashier | ✓ | Can process payments |
| Makes appointments | ✓ | Can create/edit appointments for others |
| Has appointments | ✓ | Appears as a bookable provider (column in appointment book) |
| Booking Order | 4 | Column position in the appointment book left-to-right |
| Online Bookings | Not available | Whether this provider is selectable in the online booking form |

**Online Bookings options:**
- `Not available` — provider does not appear in the online booking form
- `Available to my clients` — appears only to clients with this provider as their preferred provider
- `Available to all clients` — appears in the form for all clients

**Domain notes:**
- `Provider.booking_order` (int) — critical for rendering the appointment book columns in the correct order.
- `Provider.has_appointments` (boolean) — determines whether a column appears in the appointment book. HOUSE, ADMIN entries will have this false.
- `Provider.can_be_cashier` (boolean) — POS permission flag.
- `Provider.makes_appointments` (boolean) — whether provider can manage other providers' bookings.
- `Provider.online_booking_visibility` enum: `not_available`, `available_to_my_clients`, `available_to_all`.
- `Provider.department_id` FK → Department.
- **The booking_order integer is how the appointment book column sequence is controlled** — not alphabetical, not by hire date. Must be explicitly managed.

---

## 3. Staff Relations → Schedules (Detailed View)

**File:** `data-control-staff-relations-schedules-Screenshot 2026-04-20 at 1.05.24 PM.png`

Staff list: ADMIN, ASAMI, GUMI, HOUSE, JJ, JOANNE, MAYUMI, OLGA, RYAN, SARAH

Calendar highlights show specific dates (13th, 19th, 25th marked in purple — likely exceptions/overrides).

**Schedule status types (clickable rectangles):**

| Status | Meaning |
|--------|---------|
| TIME IN | Start of working block |
| TIME OUT | End of working block |
| DAY OFF | Provider not working this day |
| SPLIT | Split shift — two working blocks in one day |

**Repeat settings:**
- "Repeat this schedule every: **1 Week**"
- "Until: **04-19-2027**" — the template repeats until this date

**Domain notes:**
- **SPLIT** shift type is new — a provider may work 9am–1pm then 3pm–7pm with a gap. `ProviderSchedule` needs to support two time blocks per day. Either:
  - Two rows per day (same `day_of_week`, distinguished by a `block` integer: 1 or 2)
  - Or `start_time_2` / `end_time_2` nullable fields for the second block
  - Prefer two rows — cleaner and extensible.
- **"Until" date** maps to `ProviderSchedule.effective_to` — the template has an explicit end date, after which a new template is expected.
- The calendar highlights (purple dates) confirm `ProviderScheduleException` records for specific dates.

---

## 4. Staff Relations → Departments

**File:** `data-control-staff-relations-departments-Screenshot 2026-04-20 at 1.05.44 PM.png`

Departments: `<NONE>`, **COLOUR**, RECEPTION, STYLING

**COLOUR department record:**

| Field | Value |
|-------|-------|
| Code | COLOUR |
| Description | Colour Department |
| Note | (blank) |
| Can be a cashier | ✓ |
| Make appointments | ✓ |
| Has appointments | ✓ |
| Perform these services | (configurable list — empty here) |

**Domain notes:**
- `Department` is a real entity: `id`, `tenant_id`, `code`, `name`, `note`, `can_be_cashier`, `makes_appointments`, `has_appointments`.
- **"Perform these services"** — departments can be associated with a set of services they are permitted to deliver. This is a second layer of service capability gating (Department → Services, in addition to ProviderServicePrice).
  - For Phase 1, this is informational. ProviderServicePrice remains the authoritative capability gate.
- Departments: COLOUR, RECEPTION, STYLING (plus NONE). Maps roughly to our `provider_type` enum but is configurable and separate.
- RECEPTION department likely covers the HOUSE/ADMIN entries — non-service staff who handle bookings and payments.

---

## 5. Staff Relations → Security Groups

**File:** `data-control-staff-relations-security-groups-Screenshot 2026-04-20 at 1.06.04 PM.png`

Security groups: **MANAGER**, **OWNER**, **RECEPTION**, **STAFF**

**STAFF group record:**
- Code: STAFF
- Description: "Service Staff Security Group"
- Same permission grid as the Staff Profile Security tab

**Partial STAFF group permissions:**

| Permission | Allow |
|------------|-------|
| Add to/Change Waiting List | ☐ |
| Arrive an Appointment | ☐ |
| Cancel an Appointment | ✓ |
| Client Status 1 | ✓ |
| Client Status 2 | ☐ |
| Create/Change an Appointment | ☐ |

**Domain notes:**
- Four security groups: `MANAGER`, `OWNER`, `RECEPTION`, `STAFF` — these map to our `User.role` enum with more granularity.
- Phase 1 simplification: map these four groups to our role enum (`tenant_admin` ≈ OWNER/MANAGER, `staff` ≈ STAFF/RECEPTION). Full per-permission granularity is a Phase 2 concern.
- `SecurityGroup` entity needed for Phase 2: `id`, `tenant_id`, `code`, `name`, with a JSON or relational permission set.

---

## 6. Service Control → Services (Detailed — CPHHL)

**File:** `data-control-services-Screenshot 2026-04-20 at 1.07.03 PM.png`

Service CPHHL — Partial Head Highlights, Category: COLOR, Price: $130.00

**Staff Chart:**

| Staff | Price | Cost |
|-------|-------|------|
| \<Default\> | 120.00 | 10.00 |
| Joanne Skillin | 150.00 | 10.00 |
| Mayumi | 130.00 | 10.00 |

Additional service flags visible:
- `GST Exempt` checkbox
- `PST Exempt` (100.00% / 0.00%)
- `Split Comm` checkbox — split commission between two staff (1st Staff / 2nd Staff)
- `Print Client Card` checkbox
- `Points Exempt` checkbox
- `Cost as %` checkbox — cost stored as a percentage of price, not a flat amount
- `Suggestions` field — free text for related service upsells

**Time Usage for JOANNE (right panel):**

Time slots with two states:
- **taken** (yellow) — provider is actively working; cannot be scheduled for another client
- **movable** (different colour, appears from ~2:10 onward) — processing time; provider is free; appointment still running

This directly confirms our `processing_offset_minutes` / `processing_duration_minutes` model:
- For Partial Head Highlights with Joanne: ~80 min active (taken), then processing begins
- "Movable" slots = the processing window where another client can be scheduled

**Domain notes:**
- `ProviderServicePrice.cost_is_percentage` (boolean) — when true, `cost` is a % of `price`, not a flat amount.
- `Service.is_gst_exempt`, `Service.is_pst_exempt` — Canadian tax flags needed on Service.
- `Service.is_points_exempt` — for a future loyalty points system (Phase 2+).
- `Service.split_commission` — some services split commission between two providers (e.g., a service where one provider assists another). `AppointmentItem` may need a `second_provider_id` FK for this case.
- `Service.suggestions` — free text upsell note shown to staff at checkout.
- `<Default>` row in Staff Chart = `Service.default_price` / `Service.default_cost` — the fallback when no provider-specific row exists.
- Year-to-date sales: $137,396.50 for Partial Head Highlights — confirms this is one of the highest-revenue services.

---

## 7. Inventory Control → Retail

**File:** `data-control-retail Screenshot 2026-04-20 at 1.07.25 PM.png`

Product: LPMDADP500ML — "MD Anti-deposit protector 500m"

| Field | Value | Notes |
|-------|-------|-------|
| Code | LPMDADP500ML | Product SKU |
| Description | MD Anti-deposit protector 500m | |
| Supplier | LOREAL | FK → Supplier |
| Brand | LOREAL | FK → Brand |
| Category | RETAIL | |
| Reference | (field) | External/manufacturer reference |
| Manu Code | 30160637 | Manufacturer barcode/code |
| On Hand | 0 | Current stock level |
| Min | 2 | Reorder point |
| Max | 2 | Maximum stock level |
| Price | 0.00 | Client retail price |
| Sale Price | 0.00 | Promotional price |
| Cost | xx.xx | Purchase cost (hidden in screenshot) |
| Avg Cost | xx.xx | Moving average cost |
| Points Exempt | ✓ | Excluded from loyalty points |
| Don't Print Label | ✓ | |
| Avail. Online | checkbox | Available for online sale |
| GST Exempt | checkbox | |
| PST Exempt | checkbox | |
| Suggestions | field | Upsell prompts |
| Year to date sales | 117.50 | |

**Domain notes:**
- `Product` entity (Phase 2): `id`, `tenant_id`, `supplier_id`, `brand_id`, `category_id`, `code`, `name`, `manu_code`, `price`, `sale_price`, `cost`, `min_stock`, `max_stock`, `on_hand`, plus tax/points/label flags.
- Product and Service share some attributes (GST/PST exempt, Points Exempt, Suggestions, YTD sales) — but are distinct entities with different fields.
- `Brand` entity (Phase 2): `id`, `tenant_id`, `name`.
- `Supplier` entity (Phase 2): already noted from Supplier Mngmt menu.

---

## 8. Summary of ERM Impacts

### New fields required on existing Phase 1 entities

**Provider** — significant additions:

| Field | Type | Source |
|-------|------|--------|
| address_line | string | General Info tab |
| city | string | General Info tab |
| province | string | General Info tab |
| postal_code | string | General Info tab |
| personal_email | string | General Info tab (may differ from User.email) |
| home_phone | string | General Info tab |
| cell_phone | string | General Info tab |
| other_phone | string | General Info tab |
| birthday | date | General Info tab |
| notes | text | General Info tab (Note 1 + Note 2) |
| provider_photo_url | string | General Info tab |
| sin | string (encrypted) | Pay Structure tab — **must be encrypted at rest** |
| pay_type | enum | Pay Structure tab: `hourly`, `salary` |
| pay_amount | decimal | Pay Structure tab |
| department_id | uuid FK → Department | Bookings tab |
| security_group_id | uuid FK → SecurityGroup | Security tab |
| can_be_cashier | boolean | Bookings tab |
| makes_appointments | boolean | Bookings tab |
| has_appointments | boolean | Bookings tab |
| booking_order | int | Bookings tab — controls column order in appointment book |
| online_booking_visibility | enum | Bookings tab: `not_available`, `available_to_my_clients`, `available_to_all` |

**ProviderSchedule** — add SPLIT shift support:
- Two rows per day allowed (add `block` int: 1 or 2)
- `effective_to` already modelled ✓ — corresponds to the "Until" date in the Schedules UI

**Service** — additional fields:

| Field | Type | Source |
|-------|------|--------|
| is_gst_exempt | boolean | Services screen |
| is_pst_exempt | boolean | Services screen |
| is_points_exempt | boolean | Services screen |
| suggestions | text | Services screen — upsell prompt shown at checkout |
| split_commission | boolean | Services screen — flags services where commission is split between two providers |

**ProviderServicePrice** — additional field:
- `cost_is_percentage` (boolean) — when true, `cost` is a % of price not a flat amount

**AppointmentItem** — potential addition:
- `second_provider_id` (uuid FK → Provider, nullable) — for split-commission services where two providers share credit

### New Phase 1 entities

**Department**
```
Department
├── id (uuid PK)
├── tenant_id (uuid FK)
├── code (string)
├── name (string)
├── note (text, nullable)
├── can_be_cashier (boolean)
├── makes_appointments (boolean)
└── has_appointments (boolean)
```

### New Phase 2 skeleton entities

- **SecurityGroup** — MANAGER, OWNER, RECEPTION, STAFF with permission sets
- **ProviderCommissionTier** — tiered service/retail commission brackets per provider
- **ProviderGoal** — annual service/retail targets with monthly/weekly distribution
- **Product** — retail/professional inventory items
- **Brand** — product brand (LOREAL, etc.)
- **Promotion** — structured discount rules (DC $10, VIP 10%, REFERRAL $10, etc.)

---

## 12. Categories → Payment Type Categories

**File:** `categories-payment-type.png`

Payment type categories group payment types for reporting. Each has Code + Active + Description.

| Code | Description |
|------|-------------|
| ACCOUNT | On Account Payment Types |
| CASH | (cash drawer) |
| CDCCREDIT | (credit card via CDC terminal) |
| CDCDEBIT | (debit via CDC terminal) |
| CREDIT/DEBIT | General credit/debit category |
| ON HOUSE | House charges (internal, not client-facing) |
| POINTS | Loyalty points redemption |
| PREPAID | Prepaid (gift certs, series) |

**Domain note:** POINTS category confirms a **loyalty points system** exists in Milano. Clients earn points on purchases and can redeem them as a payment method. **Not currently in use at Salon Lyol** (per owner), but the data model must support it as a Phase 2 feature.

**ERM:** `PaymentTypeCategory` lookup entity (code, description, is_active). `PaymentType.category_id` FK.

---

## 13. Categories → Petty Cash Categories

**File:** `categories-petty-cash.png`

| Code | Description |
|------|-------------|
| CLEAN | Cleaning expenses |
| DELIVERY | Delivery charges |
| FOOD | Food Expenses |
| MISC | Miscellaneous Expenses |
| OFFICE | Office supplies |
| POSTAGE | Postage/courier |

The Petty Cash Report (March 2026) only showed FOOD and MISC — the others exist but weren't used that month. All are active.

**ERM:** Confirms `PettyCashCategory` entity with these seed values.

---

## 14. Promotions — Detail Screen

**File:** `promotions-detail.png`

Full promotion list (partial, scrollable): DC $5, DC $30, DC $35, DC $40, DC $45, DC $50, DC $55, DC $60, REFERRAL $10, **REFERRAL $20** (selected), REFILL 25%, STAFF D/C, VIP 5%, VIP 10%, VIP 15%, VIP 20%, VIP 25%, VIP 30%, VIP 100%, and more below scroll.

**Fields for REFERRAL $20:**

| Field | Value | Notes |
|-------|-------|-------|
| Code | REFERRAL $20 | |
| Active | ✓ | |
| Description | REFERRAL $20 | |
| Category | PROMO | Links to Category lookup |
| Day of week | (empty — all days) | "..." button for multi-day selection |
| Date range | -- to -- | Empty = no date restriction |
| Time range | (empty) | Optional time window |
| Promo by amount | 20.00 | ● selected |
| Per item | ☐ | Applied to total, not per item |
| Promo by percentage | ○ | |
| Promo by tax | ○ | |
| Service commission on full price | ☐ | Commission on discounted price |

**Discount types (radio buttons):**
- `amount` — flat dollar discount (e.g., $20 off)
- `percentage` — percent off (e.g., 10%)
- `tax` — discount equals the tax amount (unusual; likely a specific Quebec/promo scenario)

**Promotion categories visible:** PROMO. Others likely exist (VIP, STAFF, REFERRAL may have separate categories or all fall under PROMO).

**"Service commission on full price"** — when checked, commission is calculated on the pre-discount price; when unchecked, commission is on the actual charged price.

**ERM additions to `Promotion`:**
```
Promotion
├── id
├── tenant_id
├── code
├── description
├── category_id          (FK → Category)
├── is_active
├── day_of_week_mask     (bitmask or separate junction for valid days)
├── valid_from           (date, nullable)
├── valid_to             (date, nullable)
├── time_from            (time, nullable)
├── time_to              (time, nullable)
├── discount_type        (enum: amount, percentage, tax)
├── discount_value       (decimal)
├── per_item             (boolean — apply to each item vs total)
└── commission_on_full_price (boolean)
```

**Not currently used at Salon Lyol in the same structured way** — promotions exist in Milano but may be applied ad hoc.

---

## 15. Gift Certificates — Detail Screen

**File:** `gift-certs-detail.png`

Two G/C types configured: **GC** and **GIFT** (selected).

| Field | Value |
|-------|-------|
| Code | GIFT |
| Active | ✓ |
| Description | Gift Card/Certificate |
| Category | GIFT |
| Exclude GST | ✓ |
| Exclude PST | ✓ |
| Calculate PST on GST Amount | ☐ |

**Key insight:** Gift certificates are **tax-exempt on purchase** (selling a GC is not a taxable supply; tax is collected when the GC is redeemed for services/retail). Both GST and PST excluded at time of sale. This is correct Canadian tax treatment.

**ERM:** `GiftCertificateType` configuration record (template). Individual issued certificates are `GiftCertificate` instances with balance, recipient, and expiry. `GiftCertificate.exclude_gst`, `.exclude_pst` inherited from type.

The `GiftCertificateType` is essentially the product definition; `GiftCertificate` is the issued instrument. The two Milano records (GC, GIFT) may distinguish physical cards from e-certificates.

---

## 16. Service Control → Series

**File:** `service-control-series.png`

**List is empty** — no series are currently defined or in use at Salon Lyol.

**Fields (from empty form):**

| Field | Notes |
|-------|-------|
| Code | Short identifier |
| Description | |
| Service | FK dropdown → specific service this series applies to |
| Category | Category dropdown |
| Quantity | Number of prepaid uses |
| Unlimited usage | Override to unlimited redemptions |
| Override Quantity when selling | Allow selling partial/different qty |
| Percent Discount | Discount on the bundle price vs. individual |
| Price | Calculated bundle price |
| Calculate Price | Button to compute from qty × service price × discount |
| Year to Date / Last Year | Sales stats |

**Series = prepaid service bundle.** A client buys N uses of a specific service at a discount (e.g., "10 blowouts for $500 = 20% off"). Each use redeems one unit from their balance.

**Not in use at Salon Lyol.** Model as Phase 2 skeleton; include `ClientSeries` for tracking redemption balances.

```
Series (Phase 2)
├── id, tenant_id, code, description, is_active
├── service_id          (FK → Service)
├── category_id         (FK → Category)
├── quantity            (0 if unlimited_usage = true)
├── unlimited_usage     (boolean)
├── override_quantity_when_selling (boolean)
├── percent_discount
└── price

ClientSeries (Phase 2)
├── id, tenant_id
├── client_id           (FK → Client)
├── series_id           (FK → Series)
├── purchased_at        (timestamp)
├── sale_id             (FK → Sale — where purchased)
├── uses_total
└── uses_remaining
```

---

## 17. Payments → Payment Types

**File:** `payments-payment-types.png`

Full list: CASH, VISA, **MASTERCARD** (selected), AMEX, DEBIT, GIFT, ON ACCOUNT, E-TRANSFER, INVOICE TO G

Each payment type has:
- **Code** — system identifier
- **Active** — boolean
- **Category** — FK to PaymentTypeCategory (MASTERCARD → CREDIT/DEBIT)

**New types vs. Google Sheet data:**
- **GIFT** — gift certificate redemption as payment
- **INVOICE TO G** — invoice to a company/corporate client (e.g., filming shoots, events)

**ERM:**
```
PaymentType
├── id
├── tenant_id
├── code
├── description
├── is_active
├── category_id         (FK → PaymentTypeCategory)
└── display_order       (from Payment Type Order screen)
```

---

## 18. Payments → Payment Type Order

**File:** `payments-payment-type-order.png`

Ordered list (top to bottom = display order in POS checkout):
CASH → INVOICE TO G → DEBIT → VISA → MASTERCARD → AMEX → ON ACCOUNT → GIFT → E-TRANSFER

Staff reorder via Move Up/Move Down buttons. This is a pure UI configuration — maps to `PaymentType.display_order`.

---

## 19. Inventory Control → Retail Product

**File:** `inventory-retail-product.png`

Sample product: AG Touched Texture 142g (Code: AGTOUSLTEX142)

| Field | Value | Notes |
|-------|-------|-------|
| Supplier | MODERNI | FK → Supplier |
| Brand | AG | FK → Brand |
| Category | RETAIL | FK → Category |
| Reference | (internal ref) | |
| Manu. Code | 625336131947 | Barcode/UPC |
| On Hand | (qty) | Current inventory |
| Min / Max | inventory levels | Reorder triggers |
| Price | 32.00 | Regular retail price |
| Sale Price | 0.00 | Active sale price (0 = no active sale) |
| For date range | (sale window) | Sale period dates |
| Cost | xx.xx | Purchase cost |
| Avg. Cost | xx.xx | Rolling average cost |
| GST Exempt | ☐ | |
| PST Exempt | ☐ | |
| Points Exempt | ☐ | **Loyalty points — not exempt = earns points** |
| Don't Print Label | ☐ | |
| Avail. Online | ☐ | Future e-commerce flag |
| Suggestions | (linked products) | Related product recommendations |
| Year to date sales | $2,080.20 | |
| Note | free text | |

**POINTS EXEMPT flag** — new discovery. Retail products can earn loyalty points on purchase unless explicitly exempted. Confirms a loyalty/points system that was also seen in PaymentTypeCategory (POINTS). **Not currently active at Salon Lyol** but must be modeled.

**ERM additions to `Product` (Retail):**
```
RetailProduct (Phase 2)
├── id, tenant_id, code, description, is_active
├── supplier_id, brand_id, category_id
├── reference, manufacturer_code   (barcode/UPC)
├── price, sale_price
├── sale_start_date, sale_end_date
├── cost, avg_cost
├── on_hand, min_qty, max_qty
├── gst_exempt, pst_exempt
├── points_exempt                  (boolean)
├── dont_print_label               (boolean)
├── available_online               (boolean)
└── note
```

---

## 20. Inventory Control → Professional Product

**File:** `inventory-professional-product.png`

Sample: BS MT with Bondeinside 907g (Code: BS MTWB 907G) — L'Oreal product.

| Field | Value | Notes |
|-------|-------|-------|
| Supplier | LOREAL | |
| Brand | LOREAL | |
| Category | PRO | Not RETAIL |
| Manu. Code | 8844864536S5 | |
| Avg. Cost | xx.xx | |
| On Hand | (qty) | |
| Min / Max | inventory levels | |
| Note | | |
| Don't Print Label | ☐ | |

**No sale price, no GST/PST exempt flags, no points exempt** — professional products are **not sold to clients**. They are consumed in service delivery (colour product, treatments). Tracked as inventory and COGS.

**ERM:** `ProfessionalProduct` is a separate entity from `RetailProduct` — different fields, different purpose. Both have brand, supplier, cost, on-hand. Professional products link to `Service` records for COGS calculation (Phase 2).

---

## 21. Inventory Control → Retail Packages

**File:** `inventory-retail-packages.png`

Empty list — **no packages currently defined or in use at Salon Lyol.**

A Retail Package is a bundle of retail products sold together at a single price (e.g., shampoo + conditioner kit). Fields are similar to RetailProduct plus a line-item grid for constituent products.

Model as Phase 2 skeleton. Not a priority.

---

## 22. Inventory Control → Brands

**File:** `inventory-brands.png`

Complete brand list: AG, CEZANNE, DM, INVISI, KM, LOREAL, MILBON, MISC, MK, NEUMA, OLAPLEX, PAI-SHAU, PURE, REDKEN, S, SHU, WOW

Each has Code + Active + Description (description = AG shown selected).

**ERM:** `Brand` entity confirmed (Phase 2 skeleton already in ERM). Seed data: the 17 brands above.

---

## 23. Inventory Control → Physical Count

**File:** `inventory-physical-count.png`

A 4-step guided workflow for inventory counting:
1. Select brand + product types to count
2. Add items (via scanner, file, or manual)
3. View status (Counted / Not Counted / Exceptions)
4. Post count to update on-hand quantities

**No ERM entities needed** beyond existing inventory quantity fields. This is a UI operational workflow. A `PhysicalCountSession` audit log may be useful in Phase 2 but is not critical.

---

## 24. Inventory Control → Bulk Sale Pricing

**File:** `inventory-bulk-sale-pricing.png`

3-step wizard for setting sale prices across multiple products at once. Filters by Brand and Category, then allows tagging items and setting Price/Sale Price/Sale Start.

**No new ERM entities** — this is a bulk update tool operating on `RetailProduct.sale_price`. Implement as an admin operation, not a separate data model.

---

## 25. Inventory Control → Transfers

**File:** `inventory-transfers.png`

One historical record: Number 7-01-2023, Date 01/07/2023, Staff RYAN, Type "Professional to Consumed".

Transfer types indicate movement between inventory categories:
- **Professional to Consumed** — product taken from professional stock and consumed in a service (COGS tracking)
- Other types likely: Retail to Retail, Professional to Professional (location moves), Retail to Write-off

**Not actively used at Salon Lyol.** A single record from 2023 suggests this was tried and abandoned.

**ERM (Phase 2 skeleton):**
```
InventoryTransfer
├── id, tenant_id
├── transfer_number
├── transfer_date
├── staff_id            (FK → Provider)
├── transfer_type       (enum: professional_to_consumed, etc.)
├── comment
└── items: [InventoryTransferItem { product_id, quantity }]
```

---

## 26. ERM Additions from This Batch

### New entities required

| Entity | Phase | Notes |
|--------|-------|-------|
| `PaymentTypeCategory` | 2 | Lookup: ACCOUNT, CASH, CDCCREDIT, CDCDEBIT, CREDIT/DEBIT, ON HOUSE, POINTS, PREPAID |
| `PettyCashCategory` | 2 | Lookup: CLEAN, DELIVERY, FOOD, MISC, OFFICE, POSTAGE |
| `PettyCashEntry` | 2 | Already identified from Petty Cash Report |
| `GiftCertificateType` | 2 | Template record (GC, GIFT) — separate from issued GiftCertificate |
| `Series` | 2 | Prepaid service bundle (not in use at Salon Lyol) |
| `ClientSeries` | 2 | Per-client series redemption balance |
| `RetailProduct` | 2 | Retail inventory item |
| `ProfessionalProduct` | 2 | Professional product (COGS, not resold) |
| `RetailPackage` | 2 | Bundled retail product (not in use) |
| `InventoryTransfer` | 2 | Stock movement log (not in use) |

### Additions to existing entities

| Entity | Field | Notes |
|--------|-------|-------|
| `PaymentType` | `category_id`, `display_order` | Category FK; ordering from Payment Type Order screen |
| `Promotion` | `discount_type`, `per_item`, `commission_on_full_price`, `day_of_week_mask`, `valid_from/to`, `time_from/to` | Full Promotion structure now known |
| `RetailProduct` | `points_exempt`, `available_online`, `manufacturer_code`, `sale_price`, `sale_start_date`, `sale_end_date`, `avg_cost` | Loyalty points + e-commerce flag discovered |

### Loyalty Points (Phase 2)

The POINTS PaymentTypeCategory and `RetailProduct.points_exempt` field together confirm a loyalty points system:
- Clients earn points on retail (and possibly service) purchases
- Points can be redeemed as a payment type
- Individual products can be exempt from earning points

**Not active at Salon Lyol today.** ERM stub needed:
```
LoyaltyPoints (Phase 2)
├── id, tenant_id
├── client_id
├── points_balance      (current redeemable balance)
└── (detail via LoyaltyTransaction ledger)
```
- **GiftCertificate** — gift card/certificate issuance and redemption
