"""Appointment reminder email template."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReminderItem:
    service_name: str
    provider_name: str
    start_time: datetime  # naive local datetime
    duration_minutes: int


def _fmt_time(dt: datetime, time_format: str = "12h") -> str:
    if time_format == "24h":
        return f"{dt.hour}:{dt.minute:02d}"
    h = dt.hour % 12 or 12
    return f"{h}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%A, %B %-d, %Y")


def build_reminder_subject(salon_name: str, appointment_date: datetime) -> str:
    return f"Reminder: your appointment at {salon_name} — {_fmt_date(appointment_date)}"


def build_reminder_body(
    salon_name: str,
    client_first_name: str,
    appointment_date: datetime,
    items: list[ReminderItem],
    time_format: str = "12h",
) -> str:
    items_sorted = sorted(items, key=lambda i: i.start_time)

    rows = "".join(
        f"""
        <tr>
          <td style="padding:6px 0;color:#333;">{_fmt_time(it.start_time, time_format)}</td>
          <td style="padding:6px 0 6px 16px;color:#333;">{it.service_name}</td>
          <td style="padding:6px 0 6px 16px;color:#555;">with {it.provider_name}</td>
        </tr>"""
        for it in items_sorted
    )

    return f"""
<p style="margin:0 0 16px;font-size:15px;color:#333;">Hi {client_first_name},</p>
<p style="margin:0 0 20px;font-size:15px;color:#333;">
  This is a friendly reminder about your appointment at <strong>{salon_name}</strong>
  on <strong>{_fmt_date(appointment_date)}</strong>.
</p>
<table style="border-collapse:collapse;width:100%;margin-bottom:24px;">
  <tbody>{rows}</tbody>
</table>
<p style="margin:0;font-size:13px;color:#888;">
  Need to reschedule? Please contact us as soon as possible so we can accommodate you.
</p>
"""
