# 🧠 HYPERNEURON AI PLATFORM
*Sovereign, Multi-Plane Enterprise AI & Deep Research Architecture*

---

## 🏛️ Overview

**Hyperneuron AI** is a private, multi-agent enterprise intelligence platform engineered for **Corporate Intelligence**, **Legal & Financial Due Diligence**, and **Sovereign AI Operations**. 

Built on a **Multi-Plane Port Isolation Architecture**, Hyperneuron separates the distraction-free end-user generative interface from administrative agent orchestration, open-source AI databases (**PostgreSQL 16 + `pgvector`** and **Redis 7.4**), AI governance controls, and dedicated security monitoring.

---

## 🌐 Multi-Plane Network & UI Architecture

Running `python run_platform.py` or `docker compose up --build` launches **three isolated FastAPI planes** across dedicated ports and purpose-built interfaces:

| Plane & UI | Port & URL | Access Control | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **1. User End Generative UI** | `http://localhost:8000/` | Public / Guest / Google SSO / Admin | Clean, distraction-free workspace focused strictly on prompting, starter workflows, conversation history, and synthesized Markdown reports. |
| **2. Orchestrator UI** | `http://localhost:8001/orchestrator` | Admin Only (`:8001`) | Live LangGraph supervisor dashboard tracking fan-out/fan-in topology, execution traces, confidence scores, and node latencies. |
| **3. Agentic AI UI** | `http://localhost:8001/agents` | Admin Only (`:8001`) | Inspect private open-weight LLM bindings (**DeepSeek-V4.1**, **Gemma 4**, **Llama 4 Scout**, **Qwen 3.6**) and bound specialist tools. |
| **4. AI Database UI** | `http://localhost:8001/db` | Admin Only (`:8001`) | Real-time health, storage telemetry, and table counts for **PostgreSQL 16 (`pgvector`)** and **Redis 7.4** cache/pub-sub. |
| **5. Governance UI** | `http://localhost:8001/governance` | Admin Only (`:8001`) | Live policy enforcement toggles (`ENFORCE` / `AUDIT` / `DISABLED`) for Citation Provenance, Data Sovereignty, and PII Redaction. |
| **6. Security & Monitoring UI** | `http://localhost:8002/security` | Admin Only (`:8002`) | Dedicated security plane monitoring Google OAuth 2.0 SSO sessions, local admin logins, client IPs, and immutable audit trails. |

---

## 📐 Multi-Agent Orchestration Topology

Hyperneuron executes research queries using a deterministic **Hub-and-Spoke Fan-Out / Fan-In** state machine in LangGraph:

```
                  ┌────────────────────────────────────────┐
                  │ User Prompt (Public UI — Port :8000)   │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Request Quantification & Planning      │
                  │ (Chief Orchestrator: DeepSeek-V4.1)    │
                  └──────────────────┬─────────────────────┘
                                     │ (Parallel Fan-Out)
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Deep Thinking    │       │ Deep Citation    │       │ Qualified Quant  │
│ Researcher       │       │ Researcher       │       │ Researcher       │
│ (Gemma 4 31B)    │       │ (Llama 4 Scout)  │       │ (Qwen 3.6 27B)   │
└─────────┬────────┘       └─────────┬────────┘       └─────────┬────────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │ (Structured Fan-In)
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Synthesis & Governance Audit           │
                  │ (Chief Orchestrator)                   │
                  └──────────────────┬─────────────────────┘
                                     │ (SSE Stream + PG/Redis Save)
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Executive Markdown Report (:8000 UI)   │
                  └────────────────────────────────────────┘
```

---

## 🔐 Authentication, Google SSO & Default Admin

Hyperneuron supports hybrid enterprise authentication across all planes:

* **Default Local Admin Credentials:**
  * **Username:** `admin`
  * **Password:** `admin`
  * *(Configurable via `ADMIN_DEFAULT_USER` and `ADMIN_DEFAULT_PASS` in `.env`)*
* **Google OAuth 2.0 Single Sign-On (SSO):**
  1. Create OAuth 2.0 credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
  2. Add `http://localhost:8000/auth/google/callback` as an Authorized Redirect URI.
  3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env` file.

---

## 🗄️ Open-Source AI Data Layer

* **PostgreSQL 16 + `pgvector` (`5432`):** Primary relational and vector-ready store persisting user profiles, conversation threads, message history, LangGraph execution logs, governance rules, and security audit trails.
* **Redis 7.4 (`6379`):** High-speed session/conversation cache and real-time pub/sub event bus (`hyperneuron:telemetry`).
* **Zero-Config Local Fallback:** If PostgreSQL or Redis are not running when starting locally without Docker, Hyperneuron automatically falls back to local async SQLite and an in-memory cache so all UIs work immediately.

---

## ⚡ Quick Start Guide

### Option A: Docker Compose (Recommended — Starts PostgreSQL, Redis & All 3 Ports)
```bash
git clone https://github.com/roime81/hyperneuron-ai.git
cd hyperneuron-ai
cp .env.example .env
docker compose up --build
```

### Option B: Local Python Execution
```bash
git clone https://github.com/roime81/hyperneuron-ai.git
cd hyperneuron-ai

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies and configure environment
pip install -r requirements.txt
cp .env.example .env

# Launch all 3 planes (:8000, :8001, :8002)
python run_platform.py
```

---

## 📂 Repository Structure

```text
hyperneuron-ai/
├── docker-compose.yml               # PostgreSQL 16 (pgvector), Redis 7.4 & Multi-Port App
├── Dockerfile                       # Production container exposing ports 8000, 8001, 8002
├── run_platform.py                  # Concurrent Uvicorn multi-plane launcher
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment, SSO, DB & LLM configuration template
├── backend/
│   ├── core/
│   │   ├── config.py                # Centralized settings for ports, DBs, auth & models
│   │   ├── database.py              # Async SQLAlchemy (PG/pgvector) & Redis manager
│   │   └── auth.py                  # JWT cookie sessions, Admin login & Google OAuth2 SSO
│   ├── agents/
│   │   ├── __init__.py              # Python package initialization
│   │   └── workflow.py              # LangGraph fan-out/fan-in multi-agent state machine
│   └── apps/
│       ├── public_app.py            # Port :8000 — End-user generative API & SSE stream
│       ├── backend_admin_app.py     # Port :8001 — Orchestrator, Agents, DB & Governance APIs
│       └── security_app.py          # Port :8002 — Security & monitoring audit APIs
└── frontend/
    ├── public_ui.html               # Clean distraction-free end-user generative UI (:8000)
    ├── control_plane.html           # Unified admin UI for :8001 and :8002 planes
    └── shared/
        └── login.html               # Shared Google SSO & Admin login portal
```

---

## 🛠️ Troubleshooting & Common Workarounds

### 1. Missing `__init__.py` in Python Packages
* **Error:** `ModuleNotFoundError: No module named 'backend.agents.workflow'; 'backend.agents' is not a package`
* **Workaround:** Ensure all module directories (`backend/agents/`, `backend/core/`, `backend/apps/`) contain an empty `__init__.py` file so Python recognizes them as valid packages:
  ```bash
  touch backend/agents/__init__.py
  ```

### 2. Database Hostname Resolution Failure (`postgres`)
* **Error:** `psycopg.OperationalError: failed to resolve host 'postgres': [Errno -2] Name or service not known`
* **Cause:** Running `python run_platform.py` locally without Docker tries to connect to the Docker container host `postgres`.
* **Workaround:** 
  - **Option A (Docker):** Run via Docker Compose where service linking is configured:
    ```bash
    docker compose up --build
    ```
  - **Option B (Local Standalone):** Update your `.env` file to use SQLite and localhost:
    ```env
    DATABASE_URL=sqlite+aiosqlite:///./hyperneuron_local.db
    REDIS_URL=redis://localhost:6379/0
    ```
    And ensure `aiosqlite` is installed:
    ```bash
    pip install aiosqlite
    ```

### 3. Unresolved Git Merge Conflicts (`git pull` rejected)
* **Error:** `error: Pulling is not possible because you have unmerged files.` / `fatal: Exiting because of an unresolved conflict.`
* **Workaround:** To discard conflicting local changes and sync cleanly with GitHub:
  ```bash
  git merge --abort
  git fetch origin
  git reset --hard origin/main
  ```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
