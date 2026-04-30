"""
Startup import script — runs once via docker-entrypoint.sh when RUN_IMPORT=true.
Uses the app's own database connection (handles Cloud SQL Unix socket automatically).
Safe to leave RUN_IMPORT=true permanently: exits immediately after the first run.
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import func, select

DATA_DIR = Path("/app/data")
TENANT_SLUG = "salon-lyol"


async def main() -> None:
    # Import here so the app's DB engine is initialised after env vars are loaded
    from app.database import AsyncSessionLocal
    from app.legacy_import import import_clients, import_bookings
    from app.models.client import Client
    from app.models.tenant import Tenant

    async with AsyncSessionLocal() as db:
        tenant = (
            await db.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if tenant is None:
            print(f"[import] Tenant '{TENANT_SLUG}' not found — skipping", flush=True)
            return

        # Fast-path: if any clients with a legacy_id already exist, the import
        # has already run. Skip to avoid the startup cost on every deploy.
        already = (
            await db.execute(
                select(func.count()).select_from(Client).where(
                    Client.tenant_id == tenant.id,
                    Client.legacy_id.isnot(None),
                )
            )
        ).scalar()
        if already:
            print(f"[import] {already} clients already imported — skipping", flush=True)
            return

        clients_file = DATA_DIR / "Client Details.txt"
        bookings_file = DATA_DIR / "All Bookings.txt"

        if not clients_file.exists():
            print(f"[import] {clients_file} not found — skipping", flush=True)
            return

        print("[import] Importing clients …", flush=True)
        clients_result = await import_clients(db, tenant.id, clients_file.read_bytes())
        print(f"[import] Clients: {clients_result}", flush=True)

        if bookings_file.exists():
            print("[import] Importing bookings …", flush=True)
            bookings_result = await import_bookings(db, tenant.id, bookings_file.read_bytes())
            print(f"[import] Bookings: {bookings_result}", flush=True)

        print("[import] Done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
