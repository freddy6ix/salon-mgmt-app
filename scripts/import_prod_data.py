#!/usr/bin/env python3
"""
Idempotent import of legacy Salon Lyol data into the app database.

USAGE (run from repo root):
  # local dev
  DATABASE_URL=postgresql://salon:salon@localhost:5432/salon_lyol \\
      python scripts/import_prod_data.py clients

  # production via Cloud SQL proxy
  cloud-sql-proxy PROJECT:REGION:INSTANCE --port 5433 &
  DATABASE_URL=postgresql://USER:PASS@localhost:5433/DBNAME \\
      python scripts/import_prod_data.py bookings

  # list what's in the DB before mapping services
  DATABASE_URL=... python scripts/import_prod_data.py list-services
  DATABASE_URL=... python scripts/import_prod_data.py list-providers

  # dry-run (no writes)
  DATABASE_URL=... python scripts/import_prod_data.py --dry-run clients

IDEMPOTENCY:
  clients  — upsert on legacy_id (source Code field); re-running updates
             name / email / phone if the CSV was refreshed.
  bookings — skips any (client_id, appointment_date) pair that already
             exists; re-running is safe.

SOURCE FILES (data/ directory):
  Client Details.txt   — 7,114 clients
  All Bookings.txt     — 777 upcoming appointments (May 2026 onward)
"""

import argparse
import asyncio
import csv
import os
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import asyncpg

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CLIENT_FILE = DATA_DIR / "Client Details.txt"
BOOKINGS_FILE = DATA_DIR / "All Bookings.txt"

# ---------------------------------------------------------------------------
# Service code mapping: legacy booking code → service_code in our DB.
#
# Run `python scripts/import_prod_data.py list-services` to see what
# service_codes are actually in your DB, then update this dict.
#
# Keys   = codes that appear in All Bookings.txt Service column
# Values = service_code stored in the services table
# ---------------------------------------------------------------------------
SERVICE_CODE_MAP: dict[str, str] = {
    "ST1H":    "ST1",    # Type 1 Haircut
    "ST2H":    "ST2",    # Type 2 Haircut
    "ST2H+":   "ST2P",   # Type 2+ Haircut
    "SBD":     "BLD",    # Blowdry
    "CRTU":    "RTO",    # Root Touch-Up
    "CRTUB":   "RTOB",   # Root Touch-Up (bleach/high lift)
    "CPHHL":   "PHL",    # Partial Highlights
    "CFHHL":   "FHL",    # Full Highlights
    "CAHL":    "ACC",    # Accent Highlights
    "CTAO":    "TNRA",   # Toner/Gloss (add-on)
    "CTSA":    "TNR",    # Toner/Gloss Stand Alone
    "CB":      "BLY",    # Full Balayage
    "CBT":     "BLT",    # Balayage Touch-Up
    "CCAMO":   "CCAMO",  # Camo Colour
    "CFC":     "CFC",    # Color Full Color
    "CVC":     "CVC",    # Vivid Color
    "CRE":     "REF",    # Refreshing Ends
    "MTAO":    "MLBA",   # Milbon Treatment (add-on)
    "MTSA":    "MLB",    # Milbon Treatment Stand Alone
    "OLAPLEX": "MDO",    # Metal Detox/Olaplex (add-on)
    "METAL":   "MDO",    # Metal Detox/Olaplex (add-on)
    "FRINGE":  "FRG",    # Fringe/Bang Cut
    "HBWHC":   "BOT",    # Hair Botox (with home care)
    "HBWOHC":  "BOTNHC", # Hair Botox (without home care)
    "CON":     "con",    # Consultation
    "CAC":     "cac",    # Additional Colour
}

TENANT_SLUG = os.getenv("TENANT_SLUG", "salon-lyol")
NULL_DATE = "12/30/1899"
BLANK_PHONE = "(416)        "


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="latin-1") as f:
        return list(csv.DictReader(f))


def clean_phone(raw: str) -> str | None:
    if not raw or raw.strip() == BLANK_PHONE.strip() or raw.strip() == "(416)":
        return None
    digits = re.sub(r"\D", "", raw.strip())
    if len(digits) < 7:
        return None
    # Format as (XXX) XXX-XXXX for 10-digit North American numbers
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return raw.strip()


def clean_email(raw: str) -> str | None:
    v = raw.strip() if raw else ""
    if "@" not in v or "." not in v.split("@")[-1]:
        return None
    return v.lower()


def parse_name(full: str) -> tuple[str, str]:
    parts = full.strip().split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def parse_date(raw: str) -> str | None:
    if not raw or raw.strip() == NULL_DATE:
        return None
    try:
        return datetime.strptime(raw.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_booking_datetime(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M:%S %p")


def asyncpg_url(database_url: str) -> str:
    """Convert postgresql+asyncpg://... or postgresql://... to bare asyncpg URL."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def get_tenant_id(conn: asyncpg.Connection, slug: str) -> uuid.UUID:
    row = await conn.fetchrow("SELECT id FROM tenants WHERE slug = $1", slug)
    if not row:
        raise SystemExit(f"Tenant with subdomain '{slug}' not found. Set TENANT_SLUG env var.")
    return row["id"]


async def load_providers(conn: asyncpg.Connection, tenant_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """Return {upper(display_name): id}."""
    rows = await conn.fetch(
        "SELECT id, display_name FROM providers WHERE tenant_id = $1 AND is_active = true",
        tenant_id,
    )
    return {r["display_name"].upper(): r["id"] for r in rows if r["display_name"]}


async def load_services(conn: asyncpg.Connection, tenant_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """Return {service_code: id}."""
    rows = await conn.fetch(
        "SELECT id, service_code, default_price, duration_minutes FROM services WHERE tenant_id = $1 AND is_active = true",
        tenant_id,
    )
    return {r["service_code"]: r["id"] for r in rows}


async def load_service_details(conn: asyncpg.Connection, tenant_id: uuid.UUID) -> dict[str, dict]:
    """Return {service_code: {id, default_price, duration_minutes}}."""
    rows = await conn.fetch(
        "SELECT id, service_code, default_price, duration_minutes FROM services WHERE tenant_id = $1 AND is_active = true",
        tenant_id,
    )
    return {
        r["service_code"]: {
            "id": r["id"],
            "price": float(r["default_price"] or 0),
            "duration": r["duration_minutes"],
        }
        for r in rows
    }


# ---------------------------------------------------------------------------
# Client import
# ---------------------------------------------------------------------------

async def import_clients(
    conn: asyncpg.Connection,
    tenant_id: uuid.UUID,
    rows: list[dict],
    provider_map: dict[str, uuid.UUID],
    dry_run: bool,
) -> None:
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Importing clients …")

    created = updated = skipped = errors = 0

    for row in rows:
        code = (row.get("Code") or "").strip().lstrip("|")
        if not code:
            skipped += 1
            continue

        name = (row.get("Name") or "").strip()
        if not name:
            skipped += 1
            continue

        first_name, last_name = parse_name(name)
        email = clean_email(row.get("Email") or "")
        cell = clean_phone(row.get("Cell Phone") or "")
        staff = (row.get("Staff") or "").strip().upper()
        preferred_provider_id = provider_map.get(staff) if staff else None

        # Check if already imported
        existing = await conn.fetchrow(
            "SELECT id FROM clients WHERE tenant_id = $1 AND legacy_id = $2",
            tenant_id, code,
        )

        if existing:
            if not dry_run:
                await conn.execute(
                    """UPDATE clients
                       SET first_name = $3, last_name = $4, email = $5,
                           cell_phone = $6, preferred_provider_id = $7,
                           updated_at = NOW()
                     WHERE id = $1 AND tenant_id = $2""",
                    existing["id"], tenant_id,
                    first_name, last_name, email, cell, preferred_provider_id,
                )
            updated += 1
        else:
            if not dry_run:
                new_id = uuid.uuid4()
                await conn.execute(
                    """INSERT INTO clients (
                           id, tenant_id, client_code, legacy_id,
                           first_name, last_name, email, cell_phone,
                           preferred_provider_id, country, is_active,
                           no_show_count, late_cancellation_count, account_balance,
                           created_at, updated_at
                       ) VALUES (
                           $1, $2, $3, $4,
                           $5, $6, $7, $8,
                           $9, 'CA', true,
                           0, 0, 0,
                           NOW(), NOW()
                       )""",
                    new_id, tenant_id, code, code,
                    first_name, last_name, email, cell,
                    preferred_provider_id,
                )
            created += 1

    total = created + updated + skipped + errors
    print(f"  Processed {total} rows: {created} created, {updated} updated, {skipped} skipped, {errors} errors")


# ---------------------------------------------------------------------------
# Booking import
# ---------------------------------------------------------------------------

async def import_bookings(
    conn: asyncpg.Connection,
    tenant_id: uuid.UUID,
    rows: list[dict],
    provider_map: dict[str, uuid.UUID],
    service_detail: dict[str, dict],
    dry_run: bool,
) -> None:
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Importing bookings …")

    # Group rows → one appointment per (client_code, date)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        code = (row.get("Code") or "").strip()
        date_str = (row.get("Date") or "").strip()
        if code and date_str:
            groups[(code, date_str)].append(row)

    # Sort items within each group by time
    for key in groups:
        groups[key].sort(key=lambda r: r.get("TimeInt") or r.get("Time") or "")

    # Load client legacy_id → client_id map for this tenant
    client_rows = await conn.fetch(
        "SELECT id, legacy_id FROM clients WHERE tenant_id = $1 AND legacy_id IS NOT NULL",
        tenant_id,
    )
    client_map: dict[str, uuid.UUID] = {r["legacy_id"]: r["id"] for r in client_rows}

    # Warn about unmapped service codes
    legacy_codes_in_file = {r.get("Service", "").strip() for r in rows}
    unmapped = legacy_codes_in_file - set(SERVICE_CODE_MAP)
    if unmapped:
        print(f"  WARNING: {len(unmapped)} legacy service codes have no mapping — rows will be skipped:")
        for c in sorted(unmapped):
            print(f"    {c}")

    missing_services = {
        legacy: SERVICE_CODE_MAP[legacy]
        for legacy in SERVICE_CODE_MAP
        if SERVICE_CODE_MAP[legacy] not in service_detail
    }
    if missing_services:
        print(f"  WARNING: {len(missing_services)} mapped service codes not found in DB — rows will be skipped:")
        for legacy, db_code in sorted(missing_services.items()):
            print(f"    {legacy} → {db_code} (not in services table)")

    created = skipped_existing = skipped_no_client = skipped_no_service = skipped_no_provider = 0

    for (client_code, date_str), items in groups.items():
        client_id = client_map.get(client_code)
        if not client_id:
            skipped_no_client += 1
            continue

        # Appointment datetime = first item's start time
        first_item = items[0]
        try:
            appt_dt = parse_booking_datetime(date_str, first_item["Time"])
        except (ValueError, KeyError):
            skipped_no_client += 1
            continue

        # Check if appointment already exists
        existing = await conn.fetchrow(
            "SELECT id FROM appointments WHERE tenant_id = $1 AND client_id = $2 AND appointment_date = $3",
            tenant_id, client_id, appt_dt,
        )
        if existing:
            skipped_existing += 1
            continue

        # Resolve all items before writing anything
        resolved_items = []
        skip_group = False
        for seq, item in enumerate(items, start=1):
            legacy_svc = (item.get("Service") or "").strip()
            db_svc_code = SERVICE_CODE_MAP.get(legacy_svc)
            svc = service_detail.get(db_svc_code) if db_svc_code else None
            if not svc:
                skipped_no_service += 1
                skip_group = True
                break

            staff = (item.get("Staff") or "").strip().upper()
            provider_id = provider_map.get(staff)
            if not provider_id:
                skipped_no_provider += 1
                skip_group = True
                break

            try:
                item_dt = parse_booking_datetime(date_str, item["Time"])
            except (ValueError, KeyError):
                skip_group = True
                break

            resolved_items.append({
                "seq": seq,
                "service_id": svc["id"],
                "provider_id": provider_id,
                "start_time": item_dt,
                "duration": svc["duration"],
                "price": svc["price"],
            })

        if skip_group or not resolved_items:
            continue

        if not dry_run:
            appt_id = uuid.uuid4()
            await conn.execute(
                """INSERT INTO appointments (
                       id, tenant_id, client_id, appointment_date,
                       source, status, confirmation_status,
                       created_at, updated_at
                   ) VALUES (
                       $1, $2, $3, $4,
                       'staff_entered', 'confirmed', 'not_sent',
                       NOW(), NOW()
                   )""",
                appt_id, tenant_id, client_id, appt_dt,
            )
            for ri in resolved_items:
                await conn.execute(
                    """INSERT INTO appointment_items (
                           id, tenant_id, appointment_id,
                           service_id, provider_id, sequence,
                           start_time, duration_minutes, price,
                           price_is_locked, status,
                           created_at, updated_at
                       ) VALUES (
                           $1, $2, $3,
                           $4, $5, $6,
                           $7, $8, $9,
                           true, 'pending',
                           NOW(), NOW()
                       )""",
                    uuid.uuid4(), tenant_id, appt_id,
                    ri["service_id"], ri["provider_id"], ri["seq"],
                    ri["start_time"], ri["duration"], ri["price"],
                )

        created += 1

    total_groups = len(groups)
    print(f"  Processed {total_groups} appointment groups:")
    print(f"    {created} created")
    print(f"    {skipped_existing} skipped (already exist)")
    print(f"    {skipped_no_client} skipped (client not found — run 'clients' first)")
    print(f"    {skipped_no_service} skipped (service not mapped / not in DB)")
    print(f"    {skipped_no_provider} skipped (provider not found)")


# ---------------------------------------------------------------------------
# Diagnostic commands
# ---------------------------------------------------------------------------

async def list_services(conn: asyncpg.Connection, tenant_id: uuid.UUID) -> None:
    rows = await conn.fetch(
        "SELECT service_code, name, default_price, duration_minutes, is_active "
        "FROM services WHERE tenant_id = $1 ORDER BY service_code",
        tenant_id,
    )
    if not rows:
        print("No services found. Add services via Settings → Services first.")
        return
    print(f"\n{'CODE':<12} {'NAME':<40} {'PRICE':>8} {'MIN':>5} {'ACTIVE'}")
    print("-" * 72)
    for r in rows:
        active = "✓" if r["is_active"] else "✗"
        print(f"{r['service_code']:<12} {r['name']:<40} {float(r['default_price'] or 0):>8.2f} {r['duration_minutes']:>5} {active:>6}")
    print(f"\nLegacy booking codes needing a mapping entry:")
    db_codes = {r["service_code"] for r in rows}
    for legacy, db in SERVICE_CODE_MAP.items():
        status = "✓ found" if db in db_codes else "✗ MISSING"
        print(f"  {legacy:<10} → {db:<12} {status}")


async def list_providers(conn: asyncpg.Connection, tenant_id: uuid.UUID) -> None:
    rows = await conn.fetch(
        "SELECT display_name, first_name, last_name, is_active "
        "FROM providers WHERE tenant_id = $1 ORDER BY display_name",
        tenant_id,
    )
    if not rows:
        print("No providers found.")
        return
    print(f"\n{'DISPLAY':<12} {'FULL NAME':<30} ACTIVE")
    print("-" * 48)
    for r in rows:
        active = "✓" if r["is_active"] else "✗"
        full = f"{r['first_name']} {r['last_name']}"
        print(f"{r['display_name']:<12} {full:<30} {active}")
    booking_staffs = {"ASAMI", "GUMI", "JJ", "JOANNE", "MAYUMI", "OLGA", "RYAN", "SARAH"}
    provider_display = {r["display_name"].upper() for r in rows}
    unmatched = booking_staffs - provider_display
    if unmatched:
        print(f"\nWARNING: these booking staff codes won't match any provider: {sorted(unmatched)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> None:
    db_url = args.db or os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL environment variable or --db argument is required.")

    conn_url = asyncpg_url(db_url)
    conn = await asyncpg.connect(conn_url)

    try:
        tenant_id = await get_tenant_id(conn, TENANT_SLUG)
        print(f"Tenant: {TENANT_SLUG} ({tenant_id})")

        if args.command == "list-services":
            await list_services(conn, tenant_id)
            return

        if args.command == "list-providers":
            await list_providers(conn, tenant_id)
            return

        provider_map = await load_providers(conn, tenant_id)
        print(f"Loaded {len(provider_map)} provider entries")

        if args.command in ("clients", "all"):
            if not CLIENT_FILE.exists():
                sys.exit(f"File not found: {CLIENT_FILE}")
            client_rows = read_csv(CLIENT_FILE)
            print(f"Read {len(client_rows)} rows from {CLIENT_FILE.name}")
            await import_clients(conn, tenant_id, client_rows, provider_map, args.dry_run)

        if args.command in ("bookings", "all"):
            if not BOOKINGS_FILE.exists():
                sys.exit(f"File not found: {BOOKINGS_FILE}")
            booking_rows = read_csv(BOOKINGS_FILE)
            print(f"Read {len(booking_rows)} rows from {BOOKINGS_FILE.name}")
            service_detail = await load_service_details(conn, tenant_id)
            print(f"Loaded {len(service_detail)} services from DB")
            await import_bookings(
                conn, tenant_id, booking_rows, provider_map, service_detail, args.dry_run
            )

    finally:
        await conn.close()

    if args.dry_run:
        print("\n[DRY RUN] No changes were written.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import legacy Salon Lyol data into the app DB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=["clients", "bookings", "all", "list-services", "list-providers"],
        help="What to import (or list for diagnostics)",
    )
    parser.add_argument("--db", help="Database URL (overrides DATABASE_URL env var)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would happen without writing"
    )
    parser.add_argument(
        "--tenant", default=None, help=f"Tenant subdomain (default: {TENANT_SLUG})"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.tenant:
        TENANT_SLUG = args.tenant
    asyncio.run(main(args))
