# Migration to Google GenAI SDK (2026 Vision)

This project has been migrated to use the `google-genai` SDK (v1.0+) as the primary driver for advanced AI capabilities, aligning with the "Best Agent of 2026" vision.

## Key Changes

1.  **Backend LLM Provider**:
    *   The `backend/app/llm.py` module now defaults to `gemini-1.5-flash` when `LLM_PROVIDER=gemini`.
    *   It uses `langchain-google-genai` (v2.0+) for standard chat interactions.
    *   It exports a raw `get_google_sdk_client()` function for advanced usage (File API, Caching, etc.).

2.  **Infrastructure Scanning**:
    *   `scan_infrastructure` in `backend/app/tools/observability.py` now leverages `gemini-1.5-flash` to provide a one-sentence "AI Insight" summary of the system health.

3.  **Log Analysis**:
    *   `analyze_heavy_logs` and `analyze_log_patterns` prioritize the Google GenAI SDK to handle large context windows (up to 1M tokens) efficiently.
    *   Fallback to standard LLM (Ollama) is preserved for local compatibility.

## Configuration

To use the full capabilities, ensure your `.env` file is configured:

```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here
```

If `LLM_PROVIDER` is set to `ollama` (default), the agent will still work but advanced "AI Insights" and large log analysis will fallback to truncated local processing.

## Verification

Run the verification script to confirm the SDK is working:

```bash
# (Self-check was performed during migration)
python -c "from app.llm import get_google_sdk_client; print(get_google_sdk_client())"
```
