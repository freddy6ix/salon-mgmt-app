"""Internal notification email sent to salon staff when a guest submits a
booking request (P2-4).

Best-effort: failures are logged but never bubble up to the guest's submit
flow — a flaky SMTP server should not block a request from being recorded.
"""
import logging
from datetime import datetime
from html import escape

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.email import email_cfg_from_row, send_email
from app.email_layout import wrap_branded
from app.models.appointment import AppointmentRequest, AppointmentRequestItem
from app.models.email_config import TenantEmailConfig
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%A, %B %-d, %Y")


def _build_inner_body(
    salon_name: str,
    req: AppointmentRequest,
    items: list[AppointmentRequestItem],
) -> str:
    item_lines = "\n".join(
        f"<li>{escape(i.service_name)} — preferred provider {escape(i.preferred_provider_name)}</li>"
        for i in sorted(items, key=lambda x: x.sequence)
    )
    timing = (
        f"around <strong>{escape(req.desired_time_note)}</strong>"
        if req.desired_time_note
        else "(no preferred time)"
    )
    note_block = (
        f'<p style="margin:16px 0 0 0;color:#444;"><em>"{escape(req.special_note)}"</em></p>'
        if req.special_note
        else ""
    )
    contact_bits: list[str] = []
    if req.phone:
        contact_bits.append(escape(req.phone))
    if req.email:
        contact_bits.append(escape(req.email))
    contact_line = " · ".join(contact_bits) if contact_bits else "no contact info on file"

    return f"""\
<h2 style="margin:0 0 12px 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;">
  New booking request
</h2>
<p style="margin:0 0 16px 0;color:#555;">
  Submitted just now — review and confirm in the requests page when you have a moment.
</p>

<table role="presentation" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 16px 0;font-size:14px;">
  <tr><td style="padding:2px 0;color:#888;width:96px;">Client</td>
      <td style="padding:2px 0;"><strong>{escape(req.first_name)} {escape(req.last_name)}</strong></td></tr>
  <tr><td style="padding:2px 0;color:#888;">Contact</td>
      <td style="padding:2px 0;">{contact_line}</td></tr>
  <tr><td style="padding:2px 0;color:#888;">Date</td>
      <td style="padding:2px 0;">{_fmt_date(req.desired_date)}</td></tr>
  <tr><td style="padding:2px 0;color:#888;">Time</td>
      <td style="padding:2px 0;">{timing}</td></tr>
</table>

<p style="margin:0 0 6px 0;color:#888;font-size:14px;">Services requested</p>
<ul style="margin:0;padding-left:20px;">
{item_lines}
</ul>

{note_block}
"""


async def send_request_notification(
    db: AsyncSession,
    tenant_id,
    req: AppointmentRequest,
) -> None:
    """Fire-and-(mostly-)forget notification send. Never raises."""
    try:
        tenant = (
            await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        ).scalar_one_or_none()
        if tenant is None or not tenant.request_notifications_enabled:
            return
        recipients = [
            r.strip()
            for r in (tenant.request_notification_recipients or "").split(",")
            if r.strip()
        ]
        if not recipients:
            return

        smtp_row = (
            await db.execute(
                select(TenantEmailConfig).where(TenantEmailConfig.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        if smtp_row is None:
            logger.warning("Request notification skipped: tenant %s has no SMTP config", tenant_id)
            return
        smtp_cfg = email_cfg_from_row(smtp_row)

        items = (
            await db.execute(
                select(AppointmentRequestItem)
                .where(AppointmentRequestItem.request_id == req.id)
                .order_by(AppointmentRequestItem.sequence)
            )
        ).scalars().all()

        subject = f"New booking request — {req.first_name} {req.last_name}"
        inner = _build_inner_body(tenant.name, req, list(items))
        html = wrap_branded(inner, tenant, subject=subject)

        for rcpt in recipients:
            try:
                await send_email(smtp_cfg, rcpt, subject, html)
            except RuntimeError as e:
                logger.warning("Request notification to %s failed: %s", rcpt, e)
    except Exception:  # noqa: BLE001 — best-effort path; never block the request
        logger.exception("Request notification dispatch crashed for tenant %s", tenant_id)
