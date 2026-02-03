# GEMINI.md

## Project Context
This is the **Infrastructure Agent Manager**, a multi-agent system designed to troubleshoot Kubernetes, GCP, Datadog, and Azion resources.

## Core Stack
- **Backend**: Python 3.12, FastAPI, LangGraph, LangChain, SQLAlchemy (SQLite), uv
- **Frontend**: React 19 (Vite), Tailwind CSS, TypeScript
- **Communication**: REST API (FastAPI) + SSE (Server-Sent Events) for streaming

## Architecture
- **Supervisor**: Routes requests to specialized agents.
- **Specialists**: K8s, GCP, Datadog, Azion, Git, CICD, Security, Incident, Automation, Topology.
- **Tools**: Mix of Mock tools (default) and Real tools (enabled via `USE_REAL_TOOLS=true`).

## Key Learnings (Living Memory)
- **Database**: Uses SQLAlchemy with `joinedload` to avoid N+1 queries in topology visualization.
- **Frontend**: Uses `vite` instead of Next.js.
- **Testing**: Backend tests use `pytest`.

## Roadmap
- See `AGENTS.md` for the future roadmap.
