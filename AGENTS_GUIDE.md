# 🚀 Infrastructure Agents 2026 - User Guide

Welcome to the **Best Infrastructure Agent Manager of 2026**. This system leverages **LangGraph**, **Ollama**, and **Google Gemini** (via the new `google-genai` SDK) to provide intelligent, autonomous SRE capabilities.

## 🌟 Key Features

### 1. Hybrid Intelligence (Ollama + Gemini)
- **Local Privacy**: Run completely offline with Ollama (`llama3`).
- **Cloud Power**: Switch to Google Gemini 1.5 Flash for massive context windows (1M+ tokens) when analyzing heavy logs or generating complex reports.
- **Configuration**: Set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY` in `.env`.

### 2. Autonomous Incident Management
The **Incident_Specialist** agent acts as an Incident Commander:
- **Timeline Tracking**: Automatically logs hypotheses, evidence, and actions.
- **Post-Mortems**: Generates blameless post-mortem reports using RAG (Retrieval Augmented Generation) to learn from past incidents.
- **Remediation Plans**: Generates step-by-step runbooks for active issues using Gemini's reasoning.

### 3. Knowledge Base (RAG)
The system automatically indexes your:
- **Service Catalog** (Services, Dependencies)
- **Runbooks** (Automation Scripts)
- **Past Incidents** (Post-Mortems)

This allows agents to "remember" how similar issues were solved previously.

### 4. Smart Routing (Supervisor)
The **Supervisor** agent uses structured output to intelligently route tasks:
- **"Site is slow"** -> Checks **Azion** (Edge) -> **Datadog** (APM) -> **K8s** (Backend).
- **"Database error"** -> Routes directly to **GCP_Specialist**.

---

## 🛠️ Usage

### Running the Agent
```bash
# Start the backend
cd backend
uvicorn main:app --reload
```

### interacting via API
The agent exposes a streaming endpoint at `/chat`.
```bash
curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "My payment service is failing with 500 errors"}'
```

### Using Tools Directly
You can invoke specific capabilities via natural language:
- **"Create an incident for the payment API outage (SEV-1)"**
- **"Generate a post-mortem for incident 1234a"**
- **"Suggest a remediation plan for high latency on Postgres"**
- **"Scan infrastructure status"**

---

## 🧪 Testing & Development

We adhere to strict 2026 quality standards.

### Running Tests
```bash
# Run all tests (Unit + Integration)
pytest backend/tests/
```

### Key Test Files
- `backend/tests/test_incident_management.py`: Verifies the full incident lifecycle.
- `backend/tests/test_rag_system.py`: Checks Knowledge Base indexing and retrieval.
- `backend/tests/test_supervisor_routing.py`: Validates the routing logic.

---

## 📦 Project Structure

- `backend/app/graph.py`: The brain (LangGraph definition).
- `backend/app/tools/incident.py`: Incident management logic.
- `backend/app/rag.py`: Knowledge Base engine.
- `backend/app/llm.py`: Unified LLM interface (Ollama/Gemini).
