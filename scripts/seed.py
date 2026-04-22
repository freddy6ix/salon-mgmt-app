"""
Seed Salon Lyol initial data.
Run from repo root: uv --project backend run python scripts/seed.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import date, time as dtime
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth import hash_password
from app.config import settings
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.provider import Provider, ProviderType, OnlineBookingVisibility
from app.models.service import ServiceCategory, Service, PricingType
from app.models.provider_service_price import ProviderServicePrice
from app.models.schedule import TenantOperatingHours, ProviderSchedule

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with SessionLocal() as db:

        # ── Tenant ──────────────────────────────────────────────────────────
        existing = await db.execute(select(Tenant).where(Tenant.slug == "salon-lyol"))
        tenant = existing.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name="Salon Lyol", slug="salon-lyol", is_active=True)
            db.add(tenant)
            await db.flush()
            print(f"Created tenant: {tenant.id}")
        else:
            print(f"Tenant already exists: {tenant.id}")

        tid = tenant.id

        # ── Departments ─────────────────────────────────────────────────────
        dept_data = [
            dict(code="STYLING", name="Styling", has_appointments=True, makes_appointments=True),
            dict(code="COLOUR", name="Colour", has_appointments=True, makes_appointments=True),
            dict(code="RECEPTION", name="Reception", can_be_cashier=True, makes_appointments=True, has_appointments=False),
        ]
        depts = {}
        for d in dept_data:
            existing = await db.execute(
                select(Department).where(Department.tenant_id == tid, Department.code == d["code"])
            )
            dept = existing.scalar_one_or_none()
            if dept is None:
                dept = Department(tenant_id=tid, **d)
                db.add(dept)
                await db.flush()
            depts[d["code"]] = dept
        print(f"Departments: {list(depts.keys())}")

        # ── Owner user + provider (JJ) ───────────────────────────────────────
        existing = await db.execute(
            select(User).where(User.tenant_id == tid, User.email == "jj@salonlyol.ca")
        )
        jj_user = existing.scalar_one_or_none()
        if jj_user is None:
            jj_user = User(
                tenant_id=tid,
                email="jj@salonlyol.ca",
                password_hash=hash_password("changeme123"),
                role=UserRole.tenant_admin,
                is_active=True,
            )
            db.add(jj_user)
            await db.flush()
            print(f"Created user JJ: {jj_user.id}")

        # ── Providers ────────────────────────────────────────────────────────
        provider_data = [
            dict(first_name="Jini", last_name="Jung", display_name="JJ", milano_code="JJ",
                 provider_type=ProviderType.stylist, is_owner=True, booking_order=1,
                 has_appointments=True, makes_appointments=True, can_be_cashier=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 user_id=jj_user.id, department_code="STYLING"),
            dict(first_name="Antonella", last_name="Cumbo", display_name="Antonella", milano_code="ANTONELLA",
                 provider_type=ProviderType.stylist, booking_order=2,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Ryan", last_name="", display_name="Ryan", milano_code="RYAN",
                 provider_type=ProviderType.stylist, booking_order=9,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Gumi", last_name="", display_name="Gumi", milano_code="GUMI",
                 provider_type=ProviderType.stylist, booking_order=10,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Sarah", last_name="", display_name="Sarah", milano_code="SARAH",
                 provider_type=ProviderType.colourist, booking_order=3,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="COLOUR"),
            dict(first_name="Joanne", last_name="", display_name="Joanne", milano_code="JOANNE",
                 provider_type=ProviderType.colourist, booking_order=4,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="COLOUR"),
            dict(first_name="Becky", last_name="", display_name="Becky", milano_code="BECKY",
                 provider_type=ProviderType.stylist, booking_order=5,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Olga", last_name="", display_name="Olga", milano_code="OLGA",
                 provider_type=ProviderType.dualist, booking_order=6,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Mayumi", last_name="", display_name="Mayumi", milano_code="MAYUMI",
                 provider_type=ProviderType.dualist, booking_order=7,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="COLOUR"),
            dict(first_name="Asami", last_name="", display_name="Asami", milano_code="ASAMI",
                 provider_type=ProviderType.stylist, booking_order=8,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
        ]
        providers = {}
        for p in provider_data:
            dept_code = p.pop("department_code")
            existing = await db.execute(
                select(Provider).where(Provider.tenant_id == tid, Provider.milano_code == p["milano_code"])
            )
            provider = existing.scalar_one_or_none()
            if provider is None:
                provider = Provider(
                    tenant_id=tid,
                    department_id=depts[dept_code].id,
                    **p,
                )
                db.add(provider)
                await db.flush()
            providers[p["milano_code"]] = provider
        print(f"Providers: {list(providers.keys())}")

        # ── Service Categories ───────────────────────────────────────────────
        cat_data = [
            dict(name="Styling", display_order=1),
            dict(name="Colouring", display_order=2),
            dict(name="Extensions", display_order=3),
        ]
        cats = {}
        for c in cat_data:
            existing = await db.execute(
                select(ServiceCategory).where(ServiceCategory.tenant_id == tid, ServiceCategory.name == c["name"])
            )
            cat = existing.scalar_one_or_none()
            if cat is None:
                cat = ServiceCategory(tenant_id=tid, **c)
                db.add(cat)
                await db.flush()
            cats[c["name"]] = cat

        # ── Services ─────────────────────────────────────────────────────────
        service_data = [
            # Styling
            dict(category="Styling", service_code="BLD", name="Blowdry", duration_minutes=60, default_price=60),
            dict(category="Styling", service_code="ST1", name="Type 1 Haircut", duration_minutes=45, default_price=65),
            dict(category="Styling", service_code="ST2", name="Type 2 Haircut", duration_minutes=60, default_price=100),
            dict(category="Styling", service_code="ST2P", name="Type 2+ Haircut", duration_minutes=75, default_price=130),
            dict(category="Styling", service_code="FRG", name="Fringe/Bang Cut", duration_minutes=15, default_price=20, is_addon=True),
            dict(category="Styling", service_code="HTF", name="Heat Tool Finish", duration_minutes=15, default_price=10, is_addon=True),
            dict(category="Styling", service_code="UPD", name="Special Updo", duration_minutes=90, default_price=145),
            dict(category="Styling", service_code="BOT", name="Hair Botox", duration_minutes=180, default_price=400),
            dict(category="Styling", service_code="MLB", name="Milbon Treatment", duration_minutes=60, default_price=100),
            dict(category="Styling", service_code="MLBA", name="Milbon Treatment (add-on)", duration_minutes=30, default_price=65, is_addon=True),
            # Colouring
            dict(category="Colouring", service_code="CCAMO", name="Camo Colour", duration_minutes=50, default_price=50,
                 processing_offset_minutes=20, processing_duration_minutes=30),
            dict(category="Colouring", service_code="RTO", name="Root Touch-Up", duration_minutes=90, default_price=90,
                 processing_offset_minutes=15, processing_duration_minutes=35),
            dict(category="Colouring", service_code="RTOB", name="Root Touch-Up (bleach/high lift)", duration_minutes=105, default_price=100,
                 processing_offset_minutes=15, processing_duration_minutes=45),
            dict(category="Colouring", service_code="ACC", name="Accent Highlights", duration_minutes=90, default_price=110,
                 processing_offset_minutes=45, processing_duration_minutes=30),
            dict(category="Colouring", service_code="PHL", name="Partial Highlights", duration_minutes=120, default_price=140,
                 processing_offset_minutes=60, processing_duration_minutes=35),
            dict(category="Colouring", service_code="FHL", name="Full Highlights", duration_minutes=150, default_price=180,
                 processing_offset_minutes=80, processing_duration_minutes=35),
            dict(category="Colouring", service_code="BLT", name="Balayage Touch-Up", duration_minutes=150, default_price=200,
                 processing_offset_minutes=90, processing_duration_minutes=40),
            dict(category="Colouring", service_code="BLY", name="Full Balayage", duration_minutes=180, default_price=250,
                 processing_offset_minutes=100, processing_duration_minutes=45),
            dict(category="Colouring", service_code="CFC", name="Color Full Color", duration_minutes=90, default_price=100,
                 processing_offset_minutes=15, processing_duration_minutes=40),
            dict(category="Colouring", service_code="CCR", name="Colour Correction", duration_minutes=240, default_price=110,
                 pricing_type=PricingType.hourly),
            dict(category="Colouring", service_code="TNR", name="Toner/Gloss", duration_minutes=45, default_price=85,
                 processing_offset_minutes=5, processing_duration_minutes=20),
            dict(category="Colouring", service_code="TNRA", name="Toner/Gloss (add-on)", duration_minutes=30, default_price=50, is_addon=True,
                 processing_offset_minutes=5, processing_duration_minutes=20),
            dict(category="Colouring", service_code="REF", name="Refreshing Ends", duration_minutes=30, default_price=50),
            dict(category="Colouring", service_code="MDO", name="Metal Detox/Olaplex (add-on)", duration_minutes=15, default_price=35, is_addon=True),
            # Extensions
            dict(category="Extensions", service_code="EXF", name="Extensions - Fusion", duration_minutes=270, default_price=400, requires_prior_consultation=True),
            dict(category="Extensions", service_code="EXM", name="Extensions - Microbead", duration_minutes=270, default_price=400, requires_prior_consultation=True),
            dict(category="Extensions", service_code="EXT", name="Extensions - Tape-In", duration_minutes=150, default_price=250, requires_prior_consultation=True),
            dict(category="Extensions", service_code="EXW", name="Extensions - Weft", duration_minutes=150, default_price=250, requires_prior_consultation=True),
        ]
        services = {}
        for s in service_data:
            cat_name = s.pop("category")
            existing = await db.execute(
                select(Service).where(Service.tenant_id == tid, Service.service_code == s["service_code"])
            )
            svc = existing.scalar_one_or_none()
            if svc is None:
                svc = Service(
                    tenant_id=tid,
                    category_id=cats[cat_name].id,
                    is_active=True,
                    **s,
                )
                db.add(svc)
                await db.flush()
            services[s["service_code"]] = svc
        print(f"Services: {len(services)} created/existing")

        # ── Operating Hours ──────────────────────────────────────────────────
        hours_data = [
            dict(day_of_week=0, is_open=False),                                     # Monday   — closed
            dict(day_of_week=1, is_open=True, open_time="09:00", close_time="17:00"),  # Tuesday
            dict(day_of_week=2, is_open=True, open_time="09:00", close_time="20:00"),  # Wednesday
            dict(day_of_week=3, is_open=True, open_time="09:00", close_time="20:00"),  # Thursday
            dict(day_of_week=4, is_open=True, open_time="09:00", close_time="20:00"),  # Friday (Joanne until 19:00)
            dict(day_of_week=5, is_open=True, open_time="09:00", close_time="17:00"),  # Saturday
            dict(day_of_week=6, is_open=False),                                     # Sunday   — closed
        ]
        for h in hours_data:
            existing = await db.execute(
                select(TenantOperatingHours).where(
                    TenantOperatingHours.tenant_id == tid,
                    TenantOperatingHours.day_of_week == h["day_of_week"]
                )
            )
            ot = h.get("open_time")
            ct = h.get("close_time")
            rec = existing.scalar_one_or_none()
            if rec is None:
                rec = TenantOperatingHours(tenant_id=tid, day_of_week=h["day_of_week"])
                db.add(rec)
            rec.is_open = h["is_open"]
            rec.open_time = dtime.fromisoformat(ot) if ot else None
            rec.close_time = dtime.fromisoformat(ct) if ct else None
        print("Operating hours seeded")

        # ── Provider Weekly Schedules ────────────────────────────────────────
        # day_of_week: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun (ISO)
        # Values: list of (start, end) tuples per block, or [] for day off.
        # Source: docs/seed-data/provider-schedules.md
        EPOCH = date(2000, 1, 1)
        T = dtime  # shorthand

        OFF = []
        PROVIDER_SCHEDULES: dict[str, dict[int, list]] = {
            #            Mon   Tue                        Wed                        Thu                         Fri                        Sat                        Sun
            "ASAMI":   {0: OFF, 1: [(T(9,0), T(17,0))], 2: [(T(9,0), T(11,0))],  3: OFF,                      4: [(T(9,0), T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "GUMI":    {0: OFF, 1: [(T(10,0),T(17,0))], 2: [(T(9,0), T(17,0))],  3: OFF,                      4: [(T(10,0),T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "JJ":      {0: OFF, 1: OFF,                  2: OFF,                   3: [(T(9,0), T(17,0))],     4: [(T(9,0), T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "JOANNE":  {0: OFF, 1: [(T(9,0), T(17,0))], 2: OFF,                   3: [(T(11,0),T(19,0))],     4: [(T(9,0), T(19,0))],   5: OFF,                    6: OFF},
            "MAYUMI":  {0: OFF, 1: OFF,                  2: [(T(10,0),T(17,0))],  3: [(T(10,0),T(17,0))],     4: [(T(10,0),T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "OLGA":    {0: OFF, 1: OFF,                  2: [(T(9,0), T(17,0))],  3: [(T(10,0),T(17,0))],     4: [(T(9,0), T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "RYAN":    {0: OFF, 1: [(T(9,0), T(17,0))], 2: OFF,                   3: [(T(9,0), T(17,0))],     4: [(T(9,0), T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            "SARAH":   {0: OFF, 1: [(T(9,0), T(17,0))], 2: OFF,                   3: [(T(9,0), T(11,0))],     4: [(T(9,0), T(17,0))],   5: [(T(9,0), T(17,0))],   6: OFF},
            # Maternity leave — all days off
            "ANTONELLA": {dow: OFF for dow in range(7)},
            "BECKY":     {dow: OFF for dow in range(7)},
        }

        for milano_code, schedule in PROVIDER_SCHEDULES.items():
            provider = providers.get(milano_code)
            if provider is None:
                continue
            # Delete and recreate so re-runs apply updated schedules
            await db.execute(
                delete(ProviderSchedule).where(
                    ProviderSchedule.tenant_id == tid,
                    ProviderSchedule.provider_id == provider.id,
                )
            )
            for dow, blocks in schedule.items():
                if not blocks:
                    db.add(ProviderSchedule(
                        tenant_id=tid, provider_id=provider.id,
                        day_of_week=dow, block=1, is_working=False,
                        start_time=None, end_time=None,
                        effective_from=EPOCH, effective_to=None,
                    ))
                else:
                    for block_num, (start, end) in enumerate(blocks, 1):
                        db.add(ProviderSchedule(
                            tenant_id=tid, provider_id=provider.id,
                            day_of_week=dow, block=block_num, is_working=True,
                            start_time=start, end_time=end,
                            effective_from=EPOCH, effective_to=None,
                        ))
        print("Provider weekly schedules seeded")

        await db.commit()
        print("\nSeed complete.")
        print(f"  Tenant ID : {tenant.id}")
        print(f"  Login     : jj@salonlyol.ca / changeme123")


if __name__ == "__main__":
    asyncio.run(seed())
