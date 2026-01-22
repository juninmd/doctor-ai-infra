from langchain_ollama import ChatOllama
import os

# Default to llama3 if not specified, user can override via env var
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_llm():
    """Returns the configured ChatOllama instance."""
    return ChatOllama(
        model=MODEL_NAME,
        base_url=BASE_URL,
        temperature=0.7,
    )
