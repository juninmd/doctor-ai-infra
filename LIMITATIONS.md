# ⚠️ Limitations and Safe Defaults

The Doctor AI Infra Agent Manager project is built to handle complex troubleshooting and workflow integrations. However, some aspects of its behavior are deliberately constrained to maintain a small scope, ensure safe defaults, and provide robust local and open-source operations.

## Core Limitations & Safe Defaults

### 1. Simulated Actions for Destructive Workflows
Several specific tools implemented in specialized agents (e.g., `Opsy`, `SmythOS`, `FuzzyLabs`) are intended to act as SRE AI Co-Pilots managing live infrastructure. However, for the safety of real infrastructure environments, any **potentially destructive or heavily mutation-based operations** (e.g., backups via `git push`, rolling restarts, direct namespace deletion, or generating actual API tickets with external live services like Jira if unmocked) are intentionally simulated.
- The tools run analysis, determine optimal commands, and verify states securely.
- Real changes are suggested to the user, or simulated in output.

### 2. Large Language Model Dependencies
The system leverages local or hosted LLMs for root cause analysis and diagnosis via LangGraph and custom AI tools.
- **Ollama:** A local Ollama instance (`http://localhost:11434` with model `llama3` by default) must be running and healthy if the application is run in open-source zero-cost mode (`LLM_PROVIDER=ollama`). If the instance is down, AI inferences will fail.
- **Gemini:** The system is fully compatible with Gemini as an alternative (`LLM_PROVIDER=gemini`), but it strictly requires a valid `GOOGLE_API_KEY` to be passed via environment variables.
- AI reasoning uses simulated data in tests or local setups unless real infrastructure variables are exposed.

### 3. Azion and External API Credentials
Integrations requiring external endpoints, specifically the **Azion Edge tools** (`backend/app/tools/azion.py`), are strictly dependent on an active `AZION_TOKEN`.
- Similarly, Datadog tools rely exactly on `DD_API_KEY` and `DD_APP_KEY`.
- In development/testing environments, these calls must be rigorously mocked or supplied with dummy variables to prevent runtime validation errors (e.g., from Pydantic `BaseSettings`).

### 4. Limited File Modification Scope
AI verification agents operate strictly within the bounds specified by the `AGENTS.md` and `AGENTS_GUIDE.md` files. They adhere to the **Antigravity Protocol** maximum of 150 lines per management script and enforce strict typed contracts between the frontend and backend.

### 5. Frontend & Test Execution State
- The current application explicitly ignores legacy code present in `frontend_old/`. All active development for the dashboard occurs in `frontend/`.
- Backend tests may yield warnings like `LangGraphDeprecatedSinceV10`. This is expected since the codebase deliberately utilizes `create_react_agent` from `langgraph.prebuilt`.
- Running backend tests with coverage (`--cov`) is known to cause PyTorch-related conflicts and should be avoided when executing standard validations.
