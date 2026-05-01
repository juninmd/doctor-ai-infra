# 🚀 Infra Manager 2026 - User Guide

This project is a Next-Gen Infrastructure Agent Manager designed to autonomously troubleshoot Kubernetes, GCP, Datadog, and Traefik resources.

## ✨ Features

- **Multi-Agent Orchestration**: Specialized agents for K8s, GCP, Datadog, Traefik, etc.
- **Contextual Routing**: Smart routing (e.g., Latency -> Traefik -> Backend).
- **RAG Integration**: Uses a vector database for incident history.
- **Dual LLM Support**: Runs locally with Ollama (default) or Gemini Pro.

## 🛠️ Setup & Configuration

### 1. Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# LLM Selection
LLM_PROVIDER=ollama  # Options: 'ollama' or 'gemini'
OLLAMA_MODEL=llama3  # Default model
GOOGLE_API_KEY=your_gemini_key_if_using_gemini

# Cloud Providers
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Kubernetes
# (Ensure ~/.kube/config is valid or use In-Cluster config)

# Datadog
DD_API_KEY=your_dd_api_key
DD_APP_KEY=your_dd_app_key

# Traefik
TRAEFIK_API_URL=http://traefik.kube-system.svc.cluster.local:8080

# GitHub (Optional)
GITHUB_TOKEN=your_github_token
```

### 2. Running with Ollama (Local)

1.  Install [Ollama](https://ollama.com).
2.  Pull the model: `ollama pull llama3`.
3.  Set `LLM_PROVIDER=ollama`.
4.  Run backend:
    ```bash
    cd backend
    uv sync
    uv run fastapi dev main.py
    ```

### 3. Running with Gemini (Cloud)

1.  Get an API Key from Google AI Studio.
2.  Set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY`.
3.  Run backend as above.

## 💡 Example Queries

- **Full Check:** "Fazer análise completa da infraestrutura" (Runs `analyze_infrastructure_health`)
- **Latency Issue:** "O site está lento, verifique o que está acontecendo." (Routes to Traefik -> Datadog -> K8s)
- **Deployment:** "Verifique o status do último deploy no namespace default."

## 🖥️ Frontend

1.  `cd frontend`
2.  `npm install`
3.  `npm run dev`
4.  Open `http://localhost:5173`.

---
*Built for the 2026 Era.*
