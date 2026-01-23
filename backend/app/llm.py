import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

# Default to llama3 if not specified, user can override via env var
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def get_llm():
    """
    Returns the configured LLM instance.
    Prioritizes Gemini (if GOOGLE_API_KEY is set), otherwise falls back to Ollama.
    """
    if GOOGLE_API_KEY:
        # Using Gemini if API key is provided
        return ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True # Helps with some role restrictions in Gemini
        )

    # Fallback to local Ollama
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7,
    )
