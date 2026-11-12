# 🧠 HYPERNEURON AI DEEP LAB
*Private, Multi-Agent Deep Research & Intelligence Engine*

---

## 🏛️ Executive Summary

**Hyperneuron AI Deep Lab** is a sovereign, multi-agent intelligence platform built for high-stakes **Corporate Intelligence** and **Legal/Financial Due Diligence**. By pairing high-performance local/private LLMs with an orchestrated LangGraph state machine, Hyperneuron automates exhaustive research, first-principles reasoning, web citation provenance, and financial/quantitative verification without sacrificing data privacy.

---

## 📐 System Architecture & Agent Lineup

Hyperneuron operates via a deterministic **Hub-and-Spoke Fan-Out / Fan-In** supervisor pattern. The **Chief Orchestrator** decomposes prompts into structured research rubrics, dispatches tasks concurrently to specialized parallel workers, audits findings, and synthesizes an executive markdown report.

```
                  ┌────────────────────────────────────────┐
                  │ User Prompt (www.hyperneuron.io UI)    │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Request Quantification & Planning      │
                  │ (Chief Orchestrator: DeepSeek-V4.1)    │
                  └──────────────────┬─────────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Deep Thinking    │       │ Deep Citation    │       │ Qualified Quant  │
│ Researcher       │       │ Researcher       │       │ Researcher       │
│ (Gemma 4)        │       │ (Llama 4 Scout)  │       │ (Qwen 3.6)       │
└─────────┬────────┘       └─────────┬────────┘       └─────────┬────────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │ (Structured Dossiers)
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Synthesis & Citation Audit             │
                  │ (Chief Orchestrator)                   │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │ Stream Final Executive Markdown Report │
                  └────────────────────────────────────────┘
```

### Agent Specialization Matrix

| Agent Role | Responsibility | Default Model ID |
| :--- | :--- | :--- |
| **Chief Orchestrator** | Task planning, rubric generation, and final synthesis. | `deepseek-v4.1-flash` |
| **Deep Thinking Researcher** | First-principles reasoning, edge cases, strategic/risk analysis. | `gemma4:31b` |
| **Deep Citation Researcher** | Live search execution, source provenance, URL verification. | `llama4:scout` |
| **Qualified Quantified Researcher** | Quantitative metrics, financial ratios, benchmarks, data tables. | `qwen3.6:27b` |

---

## 🖥️ UI Preview & Execution Flow

The glassmorphic Tailwind frontend (`www.hyperneuron.io` interface) connects to FastAPI via Server-Sent Events (SSE), illuminating real-time agent status cards as LangGraph executes the workflow.

```
+-------------------------------------------------------------------+
| www.hyperneuron.io                        Private Multi-Agent Lab |
+-------------------------------------------------------------------+
| [ Enter enterprise intelligence or due diligence prompt... ] [Run] |
+-------------------------------------------------------------------+
| [ Request Quantification (Chief Orchestrator) ]                   |
|   DeepSeek-V4.1-Flash • Status: Completed                         |
|                                                                   |
|   [ Deep Thinking ]    [ Deep Citation ]    [ Quantified Analyst ]|
|      Gemma 4             Llama 4 Scout         Qwen 3.6           |
|      (Completed)            (Completed)           (Completed)     |
+-------------------------------------------------------------------+
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
* Python 3.10+
* [Ollama](https://ollama.com/) running locally (or custom vLLM / OpenRouter endpoints)

### 2. Clone & Setup Environment
```bash
git clone https://github.com/roime81/hyperneuron-ai.git
cd hyperneuron-ai

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Variables
Copy the environment template and configure your model tags and base URLs:
```bash
cp .env.example .env
```

Default `.env` configuration:
```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama

ORCHESTRATOR_MODEL=deepseek-v4.1-flash
THINKING_MODEL=gemma4:31b
CITATION_MODEL=llama4:scout
QUANT_MODEL=qwen3.6:27b

TAVILY_API_KEY=
```

### 4. Launch Application
```bash
uvicorn backend.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser to run Hyperneuron.

---

## 📂 Project Structure

```text
hyperneuron-ai/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── config.py          # Unified LLM client provider
│   ├── state.py           # LangGraph TypedDict & Pydantic schemas
│   ├── tools.py           # DuckDuckGo search & safe math tools
│   ├── agents.py          # Chief Orchestrator + 3 specialist nodes
│   ├── graph.py           # State machine & conditional routing
│   └── main.py            # FastAPI server & SSE streaming
└── frontend/
    └── index.html         # Tailwind UI with real-time SSE listeners
```

---

## 🛠️ Tech Stack

* **Orchestration:** LangGraph & LangChain
* **API Framework:** FastAPI & Uvicorn (with SSE streaming)
* **Frontend:** Tailwind CSS & Marked.js
* **Inference:** Ollama / vLLM / OpenRouter
* **Models:** DeepSeek, Gemma, Llama, and Qwen open-weight families

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
