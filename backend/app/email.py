import asyncio
import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)


def _send_sync(params: dict) -> None:
    resend.api_key = settings.resend_api_key
    resend.Emails.send(params)


async def send_email(to: str, subject: str, html: str) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — email not sent to %s | subject: %s", to, subject)
        return
    params = {
        "from": settings.resend_from,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    await asyncio.to_thread(_send_sync, params)


async def send_welcome_email(to: str, reset_link: str, salon_name: str = "Salon Lyol") -> None:
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <h2 style="margin-top: 0;">Welcome to {salon_name}</h2>
      <p>Your staff account has been created. Click the button below to set your password and get started.</p>
      <p style="margin: 32px 0;">
        <a href="{reset_link}"
           style="background: #18181b; color: #fff; padding: 12px 24px;
                  border-radius: 6px; text-decoration: none; font-weight: 600;">
          Set my password
        </a>
      </p>
      <p style="color: #71717a; font-size: 14px;">
        This link expires in 72 hours. If you didn't expect this email, you can ignore it.
      </p>
    </div>
    """
    await send_email(to, f"Welcome to {salon_name} — Set your password", html)


async def send_password_reset_email(to: str, reset_link: str, salon_name: str = "Salon Lyol") -> None:
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px;">
      <h2 style="margin-top: 0;">Reset your password</h2>
      <p>Click the button below to reset your password for {salon_name}.</p>
      <p style="margin: 32px 0;">
        <a href="{reset_link}"
           style="background: #18181b; color: #fff; padding: 12px 24px;
                  border-radius: 6px; text-decoration: none; font-weight: 600;">
          Reset my password
        </a>
      </p>
      <p style="color: #71717a; font-size: 14px;">
        This link expires in 72 hours. If you didn't request this, you can ignore it.
      </p>
    </div>
    """
    await send_email(to, f"Reset your {salon_name} password", html)
