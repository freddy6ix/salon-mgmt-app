# Salon Lyol Website Reference — Services, Pricing & Team

Extracted from salonlyol.ca on 2026-04-19. Source pages: /styling, /colouring, /extensions, /our-team, /cancellation-policy.

---

## 1. Service Catalogue

### 1.1 Styling Services

| Service | Price range | Notes |
|---------|-------------|-------|
| Blowdry | $55–$70 | Deliverable by stylists and dualists |
| Type 1 Haircut | $55–$80 | Clippers-based: dusting, crew cuts, fades, short cuts |
| Type 2 Haircut | $90–$125 | Scissors-based: short, mid-length, long haircuts. Most popular. |
| Type 2+ Haircut | $115–$150 | Hair redesign, extra long or large volume |
| Fringe / Bang Cut | $20 | Flat rate across all providers |
| Heat Tool Finish | $10 | Add-on only |
| Updo | $140–$150 | Select providers only |
| Hair Botox | $400 | Smoothing treatment; lasts up to 6 months |
| Milbon Treatment (standalone) | $100 | Deep nourishing; lasts up to 5 weeks |
| Milbon Treatment (add-on) | $65 | Add-on to another service |

### 1.2 Colouring Services

| Service | Price range | Notes |
|---------|-------------|-------|
| Root touch-up | $90 | Assumes < 1.5" regrowth |
| Root touch-up (bleach/lightener/high lift) | $100 | |
| Accent highlights (up to 15 foils) | $100–$120 | |
| Partial head highlights | $130–$150 | |
| Full head highlights | $170–$190 | |
| Balayage touch-up | $190–$210 | |
| Full balayage | $240–$260 | |
| Color correction | $100–$120 / hour | **Hourly pricing** — price calculated at checkout |
| Toner / gloss / clear (standalone) | $85 | |
| Refreshing ends | $50 | |
| Additional colour | $25 | |
| Toner / gloss / clear (add-on) | $50 | |
| Metal Detox / Olaplex (add-on) | $35 | |
| Milbon Treatment (add-on) | $65 | |
| Hair Botox | $400 | Also listed under Styling |

### 1.3 Extension Services

| Service | Starting price | Duration estimate |
|---------|---------------|-------------------|
| Fusion | $400+ | 4+ hours |
| Microbead | $400+ | 4+ hours |
| Tape-in | $250+ | 2+ hours |
| Weft | $250+ | 2+ hours |
| Tightening | $150+ | 1.5+ hours |
| Remove & shampoo blowdry | $150+ | 2.5+ hours |
| Rebonding | $100+ | 1.5+ hours |
| Retaping | $100+ | 1.5+ hours |

**Important notes on extensions:**
- Installation price does not include the cost of hair
- All prices subject to change depending on colourist, product used, or time required
- A **mandatory consultation at least one week prior** to installation is required
- No provider-differentiated pricing listed (unlike styling and colouring)

---

## 2. Team Roster

| Name (Milano code) | Title | Type | Specialties |
|--------------------|-------|------|-------------|
| **JJ** (Jini) | Owner, Master Stylist | Stylist | Works all 5 operating days (Tue–Sat) |
| **Antonella** | Senior Stylist, Bridal Specialist | Stylist | Precision cuts, creative updos, bridal |
| **Sarah** | Senior Colourist, Extensions Specialist | Colourist | Balayage, fashion colour, all extension methods |
| **Joanne** | Lead Colour Specialist | Colourist | General colour |
| **Becky** | Senior Stylist, Smoothing Specialist | Stylist | MK Hair Botox smoothing treatments |
| **Olga** | Senior Dualist, Airbrush Highlights | Dualist | Airbrush highlights; trilingual |
| **Mayumi** | Dualist, Balayage Specialist | Dualist | Natural/tonal balayage on bobs and layered cuts |
| **Asami** | Senior Stylist, Perm Specialist | Stylist | Japanese-certified stylist, 15 years experience |

**Notes:**
- 8 staff total: 2 colourists, 4 stylists, 2 dualists
- Most staff work 4 days per week; JJ works all 5 operating days
- Milano appointment book also shows **Ryan** and **Gume** in provider columns — these may be current staff not yet listed on the website, or former staff whose records remain active in Milano

---

## 3. Key ERM Implications

### 3.1 Pricing Types

Not all services are fixed-price. Two pricing types confirmed:

| Type | Example | Implication |
|------|---------|-------------|
| `fixed` | Root touch-up ($90) | `AppointmentItem.price` set at booking from `ProviderServicePrice` |
| `hourly` | Color correction ($100–$120/hr) | `AppointmentItem.price` calculated at checkout from actual duration; `Service.pricing_type` enum needed |

`Service` entity needs: `pricing_type` enum (`fixed`, `hourly`).
`AppointmentItem` needs: `price_locked` boolean — false for hourly services until checkout.

### 3.2 Add-On Services

Several services are explicitly add-ons to a primary service:

| Add-on service | Can attach to |
|----------------|--------------|
| Toner/gloss/clear | Colour services |
| Metal Detox / Olaplex | Colour services |
| Milbon Treatment | Colour or styling services |
| Heat Tool Finish | Haircuts / styling |

`Service` entity needs: `is_addon` boolean.
Optional: a `ServiceAddonRule` junction table defining which primary services each add-on can attach to (for UI validation). This can be deferred to Phase 2 if Phase 1 simply allows staff to add any service item to an appointment.

### 3.3 Extension Consultation Prerequisite

Hair extension installation requires a consultation appointment at least one week prior. This is a booking rule, not a scheduling constraint.

`Service` entity needs: `requires_prior_consultation` boolean.
The booking workflow should warn staff (not hard-block) when an extension service is booked without a prior consultation in the client's history.

### 3.4 Per-Provider Pricing Scope

Fringe/Bang Cut is $20 flat across all providers — not every service has per-provider price variation. The `ProviderServicePrice` junction stores overrides; the `Service.default_price` is the fallback when no provider override exists.

### 3.5 Extensions — Variable Duration

Extension services use "+" durations (e.g., "4+ hours") — duration is an estimate, not fixed. `Service.duration_minutes` represents the minimum/typical duration. For extensions, staff may need to override duration at booking time.

`AppointmentItem` needs: `duration_override_minutes` (nullable) — populated when a staff member manually adjusts the duration from the service default.

### 3.6 Service Categories Confirmed

Three top-level categories: **Styling**, **Colouring**, **Extensions**.

`ServiceCategory` entity: `id`, `name`, `tenant_id`.

### 3.7 Cancellation & No-Show Policy (from /cancellation-policy)

| Scenario | Charge |
|----------|--------|
| Cancel 2+ days before | No charge; may reschedule |
| Cancel < 2 days before | 50% of scheduled services |
| Same/next-day booking: cancel < 4 hrs before | 50% of scheduled services |
| No-show | 100% of scheduled services |

Reminders sent approximately 3 days prior. Deposits are non-refundable but transferable to a future appointment if rescheduled within a specified window.

`Appointment` entity needs: `cancellation_charge_pct` (populated when cancelled; 0, 50, or 100).
`Client` entity: aggregate no-show and cancellation counts surfaced at booking time (as seen in Milano Special Instructions popup).
