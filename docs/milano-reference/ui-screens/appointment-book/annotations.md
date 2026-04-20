# Milano Reference — Appointment Book

Screenshots from the Milano appointment book module, captured from the Salon Lyol installation on 2026-04-19. Organized by workflow rather than capture time.

---

## 1. The Appointment Book Grid

### 1.1 Day View — Full Provider Grid

![Appointment Book Grid](./Screenshot%202026-04-19%20at%204.36.29%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.36.29 PM.png`

The main appointment book in **day view**. Each column represents one provider (staff member). Visible columns left to right: Shaun, JJ, Joanne, Sarah, Olga, Mayoum, Azami, Gume, Ryan.

Row axis = time slots (15-minute increments, ruler on left edge).

**Block colour coding:**

| Colour | Meaning |
|--------|---------|
| Red | Blocked time / cancelled slot |
| Green | Confirmed / in-progress appointment |
| Yellow/tan | Regular booked appointment |
| Blue (tall column block) | Lunch break or standing blocked period |
| Dark grey | Provider unavailable (outside working hours or day off) |

**Right-side panel:** Action buttons (CallBack, Waiting, etc.) + mini-calendar for date navigation.

**Domain notes:**
- One column per active provider per day — our appointment book view must support dynamic column count as staff schedules vary.
- Dark grey (unavailable) confirms providers have defined working schedules → `ProviderSchedule` / `WorkingHours` entity needed.
- Blue block (Joanne's column, midday) is a standing blocked period, not a client appointment — blocked time is a distinct concept from an appointment.
- Block height is proportional to service duration — `AppointmentItem.duration_minutes` drives visual rendering.

---

### 1.2 Day View — After First Booking Added

![Appointment Book with CFC block](./Screenshot%202026-04-19%20at%204.42.34%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.42.34 PM.png`

Same day view after a "Color Full Color" (CFC) appointment has been created for Frederick Ferguson with Joanne. A new tan block labelled "CFC" is visible in Joanne's column. Title bar shows the logged-in staff: **Frederick Ferguson – frederick.ferguson@gmail.com**.

**Domain notes:**
- Appointment blocks display the service code (e.g. CFC) and likely the client name — `Service.service_code` is a user-visible identifier, not just an internal key.
- The logged-in user identity appears in the title bar; all actions are attributed to that session user.

---

### 1.3 Day View — Different Staff Login

![Logged in as Joanne Cooper](./Screenshot%202026-04-19%20at%204.48.08%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.48.08 PM.png`

Same appointment book, logged in as **Joanne Cooper** (`CC:MM1 – Joanne Cooper – joanne.cooper@...`). A "Cancel Wkn" (Cancel Walk-in) button is highlighted in the top-right action area.

**Domain notes:**
- The session user changes the title bar identity and may expose different action buttons — implies a role/permission layer.
- "Cancel Wkn" as an explicit button suggests walk-in management is a first-class action, not just a status change.

---

### 1.4 Day View — Client-Level Login

![Logged in as Jason Cooper](./Screenshot%202026-04-19%20at%204.49.07%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.49.07 PM.png`

Appointment book logged in as **Jason Cooper** (`ST301 – Jason Cooper – jasoncooper@...`). A new appointment block appears in Gume's column (far right).

**Domain notes:**
- A client-level or limited-access login exists in Milano — our `User` → `Role` model should accommodate at minimum `staff` and `client` roles.
- The `ST301` prefix in the login code may indicate a role/access tier.

---

## 2. Creating a New Booking

### 2.1 New Booking Dialog — Initial State

![New Booking dialog blank](./Screenshot%202026-04-19%20at%204.37.29%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.37.29 PM.png`

The **New Booking** dialog, opened by clicking a time slot in a provider's column. The Staff field is pre-populated from the column clicked (Shaun here).

| Field | Notes |
|-------|-------|
| **Staff** | Pre-filled from the column clicked; editable |
| **Client** | Lookup — triggers Find Client dialog |
| **Contact Number** | Auto-filled from client record |
| **Service** | Dropdown scoped to this provider's capabilities |
| **Request** | Free-text special requests |
| **Campaign** | Marketing campaign attribution |

Checkboxes:
- **Include client card when printing** — attach client record to printed booking slip
- **Make this a standing appointment** — create a recurring appointment

Link: **Pre-Book** — book a follow-up/future appointment.

**Domain notes:**
- Staff pre-fill from column click sets `AppointmentItem.provider_id` at creation time.
- "Make this a standing appointment" → `Appointment.is_recurring` flag or a `RecurringAppointment` entity.
- Campaign field → `Appointment.campaign_id` FK for marketing attribution.
- "Pre-Book" suggests a forward-booking workflow — a separate future `Appointment` linked to the current visit.

---

### 2.2 Find Client Dialog

![Find Client dialog](./Screenshot%202026-04-19%20at%204.38.00%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.38.00 PM.png`

The **Find Client** search dialog. Search tabs: First Name, Last Name, Phone, Code. Results grid:

| Column | Notes |
|--------|-------|
| First Name | |
| Last Name | |
| Staff | Client's preferred/assigned staff member |
| Home | Home phone |
| Work | Work phone |
| Cell | Cell phone |
| Code | Short client identifier (e.g., FERGF1) |

**Domain notes:**
- `Client` has three separate phone fields (home, work, cell) — not a single `phone` column.
- **Staff column** in results confirms `Client.preferred_staff_id` FK.
- **Client Code** is a short alphanumeric identifier — `Client.client_code`, likely generated as last-name-prefix + first-name-initial + sequence number (e.g., FERGF1 = Ferguson, Frederick, 1st).

---

### 2.3 Find Client — Search Results (Frederick)

![Find Client Frederick results](./Screenshot%202026-04-19%20at%204.38.12%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.38.12 PM.png`

Search results for "Frederick": Freda, Frederick Donovan, Frederick Ferguson. Each row includes preferred Staff and client code.

---

### 2.4 Find Client — Single Result (Frederick Shah)

![Find Client single result](./Screenshot%202026-04-19%20at%204.40.58%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.40.58 PM.png`

Single result: Frederick Shah, phone (416) 201-7100, code SHAFS1. Illustrates that the same search path is used regardless of result count.

---

### 2.5 Find Client — Full Client List (A–Z)

![All clients list](./Screenshot%202026-04-19%20at%204.45.51%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.45.51 PM.png`

Find Client with no filter applied, showing all clients starting with "A" surnames. Dozens of entries visible (ALANA1, MESAO1, etc.). Confirms client volume at Salon Lyol is substantial.

**Domain notes:**
- API client search must support prefix/LIKE matching on name and exact match on code and phone number.
- Code pattern confirmed: last-name prefix + first-name initial + sequence digit.

---

### 2.6 Find Client — Code Fragment Search ("JASAM")

![Find Client JASAM](./Screenshot%202026-04-19%20at%204.46.06%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.46.06 PM.png`

Searching by code fragment "JASAM" returns multiple Jason clients: Cooper (CCOUJ1), Fleming (FLEJA1), Grimson (GRIAJ1), Lim (LINJ1), Schultz (SCHUJ1), Schwartz (SCHWA1).

---

### 2.7 Find Client — Row Selected (Jason Fleming)

![Jason Fleming selected](./Screenshot%202026-04-19%20at%204.46.28%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.46.28 PM.png`

Jason Fleming's row highlighted. Phone: (416) 797-0102. Code: FLEJA1. Preferred staff: JJ.

---

### 2.8 New Booking — Client Selected (Joanne's Column)

![New Booking Joanne with client](./Screenshot%202026-04-19%20at%204.40.40%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.40.40 PM.png`

New Booking dialog for Joanne (column highlighted in background), with a client partially entered. Demonstrates that clicking a specific provider's column pre-assigns the provider — the booking dialog is always provider-anchored.

---

### 2.9 New Booking — Frederick Ferguson Selected

![New Booking Frederick selected](./Screenshot%202026-04-19%20at%204.41.31%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.41.31 PM.png`

Frederick Ferguson selected as the client. Contact Number auto-populated. Service field awaiting selection.

---

### 2.10 Special Instructions Popup — Cancellation/No-Show Stats

![Special Instructions with stats](./Screenshot%202026-04-19%20at%204.39.38%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.39.38 PM.png`

When a client is selected, Milano may immediately display a **Special Instructions** popup containing:
- Free-text instructions/notes area
- **Cancellations %** — client's historical cancellation rate
- **No Shows %** — client's historical no-show rate

Buttons labelled "Cancellations %" and "No Shows %" (drill-down to full history).

**Domain notes:**
- Cancellation and no-show rates are surfaced at booking time as a risk signal to staff.
- These are either stored as derived counters on `Client` or computed from `Appointment.status` history. Given the 50%/100% charge policy, accurate per-client history is important.
- The free-text area = `Client.special_instructions` or `Client.notes`.
- This popup is the primary enforcement mechanism for the cancellation policy — staff see the client's track record before confirming.

---

### 2.11 Special Instructions Popup — For Joanne Booking

![Special Instructions Joanne](./Screenshot%202026-04-19%20at%204.41.13%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.41.13 PM.png`

Same Special Instructions popup triggered for a booking in Joanne's column — confirms the popup fires per client regardless of which provider's column initiated the booking.

---

### 2.12 Special Instructions — VIP Client Note

![VIP Special Instructions](./Screenshot%202026-04-19%20at%204.46.45%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.46.45 PM.png`

Special Instructions popup for a different client showing: **"VIP 18% with JJ"** — this client is a VIP and always receives an 18% service gratuity arrangement with stylist JJ.

**Domain notes:**
- VIP and preferred-staff arrangements are currently free-text in `Client.notes` — no structured VIP flag.
- A future `client_tier` or `is_vip` boolean could surface this more systematically in the UI.

---

### 2.13 Service Selection — Colour Services (Joanne)

![Service dropdown colour Joanne](./Screenshot%202026-04-19%20at%204.41.56%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.41.56 PM.png`

Service dropdown for **Joanne** (colourist). Partial list:

| Code | Service name |
|------|-------------|
| | Additional colour |
| | Balayage-Full |
| | Balayage-Partial (Fade) |
| CCC | Colour connection |
| CCO | Colour cut color |
| CCU | Colour cut upper |
| CGT | Color gloss toner |
| CLOB | Colour lab balayage |
| CLON | Colour blonde |
| COLC | Colour connection |
| COM | Consultation |
| CPHL | Partial Head highlights |
| CPRU | Root Touch-up |
| CSTU | Root Touch-up |
| CTGH | Root Touch-up (Beach/Hig,B) |
| CTSA | Sauvignon Stand Alone |

**Domain notes:**
- Services have both a short **code** (3–4 chars) and a human-readable name → `Service.service_code` + `Service.name` both required.
- Dropdown is scoped to what Joanne can deliver, confirming the `ProviderServicePrice` junction filters the service list.
- Multiple Root Touch-up variants exist (CPRU, CSTU, CTGH) — service granularity is finer than top-level category names suggest.

---

### 2.14 Service Selection — Extended Colour List (Joanne)

![Service dropdown extended Joanne](./Screenshot%202026-04-19%20at%204.47.06%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.47.06 PM.png`

Joanne's service dropdown scrolled to reveal additional entries including "Foliage cut" — a styling-adjacent service delivered by a colourist.

**Domain notes:**
- A colourist offering "Foliage cut" confirms that provider type is informational only. The `ProviderServicePrice` junction is the authoritative source of "can this provider deliver this service?"

---

### 2.15 Service Selected — Lame Color (Joanne)

![Lame color selected](./Screenshot%202026-04-19%20at%204.42.19%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.42.19 PM.png`

"Lame color" selected. Service code displayed alongside name. OK button enabled.

---

### 2.16 Service Selected — Lame Color for Jason (Joanne)

![Lame color for Jason](./Screenshot%202026-04-19%20at%204.47.21%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.47.21 PM.png`

Same service ("Lame color") booked for a different client (Jason) with Joanne. Demonstrates same service can be booked for multiple clients on the same day.

---

### 2.17 Service Selection — Stylist Services (Mayoum / Dualist)

![Service dropdown Mayoum](./Screenshot%202026-04-19%20at%204.44.36%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.44.36 PM.png`

Service dropdown for **Mayoum** — includes both colour and styling services, indicating Mayoum is a **Dualist**. The combined list confirms that a Dualist's `ProviderServicePrice` entries span both colour and styling service categories.

---

### 2.18 Service Selected — Type 1 Haircut (Mayoum)

![Type 1 Haircut Mayoum](./Screenshot%202026-04-19%20at%204.45.02%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.45.02 PM.png`

"Type 1 Haircut" selected for Mayoum. Confirms that haircut classification (Type 1 / Type 2 / Type 2+) is the service name itself — maps to `Service.name` where haircut_type is a property of the Service entity.

---

### 2.19 Service Selection — Stylist Services (Gume)

![Service dropdown Gume](./Screenshot%202026-04-19%20at%204.48.44%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.48.44 PM.png`

Service dropdown for **Gume** (stylist). Notable entries:

| Code | Service name |
|------|-------------|
| MITAL | Milaz Demo |
| MITAD | Milano Treatment Addon |
| MTSA | Milano Treatment Stand Alone |
| SDDDV1 | Blowdry bundle 1+1 |
| SDDDV | Extra reimbursement by house |
| STY1N | Type 1 Haircut |
| STY2N | Type 2 Haircut |
| STY2+ | Type 2+ Haircut |
| TREA | Treatment |
| GLY | Blowdry |

**Domain notes:**
- **SDDDV1 (Blowdry bundle 1+1)** is legacy data — bundles are no longer offered. Our system will not model a bundle/package entity.
- Treatment has an addon variant (MITAD) + standalone (MTSA) — two service entries for the same treatment category.
- "Extra reimbursement by house" (SDDDV) appears to be an internal accounting service, not client-facing.

---

### 2.20 Service Selected — Type 2 Haircut (Gume)

![Type 2 Haircut Gume](./Screenshot%202026-04-19%20at%204.48.55%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.48.55 PM.png`

"Type 2 Haircut" selected for Gume. Client is Jason Cooper (email visible in title bar). Together with screenshot 2.16, this shows Jason has a same-day multi-provider appointment: Joanne (colour) + Gume (haircut).

---

### 2.21 Edit Booking Dialog

![Edit Booking](./Screenshot%202026-04-19%20at%204.43.27%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.43.27 PM.png`

The **Edit Booking** dialog for an existing appointment: Frederick Ferguson, service "Color full color", provider Joanne. The dialog is identical to New Booking — same fields, same layout, different title.

**Domain notes:**
- Create and edit share the same data model. No separate "draft" vs "confirmed" entity distinction at the dialog level — status is managed via the `Appointment.status` field.

---

## 3. Appointment Book — After Multiple Bookings

### 3.1 Book Finalised (logged in as Frederick Ferguson)

![Appointment book after CFC created](./Screenshot%202026-04-19%20at%204.42.34%20PM.png)

*(See also Section 1.2 above)*

---

### 3.2 Book with Joanne's New Booking Highlighted

![Joanne column highlighted](./Screenshot%202026-04-19%20at%204.44.08%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.44.08 PM.png`

Appointment book with Mayoum's column active (highlighted). CFC block visible in Joanne's column from the previous booking. Title bar shows `CFC – Frederick Ferguson – frederick.ferguson@gmail.com`.

---

### 3.3 Book with Jason Cooper's Appointments

![Appointment book Jason Cooper session](./Screenshot%202026-04-19%20at%204.49.07%20PM.png)

*(See also Section 1.4 above)*

Jason Cooper's appointment blocks visible in Joanne's and Gume's columns — a live example of the multi-provider appointment model (colour + cut on the same visit).

---

## 4. Customer Relation Management (CRM)

### 4.1 Client Record — Frederick Ferguson

![CRM Frederick Ferguson](./Screenshot%202026-04-19%20at%204.49.55%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.49.55 PM.png`

Full CRM record for Frederick Ferguson.

**Client details panel:**

| Field | Value |
|-------|-------|
| Home | (416) ... |
| Work | (416) ... |
| Cell | (416) 253-3943 |
| Address | Toronto, Ontario M4T 0Y1 |
| Email | frederick.ferguson@gmail.com |
| On Account | (balance visible) |
| Family | (linked family members) |
| References | (referral source) |

**Sales History (partial):**

| Date | Description | Staff |
|------|-------------|-------|
| 6/22/26 | Camo color | SARAH |
| | Type 2 haircut | |
| | Lame color | SARAH |
| | Type 1 haircut | JJ |
| | Consultation | JJ |

**Future Appointments:**

| Date/Time | Staff | Service code |
|-----------|-------|-------------|
| 04/21/26 9:40a | JOANNE | CFC |
| 04/21/26 10:00a | RYAN | ST3H |

Free-text **Comments** area at bottom. **Photo** placeholder (NO PHOTO).

**Domain notes:**
- `Client` confirmed fields: first_name, last_name, home_phone, work_phone, cell_phone, address_line, city, province, postal_code, email, notes.
- **On Account** → client can carry a balance; relevant for Phase 2 POS → `Client.account_balance` or a separate `ClientLedger`.
- **Family** field → `ClientHousehold` or `Client.household_id` FK — family members may share an account.
- **References** → referral source; either `Client.referred_by_client_id` or a `referral_source` enum (word of mouth, Google, etc.).
- Sales History = historical `AppointmentItem` records with service name, staff, and date.
- Future Appointments = upcoming confirmed `Appointment` records.
- **Photo** → `Client.photo_url` — store in object storage (GCS/Azure Blob), not in the DB row.

---

### 4.2 Client Record — Jason Cooper

![CRM Jason Cooper](./Screenshot%202026-04-19%20at%204.50.11%20PM.png)

**File:** `Screenshot 2026-04-19 at 4.50.11 PM.png`

CRM record for Jason Cooper — a primarily styling client (men's haircuts).

**Client details:**

| Field | Value |
|-------|-------|
| Home | (416) ... |
| Work | (416) 443... |
| Cell | (416) 392-870... |
| Address | Toronto, Ontario M4T 0Y1 |
| Email | jasoncooper@gmail.com |

**Sales History (partial):**

| Date | Description | Staff |
|------|-------------|-------|
| 4/17/26 | Type 1 Festival | JJ |
| 11/30/26 | Type 2 Men's hair cut | JJ |
| ... | Men's hair cut | JJ |
| 6/9/26 | YUXX Men's hair cut PINK | |

**Future Appointments:**

| Date/Time | Staff | Service code |
|-----------|-------|-------------|
| 04/21/26 9:40a | JOANNE | CCAMO |
| 04/21/26 10:00a | GUMI | ST3H |

**Domain notes:**
- Jason's future appointments show two providers on the same day (JOANNE + GUMI) — live confirmation of the multi-provider appointment model.
- "YUXX Men's hair cut PINK" — the colour descriptor ("PINK") appears to be appended to the service name or stored in a notes field on the AppointmentItem. Suggests `AppointmentItem.notes` for colour-specific instructions.
- "Type 1 Festival" is a named variant of Type 1 — may be a distinct service entry or a notes qualifier.

---

## 5. Summary of ERM Implications

| Observation | Implication for data model |
|-------------|---------------------------|
| One column per provider per day | `ProviderSchedule` entity with daily working windows |
| Dark grey = unavailable | `ProviderSchedule.is_working` or working hour windows |
| Block height ∝ duration | `AppointmentItem.duration_minutes` |
| Service dropdown scoped per provider | `ProviderServicePrice` junction confirmed |
| Haircut Type 1 / 2 / 2+ visible as service names | `Service.haircut_type` enum |
| Client codes (e.g. FERGF1) | `Client.client_code` generated field |
| Three phone fields (home / work / cell) | Separate columns, not a single `phone` |
| Preferred staff on client record | `Client.preferred_staff_id` FK |
| Special Instructions shown at booking time | `Client.special_instructions` text field |
| Cancellation % / No-show % surfaced at booking | Derived from `Appointment.status` history; possibly cached as counts on `Client` |
| Standing appointments checkbox | `Appointment.is_recurring` flag or `RecurringAppointment` entity |
| Campaign field on booking | `Appointment.campaign_id` FK |
| On Account on client | `Client.account_balance` or `ClientLedger` (Phase 2) |
| Family field on client | `Client.household_id` or `ClientHousehold` entity |
| References field on client | `Client.referred_by_client_id` FK or `referral_source` enum |
| Photo placeholder | `Client.photo_url` — object storage, not DB |
| Multi-provider same-day (JOANNE + GUMI for Jason) | Appointment container model confirmed in live data |
| Colourist free during processing (Jason booked in Frederick's processing window) | `Service.processing_offset_minutes` + `Service.processing_duration_minutes` on the service definition; provider available during that window |
| Processing chairs and shampoo sinks always available | These stations are NOT modelled as bookable resources — managed informally by staff |
| Primary station per provider | `AppointmentItem.station_id` references only the provider's working station (colour_application or styling chair); station_type enum: `styling`, `colour_application`, `multi_purpose` |
| VIP note in Special Instructions | Informal today; candidate for `Client.is_vip` boolean |
| AppointmentItem notes (e.g. "PINK" hair colour) | `AppointmentItem.notes` free-text field |
| Blowdry bundle (SDDDV1) in legacy data | Bundles no longer offered; no `Package` entity needed |
| Role-differentiated UI (staff vs. client login) | `User` → `Role` model; at minimum `staff` and `client` roles |
