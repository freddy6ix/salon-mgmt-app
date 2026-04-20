# Milano Reference — Data Control → Schedules

Screenshot from the Milano schedule configuration module, captured from the Salon Lyol installation on 2026-04-19.

---

## Provider Schedule Configuration

![Data Control Schedules](./Screenshot%202026-04-19%20at%205.37.28%20PM.png)

**File:** `Screenshot 2026-04-19 at 5.37.28 PM.png`

The schedule configuration screen for an individual provider. **Joanne** is selected (highlighted in the left sidebar).

**Left sidebar — Staff list:** ADMIN, AZAM (Asami), BECKY, GUME, JOANNE, OLGA, SARAH (additional staff likely scrolled off: JJ, RYAN, MAYUMI, ANTONELLA).

**Main area:**
- **Month calendar** (April 2026) — used to navigate to the target week
- **Weekly schedule grid** (right) — a visual time-slot grid representing the provider's working hours for the week. Dark blocks = unavailable; coloured blocks = working time. Staff manually paint working slots by clicking.
- **Instruction text:** *"Click on a working rectangle below, then click in the grid to set it for each day"*
- **"Repeat this schedule every:"** — a field/dropdown allowing a weekly schedule to repeat automatically (i.e., set once and propagate forward)
- **Footer note:** *"Only active staff will appear in the Appt Book"* — a provider without any active schedule will not appear as a column in the appointment book

**Domain notes:**

### Schedule model

Milano uses a **painted time-slot grid** — staff working hours are set at fine granularity (likely 15–30 min increments matching the appointment book's time ruler). This is more expressive than a simple `start_time`/`end_time` per day — it can represent split shifts, late starts, early finishes, and lunch breaks all within one visual.

For our ERM, two practical approaches:

**Option A — Simple daily windows (recommended for Phase 1):**
```
ProviderSchedule
├── provider_id
├── tenant_id
├── day_of_week      (0=Mon … 6=Sun)
├── start_time
├── end_time
├── is_working       (false = day off)
└── effective_date   (schedule version anchor)
```
Sufficient for Phase 1. Breaks and lunch gaps handled by blocked `AppointmentItem` slots (as seen in the appointment book blue blocks).

**Option B — Slot-level granularity:**
Store individual 15-min availability slots. More faithful to Milano's model but significantly more complex. Defer to Phase 2 if needed.

### Repeat schedule

The "Repeat this schedule every:" field confirms providers have a **recurring weekly template** — their schedule doesn't need to be re-entered each week. This maps to `ProviderSchedule` being a standing weekly definition (keyed by `day_of_week`) rather than a per-date record.

Exceptions (holidays, one-off days off) would be handled as overrides on specific dates — a `ProviderScheduleException` table:
```
ProviderScheduleException
├── provider_id
├── tenant_id
├── exception_date
├── is_working       (false = day off, true = working when normally off)
├── start_time       (nullable — overrides normal hours)
└── end_time         (nullable)
```

### Active staff filter

"Only active staff will appear in the Appt Book" — the `Provider` (or `Staff`) entity needs an `is_active` boolean. Inactive/former staff remain in the system (for historical appointment integrity) but are hidden from the scheduling UI.
