import json
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy import select, desc
from backend.core.config import settings
from backend.core.database import (
    init_databases,
    AsyncSessionLocal,
    Conversation,
    MessageRecord,
    redis_manager,
)
from backend.core.auth import create_auth_router, get_current_user_optional
from backend.agents.workflow import hyperneuron_graph

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

app = FastAPI(title="Hyperneuron Public Generative UI (:8000)")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.include_router(create_auth_router("PUBLIC:8000"))

@app.on_event("startup")
async def on_startup():
    await init_databases()

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def public_home():
    return (FRONTEND_DIR / "public_ui.html").read_text(encoding="utf-8")

@app.get("/login", response_class=HTMLResponse)
async def public_login_page():
    return (FRONTEND_DIR / "shared" / "login.html").read_text(encoding="utf-8")

@app.get("/api/conversations")
async def list_conversations(request: Request):
    user = get_current_user_optional(request)
    user_id = user.get("sub") if user else "guest"
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(20)
        )
        rows = res.scalars().all()
        return [{"id": r.id, "title": r.title, "domain": r.domain} for r in rows]

@app.get("/api/conversations/{conv_id}")
async def get_conversation_messages(conv_id: str):
    cached = await redis_manager.get_json(f"conv:{conv_id}")
    if cached:
        return cached
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(MessageRecord)
            .where(MessageRecord.conversation_id == conv_id)
            .order_by(MessageRecord.id)
        )
        msgs = [{"role": m.role, "content": m.content} for m in res.scalars().all()]
        await redis_manager.set_json(f"conv:{conv_id}", msgs, ttl=600)
        return msgs

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    user = get_current_user_optional(request)
    user_id = user.get("sub") if user else "guest"
    conv_id = req.conversation_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())[:12]

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = res.scalar_one_or_none()
        if not conv:
            conv = Conversation(id=conv_id, user_id=user_id, title=req.prompt[:60])
            session.add(conv)
        session.add(MessageRecord(conversation_id=conv_id, role="user", content=req.prompt))
        await session.commit()

    async def generator():
        state = {
            "trace_id": trace_id,
            "conversation_id": conv_id,
            "user_prompt": req.prompt,
            "plan": None,
            "specialist_reports": [],
            "final_report": None,
        }
        final_text = ""
        async for event in hyperneuron_graph.astream(state, stream_mode="updates"):
            for node_name, output in event.items():
                payload = {"node": node_name, "conversation_id": conv_id}
                if node_name == "orchestrator_synthesize":
                    final_text = output.get("final_report", "")
                    payload["final_report"] = final_text
                yield f"data: {json.dumps(payload)}\n\n"

        if final_text:
            async with AsyncSessionLocal() as session:
                session.add(MessageRecord(conversation_id=conv_id, role="assistant", content=final_text))
                await session.commit()
            # Invalidate Redis conversation cache so next read fetches fresh history
            await redis_manager.set_json(f"conv:{conv_id}", [], ttl=1)

        yield f"data: {json.dumps({'node': 'DONE', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
