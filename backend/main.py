import json
import logging
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from backend.config import BASE_URL
from backend.db import (
    AuditEvent, GovernancePolicy, ResearchRun, SessionLocal, User,
    engine, get_db, init_db, password_hasher,
)
from backend.graph import build_hyperneuron_graph

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("hyperneuron")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SESSION_SECRET = os.getenv("SESSION_SECRET", "local-development-change-this-secret")
if ENVIRONMENT == "production" and SESSION_SECRET == "local-development-change-this-secret":
    raise RuntimeError("SESSION_SECRET must be changed before production deployment.")
if ENVIRONMENT == "production" and os.getenv("ADMIN_PASSWORD", "admin") == "admin":
    raise RuntimeError("Set a unique ADMIN_PASSWORD before production deployment.")

UI_ORIGINS = [
    item.strip().rstrip("/")
    for item in os.getenv(
        "UI_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://localhost:3005",
    ).split(",") if item.strip()
]
COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
oauth = OAuth()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

REQUESTS = Counter("hyperneuron_http_requests_total", "HTTP requests", ["method", "path", "status"])
graph = build_hyperneuron_graph()
app = FastAPI(title="Hyperneuron Platform API", version="0.2.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="hyperneuron_session",
    same_site="lax",
    https_only=COOKIE_SECURE,
    max_age=60 * 60 * 12,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=UI_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=512)


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=512)


class ResearchRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=20000)


def audit(db: Session, action: str, actor_id: int | None = None, details: str = "", request: Request | None = None) -> None:
    client_ip = request.client.host if request and request.client else ""
    db.add(AuditEvent(actor_id=actor_id, action=action, details=details[:4000], source_ip=client_ip))
    db.commit()


def public_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "provider": user.provider,
        "must_change_password": user.must_change_password,
    }


def get_session_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.get(User, int(user_id))
    if user is None or not user.active:
        request.session.clear()
        return None
    return user


def require_user(user: User | None = Depends(get_session_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.must_change_password:
        raise HTTPException(status_code=403, detail="password_change_required")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def allowed_redirect(candidate: str | None) -> str:
    fallback = UI_ORIGINS[0] if UI_ORIGINS else "http://localhost:3000"
    if not candidate:
        return fallback
    parsed = urlsplit(candidate)
    origin = (parsed.scheme + "://" + parsed.netloc).rstrip("/")
    return candidate if parsed.scheme in {"http", "https"} and origin in UI_ORIGINS else fallback


def redis_login_guard(request: Request) -> tuple[str, int]:
    ip = request.client.host if request.client else "unknown"
    key = "hyperneuron:login-fail:" + ip
    try:
        return key, int(redis_client.get(key) or "0")
    except RedisError:
        return key, 0


@app.on_event("startup")
def startup() -> None:
    init_db()
    try:
        redis_client.ping()
        logger.info("Redis connection ready")
    except RedisError:
        logger.warning("Redis is unavailable; API remains online without cache features")


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if path not in {"/metrics", "/health"}:
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    logger.info("%s %s %s %.3fs", request.method, path, response.status_code, time.perf_counter() - started)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "hyperneuron-api"}


@app.get("/")
def root():
    return {"service": "Hyperneuron Platform API", "docs": "/docs", "health": "/health", "user_ui": "http://localhost:3000"}


@app.get("/api/auth/me")
def auth_me(user: User | None = Depends(get_session_user)):
    if user is None:
        return {"authenticated": False}
    return {"authenticated": True, "user": public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    key, attempts = redis_login_guard(request)
    if attempts >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    user = db.query(User).filter((User.username == payload.username) | (User.email == payload.username.lower())).first()
    valid = user is not None and user.active and user.password_hash is not None
    if valid:
        try:
            valid = password_hasher.verify(payload.password, user.password_hash)
        except Exception:
            valid = False
    if not valid:
        try:
            redis_client.incr(key)
            redis_client.expire(key, 900)
        except RedisError:
            pass
        audit(db, "auth.login.failed", details="Invalid local login", request=request)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        redis_client.delete(key)
    except RedisError:
        pass
    request.session.clear()
    request.session["user_id"] = user.id
    audit(db, "auth.login.success", actor_id=user.id, details="Local login", request=request)
    return {"authenticated": True, "user": public_user(user)}


@app.get("/auth/google/login")
async def google_login(request: Request, next: str | None = None):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google SSO is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    request.session["oauth_next"] = allowed_redirect(next)
    return await oauth.create_client("google").authorize_redirect(request, GOOGLE_REDIRECT_URI)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google SSO is not configured")
    client = oauth.create_client("google")
    try:
        token = await client.authorize_access_token(request)
        info = token.get("userinfo") or await client.userinfo(token=token)
        email = str(info.get("email", "")).strip().lower()
        if not email or not info.get("email_verified", False):
            raise HTTPException(status_code=403, detail="A verified Google email address is required")
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                base_username = email.split("@", 1)[0][:100] or "google-user"
                username = base_username
                suffix = 1
                while db.query(User).filter(User.username == username).first() is not None:
                    suffix += 1
                    username = base_username[:90] + str(suffix)
                user = User(
                    username=username, email=email, full_name=str(info.get("name", ""))[:255],
                    provider="google", role="user", active=True, must_change_password=False,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            if not user.active:
                raise HTTPException(status_code=403, detail="This account is disabled")
            destination = allowed_redirect(request.session.get("oauth_next"))
            request.session.clear()
            request.session["user_id"] = user.id
            audit(db, "auth.login.success", actor_id=user.id, details="Google SSO", request=request)
        finally:
            db.close()
        return RedirectResponse(destination, status_code=302)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Google OAuth callback failed")
        raise HTTPException(status_code=401, detail="Google sign-in failed") from exc


@app.post("/api/auth/change-password")
def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    user: User | None = Depends(get_session_user),
    db: Session = Depends(get_db),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    user.password_hash = password_hasher.hash(payload.new_password)
    user.must_change_password = False
    db.add(user)
    audit(db, "auth.password.changed", actor_id=user.id, request=request)
    return {"changed": True}


@app.post("/api/auth/logout")
def logout(request: Request, user: User | None = Depends(get_session_user), db: Session = Depends(get_db)):
    if user is not None:
        audit(db, "auth.logout", actor_id=user.id, request=request)
    request.session.clear()
    return {"logged_out": True}


@app.post("/api/research/stream")
async def stream_research(
    req: ResearchRequest,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    prompt = req.prompt.strip()
    run = ResearchRun(user_id=user.id, prompt=prompt, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id
    audit(db, "research.started", actor_id=user.id, details="run_id=" + str(run_id), request=request)

    async def event_generator():
        final_report = None
        initial_state = {
            "user_prompt": prompt, "plan": None, "specialist_reports": [],
            "iteration": 0, "final_report": None,
        }
        try:
            async for event in graph.astream(initial_state, stream_mode="updates"):
                if await request.is_disconnected():
                    break
                for node_name, node_output in event.items():
                    if node_name == "orchestrator_synthesize":
                        final_report = node_output.get("final_report")
                    payload = json.dumps({"node": node_name, "data": node_output}, default=str, ensure_ascii=False)
                    yield "data: " + payload + "\n\n"
            with SessionLocal() as session:
                saved_run = session.get(ResearchRun, run_id)
                if saved_run:
                    saved_run.status = "completed"
                    saved_run.final_report = final_report
                    saved_run.completed_at = datetime.now(timezone.utc)
                    session.add(saved_run)
                    session.commit()
            try:
                redis_client.setex("hyperneuron:run:" + str(run_id), 3600, json.dumps({"status": "completed"}))
            except RedisError:
                pass
            yield 'data: {"node":"DONE"}\n\n'
        except Exception:
            logger.exception("Research run %s failed", run_id)
            with SessionLocal() as session:
                saved_run = session.get(ResearchRun, run_id)
                if saved_run:
                    saved_run.status = "failed"
                    saved_run.error = "Research execution failed; inspect backend logs."
                    saved_run.completed_at = datetime.now(timezone.utc)
                    session.add(saved_run)
                    session.commit()
            yield 'data: {"node":"ERROR","message":"Research execution failed. Check the backend logs."}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/admin/overview")
def admin_overview(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "runs": db.query(func.count(ResearchRun.id)).scalar() or 0,
        "running": db.query(func.count(ResearchRun.id)).filter(ResearchRun.status == "running").scalar() or 0,
        "failed": db.query(func.count(ResearchRun.id)).filter(ResearchRun.status == "failed").scalar() or 0,
        "audit_events": db.query(func.count(AuditEvent.id)).scalar() or 0,
    }


@app.get("/api/admin/orchestrator")
def admin_orchestrator(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    recent = db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(10).all()
    return {
        "orchestrator": "LangGraph supervisor", "llm_base_url": BASE_URL,
        "model": os.getenv("ORCHESTRATOR_MODEL", "deepseek-v4.1-flash"),
        "parallel_workers": 3, "routing": "plan -> parallel specialists -> synthesis",
        "recent_runs": [{"id": r.id, "status": r.status, "prompt": r.prompt[:180], "created_at": r.created_at.isoformat()} for r in recent],
    }


@app.get("/api/admin/agents")
def admin_agents(admin: User = Depends(require_admin)):
    return {"agents": [
        {"name": "Chief Orchestrator", "model": os.getenv("ORCHESTRATOR_MODEL", "deepseek-v4.1-flash"), "role": "Planning, routing and synthesis", "status": "configured"},
        {"name": "Deep Thinking Researcher", "model": os.getenv("THINKING_MODEL", "gemma4:31b"), "role": "First-principles reasoning and risk analysis", "status": "configured"},
        {"name": "Deep Citation Researcher", "model": os.getenv("CITATION_MODEL", "llama4:scout"), "role": "Web research and source provenance", "status": "configured"},
        {"name": "Qualified Quantified Researcher", "model": os.getenv("QUANT_MODEL", "qwen3.6:27b"), "role": "Quantitative analysis and metrics", "status": "configured"},
    ]}


@app.get("/api/admin/db/health")
def admin_db_health(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    try:
        db.execute(text("SELECT 1"))
        postgres = {"status": "healthy", "dialect": engine.dialect.name}
    except Exception as exc:
        postgres = {"status": "unavailable", "error": str(exc)[:300]}
    try:
        redis_client.ping()
        redis = {"status": "healthy", "version": redis_client.info("server").get("redis_version", "unknown")}
    except RedisError as exc:
        redis = {"status": "unavailable", "error": str(exc)[:300]}
    return {"postgresql": postgres, "redis": redis}


@app.get("/api/admin/security/events")
def admin_security_events(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(50).all()
    return {"events": [
        {"id": e.id, "actor_id": e.actor_id, "action": e.action, "details": e.details, "source_ip": e.source_ip, "created_at": e.created_at.isoformat()}
        for e in events
    ]}


@app.get("/api/admin/governance/policies")
def admin_governance(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    policies = db.query(GovernancePolicy).order_by(GovernancePolicy.title.asc()).all()
    return {"policies": [
        {"id": p.id, "key": p.key, "title": p.title, "description": p.description, "owner": p.owner, "status": p.status, "updated_at": p.updated_at.isoformat()}
        for p in policies
    ]}


@app.get("/metrics")
def metrics():
    return StreamingResponse(iter([generate_latest()]), media_type=CONTENT_TYPE_LATEST)
