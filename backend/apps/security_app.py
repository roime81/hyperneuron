from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select, desc
from backend.core.config import settings
from backend.core.database import (
    init_databases,
    AsyncSessionLocal,
    UserAccount,
    SecurityAuditLog,
)
from backend.core.auth import create_auth_router, get_current_user_optional, require_admin_user

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Hyperneuron Security & Monitoring Console (:8002)")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.include_router(create_auth_router("SECURITY:8002"))

@app.on_event("startup")
async def on_startup():
    await init_databases()

@app.get("/login", response_class=HTMLResponse)
async def security_login():
    return (FRONTEND_DIR / "shared" / "login.html").read_text(encoding="utf-8")

@app.get("/")
async def security_root():
    return RedirectResponse(url="/security", status_code=303)

@app.get("/security")
async def security_ui(request: Request):
    user = get_current_user_optional(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login?next=/security", status_code=303)
    html = (FRONTEND_DIR / "control_plane.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__ACTIVE_VIEW__", "security"))

@app.get("/api/security/telemetry")
async def security_telemetry(_: dict = Depends(require_admin_user)):
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(UserAccount))).scalars().all()
        logs = (await session.execute(
            select(SecurityAuditLog).order_by(desc(SecurityAuditLog.id)).limit(30)
        )).scalars().all()

    return {
        "users": [
            {"username": u.username, "email": u.email, "role": u.role, "provider": u.auth_provider}
            for u in users
        ],
        "logs": [
            {
                "actor": l.actor,
                "action": l.action,
                "port_plane": l.port_plane,
                "status": l.status,
                "ip_address": l.ip_address,
                "details": l.details,
            }
            for l in logs
        ],
    }
