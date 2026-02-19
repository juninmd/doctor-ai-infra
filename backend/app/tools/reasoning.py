from langchain_core.tools import tool
from app.llm import get_llm, get_google_sdk_client
import json

@tool
def generate_hypothesis(context: str) -> str:
    """
    Generates a list of potential hypotheses for a given problem context.
    Uses advanced reasoning to identify root causes and suggests validation steps.

    Args:
        context: The situation description, logs, or error messages.
    """
    prompt = (
        "You are a Principal Site Reliability Engineer (SRE). "
        "Based on the provided context, generate a list of potential hypotheses for the root cause. "
        "For each hypothesis, provide a validation step (e.g., 'Check Datadog for latency spikes'). "
        "Format the output as a JSON list of objects with keys: 'hypothesis', 'validation_step', 'probability'.\n\n"
        f"Context:\n{context}"
    )

    client = get_google_sdk_client()
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            return response.text
        except Exception as e:
            print(f"Gemini SDK failed: {e}. Falling back to standard LLM.")

    # Fallback
    llm = get_llm()
    try:
        res = llm.invoke(prompt + "\n\nReturn ONLY raw JSON. Do not include markdown formatting like ```json ... ```.")
        content = res.content.strip()
        # Clean up common markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
    except Exception as e:
        return f"Error generating hypothesis: {e}"
