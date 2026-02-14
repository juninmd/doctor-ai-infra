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

## Future Roadmap

*   **Auto-Remediation Approval Flow**: UI for approving dangerous actions.
*   **Mermaid.js Topology**: Visualizing service maps directly in the chat.
