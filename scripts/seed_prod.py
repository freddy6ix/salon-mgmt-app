"""
Seed the Salon Lyol production tenant with real catalog data.

Run from repo root:
    uv --project backend run python scripts/seed_prod.py

Creates:
  - Tenant: slug=salon-lyol-prod
  - Admin user: jini@salonlyol.ca (temporary password printed at end)
  - Staff providers (same roster as dev tenant)
  - Service categories + services + per-provider pricing from docs/seed-data/Service Price List.xls
  - Retail items + opening stock from docs/seed-data/Retail Product Listing.xls
  - Promotions from docs/seed-data/Promotion List.xls

Idempotent — safe to re-run.
"""
import asyncio
import os
import secrets
import shutil
import sys
import tempfile
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import openpyxl
from urllib.parse import quote_plus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import hash_password
from app.config import settings
from app.models.department import Department
from app.models.promotion import PromotionKind, TenantPromotion
from app.models.provider import OnlineBookingVisibility, Provider, ProviderType
from app.models.retail import RetailItem, RetailStockMovement, StockMovementKind
from app.models.schedule import ProviderSchedule, TenantOperatingHours
from app.models.service import PricingType, Service, ServiceCategory
from app.models.provider_service_price import ProviderServicePrice
from app.models.tenant import Tenant
from app.models.user import User, UserRole

TENANT_SLUG = "salon-lyol-prod"
TENANT_NAME = "Salon Lyol"
ADMIN_EMAIL = "jini@salonlyol.ca"

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "seed-data")


def load_xls(filename: str):
    """Load an .xls file (which is actually xlsx) and return rows as list of tuples."""
    src = os.path.join(DATA_DIR, filename)
    tmp = tempfile.mktemp(suffix=".xlsx")
    shutil.copy(src, tmp)
    wb = openpyxl.load_workbook(tmp, read_only=True, data_only=True)
    sh = wb.active
    rows = [r for r in sh.iter_rows(values_only=True) if any(v for v in r if v is not None)]
    os.unlink(tmp)
    return rows


def service_category(code: str) -> str:
    """Map a service code to a category name."""
    code = (code or "").upper()
    if code.startswith("C") and code != "CON":
        return "Colouring"
    if code.startswith("EXT"):
        return "Extensions"
    return "Styling"


if settings.cloud_sql_instance:
    _socket_dir = f"/cloudsql/{settings.cloud_sql_instance}"
    _url = (
        f"postgresql+asyncpg://{settings.db_user}:{quote_plus(settings.db_password)}"
        f"@/{settings.db_name}"
    )
    _connect_args: dict = {"host": _socket_dir}
else:
    _url = settings.database_url
    _connect_args = {"ssl": False} if ("127.0.0.1" in _url or "localhost" in _url) else {}

engine = create_async_engine(_url, connect_args=_connect_args)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with SessionLocal() as db:

        # ── Tenant ────────────────────────────────────────────────────────────
        tenant = (await db.execute(
            select(Tenant).where(Tenant.slug == TENANT_SLUG)
        )).scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=TENANT_NAME, slug=TENANT_SLUG, is_active=True)
            db.add(tenant)
            await db.flush()
            print(f"Created tenant: {tenant.id}")
        else:
            print(f"Tenant exists: {tenant.id}")
        tid = tenant.id

        # ── Admin user ────────────────────────────────────────────────────────
        admin = (await db.execute(
            select(User).where(User.tenant_id == tid, User.email == ADMIN_EMAIL)
        )).scalar_one_or_none()
        tmp_password = None
        if admin is None:
            tmp_password = secrets.token_urlsafe(12)
            admin = User(
                tenant_id=tid,
                email=ADMIN_EMAIL,
                password_hash=hash_password(tmp_password),
                role=UserRole.tenant_admin,
                is_active=True,
            )
            db.add(admin)
            await db.flush()
            print(f"Created admin user: {ADMIN_EMAIL}")

        # ── Departments ───────────────────────────────────────────────────────
        dept_data = [
            dict(code="STYLING",   name="Styling",   has_appointments=True,  makes_appointments=True),
            dict(code="COLOUR",    name="Colour",    has_appointments=True,  makes_appointments=True),
            dict(code="RECEPTION", name="Reception", has_appointments=False, makes_appointments=True, can_be_cashier=True),
        ]
        depts = {}
        for d in dept_data:
            existing = (await db.execute(
                select(Department).where(Department.tenant_id == tid, Department.code == d["code"])
            )).scalar_one_or_none()
            if existing is None:
                existing = Department(tenant_id=tid, **d)
                db.add(existing)
                await db.flush()
            depts[d["code"]] = existing
        print(f"Departments: {list(depts.keys())}")

        # ── Providers (real roster) ────────────────────────────────────────────
        provider_data = [
            dict(first_name="Jini",      last_name="Jung",    display_name="JJ",       provider_code="JJ",       provider_type=ProviderType.dualist,   is_owner=True, booking_order=1,  has_appointments=True, makes_appointments=True, can_be_cashier=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Antonella", last_name="Cumbo",   display_name="Antonella",provider_code="ANTONELLA",provider_type=ProviderType.dualist,   booking_order=2,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Sarah",     last_name="",        display_name="Sarah",    provider_code="SARAH",    provider_type=ProviderType.dualist,   booking_order=3,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="COLOUR"),
            dict(first_name="Joanne",    last_name="",        display_name="Joanne",   provider_code="JOANNE",   provider_type=ProviderType.colourist, booking_order=4,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="COLOUR"),
            dict(first_name="Becky",     last_name="",        display_name="Becky",    provider_code="BECKY",    provider_type=ProviderType.stylist,   booking_order=5,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Olga",      last_name="",        display_name="Olga",     provider_code="OLGA",     provider_type=ProviderType.dualist,   booking_order=6,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Mayumi",    last_name="",        display_name="Mayumi",   provider_code="MAYUMI",   provider_type=ProviderType.dualist,   booking_order=7,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="COLOUR"),
            dict(first_name="Asami",     last_name="",        display_name="Asami",    provider_code="ASAMI",    provider_type=ProviderType.stylist,   booking_order=8,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Ryan",      last_name="",        display_name="Ryan",     provider_code="RYAN",     provider_type=ProviderType.dualist,   booking_order=9,  has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
            dict(first_name="Gumi",      last_name="",        display_name="Gumi",     provider_code="GUMI",     provider_type=ProviderType.dualist,   booking_order=10, has_appointments=True, makes_appointments=True, online_booking_visibility=OnlineBookingVisibility.available_to_all, department_code="STYLING"),
        ]
        providers: dict[str, Provider] = {}
        for p in provider_data:
            dept_code = p.pop("department_code")
            existing = (await db.execute(
                select(Provider).where(Provider.tenant_id == tid, Provider.provider_code == p["provider_code"])
            )).scalar_one_or_none()
            if existing is None:
                existing = Provider(tenant_id=tid, department_id=depts[dept_code].id, is_active=True, **p)
                db.add(existing)
                await db.flush()
            providers[existing.provider_code] = existing
        print(f"Providers: {list(providers.keys())}")

        # ── Operating hours (Tue–Sat 9–6) ─────────────────────────────────────
        from datetime import time as dtime
        HOURS = {1: ("09:00", "18:00"), 2: ("09:00", "18:00"), 3: ("09:00", "18:00"),
                 4: ("09:00", "18:00"), 5: ("09:00", "18:00")}
        for dow in range(7):
            existing = (await db.execute(
                select(TenantOperatingHours).where(TenantOperatingHours.tenant_id == tid,
                                                    TenantOperatingHours.day_of_week == dow)
            )).scalar_one_or_none()
            if existing is None:
                is_open = dow in HOURS
                oh = TenantOperatingHours(
                    tenant_id=tid, day_of_week=dow, is_open=is_open,
                    open_time=dtime.fromisoformat(HOURS[dow][0]) if is_open else None,
                    close_time=dtime.fromisoformat(HOURS[dow][1]) if is_open else None,
                )
                db.add(oh)
        await db.flush()

        # ── Service categories ─────────────────────────────────────────────────
        cat_data = [
            dict(name="Colouring", display_order=1),
            dict(name="Styling",   display_order=2),
            dict(name="Extensions",display_order=3),
        ]
        cats: dict[str, ServiceCategory] = {}
        for c in cat_data:
            existing = (await db.execute(
                select(ServiceCategory).where(ServiceCategory.tenant_id == tid, ServiceCategory.name == c["name"])
            )).scalar_one_or_none()
            if existing is None:
                existing = ServiceCategory(tenant_id=tid, **c)
                db.add(existing)
                await db.flush()
            cats[c["name"]] = existing
        print(f"Categories: {list(cats.keys())}")

        # ── Services + per-provider pricing ───────────────────────────────────
        svc_rows = load_xls("Service Price List.xls")
        header = svc_rows[0]  # ('Code', 'Desc', 'Staff', 'Price', 'Cost')
        data_rows = svc_rows[1:]

        # Group by service code
        from collections import defaultdict
        by_code: dict[str, list] = defaultdict(list)
        for row in data_rows:
            code = str(row[0] or "").strip()
            if code:
                by_code[code].append(row)

        svc_created = svc_price_created = 0
        services: dict[str, Service] = {}

        for code, rows in by_code.items():
            cat_name = service_category(code)
            cat = cats[cat_name]

            # Default price: row with empty Staff, else first row
            default_row = next((r for r in rows if not str(r[2] or "").strip()), rows[0])
            default_price = Decimal(str(default_row[3] or 0))
            default_cost = Decimal(str(default_row[4] or 0))
            desc = str(default_row[1] or code).strip()

            svc = (await db.execute(
                select(Service).where(Service.tenant_id == tid, Service.service_code == code)
            )).scalar_one_or_none()
            if svc is None:
                svc = Service(
                    tenant_id=tid,
                    category_id=cat.id,
                    service_code=code,
                    name=desc,
                    pricing_type=PricingType.fixed,
                    default_price=default_price,
                    default_cost=default_cost,
                    duration_minutes=60,
                    is_active=True,
                )
                db.add(svc)
                await db.flush()
                svc_created += 1
            services[code] = svc

            # Per-provider pricing for rows with a staff code
            for row in rows:
                staff_code = str(row[2] or "").strip().upper()
                if not staff_code:
                    continue
                provider = providers.get(staff_code)
                if provider is None:
                    continue
                price = Decimal(str(row[3] or 0))
                cost = Decimal(str(row[4] or 0))

                existing_psp = (await db.execute(
                    select(ProviderServicePrice).where(
                        ProviderServicePrice.tenant_id == tid,
                        ProviderServicePrice.provider_id == provider.id,
                        ProviderServicePrice.service_id == svc.id,
                    )
                )).scalar_one_or_none()
                if existing_psp is None:
                    db.add(ProviderServicePrice(
                        tenant_id=tid,
                        provider_id=provider.id,
                        service_id=svc.id,
                        price=price,
                        cost=cost,
                    ))
                    svc_price_created += 1

        await db.flush()
        print(f"Services: {svc_created} created, {svc_price_created} provider prices")

        # ── Retail items + opening stock ──────────────────────────────────────
        retail_rows = load_xls("Retail Product Listing.xls")
        # ('IsActive','Code','Description','Supplier','Brand','Category','ManuCode','Price','On Hand','Minimum','Maximum','Cost',...)
        retail_created = stock_created = 0
        for row in retail_rows[1:]:
            is_active = str(row[0] or "").strip().lower() == "true"
            sku = str(row[1] or "").strip() or None
            name = str(row[2] or "").strip()
            if not name:
                continue
            price = Decimal(str(row[7] or 0))
            on_hand = int(row[8] or 0)
            cost = Decimal(str(row[11] or 0))

            item = (await db.execute(
                select(RetailItem).where(RetailItem.tenant_id == tid, RetailItem.sku == sku)
                if sku else
                select(RetailItem).where(RetailItem.tenant_id == tid, RetailItem.name == name)
            )).scalar_one_or_none()

            if item is None:
                item = RetailItem(
                    tenant_id=tid,
                    sku=sku,
                    name=name,
                    default_price=price,
                    default_cost=cost if cost > 0 else None,
                    is_active=is_active,
                )
                db.add(item)
                await db.flush()
                retail_created += 1

                if on_hand > 0:
                    db.add(RetailStockMovement(
                        tenant_id=tid,
                        retail_item_id=item.id,
                        kind=StockMovementKind.receive,
                        quantity=on_hand,
                        unit_cost=cost if cost > 0 else None,
                        note="Opening stock from legacy system",
                    ))
                    stock_created += 1

        await db.flush()
        print(f"Retail: {retail_created} items, {stock_created} opening stock movements")

        # ── Promotions ────────────────────────────────────────────────────────
        promo_rows = load_xls("Promotion List.xls")
        # ('IsActive','Code','Desc','Amount','Type','Per Item','Category',...)
        promo_created = 0
        for row in promo_rows[1:]:
            is_active = str(row[0] or "").strip().lower() == "true"
            code = str(row[1] or "").strip()
            label = str(row[2] or code).strip()
            amount_raw = str(row[3] or "0").strip()
            try:
                value = Decimal(amount_raw)
            except Exception:
                value = Decimal("0")
            kind_raw = str(row[4] or "Amount").strip().lower()
            kind = PromotionKind.percent if kind_raw == "percent" else PromotionKind.amount
            if not code:
                continue

            existing = (await db.execute(
                select(TenantPromotion).where(TenantPromotion.tenant_id == tid, TenantPromotion.code == code)
            )).scalar_one_or_none()
            if existing is None:
                db.add(TenantPromotion(
                    tenant_id=tid,
                    code=code,
                    label=label,
                    kind=kind,
                    value=value,
                    is_active=is_active,
                ))
                promo_created += 1

        await db.flush()
        print(f"Promotions: {promo_created} created")

        await db.commit()
        print("\n✅ Production seed complete.")
        print(f"  Tenant  : {TENANT_NAME} (slug={TENANT_SLUG})")
        print(f"  Tenant ID: {tid}")
        print(f"  Admin   : {ADMIN_EMAIL}")
        if tmp_password:
            print(f"  Password: {tmp_password}  ← change this immediately via Settings → Users")
        else:
            print(f"  Password: (existing — use password reset if needed)")
        print()
        print("Next steps:")
        print("  1. Log in as jini@salonlyol.ca at the staging URL")
        print("  2. Go to Settings → Email to configure outbound email")
        print("  3. Go to Staff to fill in provider details and link login accounts")
        print("  4. Run the client import via POST /admin/import-legacy to load client history")


if __name__ == "__main__":
    asyncio.run(seed())
