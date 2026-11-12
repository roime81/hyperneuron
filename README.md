# Hyperneuron AI Platform (Multi-Plane Sovereign AI Architecture)

Hyperneuron AI separates public generative user experiences from administrative orchestration, database management, AI governance, and security monitoring across **isolated network ports and dedicated UIs**, backed by **PostgreSQL (`pgvector`)** and **Redis**.

---

## Multi-Plane Port & UI Architecture

| Plane | Port & Endpoint | Purpose & Access Control |
| :--- | :--- | :--- |
| **User End Generative UI** | `http://localhost:8000/` | Clean, distraction-free generative workspace focused purely on prompting and synthesized results. Supports Guest, **Google SSO**, and Admin sessions. |
| **Orchestrator UI** | `http://localhost:8001/orchestrator` | LangGraph supervisor telemetry, fan-out/fan-in latencies, and trace logs *(Admin Protected)*. |
| **Agentic AI UI** | `http://localhost:8001/agents` | Specialist open-weight LLM fleet (`DeepSeek-V4.1`, `Gemma 4`, `Llama 4 Scout`, `Qwen 3.6`) & tool bindings *(Admin Protected)*. |
| **AI Database UI** | `http://localhost:8001/db` | Live health, storage metrics, and table counts for **PostgreSQL 16 (`pgvector`)** and **Redis 7.4** *(Admin Protected)*. |
| **Governance UI** | `http://localhost:8001/governance` | Live enforcement toggles for Citation Provenance, Data Sovereignty, and PII Redaction *(Admin Protected)*. |
| **Security & Monitoring UI** | `http://localhost:8002/security` | Isolated security operations plane tracking Google OAuth2 SSO logins, admin access, and audit logs *(Admin Protected)*. |

---

## Authentication & Single Sign-On (SSO)

* **Default Admin Account:** `admin` / `admin` (configurable via `ADMIN_DEFAULT_USER` and `ADMIN_DEFAULT_PASS` in `.env`).
* **Google OAuth 2.0 SSO:** Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` with redirect URI `http://localhost:8000/auth/google/callback`.

---

## Quick Start

### Option A: Run with Docker Compose (Recommended — Starts PostgreSQL + pgvector, Redis & All 3 Ports)
```bash
cp .env.example .env
docker compose up --build
```

### Option B: Run Locally with Python
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run_platform.py
```
*(Note: If PostgreSQL or Redis are not running locally on ports `5432`/`6379`, Hyperneuron automatically falls back to local SQLite + in-memory cache so you can test immediately.)*
