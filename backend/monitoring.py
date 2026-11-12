import os
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.db import AuditEvent, ResearchRun, User, engine, get_db

router = APIRouter()
started_at = time.monotonic()
redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)


def require_console_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    user = db.get(User, int(user_id)) if user_id else None
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.must_change_password:
        raise HTTPException(status_code=403, detail="password_change_required")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


@router.get("/api/admin/monitoring")
def monitoring_summary(db: Session = Depends(get_db), admin: User = Depends(require_console_admin)):
    try:
        db.execute(text("SELECT 1"))
        database = {"status": "healthy", "dialect": engine.dialect.name}
    except Exception as exc:
        database = {"status": "unavailable", "detail": str(exc)[:200]}

    try:
        redis_client.ping()
        redis = {"status": "healthy"}
    except RedisError as exc:
        redis = {"status": "unavailable", "detail": str(exc)[:200]}

    return {
        "uptime_seconds": int(time.monotonic() - started_at),
        "api": "healthy",
        "postgresql": database,
        "redis": redis,
        "users": db.query(func.count(User.id)).scalar() or 0,
        "research_runs": db.query(func.count(ResearchRun.id)).scalar() or 0,
        "running_runs": db.query(func.count(ResearchRun.id)).filter(ResearchRun.status == "running").scalar() or 0,
        "failed_runs": db.query(func.count(ResearchRun.id)).filter(ResearchRun.status == "failed").scalar() or 0,
        "audit_events": db.query(func.count(AuditEvent.id)).scalar() or 0,
        "metrics_path": "/metrics",
    }
