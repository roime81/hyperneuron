from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Form
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt, JWTError
from sqlalchemy import select
from backend.core.config import settings
from backend.core.database import AsyncSessionLocal, UserAccount, SecurityAuditLog

ALGORITHM = "HS256"
COOKIE_NAME = "hyperneuron_session"

oauth = OAuth()
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

def create_access_token(data: dict, expires_minutes: int = 720) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_optional(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def require_authenticated_user(request: Request) -> dict:
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_admin_user(request: Request) -> dict:
    user = get_current_user_optional(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

async def log_security_event(actor: str, action: str, port_plane: str, status: str, ip: str, details: str):
    async with AsyncSessionLocal() as session:
        session.add(SecurityAuditLog(
            actor=actor,
            action=action,
            port_plane=port_plane,
            status=status,
            ip_address=ip,
            details=details,
        ))
        await session.commit()

def create_auth_router(port_plane: str) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Authentication"])

    @router.post("/login")
    async def local_login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        next_url: str = Form("/"),
    ):
        client_ip = request.client.host if request.client else "127.0.0.1"
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(UserAccount).where(UserAccount.username == username))
            user = res.scalar_one_or_none()

            valid = False
            if user and user.password_hash == password and user.is_active:
                valid = True
            elif username == settings.ADMIN_DEFAULT_USER and password == settings.ADMIN_DEFAULT_PASS:
                valid = True

            if not valid:
                await log_security_event(username, "LOGIN_FAILED", port_plane, "BLOCK", client_ip, "Invalid credentials")
                return RedirectResponse(url=f"/login?error=Invalid+credentials&next={next_url}", status_code=303)

            role = user.role if user else "admin"
            email = user.email if user else "admin@hyperneuron.io"
            full_name = user.full_name if user else "Administrator"

            token = create_access_token({
                "sub": username,
                "email": email,
                "name": full_name,
                "role": role,
                "provider": "local",
            })
            await log_security_event(username, "LOGIN_SUCCESS", port_plane, "ALLOW", client_ip, f"Local login ({role})")

            response = RedirectResponse(url=next_url or "/", status_code=303)
            response.set_cookie(
                key=COOKIE_NAME,
                value=token,
                httponly=True,
                samesite="lax",
                max_age=43200,
            )
            return response

    @router.get("/google")
    async def google_sso_login(request: Request, next_url: str = "/"):
        if "google" not in oauth._clients:
            # Helpful redirect if Google OAuth env keys are not yet populated
            return RedirectResponse(
                url=f"/login?error=Google+SSO+not+configured+in+.env+(Set+GOOGLE_CLIENT_ID)&next={next_url}",
                status_code=303,
            )
        request.session["next_url"] = next_url
        redirect_uri = str(request.url_for("google_sso_callback"))
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @router.get("/google/callback", name="google_sso_callback")
    async def google_sso_callback(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        if "google" not in oauth._clients:
            return RedirectResponse(url="/login?error=Google+SSO+not+configured", status_code=303)

        token_data = await oauth.google.authorize_access_token(request)
        user_info = token_data.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to retrieve Google user profile")

        email = user_info.get("email")
        name = user_info.get("name", email)

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(UserAccount).where(UserAccount.email == email))
            db_user = res.scalar_one_or_none()
            if not db_user:
                db_user = UserAccount(
                    username=email,
                    email=email,
                    full_name=name,
                    role="user",
                    auth_provider="google",
                )
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)

            jwt_token = create_access_token({
                "sub": db_user.username,
                "email": db_user.email,
                "name": db_user.full_name,
                "role": db_user.role,
                "provider": "google",
            })

        await log_security_event(email, "GOOGLE_SSO_LOGIN", port_plane, "ALLOW", client_ip, "Authenticated via Google SSO")
        next_url = request.session.pop("next_url", "/")
        response = RedirectResponse(url=next_url, status_code=303)
        response.set_cookie(key=COOKIE_NAME, value=jwt_token, httponly=True, samesite="lax", max_age=43200)
        return response

    @router.get("/me")
    async def auth_me(request: Request):
        user = get_current_user_optional(request)
        if not user:
            return JSONResponse({"authenticated": False})
        return JSONResponse({"authenticated": True, "user": user})

    @router.get("/logout")
    async def logout(request: Request):
        user = get_current_user_optional(request)
        client_ip = request.client.host if request.client else "127.0.0.1"
        if user:
            await log_security_event(user.get("sub", "unknown"), "LOGOUT", port_plane, "ALLOW", client_ip, "User signed out")
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(COOKIE_NAME)
        return response

    return router
