# 🚀 SRE Agent 2026: The Ultimate Infrastructure Manager

> **"The Best Agent of 2026"** - Autonomous, Intelligent, and Open Source.

This project is a state-of-the-art **Autonomous Infrastructure Agent** designed to troubleshoot, manage, and heal complex infrastructures including Kubernetes, Google Cloud, Datadog, and Azion.

Built with the **best stack of 2026**:
-   **LangGraph & LangChain**: Robust multi-agent orchestration.
-   **Google GenAI SDK (v1.0+)**: Powered by **Gemini 1.5 Flash** for high-speed reasoning and massive context windows (1M+ tokens).
-   **Ollama Compatibility**: Fully functional offline mode using local LLMs (Llama 3, Phi-3).
-   **React 19 + Vite**: Futuristic, real-time "Glassmorphism" dashboard.

## 🌟 Key Features

### 🧠 Autonomous Swarm Intelligence
A **Supervisor Agent** intelligently routes tasks to specialized experts:
-   **K8s_Specialist**: Deep troubleshooting of Pods, Deployments, and Logs.
-   **GCP_Specialist**: Cloud resource management and Cost Estimation.
-   **Datadog_Specialist**: Metrics analysis and Alert correlation.
-   **Incident_Specialist**: Full Incident Lifecycle (Detection -> Timeline -> Post-Mortem).
-   **Topology_Specialist**: Visualizes service dependencies and system health.
-   **Automation_Specialist**: Executes runbooks safely.

### ⚡ Inspired by Industry Leaders
We integrated the best features from top observability tools:
-   **Datadog Bits AI**: Correlation of signals (Logs, Metrics, Traces) for Root Cause Analysis.
-   **SmythOS**: Flexible, modular Agent Graph architecture.
-   **IncidentFox**: Automated **Visual Incident Timelines** (Mermaid Gantt Charts).
-   **OpsMate**: **ChatOps Collaboration** (Slack/Zoom integration) and persistent incident channels.
-   **FuzzyLabs**: Actionable Runbook execution with **Dry Run** safety.

### 🛠️ Powerful Toolset
-   **Root Cause Analysis**: Correlates K8s events, Datadog alerts, and Git commits to find the *true* cause.
-   **Self-Documenting Infrastructure**: Generates a full **Service Catalog Documentation** markdown report on demand.
-   **Visual Timelines**: Generates Mermaid.js Gantt charts of incident progression.
-   **Auto-Remediation**: Generates step-by-step remediation plans (Runbooks) using AI.
-   **Cost Estimation**: Estimates GCP monthly bills using AI.

## 🚀 Getting Started

### Prerequisites
-   **Python 3.12+**
-   **Node.js 20+**
-   **Ollama** (for local mode) OR **Google API Key** (for Gemini mode)

### 1. Backend Setup
```bash
cd backend
# Install dependencies (using uv for speed)
pip install uv
uv pip install -r requirements.txt

# Run the Agent Server
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```
Access the dashboard at `http://localhost:5173`.

### 3. Configuration
Create a `.env` file in `backend/`:

```bash
# AI Provider (Gemini Recommended for 2026 Performance)
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_gemini_key

# Infrastructure Credentials (Optional - Agents use Mocks if missing)
KUBECONFIG=~/.kube/config
GOOGLE_APPLICATION_CREDENTIALS=path/to/sa.json
DD_API_KEY=...
DD_APP_KEY=...
AZION_TOKEN=...
GITHUB_TOKEN=...
SLACK_WEBHOOK_URL=...
```

## 📚 Documentation
For detailed migration guides and architecture, see [DOCS.md](./DOCS.md).

## 🏆 Why is this the "Best of 2026"?
-   **Zero Cost Option**: Runs entirely on **Ollama** if you want to pay nothing.
-   **Hybrid Power**: Can switch to **Gemini 1.5 Flash** instantly for heavy lifting (Log Analysis).
-   **Safety First**: Runbooks support `dry_run` mode.
-   **Visual & Interactive**: Not just text - diagrams, timelines, and dashboards.

---
*Built with ❤️ for the SRE Community.*
