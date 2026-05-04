import markdown as md

from app.email import ResendApiConfig, send_email


def _to_html(content: str) -> str:
    """Wrap markdown briefing in a readable HTML email body."""
    body = md.markdown(content, extensions=["fenced_code", "tables"])
    return f"""\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            max-width:680px;margin:0 auto;padding:32px 24px;color:#1a1a1a;line-height:1.6;">
  <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.08em;
              margin-bottom:24px;border-bottom:1px solid #e5e5e5;padding-bottom:12px;">
    SalonOS Market Intelligence
  </div>
  {body}
  <div style="margin-top:32px;padding-top:16px;border-top:1px solid #e5e5e5;
              font-size:12px;color:#999;">
    Delivered by SalonOS Briefing Engine · Unsubscribe by deactivating this briefing config.
  </div>
</div>"""


async def deliver(
    content: str,
    resend_api_key: str,
    from_address: str,
    to_address: str,
    subject: str,
) -> str:
    cfg = ResendApiConfig(api_key=resend_api_key, from_address=from_address)
    html = _to_html(content)
    await send_email(cfg, to_address, subject, html)
    return f"email:{to_address}"
