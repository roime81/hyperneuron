import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from backend.graph import build_hyperneuron_graph

app = FastAPI(title="Hyperneuron AI Deep Lab MVP")
graph = build_hyperneuron_graph()

class ResearchRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_path = Path(__file__).parent.parent / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")

@app.post("/api/research/stream")
async def stream_research(req: ResearchRequest):
    async def event_generator():
        initial_state = {"user_prompt": req.prompt, "plan": None, "specialist_reports": [], "iteration": 0, "final_report": None}
        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                payload = json.dumps({"node": node_name, "data": node_output}, default=str)
                yield f"data: {payload}\n\n"
        yield 'data: {"node": "DONE"}\n\n'
    return StreamingResponse(event_generator(), media_type="text/event-stream")
