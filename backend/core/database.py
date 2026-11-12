import json
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, text, select, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import redis.asyncio as aioredis
from backend.core.config import settings

Base = declarative_base()

class UserAccount(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="user")  # admin, operator, user
    auth_provider = Column(String(50), default="local")  # local, google
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(120), index=True)
    title = Column(String(255), nullable=False)
    domain = Column(String(100), default="General")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MessageRecord(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), index=True, nullable=False)
    role = Column(String(32), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    agent_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AgentExecutionLog(Base):
    __tablename__ = "agent_executions"
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), index=True)
    conversation_id = Column(String(64), index=True)
    agent_name = Column(String(100))
    model_used = Column(String(100))
    status = Column(String(50))
    latency_ms = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    summary = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String(120), unique=True)
    category = Column(String(80))  # PII, Hallucination, Citation, Data Sovereignty
    enforcement_mode = Column(String(40), default="ENFORCE")  # ENFORCE, AUDIT, DISABLED
    description = Column(Text)
    updated_by = Column(String(120), default="admin")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(120))
    action = Column(String(120))
    port_plane = Column(String(50))  # PUBLIC:8000, BACKEND:8001, SECURITY:8002
    status = Column(String(40))  # ALLOW, BLOCK, WARN
    ip_address = Column(String(64), default="127.0.0.1")
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Engine initialization with graceful fallback if local Postgres isn't running yet
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class RedisCacheManager:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
        self.memory_fallback: Dict[str, Any] = {}
        self.connected: bool = False

    async def connect(self):
        try:
            self.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.client.ping()
            self.connected = True
        except Exception:
            self.connected = False

    async def set_json(self, key: str, value: Any, ttl: int = 3600):
        payload = json.dumps(value, default=str)
        if self.connected and self.client:
            await self.client.setex(key, ttl, payload)
        else:
            self.memory_fallback[key] = payload

    async def get_json(self, key: str) -> Optional[Any]:
        if self.connected and self.client:
            val = await self.client.get(key)
        else:
            val = self.memory_fallback.get(key)
        return json.loads(val) if val else None

    async def publish_event(self, channel: str, event: dict):
        if self.connected and self.client:
            await self.client.publish(channel, json.dumps(event, default=str))

    async def get_stats(self) -> dict:
        if self.connected and self.client:
            info = await self.client.info()
            return {
                "backend": "Redis 7.4 (Connected)",
                "status": "ONLINE",
                "used_memory_human": info.get("used_memory_human", "1.2M"),
                "connected_clients": info.get("connected_clients", 1),
                "total_commands": info.get("total_commands_processed", 0),
                "keys_count": await self.client.dbsize(),
            }
        return {
            "backend": "In-Memory Cache Fallback (Start Redis on :6379 for distributed mode)",
            "status": "FALLBACK",
            "used_memory_human": f"{len(str(self.memory_fallback))} B",
            "connected_clients": 1,
            "total_commands": len(self.memory_fallback),
            "keys_count": len(self.memory_fallback),
        }

redis_manager = RedisCacheManager()

async def init_databases():
    global engine, AsyncSessionLocal
    await redis_manager.connect()
    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:
                pass
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        # Fallback to local SQLite async if PostgreSQL container is not yet started
        fallback_url = "sqlite+aiosqlite:///./hyperneuron_local.db"
        engine = create_async_engine(fallback_url, echo=False, future=True)
        AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Seed default admin user and default governance policies
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(UserAccount).where(UserAccount.username == settings.ADMIN_DEFAULT_USER))
        if not res.scalar_one_or_none():
            session.add(UserAccount(
                username=settings.ADMIN_DEFAULT_USER,
                email="admin@hyperneuron.io",
                full_name="Platform Administrator",
                role="admin",
                auth_provider="local",
                password_hash=settings.ADMIN_DEFAULT_PASS,
            ))

        pol_res = await session.execute(select(GovernancePolicy))
        if not pol_res.scalars().first():
            session.add_all([
                GovernancePolicy(
                    policy_name="Strict Source Provenance",
                    category="Citation & Hallucination",
                    enforcement_mode="ENFORCE",
                    description="All Deep Citation Researcher claims must bind to verifiable URLs or VDR chunks."
                ),
                GovernancePolicy(
                    policy_name="Sovereign Private Inference Boundary",
                    category="Data Sovereignty",
                    enforcement_mode="ENFORCE",
                    description="Block external third-party LLM telemetry; route strictly to configured private endpoints."
                ),
                GovernancePolicy(
                    policy_name="PII & Financial Redaction Guard",
                    category="PII Protection",
                    enforcement_mode="AUDIT",
                    description="Scan incoming prompts and log sensitive entity patterns to Security Plane (:8002)."
                ),
            ])
        await session.commit()
