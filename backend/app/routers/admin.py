import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.config import settings
from app.database import get_db
from app.deps import AdminUser
from app.email import SmtpConfig, send_email, send_welcome_email
from app.models.client import Client
from app.models.email_config import TenantEmailConfig
from app.models.user import PasswordResetToken, User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])

RESET_TOKEN_EXPIRES_HOURS = 72
ALLOWED_MANAGED_ROLES = {UserRole.tenant_admin, UserRole.staff}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_smtp_config(tenant_id: uuid.UUID, db: AsyncSession) -> SmtpConfig:
    row = (
        await db.execute(
            select(TenantEmailConfig).where(TenantEmailConfig.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email not configured — set up SMTP in Settings → Email first",
        )
    return SmtpConfig(
        host=row.smtp_host,
        port=row.smtp_port,
        username=row.smtp_username,
        password=row.smtp_password,
        use_tls=row.smtp_use_tls,
        from_address=row.from_address,
    )


async def _user_out(user: User, db: AsyncSession) -> "UserOut":
    client = (
        await db.execute(
            select(Client).where(
                Client.user_id == user.id,
                Client.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    return UserOut(
        id=str(user.id),
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        client_name=f"{client.first_name} {client.last_name}" if client else None,
    )


async def _create_reset_token(user_id: uuid.UUID, db: AsyncSession) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user_id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRES_HOURS),
    ))
    return raw


# ── Users ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    client_name: str | None


@router.get("/users", response_model=list[UserOut])
async def list_users(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserOut]:
    users = (
        await db.execute(
            select(User)
            .where(User.tenant_id == current_user.tenant_id)
            .order_by(User.role, User.email)
        )
    ).scalars().all()
    return [await _user_out(u, db) for u in users]


class UserCreate(BaseModel):
    email: EmailStr
    role: str
    send_welcome: bool = True


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    if role not in ALLOWED_MANAGED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = (
        await db.execute(
            select(User).where(
                User.tenant_id == current_user.tenant_id,
                User.email == body.email,
            )
        )
    ).scalar_one_or_none()

    if existing is not None and existing.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    smtp_cfg = None
    if body.send_welcome:
        smtp_cfg = await _get_smtp_config(current_user.tenant_id, db)

    if existing is not None:
        existing.is_active = True
        existing.role = role
        user = existing
    else:
        user = User(
            tenant_id=current_user.tenant_id,
            email=body.email,
            password_hash=hash_password(secrets.token_hex(32)),
            role=role,
            is_active=True,
        )
        db.add(user)
    await db.flush()

    reset_link = None
    if body.send_welcome and smtp_cfg:
        raw = await _create_reset_token(user.id, db)
        reset_link = f"{settings.frontend_url}/reset-password?token={raw}"

    await db.commit()
    await db.refresh(user)

    if reset_link and smtp_cfg:
        await send_welcome_email(smtp_cfg, user.email, reset_link)

    return await _user_out(user, db)


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    user = (
        await db.execute(
            select(User).where(
                User.id == uuid.UUID(user_id),
                User.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        try:
            role = UserRole(body.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
        if role not in ALLOWED_MANAGED_ROLES:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = role

    if body.is_active is not None:
        if not body.is_active and user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return await _user_out(user, db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user = (
        await db.execute(
            select(User).where(
                User.id == uuid.UUID(user_id),
                User.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    await db.commit()


@router.post("/users/{user_id}/send-welcome", status_code=status.HTTP_204_NO_CONTENT)
async def resend_welcome(
    user_id: str,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    smtp_cfg = await _get_smtp_config(current_user.tenant_id, db)
    user = (
        await db.execute(
            select(User).where(
                User.id == uuid.UUID(user_id),
                User.tenant_id == current_user.tenant_id,
            )
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    raw = await _create_reset_token(user.id, db)
    await db.commit()
    reset_link = f"{settings.frontend_url}/reset-password?token={raw}"
    await send_welcome_email(smtp_cfg, user.email, reset_link)


# ── Email config ──────────────────────────────────────────────────────────────

class EmailConfigOut(BaseModel):
    is_configured: bool
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password_set: bool
    smtp_use_tls: bool
    from_address: str


class EmailConfigSave(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    from_address: str


def _email_config_out(row: TenantEmailConfig) -> EmailConfigOut:
    return EmailConfigOut(
        is_configured=True,
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_username=row.smtp_username,
        smtp_password_set=bool(row.smtp_password),
        smtp_use_tls=row.smtp_use_tls,
        from_address=row.from_address,
    )


_EMPTY_EMAIL_CONFIG = EmailConfigOut(
    is_configured=False,
    smtp_host="",
    smtp_port=587,
    smtp_username="",
    smtp_password_set=False,
    smtp_use_tls=True,
    from_address="",
)


@router.get("/email-config", response_model=EmailConfigOut)
async def get_email_config(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EmailConfigOut:
    row = (
        await db.execute(
            select(TenantEmailConfig).where(TenantEmailConfig.tenant_id == current_user.tenant_id)
        )
    ).scalar_one_or_none()
    return _email_config_out(row) if row else _EMPTY_EMAIL_CONFIG


@router.put("/email-config", response_model=EmailConfigOut)
async def save_email_config(
    body: EmailConfigSave,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EmailConfigOut:
    row = (
        await db.execute(
            select(TenantEmailConfig).where(TenantEmailConfig.tenant_id == current_user.tenant_id)
        )
    ).scalar_one_or_none()

    if row is None:
        if not body.smtp_password:
            raise HTTPException(status_code=400, detail="Password is required for initial setup")
        row = TenantEmailConfig(
            tenant_id=current_user.tenant_id,
            smtp_host=body.smtp_host.strip(),
            smtp_port=body.smtp_port,
            smtp_username=body.smtp_username.strip(),
            smtp_password=body.smtp_password,
            smtp_use_tls=body.smtp_use_tls,
            from_address=body.from_address.strip(),
        )
        db.add(row)
    else:
        row.smtp_host = body.smtp_host.strip()
        row.smtp_port = body.smtp_port
        row.smtp_username = body.smtp_username.strip()
        if body.smtp_password:
            row.smtp_password = body.smtp_password
        row.smtp_use_tls = body.smtp_use_tls
        row.from_address = body.from_address.strip()

    await db.commit()
    await db.refresh(row)
    return _email_config_out(row)


class TestEmailBody(BaseModel):
    to: EmailStr


@router.post("/email-config/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_email_config(
    body: TestEmailBody,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    smtp_cfg = await _get_smtp_config(current_user.tenant_id, db)
    html = """
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;">
      <h2 style="margin-top:0;">Test email</h2>
      <p>Your SMTP configuration is working correctly.</p>
    </div>"""
    try:
        await send_email(smtp_cfg, body.to, "Salon Lyol — SMTP test", html)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
