import os
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Default to llama3 if not specified, user can override via env var
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_llm():
    """
    Returns the configured LLM instance based on LLM_PROVIDER env var.
    Options: 'ollama' (default), 'gemini'.
    """
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if llm_provider == "gemini":
        if not google_api_key:
            raise ValueError("LLM_PROVIDER is 'gemini' but GOOGLE_API_KEY is not set.")

        # Best practice 2026: Use Flash for speed/cost, disable safety blocks for SRE logs
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0, # Precision for SRE tasks
            convert_system_message_to_human=True,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

    # Default to Ollama
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0, # Precision for SRE tasks
    )
