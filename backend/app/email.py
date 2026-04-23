import asyncio
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg.from_address
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    try:
        if cfg.use_tls:
            with smtplib.SMTP(cfg.host, cfg.port, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP_SSL(cfg.host, cfg.port, context=context, timeout=10) as smtp:
                smtp.login(cfg.username, cfg.password)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(f"Authentication failed — check username and app password. ({e.smtp_code}: {e.smtp_error.decode()})")
    except smtplib.SMTPConnectError as e:
        raise RuntimeError(f"Could not connect to {cfg.host}:{cfg.port}. ({e})")
    except smtplib.SMTPException as e:
        raise RuntimeError(f"SMTP error: {e}")
    except OSError as e:
        raise RuntimeError(f"Connection error to {cfg.host}:{cfg.port} — {e}")


async def send_email(cfg: SmtpConfig, to: str, subject: str, html: str) -> None:
    await asyncio.to_thread(_send_sync, cfg, to, subject, html)


async def send_welcome_email(cfg: SmtpConfig, to: str, reset_link: str, salon_name: str = "Salon Lyol") -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;">
      <h2 style="margin-top:0;">Welcome to {salon_name}</h2>
      <p>Your staff account has been created. Click below to set your password and get started.</p>
      <p style="margin:32px 0;">
        <a href="{reset_link}"
           style="background:#18181b;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Set my password
        </a>
      </p>
      <p style="color:#71717a;font-size:14px;">
        This link expires in 72 hours. If you didn't expect this email, you can ignore it.
      </p>
    </div>"""
    await send_email(cfg, to, f"Welcome to {salon_name} — Set your password", html)


async def send_password_reset_email(cfg: SmtpConfig, to: str, reset_link: str, salon_name: str = "Salon Lyol") -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;">
      <h2 style="margin-top:0;">Reset your password</h2>
      <p>Click below to reset your {salon_name} password.</p>
      <p style="margin:32px 0;">
        <a href="{reset_link}"
           style="background:#18181b;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:600;">
          Reset my password
        </a>
      </p>
      <p style="color:#71717a;font-size:14px;">
        This link expires in 72 hours. If you didn't request this, you can ignore it.
      </p>
    </div>"""
    await send_email(cfg, to, f"Reset your {salon_name} password", html)
