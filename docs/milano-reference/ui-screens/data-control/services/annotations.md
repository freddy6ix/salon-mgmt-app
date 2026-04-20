# Milano Reference — Data Control → Services

Screenshots from the Milano service definition module, captured from the Salon Lyol installation on 2026-04-19. This module is where services are defined, default prices set, processing time configured, and per-provider price overrides entered.

---

## 1. Service Record — No Provider Overrides

![Service record empty staff chart](./Screenshot%202026-04-19%20at%205.22.53%20PM.png)

**File:** `Screenshot 2026-04-19 at 5.22.53 PM.png`

A service record (appears to be a colour service — Color Full Color or similar) with no provider-level price overrides entered. The Staff Chart section reads: *"Only Staff who can perform this service"* with an empty grid.

**Left sidebar:** Full service code list visible, including: CAD, CAKE, CB, CCBD, CCABO, CCC, CPHL, CON, CONE, CREO, CPRUE, CPAD, CTGH, CVC, FRINGE, HBR and others.

**Service record fields:**

| Field | Notes |
|-------|-------|
| Description | Service name |
| Category | Service category (dropdown) |
| Price | Default price for this service |
| VAT Exempt | Tax exemption flag |
| Add Comm | Whether commission applies |
| PST Exempt | Provincial tax exemption flag |

**Right side — Time Grid:** Visual representation of the service's time blocks. Shows the total booking slot divided into time increments — the highlighted cells represent the service duration and, for colour services, distinguish active time from processing time.

**Bottom:** Year-to-date sales: **$50,071.00** | Last year's sales: $0.00

**Domain notes:**
- The service list on the left confirms service codes are 3–5 characters, matching what's visible in the appointment book.
- `Service` entity confirmed fields: `service_code`, `name`, `category`, `default_price`, `is_vat_exempt`, `is_commission_applicable`, `is_pst_exempt`.
- The time grid is how Milano captures `duration_minutes` and `processing_duration_minutes` — a visual time-slot picker, not a numeric field.
- Year-to-date sales tracking at the service level → either derived from `AppointmentItem` aggregates or cached on `Service`. Our system will derive this from `AppointmentItem` records rather than storing a denormalized counter.

---

## 2. Service Record — With Provider Price Override

![Service record with Joanne Strilo override](./Screenshot%202026-04-19%20at%205.23.10%20PM.png)

**File:** `Screenshot 2026-04-19 at 5.23.10 PM.png`

A service record (Root highlights or similar) showing a provider-level price override. Default price appears to be ~$110 with a 15% commission rate.

**Staff Chart — Provider overrides:**

| Staff | Price | Cost |
|-------|-------|------|
| Joanne Strilo | $195.00 | $50.00 |

The time grid on the right shows highlighted blocks spanning the service duration, with a visually distinct segment representing the **processing time** window — the portion where the service is in progress (colour developing) but the provider is free.

**Domain notes:**
- `ProviderServicePrice` confirmed fields: `provider_id`, `service_id`, `price`, `cost`. The `cost` field represents materials cost (colour product, etc.) used for margin and commission calculation — not just pricing.
- The default service price and the provider override price can differ substantially ($110 default vs. $195 for Joanne) — confirming that per-provider pricing is the norm, not an exception.
- **Processing time is a service-level attribute**, not a scheduling entity. The time grid shows it as a property of the service definition. This means `Service.processing_duration_minutes` (or equivalent) is stored on the service, and the scheduler uses it to determine the provider's free window during a booking.
- The Staff Chart being per-service (not per-provider) means the primary key of `ProviderServicePrice` is `(provider_id, service_id)` — a provider is linked in to a service, not the other way around.

---

## 3. Key Domain Decisions Confirmed by These Screenshots

### 3.1 Processing Time Lives on the Service

Milano stores processing time as a property of the service definition (the time grid). This resolves Open Question #1 from `appointment-model.md`:

**Decision:** Model processing time on `Service`, not as a separate `AppointmentItem`.

```
Service
├── duration_minutes          total slot length (application + processing + finish)
├── processing_offset_minutes when processing starts (minutes after service begins)
└── processing_duration_minutes how long the provider-free window lasts
```

The scheduler uses `processing_offset_minutes` and `processing_duration_minutes` to determine when the provider becomes free within a booking — enabling back-to-back colour clients without a gap.

### 3.2 Processing Chairs and Shampoo Sinks Are Not Scheduled

Salon Lyol has 2 dedicated colour processing chairs + 2 multi-purpose chairs + 4 shampoo sinks. Given the number of concurrently scheduled colourists (typically 2–3 at peak), there is always a processing chair and shampoo sink available. These stations are **not** modelled as bookable resources in the scheduling system.

**Decision:** `AppointmentItem.station_id` references only the provider's primary working station (colour application chair or styling chair). Processing chair and shampoo sink assignment is handled informally by staff.

**Station types that DO need to be modelled** (because they constrain scheduling):
- `styling` — 6 chairs, each assigned to a specific stylist
- `colour_application` — 3 chairs, each assigned to a specific colourist
- `multi_purpose` — 2 chairs, shared/unassigned

**Station types managed informally (not scheduled):**
- `colour_processing` — 2 chairs
- `shampoo_sink` — 4 sinks

### 3.3 ProviderServicePrice Includes Cost

`ProviderServicePrice` needs a `cost` column for materials cost (e.g., colour product cost per application). Used for commission calculation and margin reporting.

### 3.4 Salon Operating Hours

Salon Lyol is open Tuesday–Saturday only:

| Day | Hours |
|-----|-------|
| Monday | Closed |
| Tuesday | 9 a.m. – 6 p.m. |
| Wednesday | 9 a.m. – 8 p.m. |
| Thursday | 9 a.m. – 8 p.m. |
| Friday | 9 a.m. – 6 p.m. |
| Saturday | 9 a.m. – 5 p.m. |
| Sunday | Closed |

**Implication:** A `SalonHours` or `TenantOperatingHours` entity is needed to define valid booking windows per day of week. The appointment book should not allow bookings outside these windows. In Phase 3 (multi-tenant), each tenant has their own operating hours.

### 3.5 Staff Work 4-Day Weeks (Except Owner)

Most staff work 4 days per week. The owner **Jini (JJ)** works all 5 operating days. Each staff member's working days are captured in `ProviderSchedule` — their column only appears in the appointment book on days they are scheduled to work.
