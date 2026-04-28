"""Branded email layout — wraps any inner HTML body in a tenant-branded chrome.

Header is a brand-coloured band with the tenant's logo (or salon name as
fallback). Footer is the salon name + a "didn't expect this email?"
disclaimer. All styling is inline — required for Gmail/Outlook compatibility.

Address/phone/hours are intentionally not in the footer for v1; a follow-up
backlog item adds tenant contact details to the model.
"""
from html import escape

from app.models.tenant import Tenant


# Brand-agnostic palette (mirrors the in-app cream / dark-text aesthetic).
PAGE_BG = "#f5f1eb"
CARD_BG = "#ffffff"
FOOTER_BG = "#faf9f7"
FOOTER_BORDER = "#e5e0d8"
TEXT = "#222222"
MUTED = "#6b6b6b"
SUBTLE = "#9a9a9a"
DEFAULT_BRAND = "#18181b"  # near-black, matches the app's default --primary


def _readable_text_on(hex_color: str) -> str:
    """Pick white or near-black text for legibility against a hex background."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "#ffffff"
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return "#ffffff"
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#1a1a1a" if luminance >= 0.6 else "#ffffff"


def _format_address(tenant: Tenant) -> str | None:
    """Single-line address built from tenant contact fields, or None if blank."""
    street_parts = [tenant.address_line1, tenant.address_line2]
    locality_parts = [tenant.city, tenant.region]
    street = ", ".join(p for p in street_parts if p)
    locality = ", ".join(p for p in locality_parts if p)
    if locality and tenant.postal_code:
        locality = f"{locality}  {tenant.postal_code}"
    elif tenant.postal_code:
        locality = tenant.postal_code
    bits = [b for b in (street, locality) if b]
    return " · ".join(bits) if bits else None


def _header_html(tenant: Tenant, brand_color: str, on_brand: str) -> str:
    name = escape(tenant.name)
    # Always render the salon name as styled text so the header looks correct
    # even if the logo image URL is inaccessible or fails to load.
    wordmark = (
        f'<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:26px;'
        f'letter-spacing:0.10em;color:{on_brand};margin-top:8px;">{name}</div>'
    )
    if tenant.logo_url and tenant.logo_url.startswith("http"):
        # Show logo image above the wordmark only when the URL is absolute
        # (relative paths like /icon.png are inaccessible to email clients).
        logo = (
            f'<img src="{escape(tenant.logo_url)}" alt="{name}" '
            f'height="48" style="display:block;height:48px;width:auto;border:0;outline:none;'
            f'text-decoration:none;max-height:48px;margin-bottom:8px;">'
        )
        return logo + wordmark
    return wordmark


def wrap_branded(inner_html: str, tenant: Tenant, *, subject: str | None = None) -> str:
    """Wrap an inner HTML fragment in the tenant-branded email shell.

    The inner_html is expected to be the rendered body content (paragraphs,
    lists, links, etc.) — no <html>/<body> wrapper.
    """
    brand = tenant.brand_color or DEFAULT_BRAND
    on_brand = _readable_text_on(brand)
    title = escape(subject or tenant.name)
    salon = escape(tenant.name)
    header = _header_html(tenant, brand, on_brand)
    address = _format_address(tenant)
    phone = tenant.phone

    contact_lines: list[str] = []
    if address:
        contact_lines.append(f'<div style="margin-bottom:4px;">{escape(address)}</div>')
    if phone:
        contact_lines.append(f'<div style="margin-bottom:6px;">{escape(phone)}</div>')
    contact_html = "".join(contact_lines)

    # Layout uses an outer table on a coloured page background, centring a
    # 600px max-width card. Tables + inline CSS = Gmail/Outlook safe.
    return f"""\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta http-equiv="x-ua-compatible" content="IE=edge">
    <title>{title}</title>
  </head>
  <body style="margin:0;padding:0;background:{PAGE_BG};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:{PAGE_BG};padding:32px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
                 style="max-width:600px;width:100%;background:{CARD_BG};border-radius:6px;overflow:hidden;">
            <tr>
              <td align="center" valign="middle"
                  style="background:{brand};padding:28px 16px;">
                {header}
              </td>
            </tr>
            <tr>
              <td style="padding:32px 36px 28px 36px;font-family:Helvetica,Arial,sans-serif;
                         font-size:15px;line-height:1.55;color:{TEXT};">
                {inner_html}
              </td>
            </tr>
            <tr>
              <td align="center"
                  style="padding:20px 16px;background:{FOOTER_BG};
                         border-top:1px solid {FOOTER_BORDER};
                         font-family:Helvetica,Arial,sans-serif;
                         font-size:12px;color:{MUTED};">
                <div style="margin-bottom:6px;font-weight:600;color:#444;">{salon}</div>
                {contact_html}
                <div style="color:{SUBTLE};">
                  If you weren't expecting this email, you can safely ignore it.
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
