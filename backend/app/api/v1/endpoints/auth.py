import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    return ApiResponse(data=UserResponse.model_validate(user), message="Registration successful")


@router.post("/login", response_model=ApiResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id))

    # Store refresh token hash for revocation support
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    await db.flush()

    return ApiResponse(data=TokenResponse(access_token=access, refresh_token=refresh))


@router.post("/refresh", response_model=ApiResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_hash = _hash_refresh(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    stored = result.scalar_one_or_none()
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or not found")

    # Revoke old token
    stored.revoked = True
    await db.flush()

    # Load user for role
    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()

    # Issue new pair
    new_access = create_access_token(str(user.id), user.role.value)
    new_refresh = create_refresh_token(str(user.id))

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(new_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_rt)
    await db.flush()

    return ApiResponse(data=TokenResponse(access_token=new_access, refresh_token=new_refresh))


@router.post("/logout", response_model=ApiResponse)
async def logout(
    body: RefreshRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token_hash = _hash_refresh(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        await db.flush()

    return ApiResponse(message="Logged out")


@router.get("/me", response_model=ApiResponse)
async def me(user: User = Depends(get_current_user)):
    return ApiResponse(data=UserResponse.model_validate(user))
