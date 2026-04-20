# Salon Lyol Website Reference — Booking Request Form

Source: Google Form used for online appointment requests.
URL: https://docs.google.com/forms/d/1DfAmK0wOhigCrDPzpZaEnDOkzyPBsu_AzmvL40Qo6ms
Captured: 2026-04-19

This form is the client-facing entry point for appointment requests submitted via salonlyol.ca. Submissions flow into the salon; staff review them and confirm bookings in Milano.

---

## Form Fields

### Client Identity

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| First Name | Yes | Text | |
| Last Name | Yes | Text | |
| Email | Yes | Email | Used for confirmations and reminders |
| Phone | Yes | Text | |
| Pronouns | No | Text | Gender-neutral service context |
| Name of person completing form on behalf of Guest | No | Text | Third-party booking (e.g. parent, partner) |

### Appointment Details

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| Desired Booking Date | Yes | Date picker (MM/DD/YYYY) | Preferred date — not guaranteed |
| Desired Booking Time | Yes | Free text | No time picker; client types a preference |

### Service Selections (up to 2)

Two service slots, each with:

| Field | Required | Type |
|-------|----------|------|
| Service (dropdown) | Yes (at least 1) | Dropdown |
| Preferred Staff (dropdown) | Yes | Dropdown |

**Service dropdown options:**
- Consultation
- Type 1–2+ Haircuts
- Shampoo Blowdry
- Special Updo
- Root touch-ups
- Camo Colour
- Highlight options (Accent / Partial / Full)
- Balayage options
- Colour correction
- Toner / gloss
- Refreshing ends
- Treatments (Metal Detox / Olaplex)
- Japanese Milbon options
- Hair Botox Smoothing Treatment

**Staff dropdown options (both Service 1 and Service 2):**
Asami, Gumi, JJ, Joanne, Mayumi, Olga, Ryan, Sarah

### Acknowledgments (both required)

| Field | Notes |
|-------|-------|
| Waiver and Release | Client consents to salon waiver |
| Cancellations and Refunds Policy | Client acknowledges the cancellation/no-show charge policy |

### Additional

| Field | Required | Notes |
|-------|----------|-------|
| Special Note | No | Free text — allergies, accessibility needs, style notes, etc. |

---

## Key Domain Observations

### AppointmentRequest Entity

The Google Form submission becomes an `AppointmentRequest` record in our system. Fields map as follows:

```
AppointmentRequest
├── id
├── tenant_id
├── first_name                   (from form)
├── last_name                    (from form)
├── email                        (from form)
├── phone                        (from form)
├── pronouns                     (from form, optional)
├── submitted_by_name            (from "on behalf of" field, optional)
├── desired_date                 (from form)
├── desired_time_note            (free text — not a structured time)
├── special_note                 (from form, optional)
├── waiver_acknowledged          (boolean — must be true to submit)
├── cancellation_policy_acknowledged (boolean — must be true to submit)
├── status                       (new / reviewed / converted / declined)
├── converted_to_appointment_id  (FK → Appointment, set when staff confirm)
└── submitted_at                 (timestamp)
```

Each form submission can include up to 2 service requests:

```
AppointmentRequestItem
├── id
├── request_id                   (FK → AppointmentRequest)
├── sequence                     (1 or 2)
├── service_name                 (text — as selected in form dropdown)
├── preferred_provider_name      (text — as selected in form dropdown)
└── converted_to_item_id         (FK → AppointmentItem, set when confirmed)
```

**Why store service and provider as text (not FKs) on the request?**
The request is submitted by a client before any staff review. The service name and provider name from the form may not map 1:1 to internal `Service` and `Provider` records (different naming, or the requested provider is unavailable). Staff resolve the mapping when converting the request to a confirmed `Appointment`.

### Staff Confirmation Workflow

```
AppointmentRequest (status: new)
    → staff reviews
    → creates Appointment + AppointmentItems with real provider/time/service assignments
    → AppointmentRequest.status = converted
    → AppointmentRequest.converted_to_appointment_id = <new appointment id>
```

The request record is preserved for audit and CRM history even after conversion.

### Maximum 2 Services per Online Request

The form supports up to 2 service slots. Multi-service appointments with 3+ services must be handled by phone or email, or added by staff after the initial booking is confirmed.

### Desired Time is Free Text

Clients type their preferred time rather than selecting from a picker. Staff interpret this when confirming. Our system should store this as a text field (`desired_time_note`) rather than a structured `time` type — it may say "morning", "after 2pm", "anytime", etc.

### Policy Acknowledgment at Request Time

Both the Waiver and the Cancellations Policy are acknowledged at the point of online request — before staff confirm. This is important for the cancellation charge model: clients cannot claim ignorance of the policy for online bookings.

`AppointmentRequest.waiver_acknowledged` and `cancellation_policy_acknowledged` should both be non-nullable booleans, defaulting false, and the form should prevent submission unless both are true.

### Third-Party Booking

The "on behalf of" field means the submitter may not be the client receiving services. `AppointmentRequest.submitted_by_name` captures this. When staff convert the request, they match to the actual client record (the guest), not the submitter.

---

## Current Workflow — Email Delivery

The Google Form currently sends a formatted email to **info@salonlyol.ca** on each submission. Staff read the email and manually enter the booking into Milano. There is no direct integration between the form and Milano.

### Email format (actual example)

**Subject:** `NEW Booking Request - Frederick Ferguson - frederick.ferguson@gmail.com - 2293476511`

**Body:**

| Field | Value |
|-------|-------|
| FROM | Frederick Ferguson |
| PRONOUNS | he |
| EMAIL | frederick.ferguson@gmail.com |
| PHONE | 2293476511 |
| SUBMITTED BY | self |
| WAIVER? | I acknowledge and agree. |
| CANCELLATIONS? | I acknowledge and agree. |
| DATE | 4/13/2026 |
| TIME | anytime |
| SERVICE 1 | Special Updo |
| STAFF 1 | Asami |
| SERVICE 2 | Type 1 Haircut |
| STAFF 2 | JJ |
| NOTE | just testing |

### Implications for Phase 1

**The Google Form + email workflow will be replaced by a native booking request form in our system.** The form writes directly to `AppointmentRequest` in the database. Staff see new requests in the appointment book UI rather than in their inbox.

**Two distinct inbound channels exist today, both arriving as email:**

| Channel | Format | Current handling |
|---------|--------|-----------------|
| Google Form submission | Structured key-value email (shown above) | Staff read and manually enter into Milano |
| Direct client email to info@salonlyol.ca | Natural language — "Hi, I'd love to book a balayage with Joanne next Thursday afternoon if possible" | Staff read and manually enter into Milano |

Both channels result in the same action: staff manually create an appointment in Milano. In our system:
- The Google Form path is replaced by a native booking request form that writes directly to `AppointmentRequest`.
- The natural language email path requires staff to manually create an `AppointmentRequest` record with `source = email` — or in Phase 2, the AI CRM parses inbound emails and creates the request automatically.

`AppointmentRequest.source` enum: `online_form`, `email`, `phone`, `walk_in`, `staff_entered`.

**Subject line pattern** (`NEW Booking Request - [Name] - [Email] - [Phone]`) is useful context for the staff request queue UI — a similar summary format makes sense for surfacing new requests.
