import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

SECTION = os.getenv("CONSOLE_SECTION", "user").strip().lower()
VALID_SECTIONS = {"user", "orchestrator", "agents", "database", "security", "governance"}
if SECTION not in VALID_SECTIONS:
    raise RuntimeError("CONSOLE_SECTION must be one of: " + ", ".join(sorted(VALID_SECTIONS)))

app = FastAPI(title="Hyperneuron " + SECTION.title() + " UI")


@app.get("/", response_class=HTMLResponse)
def index():
    root = Path(__file__).resolve().parent.parent
    filename = "index.html" if SECTION == "user" else "console.html"
    html = (root / "frontend" / filename).read_text(encoding="utf-8")
    return html.replace("{{SECTION}}", SECTION)
