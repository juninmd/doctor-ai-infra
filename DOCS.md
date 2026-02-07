# SRE Agent - The Best Infrastructure Manager of 2026

Welcome to the future of SRE. This project implements a cutting-edge **Autonomous Infrastructure Agent** that manages, troubleshoots, and heals your infrastructure.

It is built with the **Best Stack of 2026**:
-   **LangGraph** for robust multi-agent orchestration.
-   **Google GenAI SDK (v1.0+)** for high-speed, long-context reasoning with Gemini 1.5 Flash.
-   **Ollama** compatibility for local, privacy-focused operations.
-   **React 19 + Vite** for a futuristic, real-time dashboard.

## Key Features

### 1. Autonomous Agent Swarm (The Supervisor)
The system uses a **Supervisor Agent** that intelligently routes tasks to specialized sub-agents:
-   **K8s_Specialist**: Deep dives into pods, logs, and events.
-   **GCP_Specialist**: Manages Cloud resources and GMP.
-   **Datadog_Specialist**: Checks metrics and alerts.
-   **Azion_Specialist**: Manages Edge Computing and CDNs.
-   **Incident_Specialist**: Handles the full incident lifecycle (Detection -> Timeline -> Post-Mortem).
-   **Topology_Specialist**: Visualizes the entire system map.

### 2. AI-Driven Root Cause Analysis
Unlike traditional tools that just dump logs, our agent **correlates signals** from K8s, Datadog, and GCP to find the *true* root cause.
-   **Tool:** `investigate_root_cause`
-   **Mechanism:** Aggregates data -> Uses Gemini 1.5 Flash (via `analyze_heavy_logs`) -> Outputs a Probability Score for each potential cause.

### 3. Smart Remediation (Runbooks on the Fly)
Don't have a runbook for an issue? The agent generates one for you.
-   **Tool:** `generate_remediation_plan`
-   **Mechanism:** Analyzes the incident context -> Generates a step-by-step, actionable Markdown checklist with specific `kubectl` or `gcloud` commands.

### 4. Live Infrastructure Scan
Get a holistic view of your stack in seconds.
-   **Tool:** `scan_infrastructure`
-   **Output:** A human-readable summary AND a structured JSON block for frontend integration.

### 5. Topology Visualization
Understand your dependencies instantly.
-   **Tool:** `generate_topology_diagram`
-   **Output:** Mermaid.js graph definition.

## Getting Started

### Prerequisites
-   Python 3.12+
-   Node.js 20+
-   `uv` (Recommended for fast Python package management)

### Configuration
Set the following environment variables in `.env`:

```bash
# LLM Provider
LLM_PROVIDER=gemini  # or 'ollama'
GOOGLE_API_KEY=your_gemini_api_key

# Infrastructure Credentials (for Real Tools)
KUBECONFIG=~/.kube/config
GOOGLE_APPLICATION_CREDENTIALS=path/to/sa.json
DD_API_KEY=...
DD_APP_KEY=...
AZION_TOKEN=...
GITHUB_TOKEN=...
```

### Running the Backend
```bash
cd backend
uv pip install -r requirements.txt
python main.py
```

### Running the Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## Migration Note (Google ADK)
This project has been fully migrated to use the **Google GenAI SDK (v1.0+)** (`google-genai`).
-   Legacy `google.generativeai` usage has been removed.
-   `langchain-google-genai` >= 2.0 is used for LangChain integration.
-   Direct SDK calls are used for high-throughput tasks like Log Analysis.

## Inspiration
This project integrates the best ideas from:
-   **Datadog Bits AI**: Correlation & Remediation.
-   **SmythOS**: Flexible Agent Graph.
-   **IncidentFox**: Automated Timelines.
