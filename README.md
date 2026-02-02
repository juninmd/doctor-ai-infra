# Infrastructure Agent Manager

The best-in-class Infrastructure Agent Manager for 2026. Troubleshoot your K8s, GCP, Datadog, and Azion resources with an intelligent, multi-agent system.

## Features
- **Multi-Agent Architecture**: Supervisor routes queries to specialized agents (K8s, GCP, Datadog, Azion).
- **Local LLM**: Powered by Ollama (compatible with Gemini).
- **Relaxed Personality**: Direct, no-nonsense feedback.
- **Modern Stack**:
  - **Backend**: FastAPI, LangGraph, LangChain, uv
  - **Frontend**: React + Vite, Tailwind CSS, Shadcn/UI

## Prerequisites
- **Python 3.12+** (managed via `uv`)
- **Node.js 20+**
- **Ollama** running locally (default: `http://localhost:11434`)

## Getting Started

### 1. Start Ollama
Ensure you have Ollama installed and running. Pull the model (default `llama3`):
```bash
ollama serve
ollama pull llama3
```

### 2. Backend Setup
```bash
cd backend
# Install dependencies
uv sync
# Run the server
uv run uvicorn main:app --reload --port 8000
```
Backend will be available at `http://localhost:8000`.

### Configuration (Real Infrastructure)
By default, the agents run in **Mock Mode** for safety and demonstration. To enable **Real Infrastructure** interaction:

1.  Set the environment variable:
    ```bash
    export USE_REAL_TOOLS=true
    ```
2.  Provide the necessary credentials in `.env` or your shell:
    *   **Kubernetes**: Ensure `~/.kube/config` is valid or run inside a cluster with ServiceAccount.
    *   **GCP**: `export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"`
    *   **Datadog**: `export DD_API_KEY=...` and `export DD_APP_KEY=...`
    *   **Azion**: `export AZION_TOKEN=...`
    *   **GitHub**: `export GITHUB_TOKEN=...`

### 3. Frontend Setup
```bash
cd frontend
# Install dependencies
npm install
# Run the development server
npm run dev
```
Frontend will be available at `http://localhost:3000`.

## Architecture
- **Supervisor Node**: Analyzes the request and routes to the correct specialist.
- **Specialists**:
  - `K8sAgent`: Inspects pods, logs, events.
  - `GCPAgent`: Checks cloud resources.
  - `DatadogAgent`: Checks metrics.
  - `AzionAgent`: Checks edge functions.
- **UI**: Shows the conversation and expands the "Thought Process" to reveal internal agent actions.
