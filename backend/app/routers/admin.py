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
from app.email import send_welcome_email
from app.models.client import Client
from app.models.user import PasswordResetToken, User, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])

RESET_TOKEN_EXPIRES_HOURS = 72

ALLOWED_MANAGED_ROLES = {UserRole.tenant_admin, UserRole.staff}


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    client_name: str | None


async def _user_out(user: User, db: AsyncSession) -> UserOut:
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
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    db.add(PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRES_HOURS),
    ))
    return raw


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
    if body.send_welcome:
        if not settings.resend_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service not configured — set RESEND_API_KEY",
            )
        raw = await _create_reset_token(user.id, db)
        reset_link = f"{settings.frontend_url}/reset-password?token={raw}"

    await db.commit()
    await db.refresh(user)

    if reset_link:
        await send_welcome_email(user.email, reset_link)

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
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured — set RESEND_API_KEY",
        )
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
    await send_welcome_email(user.email, reset_link)
