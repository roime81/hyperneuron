# ================================================================================

# 

# HYPERNEURON AI DEEP LAB (MVP)

# 

# ================================================================================

# 

# 

# 

# A private, multi-agent deep research and intelligence engine built with 

# 

# LangGraph, FastAPI, and a Next.js-inspired Tailwind UI. Designed for corporate 

# 

# intelligence and legal/financial due diligence.

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 1\. ARCHITECTURE \& AGENT LINEUP

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# Hyperneuron follows a deterministic Hub-and-Spoke (Supervisor) Fan-Out / Fan-In 

# 

# state machine. The Chief Orchestrator decomposes queries and dispatches tasks 

# 

# to three specialized parallel researcher agents powered by state-of-the-art 

# 

# open-weight models:

# 

# 

# 

# &#x20;                 \[ User Prompt (www.hyperneuron.io) ]

# 

# &#x20;                                 |

# 

# &#x20;                                 v

# 

# &#x20;          \[ Request Quantification (Chief Orchestrator) ]

# 

# &#x20;                    (Model: DeepSeek-V4.1-Flash)

# 

# &#x20;                                 |

# 

# &#x20;         +-----------------------+-----------------------+

# 

# &#x20;         v                       v                       v

# 

# \[ Deep Thinking Researcher ] \[ Deep Citation Researcher ] \[ Qualified Quantified Researcher ]

# 

# &#x20;    (Model: Gemma 4)         (Model: Llama 4 Scout)       (Model: Qwen 3.6)

# 

# &#x20;         |                       |                       |

# 

# &#x20;         +-----------------------+-----------------------+

# 

# &#x20;                                 | (Structured JSON Dossiers)

# 

# &#x20;                                 v

# 

# &#x20;                \[ Chief Orchestrator (Synthesis) ]

# 

# &#x20;                                 |

# 

# &#x20;                                 v

# 

# &#x20;                   \[ Stream Final Markdown Report ]

# 

# 

# 

# AGENT ROLES \& MODEL ASSIGNMENTS:

# 

# \* Chief Orchestrator (deepseek-v4.1-flash)

# 

# &#x20; - Responsibility: Request quantification, task planning, and final synthesis.

# 

# \* Deep Thinking Researcher (gemma4:31b)

# 

# &#x20; - Responsibility: First-principles reasoning, edge cases, and risk analysis.

# 

# \* Deep Citation Researcher (llama4:scout)

# 

# &#x20; - Responsibility: Live search execution, source provenance, and URL verification.

# 

# \* Qualified Quantified Researcher (qwen3.6:27b)

# 

# &#x20; - Responsibility: Quantitative metrics, financial ratios, and data tables.

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 2\. UI PREVIEW

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# Live execution UI mirroring your www.hyperneuron.io wireframe with real-time 

# 

# agent status cards and Server-Sent Events (SSE) streaming:

# 

# 

# 

# +-------------------------------------------------------------------+

# 

# | www.hyperneuron.io                        Private Multi-Agent Lab |

# 

# +-------------------------------------------------------------------+

# 

# | \[ Enter enterprise intelligence or due diligence prompt... ] \[Run] |

# 

# +-------------------------------------------------------------------+

# 

# | \[ Request Quantification (Chief Orchestrator) ]                   |

# 

# |   DeepSeek-V4.1-Flash - Status: Done                              |

# 

# |                                                                   |

# 

# |   \[ Deep Thinking ]    \[ Deep Citation ]    \[ Quantified Analyst ]|

# 

# |      Gemma 4             Llama 4 Scout         Qwen 3.6           |

# 

# |      (Done)                 (Done)                (Done)          |

# 

# +-------------------------------------------------------------------+

# 

# 

# 

# (Note: Save your actual UI screenshot as docs/screenshot.png in your repository)

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 3\. QUICK START GUIDE

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# PREREQUISITES:

# 

# \* Python 3.10+

# 

# \* Ollama running locally (or endpoints configured for vLLM / OpenRouter)

# 

# 

# 

# STEP 1: CLONE \& INSTALL

# 

# &#x20; git clone https://github.com/<your-username>/hyperneuron-mvp.git

# 

# &#x20; cd hyperneuron-mvp

# 

# 

# 

# &#x20; # Create and activate virtual environment

# 

# &#x20; python -m venv .venv

# 

# &#x20; source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate

# 

# 

# 

# &#x20; # Install dependencies

# 

# &#x20; pip install -r requirements.txt

# 

# 

# 

# STEP 2: CONFIGURE ENVIRONMENT

# 

# &#x20; Copy the example environment file and adjust your base URLs and model tags:

# 

# &#x20; cp .env.example .env

# 

# 

# 

# &#x20; Your .env file should look like this:

# 

# &#x20; LLM\_BASE\_URL=http://localhost:11434/v1

# 

# &#x20; LLM\_API\_KEY=ollama

# 

# 

# 

# &#x20; ORCHESTRATOR\_MODEL=deepseek-v4.1-flash

# 

# &#x20; THINKING\_MODEL=gemma4:31b

# 

# &#x20; CITATION\_MODEL=llama4:scout

# 

# &#x20; QUANT\_MODEL=qwen3.6:27b

# 

# 

# 

# &#x20; # Optional: Tavily API key for advanced web search

# 

# &#x20; TAVILY\_API\_KEY=

# 

# 

# 

# STEP 3: RUN THE DEVELOPMENT SERVER

# 

# &#x20; uvicorn backend.main:app --reload --port 8000

# 

# 

# 

# &#x20; Open your browser and navigate to http://localhost:8000 to access the UI.

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 4\. PROJECT STRUCTURE

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# hyperneuron-mvp/

# 

# |-- .env.example

# 

# |-- .gitignore

# 

# |-- README.txt

# 

# |-- requirements.txt

# 

# |-- backend/

# 

# |   |-- \_\_init\_\_.py

# 

# |   |-- config.py          # Unified LLM client provider (Ollama / vLLM / OpenRouter)

# 

# |   |-- state.py           # LangGraph TypedDict state \& Pydantic schemas

# 

# |   |-- tools.py           # DuckDuckGo search \& safe calculation tools

# 

# |   |-- agents.py          # Orchestrator + 3 parallel specialist nodes

# 

# |   |-- graph.py           # LangGraph state machine \& conditional routing

# 

# |   +-- main.py            # FastAPI server + SSE streaming \& static UI host

# 

# +-- frontend/

# 

# &#x20;   +-- index.html         # Glassmorphic Tailwind UI with real-time SSE listeners

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 5\. TECH STACK

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# \* Orchestration:     LangGraph \& LangChain

# 

# \* API Framework:     FastAPI \& Uvicorn (Server-Sent Events for streaming)

# 

# \* Frontend:          HTML5, Tailwind CSS, and Marked.js

# 

# \* Inference Runtime: Ollama / vLLM (compatible with OpenAI client specs)

# 

# \* Models:            DeepSeek, Gemma, Llama, and Qwen open-weight architectures

# 

# 

# 

# \--------------------------------------------------------------------------------

# 

# 6\. LICENSE

# 

# \--------------------------------------------------------------------------------

# 

# 

# 

# Distributed under the MIT License. See LICENSE for more information.

# 

# ================================================================================```

