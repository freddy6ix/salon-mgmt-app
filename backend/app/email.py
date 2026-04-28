import asyncio
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    use_tls: bool
    from_address: str


def _send_sync(cfg: SmtpConfig, to: str, subject: str, html: str) -> None:
    if not cfg.host:
        raise RuntimeError("SMTP host is not configured — fill in all fields and click Save first")
    if not cfg.username:
        raise RuntimeError("SMTP username is not configured")
    if not cfg.password:
        raise RuntimeError("SMTP password is not configured")
    if not cfg.from_address:
        raise RuntimeError("From address is not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.from_address
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    try:
        if cfg.use_tls:
            with smtplib.SMTP(cfg.host, cfg.port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg.host, cfg.port, context=context, timeout=30) as smtp:
                smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(f"Authentication failed — check username and app password. ({e.smtp_code}: {e.smtp_error.decode()})")
    except smtplib.SMTPServerDisconnected as e:
        raise RuntimeError(f"SMTP connection dropped — try again or check your SMTP settings. ({e})")
    except smtplib.SMTPConnectError as e:
        raise RuntimeError(f"Could not connect to {cfg.host}:{cfg.port}. ({e})")
    except smtplib.SMTPException as e:
        raise RuntimeError(f"SMTP error: {e}")
    except OSError as e:
        raise RuntimeError(f"Connection error to {cfg.host}:{cfg.port} — {e}")


async def send_email(cfg: SmtpConfig, to: str, subject: str, html: str, retries: int = 2) -> None:
    """Send an email, retrying on transient connection drops (SMTPServerDisconnected)."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            await asyncio.to_thread(_send_sync, cfg, to, subject, html)
            return
        except RuntimeError as e:
            last_err = e
            if "connection dropped" not in str(e).lower() or attempt == retries - 1:
                raise
            logger.warning("SMTP connection dropped on attempt %d, retrying…", attempt + 1)
            await asyncio.sleep(2)
    if last_err:
        raise last_err


def _cta_button(href: str, label: str, brand_color: str | None) -> str:
    # Brand-aware CTA button. Computed text colour for legibility against the brand.
    from app.email_layout import _readable_text_on, DEFAULT_BRAND  # local to avoid cycles
    bg = brand_color or DEFAULT_BRAND
    fg = _readable_text_on(bg)
    return (
        f'<a href="{href}" '
        f'style="display:inline-block;background:{bg};color:{fg};padding:12px 28px;'
        f'border-radius:4px;text-decoration:none;font-weight:600;letter-spacing:0.04em;">'
        f'{label}</a>'
    )


async def send_welcome_email(cfg: SmtpConfig, tenant: "Tenant", to: str, reset_link: str) -> None:
    from app.email_layout import wrap_branded
    salon_name = tenant.name
    cta = _cta_button(reset_link, "Set my password", tenant.brand_color)
    inner = f"""\
<h2 style="margin:0 0 16px 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;">
  Welcome to {salon_name}
</h2>
<p style="margin:0 0 16px 0;">
  Your staff account has been created. Click below to set your password and get started.
</p>
<p style="margin:24px 0;">{cta}</p>
<p style="margin:24px 0 0 0;color:#6b6b6b;font-size:13px;">
  This link expires in 72 hours.
</p>"""
    subject = f"Welcome to {salon_name} — Set your password"
    await send_email(cfg, to, subject, wrap_branded(inner, tenant, subject=subject))


async def send_password_reset_email(cfg: SmtpConfig, tenant: "Tenant", to: str, reset_link: str) -> None:
    from app.email_layout import wrap_branded
    salon_name = tenant.name
    cta = _cta_button(reset_link, "Reset my password", tenant.brand_color)
    inner = f"""\
<h2 style="margin:0 0 16px 0;font-family:Georgia,'Times New Roman',serif;font-weight:400;">
  Reset your password
</h2>
<p style="margin:0 0 16px 0;">
  Click below to reset your {salon_name} password.
</p>
<p style="margin:24px 0;">{cta}</p>
<p style="margin:24px 0 0 0;color:#6b6b6b;font-size:13px;">
  This link expires in 72 hours. If you didn't request this, you can ignore it.
</p>"""
    subject = f"Reset your {salon_name} password"
    await send_email(cfg, to, subject, wrap_branded(inner, tenant, subject=subject))
