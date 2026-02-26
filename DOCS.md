# Infra Manager 2026 - Feature Documentation

Welcome to the Next-Gen Autonomous Infrastructure Manager. This document outlines the new features introduced in the 2026 release.

## 🧠 AI Insights

The **Live Status** dashboard now includes an **AI Insight** card.
*   **What it is:** A real-time, AI-generated executive summary of your infrastructure's health.
*   **How it works:** When you click "Refresh" (or run a scan), the agent aggregates data from K8s, GCP, Datadog, and Azion. It then uses Gemini 1.5 Flash to synthesize this data into a single, actionable sentence.
*   **Example:** *"System Normal: All pods are running, but Datadog reports a slight latency spike in the payment service."*

## 📚 Dynamic Knowledge Base

The agent now learns! You can feed it runbooks, notes, or incident reports on the fly.

### New Tool: `add_knowledge_base_item`
*   **Usage:** The agent (or you via chat) can add information to the RAG system.
*   **Example Chat Command:** "Remember that error 503 on service X usually means the DB is restarting."
*   **Under the Hood:** The agent calls `add_knowledge_base_item`, indexing the text into ChromaDB for future retrieval.

## 🔄 Proactive Refresh

*   **Refresh Button:** A new refresh button on the dashboard triggers a `scan_infrastructure` command behind the scenes.
*   **Chat Integration:** The refresh action is treated as a user request ("Scan infrastructure status"), ensuring the conversation context is updated with the latest findings.

## 🛠️ Tech Stack & Compatibility

*   **Google GenAI SDK**: Utilizing `gemini-1.5-flash` for high speed and low cost.
*   **Ollama Fallback**: Fully compatible with local models (Llama 3) for offline or air-gapped environments.
*   **Frontend**: React 19 + Vite + Framer Motion for a "Glassmorphism" UI.

## 🚀 Best of 2026 Features (New!)

### 🧠 Self-Learning Incident Post-Mortems
The system now automatically "learns" from past incidents.
*   **How it works:** When an `Incident_Specialist` generates a Post-Mortem report using `generate_postmortem`, the content is immediately indexed into the RAG Knowledge Base.
*   **Benefit:** Future incidents with similar symptoms will automatically retrieve relevant past solutions and lessons learned.

### 📖 Automated Runbook Generation
Turn your incident learnings into actionable runbooks instantly.
*   **New Tool:** `generate_runbook_from_incident(incident_id, runbook_name)`
*   **Workflow:** After resolving an incident, ask the agent: *"Create a runbook named 'db_restart_procedure' from incident inc-123"*.
*   **Result:** The AI extracts the successful remediation steps from the Post-Mortem and saves a new **Manual Runbook** to the library.

### 🔔 Smart Alert Correlation
Stop alert fatigue with AI-driven correlation.
*   **New Tool:** `correlate_alerts` (available to Datadog & Planner Specialists).
*   **Capability:** The agent analyzes a list of active alerts to identify patterns (e.g., *"High DB CPU is causing API Latency"*).
*   **Usage:** Ask *"Check active alerts and find the root cause"*.

### 📝 Manual Runbook Execution
The agent can now guide you through manual procedures.
*   **Support:** Runbooks can be defined as `manual_steps` (Markdown text) instead of Python code.
*   **Execution:** When you run `execute_runbook` on a manual runbook, the agent displays the step-by-step instructions for you to follow.

## Future Roadmap

*   **Auto-Remediation Approval Flow**: UI for approving dangerous actions.
*   **Mermaid.js Topology**: Visualizing service maps directly in the chat.
