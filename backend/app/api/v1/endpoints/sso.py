import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.models.user import RefreshToken, Role, User

router = APIRouter(prefix="/auth", tags=["sso"])


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.get("/sso/login")
async def sso_login():
    """Redirect staff to Keycloak login page."""
    state = secrets.token_urlsafe(32)
    auth_url = (
        f"{settings.keycloak_auth_url}"
        f"?client_id={settings.keycloak_client_id}"
        f"&redirect_uri={settings.keycloak_redirect_uri}"
        f"&response_type=code"
        f"&scope=openid+profile+email"
        f"&state={state}"
    )
    response = RedirectResponse(url=auth_url)
    response.set_cookie("sso_state", state, httponly=True, max_age=300, samesite="lax")
    return response


@router.get("/sso/callback")
async def sso_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Keycloak callback: exchange code, create user, issue JWT."""
    # CSRF state check
    cookie_state = request.cookies.get("sso_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SSO state")

    # Exchange authorization code for tokens
    async with httpx.AsyncClient(verify=settings.keycloak_verify_ssl) as client:
        token_resp = await client.post(
            settings.keycloak_token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
                "code": code,
                "redirect_uri": settings.keycloak_redirect_uri,
            },
        )

    if token_resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token exchange failed")

    kc_access_token = token_resp.json().get("access_token")

    # Fetch userinfo from Keycloak
    async with httpx.AsyncClient(verify=settings.keycloak_verify_ssl) as client:
        userinfo_resp = await client.get(
            settings.keycloak_userinfo_url,
            headers={"Authorization": f"Bearer {kc_access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to fetch userinfo")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    full_name = userinfo.get("name") or email

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email returned from Keycloak")

    # All SSO users are staff — assign admin role
    role = Role.ADMIN

    # Find or create user in local DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            hashed_password="!sso",  # SSO users have no local password
            full_name=full_name,
            role=role,
        )
        db.add(user)
    else:
        user.full_name = full_name
        user.role = role

    await db.flush()

    # Issue local JWT tokens
    access = create_access_token(str(user.id), user.role.value)
    refresh = create_refresh_token(str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(rt)
    await db.flush()

    # Redirect to frontend SSO callback page with tokens
    redirect_url = (
        f"{settings.frontend_url}/sso-callback"
        f"?access_token={access}"
        f"&refresh_token={refresh}"
    )
    response = RedirectResponse(url=redirect_url)
    response.delete_cookie("sso_state")
    return response
