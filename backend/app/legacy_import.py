"""
One-time import of legacy Salon Lyol data.

Called from the POST /admin/import-legacy endpoint.
Idempotent: clients upsert on legacy_id, bookings skip if
(client_id, appointment_date) already exists.
"""

import csv
import io
import re
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Maps legacy booking service codes → service_code in our DB.
# Update if Jini used different codes when creating CON/CAC.
SERVICE_CODE_MAP: dict[str, str] = {
    "ST1H":    "ST1",
    "ST2H":    "ST2",
    "ST2H+":   "ST2P",
    "SBD":     "BLD",
    "CRTU":    "RTO",
    "CRTUB":   "RTOB",
    "CPHHL":   "PHL",
    "CFHHL":   "FHL",
    "CAHL":    "ACC",
    "CTAO":    "TNRA",
    "CTSA":    "TNR",
    "CB":      "BLY",
    "CBT":     "BLT",
    "CCAMO":   "CCAMO",
    "CFC":     "CFC",
    "CVC":     "CVC",
    "CRE":     "REF",
    "MTAO":    "MLBA",
    "MTSA":    "MLB",
    "OLAPLEX": "MDO",
    "METAL":   "MDO",
    "FRINGE":  "FRG",
    "HBWHC":   "BOT",
    "HBWOHC":  "BOTNHC",
    "CON":     "con",
    "CAC":     "cac",
}

BLANK_PHONE = "(416)"


def _read_csv(content: bytes) -> list[dict]:
    text_content = content.decode("latin-1")
    return list(csv.DictReader(io.StringIO(text_content)))


def _clean_phone(raw: str) -> str | None:
    if not raw:
        return None
    stripped = raw.strip()
    if stripped.replace("(416)", "").strip() == "" or len(stripped) < 7:
        return None
    digits = re.sub(r"\D", "", stripped)
    if len(digits) < 7:
        return None
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return stripped


def _clean_email(raw: str) -> str | None:
    v = (raw or "").strip()
    if "@" not in v or "." not in v.split("@")[-1]:
        return None
    return v.lower()


def _parse_name(full: str) -> tuple[str, str]:
    parts = full.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def _parse_booking_dt(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M:%S %p")


async def import_clients(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    content: bytes,
) -> dict:
    rows = _read_csv(content)

    # Load provider display_name → id map
    prov_rows = await db.execute(
        text("SELECT id, display_name FROM providers WHERE tenant_id = :tid AND is_active = true"),
        {"tid": tenant_id},
    )
    provider_map: dict[str, uuid.UUID] = {
        r.display_name.upper(): r.id for r in prov_rows if r.display_name
    }

    created = updated = skipped = 0

    for row in rows:
        code = (row.get("Code") or "").strip().lstrip("|")
        name = (row.get("Name") or "").strip()
        if not code or not name:
            skipped += 1
            continue

        first_name, last_name = _parse_name(name)
        email = _clean_email(row.get("Email") or "")
        cell = _clean_phone(row.get("Cell Phone") or "")
        staff = (row.get("Staff") or "").strip().upper()
        preferred_provider_id = provider_map.get(staff) if staff else None

        existing = (
            await db.execute(
                text("SELECT id FROM clients WHERE tenant_id = :tid AND legacy_id = :code"),
                {"tid": tenant_id, "code": code},
            )
        ).fetchone()

        if existing:
            await db.execute(
                text(
                    "UPDATE clients SET first_name = :fn, last_name = :ln, email = :email,"
                    " cell_phone = :cell, preferred_provider_id = :ppid, updated_at = NOW()"
                    " WHERE id = :id AND tenant_id = :tid"
                ),
                {
                    "fn": first_name, "ln": last_name, "email": email,
                    "cell": cell, "ppid": preferred_provider_id,
                    "id": existing.id, "tid": tenant_id,
                },
            )
            updated += 1
        else:
            await db.execute(
                text(
                    "INSERT INTO clients (id, tenant_id, client_code, legacy_id,"
                    " first_name, last_name, email, cell_phone, preferred_provider_id,"
                    " country, is_active, no_show_count, late_cancellation_count,"
                    " account_balance, created_at, updated_at)"
                    " VALUES (:id, :tid, :code, :code, :fn, :ln, :email, :cell, :ppid,"
                    " 'CA', true, 0, 0, 0, NOW(), NOW())"
                ),
                {
                    "id": uuid.uuid4(), "tid": tenant_id, "code": code,
                    "fn": first_name, "ln": last_name, "email": email,
                    "cell": cell, "ppid": preferred_provider_id,
                },
            )
            created += 1

    await db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}


async def import_bookings(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    content: bytes,
) -> dict:
    rows = _read_csv(content)

    # Load lookup maps
    prov_rows = await db.execute(
        text("SELECT id, display_name FROM providers WHERE tenant_id = :tid AND is_active = true"),
        {"tid": tenant_id},
    )
    provider_map: dict[str, uuid.UUID] = {
        r.display_name.upper(): r.id for r in prov_rows if r.display_name
    }

    svc_rows = await db.execute(
        text(
            "SELECT id, service_code, default_price, duration_minutes"
            " FROM services WHERE tenant_id = :tid AND is_active = true"
        ),
        {"tid": tenant_id},
    )
    service_detail: dict[str, dict] = {
        r.service_code: {"id": r.id, "price": float(r.default_price or 0), "duration": r.duration_minutes}
        for r in svc_rows
    }

    client_rows = await db.execute(
        text("SELECT id, legacy_id FROM clients WHERE tenant_id = :tid AND legacy_id IS NOT NULL"),
        {"tid": tenant_id},
    )
    client_map: dict[str, uuid.UUID] = {r.legacy_id: r.id for r in client_rows}

    # Group rows → one appointment per (client_code, date)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        code = (row.get("Code") or "").strip()
        date_str = (row.get("Date") or "").strip()
        if code and date_str:
            groups[(code, date_str)].append(row)
    for key in groups:
        groups[key].sort(key=lambda r: r.get("TimeInt") or r.get("Time") or "")

    created = skipped_existing = skipped_no_client = skipped_no_service = skipped_no_provider = 0
    unmapped_codes: set[str] = set()

    for (client_code, date_str), items in groups.items():
        client_id = client_map.get(client_code)
        if not client_id:
            skipped_no_client += 1
            continue

        try:
            appt_dt = _parse_booking_dt(date_str, items[0]["Time"])
        except (ValueError, KeyError):
            skipped_no_client += 1
            continue

        existing = (
            await db.execute(
                text(
                    "SELECT id FROM appointments"
                    " WHERE tenant_id = :tid AND client_id = :cid AND appointment_date = :dt"
                ),
                {"tid": tenant_id, "cid": client_id, "dt": appt_dt},
            )
        ).fetchone()
        if existing:
            skipped_existing += 1
            continue

        # Resolve all items before writing
        resolved = []
        skip_group = False
        for seq, item in enumerate(items, start=1):
            legacy_svc = (item.get("Service") or "").strip()
            db_code = SERVICE_CODE_MAP.get(legacy_svc)
            if not db_code:
                unmapped_codes.add(legacy_svc)
                skip_group = True
                break
            svc = service_detail.get(db_code)
            if not svc:
                unmapped_codes.add(f"{legacy_svc}→{db_code}(missing)")
                skip_group = True
                break
            staff = (item.get("Staff") or "").strip().upper()
            provider_id = provider_map.get(staff)
            if not provider_id:
                skipped_no_provider += 1
                skip_group = True
                break
            try:
                item_dt = _parse_booking_dt(date_str, item["Time"])
            except (ValueError, KeyError):
                skip_group = True
                break
            resolved.append({
                "seq": seq, "service_id": svc["id"], "provider_id": provider_id,
                "start_time": item_dt, "duration": svc["duration"], "price": svc["price"],
            })

        if skip_group or not resolved:
            if not skip_group:
                skipped_no_client += 1
            else:
                skipped_no_service += 1
            continue

        appt_id = uuid.uuid4()
        await db.execute(
            text(
                "INSERT INTO appointments (id, tenant_id, client_id, appointment_date,"
                " source, status, confirmation_status, created_at, updated_at)"
                " VALUES (:id, :tid, :cid, :dt,"
                " 'staff_entered', 'confirmed', 'not_sent', NOW(), NOW())"
            ),
            {"id": appt_id, "tid": tenant_id, "cid": client_id, "dt": appt_dt},
        )
        for ri in resolved:
            await db.execute(
                text(
                    "INSERT INTO appointment_items (id, tenant_id, appointment_id,"
                    " service_id, provider_id, sequence, start_time, duration_minutes, price,"
                    " price_is_locked, status, created_at, updated_at)"
                    " VALUES (:id, :tid, :appt_id,"
                    " :svc_id, :prov_id, :seq, :start_time, :dur, :price,"
                    " true, 'pending', NOW(), NOW())"
                ),
                {
                    "id": uuid.uuid4(), "tid": tenant_id, "appt_id": appt_id,
                    "svc_id": ri["service_id"], "prov_id": ri["provider_id"],
                    "seq": ri["seq"], "start_time": ri["start_time"],
                    "dur": ri["duration"], "price": ri["price"],
                },
            )
        created += 1

    await db.commit()
    return {
        "created": created,
        "skipped_existing": skipped_existing,
        "skipped_no_client": skipped_no_client,
        "skipped_no_service": skipped_no_service,
        "skipped_no_provider": skipped_no_provider,
        "unmapped_service_codes": sorted(unmapped_codes),
    }
