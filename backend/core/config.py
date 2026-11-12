import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Hyperneuron AI"
    VERSION: str = "2.1"

    PUBLIC_PORT: int = int(os.getenv("PUBLIC_PORT", 8000))
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8001))
    SECURITY_PORT: int = int(os.getenv("SECURITY_PORT", 8002))

    SECRET_KEY: str = os.getenv("SECRET_KEY", "hyperneuron-dev-secret-key-2026")
    ADMIN_DEFAULT_USER: str = os.getenv("ADMIN_DEFAULT_USER", "admin")
    ADMIN_DEFAULT_PASS: str = os.getenv("ADMIN_DEFAULT_PASS", "admin")

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://hyperneuron:hyperneuron_secret@localhost:5432/hyperneuron_ai"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "ollama")

    ORCHESTRATOR_MODEL: str = os.getenv("ORCHESTRATOR_MODEL", "deepseek-v4.1-flash")
    THINKING_MODEL: str = os.getenv("THINKING_MODEL", "gemma4:31b")
    CITATION_MODEL: str = os.getenv("CITATION_MODEL", "llama4:scout")
    QUANT_MODEL: str = os.getenv("QUANT_MODEL", "qwen3.6:27b")

settings = Settings()
