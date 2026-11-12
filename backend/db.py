import os
from datetime import datetime, timezone

from pwdlib import PasswordHash
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hyperneuron.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
password_hasher = PasswordHash.recommended()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), default="local")
    role: Mapped[str] = mapped_column(String(32), default="user")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    final_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    source_ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(120), default="Platform Admin")
    status: Mapped[str] = mapped_column(String(32), default="active")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
        password = os.getenv("ADMIN_PASSWORD", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@hyperneuron.local").strip().lower()
        admin = db.query(User).filter(User.username == username).first()
        if admin is None:
            db.add(User(
                username=username,
                email=email,
                full_name="Hyperneuron Administrator",
                password_hash=password_hasher.hash(password),
                provider="local",
                role="admin",
                active=True,
                must_change_password=True,
            ))

        starter_policies = [
            ("data-retention", "Data retention", "Research prompts, results and audit events must follow an approved retention schedule."),
            ("model-approval", "Model approval", "Only approved model endpoints and model versions may be used by production agents."),
            ("human-oversight", "Human oversight", "High-impact outputs and external actions require an accountable human review."),
            ("access-review", "Access review", "Administrative access and role assignments must be reviewed periodically."),
        ]
        for key, title, description in starter_policies:
            if db.query(GovernancePolicy).filter(GovernancePolicy.key == key).first() is None:
                db.add(GovernancePolicy(key=key, title=title, description=description))
        db.commit()
