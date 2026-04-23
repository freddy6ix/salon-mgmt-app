import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.deps import CurrentUser
from app.models.client import Client
from app.models.tenant import Tenant
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str

    model_config = {"from_attributes": True}


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        tenant_id=str(user.tenant_id),
    )
    return TokenResponse(access_token=token)


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    tenant = (
        await db.execute(
            select(Tenant).where(
                Tenant.slug == settings.default_tenant_slug,
                Tenant.is_active == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Registration unavailable")

    existing = (
        await db.execute(
            select(User).where(User.tenant_id == tenant.id, User.email == body.email)
        )
    ).scalar_one_or_none()

    if existing is not None and existing.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if existing is not None and not existing.is_active:
        # Reactivate the previously deactivated account with fresh credentials
        existing.is_active = True
        existing.password_hash = hash_password(body.password)
        user = existing
    else:
        user = User(
            tenant_id=tenant.id,
            email=body.email,
            password_hash=hash_password(body.password),
            role=UserRole.guest,
        )
        db.add(user)
    await db.flush()

    client_code = f"G{random.randint(10000, 99999)}"
    client = Client(
        tenant_id=tenant.id,
        user_id=user.id,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        cell_phone=body.phone,
        client_code=client_code,
    )
    db.add(client)
    await db.commit()

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        tenant_id=str(user.tenant_id),
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def me(current_user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role.value,
        tenant_id=str(current_user.tenant_id),
    )
