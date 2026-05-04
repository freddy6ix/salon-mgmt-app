"""Appointment reminder dispatcher.

Called by POST /internal/dispatch-reminders (via Cloud Scheduler).
Finds all scheduled reminders whose scheduled_at <= now(), sends the
email, and marks them sent or failed.

Also exposes schedule_reminder() and cancel_reminders() for use by
the appointment routers.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.email import email_cfg_from_row, send_email
from app.email_layout import wrap_branded
from app.models.appointment import Appointment, AppointmentItem, AppointmentStatus
from app.models.appointment import AppointmentReminder, ReminderChannel, ReminderStatus
from app.models.client import Client
from app.models.email_config import TenantEmailConfig
from app.models.tenant import Tenant
from app.reminder_template import ReminderItem, build_reminder_body, build_reminder_subject

logger = logging.getLogger(__name__)

BUSINESS_TZ = "America/Toronto"


async def schedule_reminder(
    appt: Appointment,
    tenant: Tenant,
    db: AsyncSession,
) -> None:
    """Create a scheduled AppointmentReminder for a newly confirmed appointment.

    No-ops if reminders are disabled, the client has no email, the reminder
    would fire in the past, or one already exists for this appointment.
    """
    if not tenant.reminder_enabled:
        return

    # Load client email
    client = (
        await db.execute(select(Client).where(Client.id == appt.client_id))
    ).scalar_one_or_none()
    if not client or not client.email:
        return

    # Find the earliest item start_time to anchor the reminder
    items = (
        await db.execute(
            select(AppointmentItem)
            .where(AppointmentItem.appointment_id == appt.id)
            .order_by(AppointmentItem.start_time)
        )
    ).scalars().all()
    if not items:
        return

    earliest: datetime = items[0].start_time  # naive local datetime
    # Treat as Toronto local, compute scheduled_at in UTC
    # start_time is stored naive; subtract lead hours and compare to now UTC
    scheduled_at = earliest - timedelta(hours=tenant.reminder_lead_hours)
    # Convert naive local to UTC by assuming America/Toronto offset (~UTC-4/5).
    # We use a pragmatic approach: store aware UTC for the scheduler check.
    # For simplicity we use pytz-free arithmetic: just make it UTC-aware with
    # a fixed offset acceptable for scheduling purposes. The dispatcher uses
    # datetime.now(timezone.utc) for comparison.
    import zoneinfo
    tz = zoneinfo.ZoneInfo(BUSINESS_TZ)
    scheduled_at_aware = scheduled_at.replace(tzinfo=tz).astimezone(timezone.utc)

    if scheduled_at_aware <= datetime.now(timezone.utc):
        # Appointment is too soon — skip
        return

    # Idempotent: skip if a scheduled reminder already exists
    existing = (
        await db.execute(
            select(AppointmentReminder).where(
                AppointmentReminder.appointment_id == appt.id,
                AppointmentReminder.status == ReminderStatus.scheduled,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    db.add(AppointmentReminder(
        tenant_id=tenant.id,
        appointment_id=appt.id,
        channel=ReminderChannel.email,
        scheduled_at=scheduled_at_aware,
        status=ReminderStatus.scheduled,
    ))


async def cancel_reminders(appointment_id: uuid.UUID, db: AsyncSession) -> None:
    """Cancel any pending reminders for an appointment (call on cancel/no-show)."""
    reminders = (
        await db.execute(
            select(AppointmentReminder).where(
                AppointmentReminder.appointment_id == appointment_id,
                AppointmentReminder.status == ReminderStatus.scheduled,
            )
        )
    ).scalars().all()
    for r in reminders:
        r.status = ReminderStatus.cancelled


async def dispatch_due_reminders(db: AsyncSession) -> dict:
    """Find and send all due reminders. Returns counts for logging."""
    now = datetime.now(timezone.utc)

    due = (
        await db.execute(
            select(AppointmentReminder).where(
                AppointmentReminder.status == ReminderStatus.scheduled,
                AppointmentReminder.scheduled_at <= now,
            )
        )
    ).scalars().all()

    sent = failed = skipped = 0

    for reminder in due:
        try:
            appt = (
                await db.execute(select(Appointment).where(Appointment.id == reminder.appointment_id))
            ).scalar_one_or_none()

            # Skip if appointment no longer warrants a reminder
            if appt is None or appt.status in (
                AppointmentStatus.cancelled,
                AppointmentStatus.completed,
                AppointmentStatus.no_show,
            ):
                reminder.status = ReminderStatus.cancelled
                skipped += 1
                continue

            tenant = (
                await db.execute(select(Tenant).where(Tenant.id == reminder.tenant_id))
            ).scalar_one_or_none()
            if tenant is None or not tenant.reminder_enabled:
                reminder.status = ReminderStatus.cancelled
                skipped += 1
                continue

            client = (
                await db.execute(select(Client).where(Client.id == appt.client_id))
            ).scalar_one_or_none()
            if not client or not client.email:
                reminder.status = ReminderStatus.cancelled
                skipped += 1
                continue

            email_cfg_row = (
                await db.execute(
                    select(TenantEmailConfig).where(TenantEmailConfig.tenant_id == reminder.tenant_id)
                )
            ).scalar_one_or_none()
            if email_cfg_row is None:
                reminder.status = ReminderStatus.failed
                failed += 1
                continue

            items = (
                await db.execute(
                    select(AppointmentItem)
                    .where(AppointmentItem.appointment_id == appt.id)
                    .order_by(AppointmentItem.start_time)
                )
            ).scalars().all()

            # Load service names via joined query
            from app.models.service import Service
            from app.models.provider import Provider

            ri_list: list[ReminderItem] = []
            for it in items:
                svc = (await db.execute(select(Service).where(Service.id == it.service_id))).scalar_one_or_none()
                prov = (await db.execute(select(Provider).where(Provider.id == it.provider_id))).scalar_one_or_none()
                ri_list.append(ReminderItem(
                    service_name=svc.name if svc else "Service",
                    provider_name=prov.display_name if prov else "Staff",
                    start_time=it.start_time,
                    duration_minutes=it.duration_minutes,
                ))

            subject = build_reminder_subject(tenant.name, appt.appointment_date)
            body_html = build_reminder_body(
                salon_name=tenant.name,
                client_first_name=client.first_name,
                appointment_date=appt.appointment_date,
                items=ri_list,
                time_format=tenant.time_format,
            )
            branded_html = wrap_branded(body_html, tenant, subject=subject)

            cfg = email_cfg_from_row(email_cfg_row)
            await send_email(cfg, client.email, subject, branded_html)

            reminder.status = ReminderStatus.sent
            reminder.sent_at = now
            sent += 1

        except Exception as exc:
            logger.error("Failed to send reminder %s: %s", reminder.id, exc)
            reminder.status = ReminderStatus.failed
            failed += 1

    await db.commit()
    return {"sent": sent, "failed": failed, "skipped": skipped}
