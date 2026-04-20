# Salon Lyol — End-to-End Entity Relationship Model

> **Status:** Working draft v0.3 — 2026-04-20
> Phase 1 entities are fully attributed. Phase 2–4 entities are skeletons (named, primary relationships, minimal attributes). Expect 10–20% of Phase 1 schema to evolve through real-world use.
>
> **v0.3 changes:** Added PaymentType, PaymentTypeCategory, PettyCashCategory, PettyCashEntry, GiftCertificateType, Series, ClientSeries, RetailProduct, ProfessionalProduct, RetailPackage, OnAccountTransaction, InventoryTransfer, LoyaltyTransaction as Phase 2 skeletons; split Product into RetailProduct + ProfessionalProduct; expanded Sale/SaleItem with tax and adjustment fields; added Client.milano_code; expanded Promotion with full constraint/discount fields; added PaymentType.display_order and category FK.

---

## Entity Inventory by Phase

| Phase | Entity | Notes |
|-------|--------|-------|
| **1** | Tenant | Multi-tenant anchor; single row in Phase 1 |
| **1** | User | Staff login accounts |
| **1** | Department | COLOUR / STYLING / RECEPTION — staff groupings |
| **1** | Provider | Staff member who appears in the appointment book |
| **1** | ProviderSchedule | Weekly working hours template per provider; supports split shifts |
| **1** | ProviderScheduleException | Date-specific overrides (holidays, one-off days) |
| **1** | TenantOperatingHours | Salon open/close hours by day of week |
| **1** | Station | Schedulable physical chairs (styling, colour application, multi-purpose) |
| **1** | ServiceCategory | Styling / Colouring / Extensions |
| **1** | Service | Individual service definition with duration and processing time |
| **1** | ProviderServicePrice | Per-provider price and cost override with effective date range |
| **1** | ClientHousehold | Family/household grouping for clients |
| **1** | Client | Client record — the person receiving services |
| **1** | AppointmentRequest | Raw inbound request before staff confirm |
| **1** | AppointmentRequestItem | Service line items within a request |
| **1** | Appointment | Container for a client's visit |
| **1** | AppointmentItem | Atomic unit: one service, one provider, one time window |
| **1** | AppointmentReminder | Scheduled email/SMS reminders |
| **2** | SecurityGroup | Configurable permission groups (MANAGER, OWNER, RECEPTION, STAFF) |
| **2** | ProviderCommissionTier | Tiered service/retail commission brackets per provider |
| **2** | ProviderGoal | Annual service/retail targets with monthly/weekly distribution |
| **2** | Campaign | Marketing campaign for booking attribution |
| **2** | Promotion | Structured discount rules (flat, %, tax-based) with day/date/time constraints |
| **2** | GiftCertificateType | G/C template (GC, GIFT) — tax treatment configuration |
| **2** | GiftCertificate | Issued gift card instance with balance and expiry |
| **2** | Series | Prepaid service bundle (e.g. 10 blowouts at 20% off) — not in use at Salon Lyol |
| **2** | ClientSeries | Per-client series purchase and redemption balance |
| **2** | Deposit | Client deposit against a future appointment |
| **2** | Sale | POS transaction closing an appointment |
| **2** | SaleItem | Line item within a sale (service or retail) |
| **2** | Payment | Payment record against a sale |
| **2** | PaymentType | Payment method (CASH, VISA, DEBIT, etc.) |
| **2** | PaymentTypeCategory | Payment type grouping (CASH, CREDIT/DEBIT, PREPAID, POINTS, etc.) |
| **2** | OnAccountTransaction | Client in-house credit/charge ledger |
| **2** | RetailProduct | Retail inventory item sold to clients |
| **2** | ProfessionalProduct | Professional product consumed in service delivery (COGS) |
| **2** | RetailPackage | Bundle of retail products — not in use at Salon Lyol |
| **2** | Brand | Product brand (LOREAL, MILBON, OLAPLEX, etc.) |
| **2** | PettyCashEntry | Individual petty cash disbursement |
| **2** | PettyCashCategory | Petty cash expense categories (FOOD, MISC, CLEAN, etc.) |
| **2** | InventoryTransfer | Stock movement log (Professional → Consumed etc.) — not in use |
| **2** | LoyaltyTransaction | Client loyalty points ledger — not in use at Salon Lyol |
| **2** | CrmConversation | AI-assisted email or chat conversation thread |
| **2** | CrmMessage | Individual message within a CRM conversation |
| **3** | TenantSubscriptionPlan | SaaS plan tiers |
| **3** | TenantSubscription | A tenant's active plan |
| **4** | VoiceCall | AI voice call record |

---

## ER Diagram

```mermaid
erDiagram

    %% ─────────────────────────────────────────
    %% PHASE 1 — CORE
    %% ─────────────────────────────────────────

    TENANT {
        uuid id PK
        string name
        string slug
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    USER {
        uuid id PK
        uuid tenant_id FK
        string email
        string password_hash
        enum role
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    DEPARTMENT {
        uuid id PK
        uuid tenant_id FK
        string code
        string name
        text note
        boolean can_be_cashier
        boolean makes_appointments
        boolean has_appointments
    }

    PROVIDER {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid department_id FK
        string first_name
        string last_name
        string display_name
        string milano_code
        enum provider_type
        boolean is_owner
        boolean is_active
        string address_line
        string city
        string province
        string postal_code
        string personal_email
        string home_phone
        string cell_phone
        string other_phone
        date birthday
        text notes
        string provider_photo_url
        string sin_encrypted
        enum pay_type
        decimal pay_amount
        boolean can_be_cashier
        boolean makes_appointments
        boolean has_appointments
        int booking_order
        enum online_booking_visibility
        timestamptz created_at
        timestamptz updated_at
    }

    PROVIDER_SCHEDULE {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        int day_of_week
        int block
        time start_time
        time end_time
        boolean is_working
        date effective_from
        date effective_to
    }

    PROVIDER_SCHEDULE_EXCEPTION {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        date exception_date
        boolean is_working
        time start_time
        time end_time
        text note
    }

    TENANT_OPERATING_HOURS {
        uuid id PK
        uuid tenant_id FK
        int day_of_week
        boolean is_open
        time open_time
        time close_time
    }

    STATION {
        uuid id PK
        uuid tenant_id FK
        uuid default_provider_id FK
        string name
        enum station_type
        boolean is_active
    }

    SERVICE_CATEGORY {
        uuid id PK
        uuid tenant_id FK
        string name
        int display_order
        boolean is_active
    }

    SERVICE {
        uuid id PK
        uuid tenant_id FK
        uuid category_id FK
        string service_code
        string name
        text description
        enum haircut_type
        enum pricing_type
        decimal default_price
        decimal default_cost
        int duration_minutes
        int processing_offset_minutes
        int processing_duration_minutes
        boolean is_addon
        boolean requires_prior_consultation
        boolean is_gst_exempt
        boolean is_pst_exempt
        boolean is_points_exempt
        boolean split_commission
        text suggestions
        boolean is_active
        int display_order
        timestamptz created_at
        timestamptz updated_at
    }

    PROVIDER_SERVICE_PRICE {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        uuid service_id FK
        decimal price
        decimal cost
        boolean cost_is_percentage
        date effective_from
        date effective_to
        boolean is_active
    }

    CLIENT_HOUSEHOLD {
        uuid id PK
        uuid tenant_id FK
        string name
        timestamptz created_at
    }

    CLIENT {
        uuid id PK
        uuid tenant_id FK
        uuid household_id FK
        uuid preferred_provider_id FK
        uuid referred_by_client_id FK
        string client_code
        string first_name
        string last_name
        string pronouns
        string email
        string home_phone
        string work_phone
        string cell_phone
        string address_line
        string city
        string province
        string postal_code
        string country
        text special_instructions
        boolean is_vip
        string photo_url
        enum referral_source
        int no_show_count
        int late_cancellation_count
        decimal account_balance
        timestamptz waiver_acknowledged_at
        timestamptz cancellation_policy_acknowledged_at
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    APPOINTMENT_REQUEST {
        uuid id PK
        uuid tenant_id FK
        uuid reviewed_by_user_id FK
        uuid converted_to_appointment_id FK
        string first_name
        string last_name
        string email
        string phone
        string pronouns
        string submitted_by_name
        date desired_date
        text desired_time_note
        enum source
        text special_note
        boolean waiver_acknowledged
        boolean cancellation_policy_acknowledged
        enum status
        text staff_notes
        timestamptz submitted_at
        timestamptz reviewed_at
        timestamptz created_at
        timestamptz updated_at
    }

    APPOINTMENT_REQUEST_ITEM {
        uuid id PK
        uuid request_id FK
        uuid converted_to_item_id FK
        int sequence
        string service_name
        string preferred_provider_name
    }

    APPOINTMENT {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        uuid request_id FK
        uuid created_by_user_id FK
        uuid campaign_id FK
        date appointment_date
        enum source
        enum status
        text cancellation_reason
        int cancellation_charge_pct
        boolean is_recurring
        uuid recurring_group_id
        text notes
        timestamptz created_at
        timestamptz updated_at
    }

    APPOINTMENT_ITEM {
        uuid id PK
        uuid tenant_id FK
        uuid appointment_id FK
        uuid service_id FK
        uuid provider_id FK
        uuid second_provider_id FK
        uuid station_id FK
        int sequence
        timestamptz start_time
        int duration_minutes
        int duration_override_minutes
        decimal price
        boolean price_is_locked
        decimal cost
        enum status
        text notes
        timestamptz created_at
        timestamptz updated_at
    }

    APPOINTMENT_REMINDER {
        uuid id PK
        uuid tenant_id FK
        uuid appointment_id FK
        enum channel
        timestamptz scheduled_at
        timestamptz sent_at
        enum status
    }

    %% ─────────────────────────────────────────
    %% PHASE 2 — POS + CRM + STAFF (skeletons)
    %% ─────────────────────────────────────────

    SECURITY_GROUP {
        uuid id PK
        uuid tenant_id FK
        string code
        string name
        json permissions
    }

    PROVIDER_COMMISSION_TIER {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        enum tier_type
        decimal from_amount
        decimal to_amount
        decimal percentage
        boolean is_retroactive
    }

    PROVIDER_GOAL {
        uuid id PK
        uuid tenant_id FK
        uuid provider_id FK
        int year
        decimal service_goal
        decimal retail_goal
        boolean hide_on_login
    }

    CAMPAIGN {
        uuid id PK
        uuid tenant_id FK
        string name
        boolean is_active
    }

    PROMOTION {
        uuid id PK
        uuid tenant_id FK
        uuid category_id FK
        string code
        string description
        enum discount_type
        decimal discount_value
        boolean per_item
        int day_of_week_mask
        date valid_from
        date valid_to
        time time_from
        time time_to
        boolean commission_on_full_price
        boolean is_active
    }

    GIFT_CERTIFICATE_TYPE {
        uuid id PK
        uuid tenant_id FK
        string code
        string description
        boolean exclude_gst
        boolean exclude_pst
        boolean is_active
    }

    GIFT_CERTIFICATE {
        uuid id PK
        uuid tenant_id FK
        uuid type_id FK
        uuid issued_to_client_id FK
        uuid sale_id FK
        string code
        decimal original_amount
        decimal remaining_balance
        enum status
        timestamptz issued_at
        timestamptz expires_at
    }

    SERIES {
        uuid id PK
        uuid tenant_id FK
        uuid service_id FK
        string code
        string description
        int quantity
        boolean unlimited_usage
        decimal percent_discount
        decimal price
        boolean is_active
    }

    CLIENT_SERIES {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        uuid series_id FK
        uuid sale_id FK
        timestamptz purchased_at
        int uses_total
        int uses_remaining
    }

    DEPOSIT {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        uuid appointment_id FK
        decimal amount
        enum status
        timestamptz created_at
    }

    SALE {
        uuid id PK
        uuid tenant_id FK
        uuid appointment_id FK
        uuid client_id FK
        string receipt_number
        decimal service_gross
        decimal retail_gross
        decimal discount_total
        decimal return_total
        decimal gst_collected
        decimal pst_collected
        decimal total_amount
        enum status
        timestamptz created_at
    }

    SALE_ITEM {
        uuid id PK
        uuid sale_id FK
        uuid appointment_item_id FK
        uuid retail_product_id FK
        uuid promotion_id FK
        text description
        enum item_type
        decimal unit_price
        int quantity
        decimal discount_amount
        boolean is_voided
    }

    PAYMENT_TYPE_CATEGORY {
        uuid id PK
        uuid tenant_id FK
        string code
        string description
        boolean is_active
    }

    PAYMENT_TYPE {
        uuid id PK
        uuid tenant_id FK
        uuid category_id FK
        string code
        string description
        int display_order
        boolean is_active
    }

    PAYMENT {
        uuid id PK
        uuid tenant_id FK
        uuid sale_id FK
        uuid payment_type_id FK
        uuid gift_certificate_id FK
        decimal amount
        timestamptz created_at
    }

    ON_ACCOUNT_TRANSACTION {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        uuid sale_id FK
        date transaction_date
        decimal amount
        enum transaction_type
        text notes
    }

    BRAND {
        uuid id PK
        uuid tenant_id FK
        string code
        string description
        boolean is_active
    }

    RETAIL_PRODUCT {
        uuid id PK
        uuid tenant_id FK
        uuid brand_id FK
        uuid supplier_id FK
        string code
        string description
        string manufacturer_code
        decimal price
        decimal sale_price
        date sale_start_date
        date sale_end_date
        decimal cost
        decimal avg_cost
        int on_hand
        int min_qty
        int max_qty
        boolean gst_exempt
        boolean pst_exempt
        boolean points_exempt
        boolean available_online
        boolean is_active
    }

    PROFESSIONAL_PRODUCT {
        uuid id PK
        uuid tenant_id FK
        uuid brand_id FK
        uuid supplier_id FK
        string code
        string description
        string manufacturer_code
        decimal cost
        decimal avg_cost
        int on_hand
        int min_qty
        int max_qty
        boolean is_active
    }

    PETTY_CASH_CATEGORY {
        uuid id PK
        uuid tenant_id FK
        string code
        string description
        boolean is_active
    }

    PETTY_CASH_ENTRY {
        uuid id PK
        uuid tenant_id FK
        uuid category_id FK
        uuid cashier_id FK
        date entry_date
        decimal amount
        decimal gst_amount
        decimal pst_amount
        text comment
    }

    LOYALTY_TRANSACTION {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        uuid sale_id FK
        int points_delta
        enum transaction_type
        timestamptz created_at
    }

    CRM_CONVERSATION {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        enum channel
        enum status
        timestamptz created_at
    }

    CRM_MESSAGE {
        uuid id PK
        uuid conversation_id FK
        enum direction
        text content
        timestamptz sent_at
    }

    %% ─────────────────────────────────────────
    %% PHASE 3 — MULTI-TENANCY (skeletons)
    %% ─────────────────────────────────────────

    TENANT_SUBSCRIPTION_PLAN {
        uuid id PK
        string name
        decimal monthly_price
    }

    TENANT_SUBSCRIPTION {
        uuid id PK
        uuid tenant_id FK
        uuid plan_id FK
        enum status
        date started_at
        date ended_at
    }

    %% ─────────────────────────────────────────
    %% PHASE 4 — VOICE AI (skeleton)
    %% ─────────────────────────────────────────

    VOICE_CALL {
        uuid id PK
        uuid tenant_id FK
        uuid client_id FK
        int duration_seconds
        string transcript_url
        timestamptz created_at
    }

    %% ─────────────────────────────────────────
    %% RELATIONSHIPS
    %% ─────────────────────────────────────────

    TENANT ||--o{ USER : "has"
    TENANT ||--o{ DEPARTMENT : "has"
    TENANT ||--o{ PROVIDER : "has"
    TENANT ||--o{ STATION : "has"
    TENANT ||--o{ SERVICE_CATEGORY : "has"
    TENANT ||--o{ SERVICE : "has"
    TENANT ||--o{ CLIENT : "has"
    TENANT ||--o{ APPOINTMENT : "has"
    TENANT ||--|{ TENANT_OPERATING_HOURS : "defines"
    TENANT ||--o| TENANT_SUBSCRIPTION : "has"

    USER ||--o| PROVIDER : "is"

    DEPARTMENT ||--o{ PROVIDER : "groups"

    PROVIDER ||--o{ PROVIDER_SCHEDULE : "has"
    PROVIDER ||--o{ PROVIDER_SCHEDULE_EXCEPTION : "has"
    PROVIDER ||--o{ PROVIDER_SERVICE_PRICE : "offers"
    PROVIDER ||--o{ APPOINTMENT_ITEM : "assigned to"
    PROVIDER ||--o{ APPOINTMENT_ITEM : "second provider on"
    PROVIDER ||--o{ STATION : "default at"
    PROVIDER ||--o{ PROVIDER_COMMISSION_TIER : "has"
    PROVIDER ||--o{ PROVIDER_GOAL : "has"

    SERVICE_CATEGORY ||--|{ SERVICE : "contains"
    SERVICE ||--o{ PROVIDER_SERVICE_PRICE : "priced via"
    SERVICE ||--o{ APPOINTMENT_ITEM : "booked as"

    CLIENT_HOUSEHOLD ||--o{ CLIENT : "groups"
    CLIENT }o--o| PROVIDER : "prefers"
    CLIENT }o--o| CLIENT : "referred by"
    CLIENT ||--o{ APPOINTMENT : "books"
    CLIENT ||--o{ DEPOSIT : "places"
    CLIENT ||--o{ GIFT_CERTIFICATE : "holds"
    CLIENT ||--o{ CLIENT_SERIES : "owns"
    CLIENT ||--o{ ON_ACCOUNT_TRANSACTION : "has"
    CLIENT ||--o{ LOYALTY_TRANSACTION : "earns"
    CLIENT ||--o{ CRM_CONVERSATION : "has"
    CLIENT ||--o{ VOICE_CALL : "has"

    APPOINTMENT_REQUEST ||--|{ APPOINTMENT_REQUEST_ITEM : "contains"
    APPOINTMENT_REQUEST }o--o| USER : "reviewed by"
    APPOINTMENT_REQUEST }o--o| APPOINTMENT : "converts to"
    APPOINTMENT_REQUEST_ITEM }o--o| APPOINTMENT_ITEM : "converts to"

    APPOINTMENT }o--o| APPOINTMENT_REQUEST : "sourced from"
    APPOINTMENT }o--o| CAMPAIGN : "attributed to"
    APPOINTMENT ||--|{ APPOINTMENT_ITEM : "contains"
    APPOINTMENT ||--o{ APPOINTMENT_REMINDER : "triggers"
    APPOINTMENT ||--o{ DEPOSIT : "holds"

    APPOINTMENT_ITEM }o--o| STATION : "uses"

    SALE }o--o| APPOINTMENT : "closes"
    SALE ||--o{ SALE_ITEM : "contains"
    SALE ||--o{ PAYMENT : "settled by"
    SALE_ITEM }o--o| APPOINTMENT_ITEM : "for"
    SALE_ITEM }o--o| RETAIL_PRODUCT : "sells"
    SALE_ITEM }o--o| PROMOTION : "discounted by"

    PAYMENT_TYPE_CATEGORY ||--o{ PAYMENT_TYPE : "groups"
    PAYMENT }o--o| PAYMENT_TYPE : "uses"
    PAYMENT }o--o| GIFT_CERTIFICATE : "redeems"

    GIFT_CERTIFICATE_TYPE ||--o{ GIFT_CERTIFICATE : "templates"

    SERIES }o--|| SERVICE : "bundles"
    CLIENT_SERIES }o--|| CLIENT : "belongs to"
    CLIENT_SERIES }o--|| SERIES : "of"

    BRAND ||--o{ RETAIL_PRODUCT : "has"
    BRAND ||--o{ PROFESSIONAL_PRODUCT : "has"

    PETTY_CASH_CATEGORY ||--o{ PETTY_CASH_ENTRY : "categorises"
    PETTY_CASH_ENTRY }o--|| PROVIDER : "entered by"

    LOYALTY_TRANSACTION }o--o| SALE : "from"

    CRM_CONVERSATION ||--o{ CRM_MESSAGE : "contains"

    TENANT_SUBSCRIPTION_PLAN ||--o{ TENANT_SUBSCRIPTION : "governs"
```

---

## Entity Reference — Phase 1

### Tenant

The top-level multi-tenancy anchor. In Phase 1 there is exactly one row (Salon Lyol). In Phase 3, each salon is a row.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| name | string | "Salon Lyol" |
| slug | string | URL-safe identifier, unique; used for subdomain routing in Phase 3 |
| is_active | boolean | Soft-disable a tenant without deleting |
| created_at / updated_at | timestamptz | |

---

### User

Anyone who can log into the system. In Phase 1, all Users are staff members.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| email | string | Unique per tenant — the system login email |
| password_hash | string | bcrypt or Argon2 |
| role | enum | `super_admin`, `tenant_admin`, `staff` |
| is_active | boolean | Deactivated users cannot log in |

**role enum:**
- `super_admin` — platform operator (no tenant_id)
- `tenant_admin` — salon owner / manager (maps to Milano's OWNER/MANAGER security groups)
- `staff` — service providers and reception (maps to Milano's STAFF/RECEPTION security groups)

**Phase 2 note:** Full per-permission granularity (Milano's Security Groups + individual overrides) will be modelled in the `SecurityGroup` entity. For Phase 1, the three-value role enum is sufficient.

---

### Department

Staff are grouped into departments. Each department has default capability flags that apply to all its members. In Phase 1, departments are informational — `ProviderServicePrice` remains the authoritative service capability gate.

Departments at Salon Lyol: **COLOUR**, **STYLING**, **RECEPTION**, *(none)*

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| code | string | e.g., "COLOUR", "STYLING", "RECEPTION" |
| name | string | Full description |
| note | text | Nullable |
| can_be_cashier | boolean | Default for members — overridable at Provider level |
| makes_appointments | boolean | Default — can create/edit appointments |
| has_appointments | boolean | Default — appears as a bookable provider column |

---

### Provider

A staff member. May deliver services (has_appointments = true) or be admin/reception only. Every Provider has a corresponding User login. Not every User is a Provider.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| user_id | uuid FK → User | 1:1 — the login account |
| department_id | uuid FK → Department | |
| first_name | string | |
| last_name | string | |
| display_name | string | Column header in appointment book (e.g., "JJ", "Joanne") |
| milano_code | string | Milano's identifier (e.g., "JOANNE"); kept for migration reference |
| provider_type | enum | `stylist`, `colourist`, `dualist` — informational; capability governed by ProviderServicePrice |
| is_owner | boolean | True for Jini (JJ) |
| is_active | boolean | Inactive providers do not appear in the appointment book |
| **Personal info** | | |
| address_line | string | Nullable — home address |
| city | string | Nullable |
| province | string | Nullable |
| postal_code | string | Nullable |
| personal_email | string | Nullable — personal email; may differ from User.email (system login) |
| home_phone | string | Nullable |
| cell_phone | string | Nullable |
| other_phone | string | Nullable |
| birthday | date | Nullable |
| notes | text | Nullable — internal HR notes (emergency contact, etc.) |
| provider_photo_url | string | Nullable — object storage |
| **Compensation** | | |
| sin_encrypted | string | Nullable — Social Insurance Number, **encrypted at rest**; access restricted to OWNER role |
| pay_type | enum | `hourly`, `salary` |
| pay_amount | decimal | Base hourly rate or salary amount |
| **Booking behaviour** | | |
| can_be_cashier | boolean | Can process payments at POS |
| makes_appointments | boolean | Can create/edit appointments for other providers |
| has_appointments | boolean | Appears as a bookable column in the appointment book |
| booking_order | int | Column position left-to-right in the appointment book |
| online_booking_visibility | enum | `not_available`, `available_to_my_clients`, `available_to_all` |

**online_booking_visibility enum:**
- `not_available` — provider does not appear in the online booking form
- `available_to_my_clients` — appears only for clients who have this provider as their preferred provider
- `available_to_all` — appears for all clients

**booking_order note:** Controls the column sequence in the appointment book. Not alphabetical — explicitly set per provider by management.

**sin_encrypted note:** Stored using application-level encryption (e.g., AES-256), not just at-rest disk encryption. Only accessible to Users with role `tenant_admin`. Consider a separate `ProviderSensitiveInfo` table in Phase 2 for stricter access control and audit logging.

---

### ProviderSchedule

The provider's recurring weekly working schedule. Stored as a template that repeats each week until `effective_to`. Supports split shifts (two working blocks in one day) via the `block` field.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| provider_id | uuid FK → Provider | |
| day_of_week | int | 0 = Monday … 6 = Sunday |
| block | int | 1 = first working block; 2 = second block (split shift). Default 1. |
| start_time | time | Working start for this block |
| end_time | time | Working end for this block |
| is_working | boolean | False = day off (block = 1, no block 2 needed) |
| effective_from | date | When this schedule version takes effect |
| effective_to | date | Nullable — null = currently active; set from the Milano "Until" date |

**Split shift example:** A provider working 9am–1pm and 3pm–6pm on Tuesday has two rows: `(Tuesday, block=1, 09:00, 13:00)` and `(Tuesday, block=2, 15:00, 18:00)`.

**Salon operating days:** Tuesday–Saturday. All providers will have `is_working = false` for Monday (0) and Sunday (6). Most providers work 4 of the 5 operating days; Jini (JJ) works all 5.

---

### ProviderScheduleException

A one-off override to the weekly template — a holiday, sick day, or extra working day.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| provider_id | uuid FK → Provider | |
| exception_date | date | The specific date being overridden |
| is_working | boolean | False = day off; true = working on a normally-off day |
| start_time | time | Nullable — overrides normal start |
| end_time | time | Nullable — overrides normal end |
| note | text | Optional reason (e.g., "vacation", "training day") |

---

### TenantOperatingHours

The salon's opening hours by day of week. Constrains appointment booking windows.

Salon Lyol hours:

| Day | Open | Close |
|-----|------|-------|
| Monday | Closed | — |
| Tuesday | 09:00 | 18:00 |
| Wednesday | 09:00 | 20:00 |
| Thursday | 09:00 | 20:00 |
| Friday | 09:00 | 18:00 |
| Saturday | 09:00 | 17:00 |
| Sunday | Closed | — |

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| day_of_week | int | 0 = Monday … 6 = Sunday |
| is_open | boolean | False for Monday and Sunday |
| open_time | time | Nullable when is_open = false |
| close_time | time | Nullable when is_open = false |

---

### Station

A physical station (chair) assigned to an AppointmentItem. Only stations that constrain scheduling are modelled — processing chairs and shampoo sinks are managed informally.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| default_provider_id | uuid FK → Provider | Nullable — null for multi_purpose stations |
| name | string | e.g., "Joanne's Colour Chair", "Multi-purpose A" |
| station_type | enum | `styling`, `colour_application`, `multi_purpose` |
| is_active | boolean | |

**station_type enum:**
- `styling` — 6 chairs; each assigned to a specific stylist
- `colour_application` — 3 chairs; each assigned to a specific colourist
- `multi_purpose` — 2 shared chairs; no default provider

**Not modelled:** `colour_processing` (2 chairs), `shampoo_sink` (4 sinks) — always available given Salon Lyol's concurrent provider count; managed informally.

---

### ServiceCategory

Top-level grouping of services.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| name | string | "Styling", "Colouring", "Extensions" |
| display_order | int | Controls UI ordering |
| is_active | boolean | |

---

### Service

A specific service offered by the salon. Defines duration, processing time, default pricing, and tax treatment. Per-provider price overrides live in ProviderServicePrice.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| category_id | uuid FK → ServiceCategory | |
| service_code | string | Short code displayed in the appointment book (e.g., "CFC", "STY2N") |
| name | string | Full display name (e.g., "Color Full Color", "Type 2 Haircut") |
| description | text | Nullable — client-facing description |
| haircut_type | enum | Nullable — `type_1`, `type_2`, `type_2_plus`; only set for haircut services |
| pricing_type | enum | `fixed` (price at booking) or `hourly` (price finalized at checkout) |
| default_price | decimal | Nullable — fallback when no ProviderServicePrice row exists |
| default_cost | decimal | Nullable — fallback materials cost |
| duration_minutes | int | Total calendar slot length |
| processing_offset_minutes | int | Default 0 — minutes after start when provider becomes free |
| processing_duration_minutes | int | Default 0 — length of provider-free window; 0 for non-colour services |
| is_addon | boolean | True for Toner, Metal Detox/Olaplex, Heat Tool Finish, Milbon add-on |
| requires_prior_consultation | boolean | True for extension installation services |
| is_gst_exempt | boolean | Canadian GST exemption flag |
| is_pst_exempt | boolean | Canadian PST exemption flag |
| is_points_exempt | boolean | Excluded from loyalty points (Phase 2+) |
| split_commission | boolean | Commission split between two providers (second_provider_id on AppointmentItem) |
| suggestions | text | Nullable — upsell prompt shown to staff at checkout |
| is_active | boolean | |
| display_order | int | |
| created_at / updated_at | timestamptz | |

**Processing time example — Partial Head Highlights:**
- `duration_minutes` = 150
- `processing_offset_minutes` = 80 (provider applies foils for 80 min, then processing begins)
- `processing_duration_minutes` = 40 (provider free for 40 min while colour develops)
- Scheduler uses this window to slot another client's service with the same provider

---

### ProviderServicePrice

Junction between Provider and Service. Records capability (existence of a row = provider can deliver this service), price, and cost. Supports historical pricing via effective date range.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| provider_id | uuid FK → Provider | |
| service_id | uuid FK → Service | |
| price | decimal | Provider's price for this service |
| cost | decimal | Nullable — materials cost |
| cost_is_percentage | boolean | When true, `cost` is a % of price; when false, `cost` is a flat amount |
| effective_from | date | When this price took effect |
| effective_to | date | Nullable — null = currently active |
| is_active | boolean | |

**Unique constraint:** `(tenant_id, provider_id, service_id, effective_from)`

**Price lookup at booking:** Select the active row where `effective_from <= booking_date AND (effective_to IS NULL OR effective_to >= booking_date)`. The resolved price is captured on `AppointmentItem.price` — future price changes do not affect historical appointments.

---

### ClientHousehold

Groups family members sharing a household. Used for relationship tracking and reporting.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| name | string | e.g., "Ferguson Family" |
| created_at | timestamptz | |

---

### Client

The person receiving services. No system login in Phase 1.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| household_id | uuid FK → ClientHousehold | Nullable |
| preferred_provider_id | uuid FK → Provider | Nullable |
| referred_by_client_id | uuid FK → Client | Nullable — self-referential |
| client_code | string | Short identifier, unique per tenant (e.g., FERGF1) |
| milano_code | string | Nullable — Milano's generated code (e.g., FERGF01); populated during migration cutover for lookup |
| first_name | string | |
| last_name | string | |
| pronouns | string | Nullable |
| email | string | Nullable — primary contact for reminders |
| home_phone | string | Nullable |
| work_phone | string | Nullable |
| cell_phone | string | Nullable |
| address_line | string | Nullable |
| city | string | Nullable |
| province | string | Nullable |
| postal_code | string | Nullable |
| country | string | Default "CA" |
| special_instructions | text | Nullable — shown to staff at booking time |
| is_vip | boolean | Default false |
| photo_url | string | Nullable — object storage |
| referral_source | enum | Nullable: `client_referral`, `google`, `instagram`, `walk_by`, `other` |
| no_show_count | int | Default 0 — incremented when Appointment.status = no_show |
| late_cancellation_count | int | Default 0 — incremented on late cancellations |
| account_balance | decimal | Default 0 — Phase 2 POS on-account |
| waiver_acknowledged_at | timestamptz | Nullable |
| cancellation_policy_acknowledged_at | timestamptz | Nullable |
| is_active | boolean | Default true |
| created_at / updated_at | timestamptz | |

**client_code generation:** `UPPER(last_name[0:4]) + UPPER(first_name[0:1]) + sequence_digit`. Example: Ferguson, Frederick → FERGF1.

---

### AppointmentRequest

A raw inbound booking request before staff review. Contact details stored as free text — the client may not yet exist in the system.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| reviewed_by_user_id | uuid FK → User | Nullable |
| converted_to_appointment_id | uuid FK → Appointment | Nullable |
| first_name | string | |
| last_name | string | |
| email | string | |
| phone | string | |
| pronouns | string | Nullable |
| submitted_by_name | string | Nullable — "on behalf of" |
| desired_date | date | Client's preferred date — not a commitment |
| desired_time_note | text | Free text: "anytime", "after 2pm" |
| source | enum | `online_form`, `email`, `phone`, `walk_in` |
| special_note | text | Nullable |
| waiver_acknowledged | boolean | |
| cancellation_policy_acknowledged | boolean | |
| status | enum | `new`, `reviewed`, `converted`, `declined` |
| staff_notes | text | Nullable — internal notes from staff review |
| submitted_at | timestamptz | |
| reviewed_at | timestamptz | Nullable |
| created_at / updated_at | timestamptz | |

---

### AppointmentRequestItem

Service line items within a booking request. Stored as free text — resolved to real Service/Provider FKs when staff convert to a confirmed Appointment.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| request_id | uuid FK → AppointmentRequest | |
| converted_to_item_id | uuid FK → AppointmentItem | Nullable |
| sequence | int | 1 or 2 (form supports up to 2 services) |
| service_name | string | As selected in form |
| preferred_provider_name | string | As selected in form |

---

### Appointment

Container for a client's visit. Duration, total price, and involved providers all derive from its AppointmentItems.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| client_id | uuid FK → Client | |
| request_id | uuid FK → AppointmentRequest | Nullable |
| created_by_user_id | uuid FK → User | |
| campaign_id | uuid FK → Campaign | Nullable — Phase 2 FK included now to avoid future migration |
| appointment_date | date | |
| source | enum | `online_form`, `email`, `phone`, `walk_in`, `staff_entered` |
| status | enum | `requested`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show` |
| cancellation_reason | text | Nullable |
| cancellation_charge_pct | int | Nullable — 0, 50, or 100 per cancellation policy |
| is_recurring | boolean | Default false |
| recurring_group_id | uuid | Nullable — links all instances of a recurring series |
| notes | text | Nullable |
| created_at / updated_at | timestamptz | |

**cancellation_charge_pct logic:**
- Cancel 2+ days before → 0%
- Cancel < 2 days before → 50%
- Same/next-day booking, cancel < 4 hrs before → 50%
- No-show → 100%

**Derived fields (not stored):** total_price, total_duration_minutes, start_time, end_time, providers list.

---

### AppointmentItem

The atomic scheduling unit. One service, one primary provider, one time window.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| appointment_id | uuid FK → Appointment | |
| service_id | uuid FK → Service | |
| provider_id | uuid FK → Provider | Primary provider |
| second_provider_id | uuid FK → Provider | Nullable — for split-commission services (Service.split_commission = true) |
| station_id | uuid FK → Station | Nullable — null for add-on services without a chair |
| sequence | int | Order within the appointment (1, 2, 3…) |
| start_time | timestamptz | |
| duration_minutes | int | Copied from Service at booking; not updated if service duration changes |
| duration_override_minutes | int | Nullable — staff override for variable-duration services (e.g., extensions) |
| price | decimal | **Captured at booking time** — historical integrity |
| price_is_locked | boolean | Default true; false for hourly services until checkout |
| cost | decimal | Nullable — materials cost captured at booking time |
| status | enum | `pending`, `in_progress`, `completed`, `cancelled` |
| notes | text | Nullable — e.g., colour formula, "PINK", style instructions |
| created_at / updated_at | timestamptz | |

**Computed values (not stored):**
- `end_time` = `start_time + duration_minutes`
- `processing_start_time` = `start_time + service.processing_offset_minutes`
- `processing_end_time` = `processing_start_time + service.processing_duration_minutes`

**Colour processing scheduling example:**
Frederick's Color Full Color with Joanne, start 09:00:
- Joanne applies colour 09:00 → 09:45 (provider occupied)
- Processing 09:45 → 10:30 (Joanne free — Jason's Lame Color can be scheduled here)
- Rinse + finish 10:30 → 10:30+
- Frederick moves to a processing chair at 09:45; Joanne takes Jason at her application chair

---

### AppointmentReminder

Scheduled communication sent to the client before their appointment.

| Field | Type | Notes |
|-------|------|-------|
| id | uuid PK | |
| tenant_id | uuid FK → Tenant | |
| appointment_id | uuid FK → Appointment | |
| channel | enum | `email`, `sms` |
| scheduled_at | timestamptz | |
| sent_at | timestamptz | Nullable |
| status | enum | `scheduled`, `sent`, `failed`, `cancelled` |

**Open item:** Reminder timing rule (3 days before per salonlyol.ca; 2 days per owner's statement) needs a decision before Phase 1 launch.

---

## Entity Reference — Phase 2 (Skeletons)

### SecurityGroup
Configurable permission groups with per-module Allow flags. Four groups in Salon Lyol: **MANAGER**, **OWNER**, **RECEPTION**, **STAFF**.
- Relationships: Provider `}o--o|` SecurityGroup (added in Phase 2)

### ProviderCommissionTier
Tiered commission structure per provider. Service tiers and retail tiers stored separately (`tier_type` enum: `service`, `retail`). "Retroactive" flag means hitting a higher bracket applies the higher % to the whole period.
- Relationships: Provider `||--o{` ProviderCommissionTier

### ProviderGoal
Annual service and retail revenue targets, with monthly and weekly distribution percentages.
- Relationships: Provider `||--o{` ProviderGoal

### Campaign
Marketing campaign for attributing appointments to a promotional source (e.g., Instagram campaign, referral program).
- Relationships: Appointment `}o--o|` Campaign

### Promotion
Structured discount rules applied at POS checkout. Three discount types: `amount` (flat $ off), `percentage` (% off), `tax` (discount = tax amount). Can be constrained by day of week (bitmask), date range, or time window. `per_item` flag applies the discount to each service item rather than the appointment total. `commission_on_full_price` determines whether commission is calculated on the pre-discount price. Examples from Milano: DC $10, VIP 10%, REFERRAL $20, STAFF D/C, REFILL 25%.
- Relationships: SaleItem `}o--o|` Promotion (applied at line-item level)

### GiftCertificateType
Template record configuring tax treatment for a class of gift certificates (e.g., GC, GIFT). Both exclude GST and PST on purchase (correct Canadian treatment — tax collected on redemption, not sale).

### GiftCertificate
Individual issued gift card or certificate. Tracks remaining balance. Used as a payment method at POS (`Payment.gift_certificate_id`).
- Relationships: GiftCertificateType `||--o{` GiftCertificate, Client `||--o{` GiftCertificate, Payment `}o--o|` GiftCertificate

### Series
Prepaid service bundle — a client purchases N uses of a specific service at a discount. Example: 10 blowouts for $500 (20% off). Tracks quantity, unlimited usage flag, percent discount, and bundle price. **Not currently in use at Salon Lyol.**
- Relationships: Series `}o--||` Service, ClientSeries tracks per-client balances

### ClientSeries
Per-client purchase and redemption balance for a Series. `uses_remaining` decrements on each redemption.
- Relationships: Client `||--o{` ClientSeries, Series `||--o{` ClientSeries

### Deposit
Non-refundable client deposit against a future appointment. Transferable if rescheduled within policy window.
- Relationships: Client `||--o{` Deposit, Appointment `||--o{` Deposit

### Sale
POS transaction closing an appointment. Tracks gross service/retail revenue, total discounts, returns, and separately reported GST/PST for the Daily Sales Report. `receipt_number` is the Milano-compatible display reference (e.g., 50391).
- Relationships: Appointment `|o--||` Sale, Sale `||--o{` SaleItem, Sale `||--o{` Payment

### SaleItem
A line item within a sale. `item_type` distinguishes `service` (from an AppointmentItem), `retail` (retail product), `gift_certificate`, `series`. `discount_amount` records the promotion or manual discount. `is_voided` marks same-session cancellations.
- Relationships: Sale `||--o{` SaleItem, SaleItem `}o--o|` AppointmentItem, SaleItem `}o--o|` RetailProduct, SaleItem `}o--o|` Promotion

### PaymentType
Configurable payment methods (CASH, VISA, MASTERCARD, AMEX, DEBIT, GIFT, ON ACCOUNT, E-TRANSFER, INVOICE TO G). `display_order` from the Payment Type Order screen. `category_id` groups for reporting.
- Relationships: PaymentTypeCategory `||--o{` PaymentType, Payment `}o--o|` PaymentType

### PaymentTypeCategory
Groups payment types for reporting: ACCOUNT, CASH, CDCCREDIT, CDCDEBIT, CREDIT/DEBIT, ON HOUSE, POINTS, PREPAID.

### Payment
A single payment record against a sale. A sale may have multiple payments (split tender). `gift_certificate_id` populated when payment method is GIFT.
- Relationships: Sale `||--o{` Payment, Payment `}o--o|` PaymentType, Payment `}o--o|` GiftCertificate

### OnAccountTransaction
Client in-house credit/charge ledger. `transaction_type` = `charge` (positive) when services charged to account, `payment` (negative) when client settles the balance. Net sum = `Client.account_balance`. Confirmed from Daily Sales Report ("On Account Sales" line).
- Relationships: Client `||--o{` OnAccountTransaction, OnAccountTransaction `}o--o|` Sale

### RetailProduct
Retail inventory item sold directly to clients. Includes sale price window, loyalty points exemption, available-online flag for future e-commerce, and per-unit/avg cost for COGS reporting. **Brands confirmed:** AG, CEZANNE, DM, INVISI, KM, LOREAL, MILBON, MISC, MK, NEUMA, OLAPLEX, PAI-SHAU, PURE, REDKEN, SHU, WOW.
- Relationships: Brand `||--o{` RetailProduct

### ProfessionalProduct
Product consumed in service delivery — not sold to clients. Tracked for COGS and inventory purposes (L'Oreal colour, Olaplex, Milbon treatments). No sale price or tax exemption flags. **Not actively tracked via Transfers at Salon Lyol** (only one historical transfer record from 2023).
- Relationships: Brand `||--o{` ProfessionalProduct

### RetailPackage
Bundle of retail products sold together at a single price. **Not in use at Salon Lyol.** Phase 2 skeleton only.

### Brand
Product brand lookup. Confirmed values: AG, CEZANNE, DM, INVISI, KM, LOREAL, MILBON, MISC, MK, NEUMA, OLAPLEX, PAI-SHAU, PURE, REDKEN, S, SHU, WOW.

### PettyCashEntry
Individual cash disbursement from the salon till. Categories: CLEAN, DELIVERY, FOOD, MISC, OFFICE, POSTAGE. Reconciles into the Daily Sales Report's "Plus Petty Cash" line. GST/PST tracked per entry. Cashier = the provider who processed the disbursement.
- Relationships: PettyCashCategory `||--o{` PettyCashEntry, PettyCashEntry `}o--||` Provider

### PettyCashCategory
Lookup for petty cash expense types: CLEAN, DELIVERY, FOOD, MISC, OFFICE, POSTAGE.

### InventoryTransfer
Records stock movement between inventory categories (e.g., Professional → Consumed for COGS tracking). **Not actively used at Salon Lyol** — one historical record from 2023. Phase 2 skeleton.

### LoyaltyTransaction
Ledger of loyalty points earned and redeemed by clients. `points_delta` is positive for earnings, negative for redemptions. `POINTS` is a PaymentTypeCategory, confirming points can be redeemed at checkout. **Not currently active at Salon Lyol.**
- Relationships: Client `||--o{` LoyaltyTransaction, LoyaltyTransaction `}o--o|` Sale

### CrmConversation / CrmMessage
AI-assisted conversation threads with clients over email or chat. Phase 2 replaces the current manual email workflow with AI parsing.
- Relationships: Client `||--o{` CrmConversation, CrmConversation `||--o{` CrmMessage

---

## Entity Reference — Phase 3 (Skeletons)

### TenantSubscriptionPlan / TenantSubscription
SaaS billing tiers and per-tenant subscription records. Activating multi-tenancy in Phase 3 requires onboarding flow + feature flag, not schema changes.

---

## Entity Reference — Phase 4 (Skeleton)

### VoiceCall
AI voice call record — transcript, duration, linked client.

---

## Key Design Decisions

### 1. Multi-tenant from day one
Every tenant-scoped table includes `tenant_id`. Phase 1 queries filter by the single Salon Lyol tenant. Phase 3 multi-tenancy activation requires only a feature flag + onboarding flow — no schema migration.

### 2. Provider capability via ProviderServicePrice, not provider_type
`Provider.provider_type` (stylist/colourist/dualist) is informational. The `ProviderServicePrice` junction is the authoritative capability gate. This handles cross-trained providers, new services, and exceptions without schema changes.

### 3. Processing time on Service, not as separate AppointmentItems
Colour processing time is modelled as `Service.processing_offset_minutes` and `Service.processing_duration_minutes`. The scheduler computes the free window from these values. Processing chairs and shampoo sinks are not scheduled — always available at Salon Lyol's scale.

### 4. Price captured at booking time on AppointmentItem
`AppointmentItem.price` is set at booking and never updated by price list changes. Historical revenue is always accurate. `ProviderServicePrice` uses effective date ranges to preserve price change history.

### 5. AppointmentRequest stores contact info as free text
Client details on `AppointmentRequest` are strings, not FKs. The requesting person may not exist in the system yet. Staff resolve the match when converting to a confirmed Appointment.

### 6. Hourly pricing on Service
Color correction is priced per hour. `Service.pricing_type = hourly` signals `AppointmentItem.price_is_locked = false` until checkout.

### 7. no_show_count / late_cancellation_count as counters on Client
Maintained as integer counters, incremented on status change. Surfaced to staff at booking time (equivalent of Milano's Special Instructions popup). Not recomputed from history on each read.

### 8. ProviderSchedule as a weekly template with split-shift support
Weekly template keyed by `(provider_id, day_of_week, block)`. Block 1 and 2 support split shifts. `effective_to` corresponds to Milano's "Until" date on the repeat schedule. One-off exceptions go into `ProviderScheduleException`.

### 9. Department is informational in Phase 1
`Provider.department_id` FK is included but departments do not gate service capability in Phase 1. ProviderServicePrice remains the sole capability gate. Department-level service associations (from Milano's Departments screen) are a Phase 2 constraint if needed.

### 10. SIN stored encrypted at application level
`Provider.sin_encrypted` uses application-level encryption (not just disk encryption). Access restricted to `tenant_admin` role. Phase 2 consideration: move to a `ProviderSensitiveInfo` table with audit logging.

---

## Deferred / Open Items

| Item | Decision | When |
|------|----------|------|
| Appointment reminder timing | Website says 3 days before; owner said 2 days. Needs a decision before Phase 1 launch. | Before Phase 1 launch |
| `ServiceAddonRule` junction | Which add-ons attach to which primary services. Phase 1 allows any service item in any appointment; validation by convention. | Phase 2 |
| Client login / self-service portal | Clients have no login in Phase 1. Adding a portal requires `Client.user_id` FK. | Phase 3+ |
| Commission calculation rules | ProviderCommissionTier structure defined; calculation logic (retroactive vs. forward) not yet implemented. | Phase 2 |
| Deposit amount rules | Which appointment types require a deposit, and for how much. | Phase 2 |
| SecurityGroup full permission model | Phase 1 uses simplified `User.role` enum. Full per-module permission granularity deferred. | Phase 2 |
| Retail product sales | `SaleItem` can represent retail products; `Product` entity is a Phase 2 skeleton. | Phase 2 |
| Appointment request for 3+ services | Form supports 2; 3+ come via phone/email and are staff-entered. No schema change needed. | If online form expands |
| `Provider.sin_encrypted` access controls | Phase 1: role-based guard in application code. Phase 2: consider `ProviderSensitiveInfo` table with audit log. | Phase 2 |
| Loyalty points activation | POINTS payment type category and `RetailProduct.points_exempt` are modeled. Actual earning/redemption rules (points per dollar, redemption rate) not yet defined. Not active at Salon Lyol. | Phase 2+ |
| Supplier entity | Referenced by RetailProduct and ProfessionalProduct (`supplier_id`) but not yet modeled as a full entity. Add Supplier skeleton to Phase 2. | Phase 2 |
| Payroll report spec | Payroll % of Net Sales is the primary KPI. Full payroll calculation rules (ProviderCommissionTier logic, hourly rate × hours) need design before Phase 2 reporting implementation. | Phase 2 |
| Tax remittance report | Needs GST collected − GST inputs = HST net (for CRA remittance). GST inputs (claimable tax on expenses) are tracked externally today. Define whether our system tracks expense tax inputs or just the sales tax side. | Phase 2 |
