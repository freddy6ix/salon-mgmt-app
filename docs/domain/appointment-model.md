# Appointment Model

The appointment book is the central feature of the system. This document captures the domain rules the data model and scheduling logic must honour.

## Core Insight: Appointments Are Containers

An **Appointment** is not a single service at a single time. It is a container grouping one or more **Appointment Items**, each representing a single service delivered by a single provider in a defined time window.

This distinction is foundational. It determines how scheduling works, how prices aggregate, and how the UI surfaces a client's visit.

## Entities

### Appointment

Represents a client's visit to the salon.

Key attributes:
- Client (required)
- Date
- Overall status: `requested` / `confirmed` / `in_progress` / `completed` / `cancelled` / `no_show`
- Source: `online_request` / `staff_entered` / `walk_in` / `phone`
- Optional notes

Duration, total price, and the set of providers involved all **derive** from the appointment's items.

### Appointment Item

The atomic unit of scheduling.

Key attributes:
- Parent Appointment
- Service
- Provider (assigned)
- Start time
- Duration
- Price **captured at booking time** (may differ from current price list — historical integrity matters for reporting)
- Sequence within the appointment (1, 2, 3...)
- Status: `pending` / `in_progress` / `completed` / `cancelled`

**Scheduling optimization operates at this level.** Idle-time minimization reshuffles individual Appointment Items across provider calendars — it does not move whole Appointments as a block.

## Services and Providers

### Service Categories

- **Colour services:** root touchup, refresh ends, toner, full colour, gloss, etc.
- **Cutting & styling:** haircuts (Type 1 / 2 / 2+), blowdries, treatments, updos
- **Shared services:** blowdries (deliverable by either colourists or stylists)

### Provider Types

- **Colourist** — delivers colour services
- **Stylist** — delivers cuts, styling, and related services
- **Dualist** — delivers both

Provider *type* is informational. The system's source of truth for "can this provider deliver this service?" is the explicit `ProviderServicePrice` table below — not the type. This handles cross-trained providers, new services, and exceptions naturally.

### Per-Provider Pricing

Each provider may have their own price for each service they deliver. This is a junction entity:

```
ProviderServicePrice
├── provider_id
├── service_id
├── price
├── effective_from
├── effective_to       (nullable — open-ended = currently active)
└── is_active
```

Historical price changes are preserved via `effective_from` / `effective_to` so past appointments remain accurately priced.

## Pricing Philosophy: Gender-Free

Salon Lyol uses **gender-free pricing**. Prices reflect the effort, creativity, and expertise of the provider — not the client's gender.

### Haircut Classification

Haircut type is a property of the Service entity.

| Type | Description | Typical work |
|------|-------------|--------------|
| **Type 1** | Clippers-based | Dusting, crew cuts, fades, short cuts |
| **Type 2** (most popular) | Scissors-based | Short, mid-length, long haircuts |
| **Type 2+** | High-effort | Redesigns, extra long hair, large volume |

Each provider sets their own price per type via `ProviderServicePrice`.

## Booking Rules

### Customer flow

1. Customer submits a **request** via salonlyol.ca with desired date and time.
2. Staff review the request.
3. Staff **confirm** the booking, assigning providers and exact time slots.

Customers do **not** self-book. This is deliberate: coordinating multi-service, multi-provider appointments (with ordering constraints, provider availability, and idle-time optimization) is not something customers do well.

### Staff flow

Staff can:
- Create appointments directly (walk-ins, phone bookings)
- Convert online requests into confirmed appointments
- Reassign providers within an appointment item
- Reschedule individual appointment items
- Cancel / no-show appointments or items

## Scheduling Constraints

### Sequencing

Many services have ordering dependencies:
- Colour typically finishes before cutting begins
- Treatments may need to happen between washes
- Final blowdry / style typically concludes the visit

Sequence is captured explicitly on Appointment Item. The scheduling engine should understand common patterns and warn on violations rather than hard-block.

### Idle-time optimization

For each provider across a day, idle time between consecutive Appointment Items should be minimized. The scheduler should:
- Pack items tightly within provider availability
- Respect intra-appointment sequencing (colour before cut)
- Respect provider working hours, breaks, days off
- Allow manual override by staff (staff judgement wins)

## Open Questions

These need resolution as the ERM and scheduling logic take shape:

1. **Parallel / processing-time services.** Colour often has 20–30 minutes of processing time where the chair is occupied but the colourist is free. Can a provider deliver a different service to a different client during that window? How is "chair/station" modeled separately from "provider"?

2. **Rooms / stations as finite resources.** How many chairs, wash stations, colour stations does Salon Lyol have? Do they constrain scheduling?

3. **Walk-ins.** Are walk-ins represented as Appointments with status `walk_in`, or a separate entity? Leaning toward the former for consistency.

4. **No-shows and late cancellations.** Do they affect client records (e.g. flags, deposits required)? Phase 1 or later?

5. **Service bundling / packages.** Does Salon Lyol offer fixed-price packages (e.g. "colour + cut combo")? If yes, how does that interact with per-provider pricing?

These are recorded here so they're not lost — most will be resolved when modelling the ERM in detail.
