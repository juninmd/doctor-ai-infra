# Infrastructure Agent Manager (Backend)

## Overview
This is the backend for the "Best Agent of 2026", an advanced SRE agent manager built with LangGraph.
It orchestrates specialized agents (K8s, GCP, Datadog, Azion, etc.) to perform complex troubleshooting, root cause analysis, and remediation.

## Features
- **LangGraph Architecture**: Supervisor-worker pattern with specialized agents.
- **Advanced LLM Support**: Uses `google-genai` SDK (Gemini 1.5 Flash) for high-performance tasks and `Ollama` for local compatibility.
- **Comprehensive Toolset**:
  - Kubernetes (Pod analysis, log patterns)
  - Google Cloud (Status, Logs, GMP)
  - Datadog (Metrics, Alerts)
  - Azion (Edge status, WAF, Cache Purge)
  - GitHub (Code fixes, PR creation, CI analysis)
  - Incident Management (Timeline, Post-mortems, Remediation Plans)
  - Runbooks (Automated actions with safety checks)
  - Slack Integration (Notifications)
- **Streaming API**: Real-time updates via SSE (Server-Sent Events) including tool outputs.
- **Persistence**: Supports thread history and human-in-the-loop approval flows.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file with the following keys:
    ```bash
    GOOGLE_API_KEY=...
    GITHUB_TOKEN=...
    DD_API_KEY=...
    DD_APP_KEY=...
    AZION_TOKEN=...
    SLACK_WEBHOOK_URL=...
    LLM_PROVIDER=gemini  # or ollama
    ```

## Running the Server

Start the FastAPI server:
```bash
# Ensure you are in the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
python backend/main.py
```
The server will start on `http://0.0.0.0:8000`.

## Running Tests

Run the comprehensive test suite:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
pytest backend/tests/
```
All tests should pass, verifying the graph logic, tool integrations, and API endpoints.

### Best of 2026 Features Tests
To verify the advanced capabilities (Service Catalog Docs, Incident Timelines, Remediation Plans, On-Call Schedules), run:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
pytest backend/tests/test_best_of_2026.py
```
These tests ensure that the agent correctly generates Markdown documentation, Mermaid Gantt charts, and handles LLM fallbacks (Gemini vs Ollama) for complex reasoning tasks.

## API Usage

- **POST /chat**: interact with the agent.
  - Body: `{"message": "Check system health", "thread_id": "optional-uuid"}`
  - Returns: Stream of JSON events (`activity`, `message`, `tool_output`, `approval_required`, `final`).

- **POST /chat/resume**: Resume a paused workflow (e.g., after approval).
  - Body: `{"thread_id": "...", "action": "approve"}`
