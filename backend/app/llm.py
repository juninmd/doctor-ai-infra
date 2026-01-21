import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Returns the configured LLM instance based on environment variables.
    Defaults to Ollama (via ChatOpenAI compatible endpoint) if not specified.
    """
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if llm_provider == "gemini":
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider")

        return ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=google_api_key,
            temperature=0
        )

    elif llm_provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        return ChatOpenAI(
            base_url=base_url,
            api_key="ollama", # required but ignored
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            temperature=0
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
