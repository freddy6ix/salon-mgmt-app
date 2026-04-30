"""
Startup import script — runs via docker-entrypoint.sh when RUN_IMPORT=true.
Uses the app's own database connection (handles Cloud SQL Unix socket automatically).
Safe to leave RUN_IMPORT=true permanently: exits immediately after the first run.

Import order (each step is idempotent):
  1. Clients
  2. Receipt transactions → completed appointments + sales
  3. Past bookings with no receipt → confirmed appointments (client never arrived)
  4. Future bookings → confirmed upcoming appointments
"""

import asyncio
from pathlib import Path

from sqlalchemy import func, select

DATA_DIR = Path("/app/data")
TENANT_SLUG = "salon-lyol"

CLIENTS_FILE        = DATA_DIR / "Client Details.txt"
RECEIPTS_FILE       = DATA_DIR / "Receipt Transactions.txt"
ALL_BOOKINGS_FILE   = DATA_DIR / "Future and Past Bookings.txt"


async def main() -> None:
    from app.database import AsyncSessionLocal
    from app.legacy_import import (
        import_clients,
        import_bookings,
        import_receipts,
        import_past_unreceipted_bookings,
    )
    from app.models.client import Client
    from app.models.tenant import Tenant

    async with AsyncSessionLocal() as db:
        tenant = (
            await db.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if tenant is None:
            print(f"[import] Tenant '{TENANT_SLUG}' not found — skipping", flush=True)
            return

        # Fast-path: skip if a full import has already completed (> 5000 clients
        # with legacy_id means the client step finished successfully).
        already = (await db.execute(
            select(func.count()).select_from(Client).where(
                Client.tenant_id == tenant.id,
                Client.legacy_id.isnot(None),
            )
        )).scalar()
        if already > 5000:
            print(f"[import] {already} clients already imported — skipping", flush=True)
            return

        if not CLIENTS_FILE.exists():
            print(f"[import] {CLIENTS_FILE} not found — skipping", flush=True)
            return

        # 1. Clients
        print("[import] Step 1/4 — clients …", flush=True)
        r = await import_clients(db, tenant.id, CLIENTS_FILE.read_bytes())
        print(f"[import] Clients: {r}", flush=True)

        # 2. Completed appointments from receipt transactions
        if RECEIPTS_FILE.exists() and ALL_BOOKINGS_FILE.exists():
            print("[import] Step 2/4 — receipt transactions (completed appointments) …", flush=True)
            r = await import_receipts(
                db, tenant.id,
                RECEIPTS_FILE.read_bytes(),
                ALL_BOOKINGS_FILE.read_bytes(),
            )
            print(f"[import] Receipts: {r}", flush=True)
        else:
            print("[import] Step 2/4 — receipt files missing, skipping", flush=True)

        # 3. Past bookings with no receipt (client never arrived)
        if ALL_BOOKINGS_FILE.exists():
            print("[import] Step 3/4 — past unreceipted bookings …", flush=True)
            r = await import_past_unreceipted_bookings(
                db, tenant.id, ALL_BOOKINGS_FILE.read_bytes()
            )
            print(f"[import] Past unreceipted: {r}", flush=True)

        # 4. Future bookings
        if ALL_BOOKINGS_FILE.exists():
            print("[import] Step 4/4 — future bookings …", flush=True)
            r = await import_bookings(
                db, tenant.id,
                ALL_BOOKINGS_FILE.read_bytes(),
                future_only=True,
            )
            print(f"[import] Future bookings: {r}", flush=True)

        print("[import] Done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
