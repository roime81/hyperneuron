from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from backend.core.config import settings
from backend.core.database import (
    init_databases,
    AsyncSessionLocal,
    UserAccount,
    Conversation,
    MessageRecord,
    AgentExecutionLog,
    GovernancePolicy,
    SecurityAuditLog,
    redis_manager,
)
from backend.core.auth import create_auth_router, get_current_user_optional, require_admin_user

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Hyperneuron Backend Control Plane (:8001)")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.include_router(create_auth_router("BACKEND:8001"))

@app.on_event("startup")
async def on_startup():
    await init_databases()

def _render_control_view(request: Request, view_name: str):
    user = get_current_user_optional(request)
    if not user or user.get("role") != "admin":
        return RedirectResponse(url=f"/login?next=/{view_name}", status_code=303)
    html = (FRONTEND_DIR / "control_plane.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__ACTIVE_VIEW__", view_name))

@app.get("/login", response_class=HTMLResponse)
async def backend_login():
    return (FRONTEND_DIR / "shared" / "login.html").read_text(encoding="utf-8")

@app.get("/")
async def backend_root():
    return RedirectResponse(url="/orchestrator", status_code=303)

@app.get("/orchestrator")
async def orchestrator_ui(request: Request):
    return _render_control_view(request, "orchestrator")

@app.get("/agents")
async def agentic_ai_ui(request: Request):
    return _render_control_view(request, "agents")

@app.get("/db")
async def database_ui(request: Request):
    return _render_control_view(request, "db")

@app.get("/governance")
async def governance_ui(request: Request):
    return _render_control_view(request, "governance")

@app.get("/api/admin/overview")
async def admin_overview(_: dict = Depends(require_admin_user)):
    async with AsyncSessionLocal() as session:
        conv_count = (await session.execute(select(func.count(Conversation.id)))).scalar() or 0
        exec_count = (await session.execute(select(func.count(AgentExecutionLog.id)))).scalar() or 0
        recent = (await session.execute(
            select(AgentExecutionLog).order_by(desc(AgentExecutionLog.id)).limit(15)
        )).scalars().all()

    return {
        "models": {
            "orchestrator": settings.ORCHESTRATOR_MODEL,
            "thinking": settings.THINKING_MODEL,
            "citation": settings.CITATION_MODEL,
            "quant": settings.QUANT_MODEL,
        },
        "counts": {"conversations": conv_count, "executions": exec_count},
        "recent_executions": [
            {
                "trace_id": r.trace_id,
                "agent_name": r.agent_name,
                "model_used": r.model_used,
                "latency_ms": r.latency_ms,
                "confidence": r.confidence,
                "status": r.status,
            }
            for r in recent
        ],
    }

@app.get("/api/admin/db-status")
async def db_status(_: dict = Depends(require_admin_user)):
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(func.count(UserAccount.id)))).scalar() or 0
        convs = (await session.execute(select(func.count(Conversation.id)))).scalar() or 0
        msgs = (await session.execute(select(func.count(MessageRecord.id)))).scalar() or 0
        audits = (await session.execute(select(func.count(SecurityAuditLog.id)))).scalar() or 0
        dialect = session.bind.dialect.name if session.bind else "postgresql"

    redis_stats = await redis_manager.get_stats()
    return {
        "postgres": {
            "status": "ONLINE",
            "dialect": f"{dialect.upper()} (pgvector ready)",
            "users": users,
            "conversations": convs,
            "messages": msgs,
            "audit_logs": audits,
        },
        "redis": redis_stats,
    }

@app.get("/api/admin/governance")
async def get_policies(_: dict = Depends(require_admin_user)):
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(GovernancePolicy).order_by(GovernancePolicy.id))).scalars().all()
        return [
            {
                "id": p.id,
                "policy_name": p.policy_name,
                "category": p.category,
                "enforcement_mode": p.enforcement_mode,
                "description": p.description,
            }
            for p in rows
        ]

class PolicyUpdate(BaseModel):
    enforcement_mode: str

@app.post("/api/admin/governance/{policy_id}")
async def update_policy(policy_id: int, body: PolicyUpdate, admin: dict = Depends(require_admin_user)):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(GovernancePolicy).where(GovernancePolicy.id == policy_id))
        pol = res.scalar_one_or_none()
        if pol:
            pol.enforcement_mode = body.enforcement_mode
            pol.updated_by = admin.get("sub", "admin")
            await session.commit()
    return {"status": "updated"}
