from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, appointment_requests, appointments, auth, clients, providers, schedules, services
from app.routers import settings as settings_router

app = FastAPI(
    title="Salon Lyol Management API",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(appointments.router)
app.include_router(appointment_requests.router)
app.include_router(providers.router)
app.include_router(clients.router)
app.include_router(services.router)
app.include_router(schedules.router)
app.include_router(settings_router.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
