"""Default confirmation-email template.

Builds a sensible default subject + HTML body for an appointment
confirmation. Hardcoded for v1; tenant-customizable templates are a
future backlog item.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TemplateItem:
    service_name: str
    provider_name: str
    start_time: datetime  # naive local datetime (matches AppointmentItem.start_time)
    duration_minutes: int


def _fmt_time(dt: datetime) -> str:
    # 12-hour format without leading zero on the hour, e.g. "9:30 AM".
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def _fmt_date(dt: datetime) -> str:
    # "Friday, May 8, 2026"
    return dt.strftime("%A, %B %-d, %Y")


def build_default_subject(salon_name: str, appointment_date: datetime) -> str:
    return f"Your appointment at {salon_name} — {_fmt_date(appointment_date)}"


def build_default_body(
    salon_name: str,
    client_first_name: str,
    appointment_date: datetime,
    items: list[TemplateItem],
) -> str:
    items_sorted = sorted(items, key=lambda i: i.start_time)
    item_lines = "\n".join(
        f"<li>{_fmt_time(i.start_time)} — {i.service_name} with {i.provider_name}</li>"
        for i in items_sorted
    )
    earliest = items_sorted[0].start_time if items_sorted else appointment_date
    return f"""\
<p>Hi {client_first_name},</p>

<p>This confirms your appointment at {salon_name} on \
<strong>{_fmt_date(appointment_date)}</strong>, arriving at \
<strong>{_fmt_time(earliest)}</strong>:</p>

<ul>
{item_lines}
</ul>

<p>If you need to reschedule or cancel, please reply to this email or \
give us a call at least 24 hours ahead.</p>

<p>See you soon,<br>The {salon_name} team</p>
"""
