import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")

def get_llm(model_env_var: str, default_model: str, temperature: float = 0.2) -> ChatOpenAI:
    model_name = os.getenv(model_env_var, default_model)
    return ChatOpenAI(
        model=model_name,
        base_url=BASE_URL,
        api_key=API_KEY,
        temperature=temperature,
    )
