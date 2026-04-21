from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import appointments, auth, clients, providers, schedules, services

app = FastAPI(
    title="Salon Lyol Management API",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(providers.router)
app.include_router(clients.router)
app.include_router(services.router)
app.include_router(schedules.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "environment": settings.environment}
