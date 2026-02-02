# GEMINI.md - Living Memory

## 🧠 Memory Bank
This file serves as the persistent memory for the AI Agents working on this repository.

### 📅 Session Log

#### 2024-05-23 - Initial Audit
*   **Context**: Performed "Antigravity Audit".
*   **Discovery**: Frontend is Vite + React, not Next.js.
*   **Action**: Standardized repository structure and improved Supervisor robustness.
*   **Security**: Found moderate vulnerability in `mermaid` (via `lodash-es`) in frontend. Deferred fix to avoid breaking changes.

### 🗺️ Architecture Insights
*   **Backend**: FastAPI + LangGraph. `Supervisor` node routes to specialists.
*   **Frontend**: Vite + React SPA.
*   **Tools**: Agents use a mix of "Real" and "Mock" tools based on `USE_REAL_TOOLS` env var.

### 📝 Conventions
*   **Commits**: Use Semantic Commit Messages (feat, fix, docs, style, refactor, perf, test, chore).
*   **Python**: `uv` for dependency management.
*   **Node**: `npm` (project uses `package-lock.json`, so `npm` is preferred over `pnpm` despite protocol suggestion, to avoid lockfile noise).

## 🚀 Roadmap status
See `AGENTS.md` for the official Feature Roadmap.
