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

_url = settings.database_url
# Cloud SQL Proxy via TCP doesn't support SSL negotiation — disable it.
# Unix-socket connections (Cloud Run) are unaffected.
_connect_args = {"ssl": False} if ("127.0.0.1" in _url or "localhost" in _url) else {}
engine = create_async_engine(_url, connect_args=_connect_args)
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

        # Backfill / refresh contact details (idempotent)
        if tenant.address_line1 is None:
            tenant.address_line1 = "1452 Yonge Street"
        if tenant.city is None:
            tenant.city = "Toronto"
        if tenant.region is None:
            tenant.region = "ON"
        if tenant.country is None:
            tenant.country = "CA"
        if tenant.phone is None:
            tenant.phone = "416-922-0511"
        if tenant.hours_summary is None:
            tenant.hours_summary = "Tue–Sat · by appointment"

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
                 provider_type=ProviderType.dualist, is_owner=True, booking_order=1,
                 has_appointments=True, makes_appointments=True, can_be_cashier=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 user_id=jj_user.id, department_code="STYLING"),
            dict(first_name="Antonella", last_name="Cumbo", display_name="Antonella", milano_code="ANTONELLA",
                 provider_type=ProviderType.dualist, booking_order=2,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Ryan", last_name="", display_name="Ryan", milano_code="RYAN",
                 provider_type=ProviderType.dualist, booking_order=9,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Gumi", last_name="", display_name="Gumi", milano_code="GUMI",
                 provider_type=ProviderType.dualist, booking_order=10,
                 has_appointments=True, makes_appointments=True,
                 online_booking_visibility=OnlineBookingVisibility.available_to_all,
                 department_code="STYLING"),
            dict(first_name="Sarah", last_name="", display_name="Sarah", milano_code="SARAH",
                 provider_type=ProviderType.dualist, booking_order=3,
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
            else:
                provider.provider_type = p["provider_type"]
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
            dict(category="Styling", service_code="FRG", name="Fringe/Bang Cut", duration_minutes=15, default_price=20, ),
            dict(category="Styling", service_code="HTF", name="Heat Tool Finish", duration_minutes=15, default_price=10, ),
            dict(category="Styling", service_code="UPD", name="Special Updo", duration_minutes=90, default_price=145),
            dict(category="Styling", service_code="BOT", name="Hair Botox", duration_minutes=180, default_price=400),
            dict(category="Styling", service_code="MLB", name="Milbon Treatment", duration_minutes=60, default_price=100),
            dict(category="Styling", service_code="MLBA", name="Milbon Treatment (add-on)", duration_minutes=30, default_price=65, ),
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
            dict(category="Colouring", service_code="TNRA", name="Toner/Gloss (add-on)", duration_minutes=30, default_price=50,
                 processing_offset_minutes=5, processing_duration_minutes=20),
            dict(category="Colouring", service_code="REF", name="Refreshing Ends", duration_minutes=30, default_price=50),
            dict(category="Colouring", service_code="MDO", name="Metal Detox/Olaplex (add-on)", duration_minutes=15, default_price=35, ),
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
            dict(day_of_week=1, is_open=True, open_time="09:00", close_time="18:00"),  # Tuesday  (last out 18:00)
            dict(day_of_week=2, is_open=True, open_time="09:00", close_time="20:00"),  # Wednesday (last out 20:00)
            dict(day_of_week=3, is_open=True, open_time="09:00", close_time="20:00"),  # Thursday  (last out 20:00)
            dict(day_of_week=4, is_open=True, open_time="09:00", close_time="18:00"),  # Friday   (last out 18:00)
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
            #            Mon   Tue                           Wed                          Thu                          Fri                          Sat                        Sun
            "ASAMI":   {0: OFF, 1: [(T(9,0),  T(18,0))],  2: [(T(11,0),T(20,0))],    3: [(T(9,0),  T(18,0))],    4: OFF,                      5: [(T(9,0), T(17,0))],   6: OFF},
            "GUMI":    {0: OFF, 1: [(T(9,0),  T(18,0))],  2: [(T(11,0),T(20,0))],    3: [(T(9,0),  T(18,0))],    4: [(T(9,0),  T(18,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "JJ":      {0: OFF, 1: [(T(9,0),  T(18,0))],  2: [(T(9,0), T(20,0))],    3: [(T(9,0),  T(20,0))],    4: [(T(9,0),  T(18,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "JOANNE":  {0: OFF, 1: [(T(9,0),  T(17,0))],  2: [(T(9,0), T(16,0))],    3: [(T(11,0), T(19,0))],    4: [(T(9,0),  T(17,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "MAYUMI":  {0: OFF, 1: [(T(10,0), T(18,0))],  2: OFF,                     3: [(T(10,0), T(20,0))],    4: [(T(10,0), T(18,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "OLGA":    {0: OFF, 1: [(T(9,0),  T(17,0))],  2: [(T(11,0),T(20,0))],    3: OFF,                      4: [(T(10,0), T(18,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "RYAN":    {0: OFF, 1: [(T(9,0),  T(18,0))],  2: [(T(11,0),T(20,0))],    3: OFF,                      4: [(T(9,0),  T(18,0))],    5: [(T(9,0), T(17,0))],   6: OFF},
            "SARAH":   {0: OFF, 1: [(T(9,0),  T(16,30))], 2: [(T(9,0), T(16,30))],   3: [(T(11,0), T(19,0))],    4: OFF,                      5: [(T(9,0), T(17,0))],   6: OFF},
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

        # ── Provider Service Prices ──────────────────────────────────────────
        # Source: Google Sheet shared by owner (2026-04-28).
        #
        # Omissions (not in the sheet — need owner input):
        #   CCAMO  Camo Colour            — no per-provider pricing provided
        #   CFC    Color Full Color       — no per-provider pricing provided
        #   "Additional colour $25"       — in sheet but no service code in catalog
        #
        # By-request / n/a entries (no PSP row created):
        #   JJ:    Updo, Hair Botox       — "by request"
        #   JJ:    all colour services    — not listed (colour by request)
        #   Asami: Updo                   — "n/a"
        #   Becky, Antonella              — on maternity leave, not listed
        PSP_DATA: list[tuple[str, str, float]] = [
            # ── JJ (styling only) ─────────────────────────────────────────
            ("JJ", "BLD",  70),
            ("JJ", "ST1",  80),
            ("JJ", "ST2",  125),
            ("JJ", "ST2P", 150),
            ("JJ", "HTF",  10),
            ("JJ", "FRG",  20),
            ("JJ", "MLB",  100),
            ("JJ", "MLBA", 65),

            # ── Gumi (dualist) ─────────────────────────────────────────────
            ("GUMI", "BLD",  60),
            ("GUMI", "ST1",  65),
            ("GUMI", "ST2",  100),
            ("GUMI", "ST2P", 125),
            ("GUMI", "HTF",  10),
            ("GUMI", "FRG",  20),
            ("GUMI", "UPD",  150),
            ("GUMI", "MLB",  100),
            ("GUMI", "MLBA", 65),
            ("GUMI", "BOT",  400),
            ("GUMI", "RTO",  90),
            ("GUMI", "RTOB", 100),
            ("GUMI", "ACC",  100),
            ("GUMI", "PHL",  130),
            ("GUMI", "FHL",  170),
            ("GUMI", "BLT",  190),
            ("GUMI", "BLY",  240),
            ("GUMI", "CCR",  100),
            ("GUMI", "TNR",  85),
            ("GUMI", "REF",  50),
            ("GUMI", "TNRA", 50),
            ("GUMI", "MDO",  35),

            # ── Asami (stylist only) ───────────────────────────────────────
            ("ASAMI", "BLD",  55),
            ("ASAMI", "ST1",  60),
            ("ASAMI", "ST2",  90),
            ("ASAMI", "ST2P", 115),
            ("ASAMI", "HTF",  10),
            ("ASAMI", "FRG",  20),
            ("ASAMI", "MLB",  100),
            ("ASAMI", "MLBA", 65),
            ("ASAMI", "BOT",  400),

            # ── Mayumi (dualist) ───────────────────────────────────────────
            ("MAYUMI", "BLD",  55),
            ("MAYUMI", "ST1",  55),
            ("MAYUMI", "ST2",  90),
            ("MAYUMI", "ST2P", 115),
            ("MAYUMI", "HTF",  10),
            ("MAYUMI", "FRG",  20),
            ("MAYUMI", "UPD",  140),
            ("MAYUMI", "MLB",  100),
            ("MAYUMI", "MLBA", 65),
            ("MAYUMI", "BOT",  400),
            ("MAYUMI", "RTO",  90),
            ("MAYUMI", "RTOB", 100),
            ("MAYUMI", "ACC",  100),
            ("MAYUMI", "PHL",  130),
            ("MAYUMI", "FHL",  170),
            ("MAYUMI", "BLT",  190),
            ("MAYUMI", "BLY",  240),
            ("MAYUMI", "CCR",  100),
            ("MAYUMI", "TNR",  85),
            ("MAYUMI", "REF",  50),
            ("MAYUMI", "TNRA", 50),
            ("MAYUMI", "MDO",  35),

            # ── Olga (dualist) ─────────────────────────────────────────────
            ("OLGA", "BLD",  55),
            ("OLGA", "ST1",  55),
            ("OLGA", "ST2",  90),
            ("OLGA", "ST2P", 115),
            ("OLGA", "HTF",  10),
            ("OLGA", "FRG",  20),
            ("OLGA", "UPD",  140),
            ("OLGA", "MLB",  100),
            ("OLGA", "MLBA", 65),
            ("OLGA", "BOT",  400),
            ("OLGA", "RTO",  90),
            ("OLGA", "RTOB", 100),
            ("OLGA", "ACC",  100),
            ("OLGA", "PHL",  130),
            ("OLGA", "FHL",  170),
            ("OLGA", "BLT",  190),
            ("OLGA", "BLY",  240),
            ("OLGA", "CCR",  100),
            ("OLGA", "TNR",  85),
            ("OLGA", "REF",  50),
            ("OLGA", "TNRA", 50),
            ("OLGA", "MDO",  35),

            # ── Ryan (dualist) ─────────────────────────────────────────────
            ("RYAN", "BLD",  60),
            ("RYAN", "ST1",  65),
            ("RYAN", "ST2",  100),
            ("RYAN", "ST2P", 125),
            ("RYAN", "HTF",  10),
            ("RYAN", "FRG",  20),
            ("RYAN", "UPD",  150),
            ("RYAN", "MLB",  100),
            ("RYAN", "MLBA", 65),
            ("RYAN", "BOT",  400),
            ("RYAN", "RTO",  90),
            ("RYAN", "RTOB", 100),
            ("RYAN", "ACC",  100),
            ("RYAN", "PHL",  130),
            ("RYAN", "FHL",  170),
            ("RYAN", "BLT",  190),
            ("RYAN", "BLY",  240),
            ("RYAN", "CCR",  100),
            ("RYAN", "TNR",  85),
            ("RYAN", "REF",  50),
            ("RYAN", "TNRA", 50),
            ("RYAN", "MDO",  35),

            # ── Joanne (colourist) ─────────────────────────────────────────
            ("JOANNE", "RTO",  90),
            ("JOANNE", "RTOB", 100),
            ("JOANNE", "ACC",  120),
            ("JOANNE", "PHL",  150),
            ("JOANNE", "FHL",  190),
            ("JOANNE", "BLT",  210),
            ("JOANNE", "BLY",  260),
            ("JOANNE", "CCR",  120),
            ("JOANNE", "TNR",  85),
            ("JOANNE", "MLB",  100),
            ("JOANNE", "BOT",  400),
            ("JOANNE", "REF",  50),
            ("JOANNE", "TNRA", 50),
            ("JOANNE", "MLBA", 65),
            ("JOANNE", "MDO",  35),

            # ── Sarah (colourist) ──────────────────────────────────────────
            ("SARAH", "RTO",  90),
            ("SARAH", "RTOB", 100),
            ("SARAH", "ACC",  100),
            ("SARAH", "PHL",  130),
            ("SARAH", "FHL",  170),
            ("SARAH", "BLT",  190),
            ("SARAH", "BLY",  240),
            ("SARAH", "CCR",  100),
            ("SARAH", "TNR",  85),
            ("SARAH", "MLB",  100),
            ("SARAH", "BOT",  400),
            ("SARAH", "REF",  50),
            ("SARAH", "TNRA", 50),
            ("SARAH", "MLBA", 65),
            ("SARAH", "MDO",  35),
        ]

        psp_count = 0
        for milano_code, svc_code, price in PSP_DATA:
            prov = providers.get(milano_code)
            svc  = services.get(svc_code)
            if prov is None or svc is None:
                print(f"  WARN: skipping PSP ({milano_code}, {svc_code}) — not found")
                continue
            existing_psp = (
                await db.execute(
                    select(ProviderServicePrice).where(
                        ProviderServicePrice.tenant_id == tid,
                        ProviderServicePrice.provider_id == prov.id,
                        ProviderServicePrice.service_id == svc.id,
                    )
                )
            ).scalar_one_or_none()
            if existing_psp is None:
                db.add(ProviderServicePrice(
                    tenant_id=tid,
                    provider_id=prov.id,
                    service_id=svc.id,
                    price=price,
                    effective_from=date(2000, 1, 1),
                    is_active=True,
                ))
                psp_count += 1
            elif float(existing_psp.price) != price:
                existing_psp.price = price
                psp_count += 1
        print(f"Provider service prices: {psp_count} created/updated")

        await db.commit()
        print("\nSeed complete.")
        print(f"  Tenant ID : {tenant.id}")
        print(f"  Login     : jj@salonlyol.ca / changeme123")
        print()
        print("NOTE — prices not yet seeded (not in sheet):")
        print("  CCAMO  Camo Colour       — needs per-provider pricing")
        print("  CFC    Color Full Color  — needs per-provider pricing")
        print("  'Additional colour $25'  — needs a service code in catalog")


if __name__ == "__main__":
    asyncio.run(seed())
