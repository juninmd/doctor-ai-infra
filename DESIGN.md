# Infrastructure Agent Manager - Design Document

## Overview
This project is an advanced Infrastructure Agent Manager designed to troubleshoot and analyze resources across multiple platforms: Kubernetes, GCP, Datadog, and Azion. It aims to be the best-in-class solution for 2026, featuring automatic agent selection and a user-friendly interface.

## Tech Stack
*   **Backend**: Python 3.11+
    *   **Framework**: FastAPI
    *   **AI Orchestration**: LangGraph / LangChain
    *   **LLM Runtime**: Ollama (Local) / Gemini (Cloud)
    *   **Database**: SQLite (for session history/metadata)
    *   **Vector Store**: ChromaDB (for RAG/Context)
*   **Frontend**: Next.js (React)
    *   **Language**: TypeScript
    *   **Styling**: Tailwind CSS
    *   **Components**: Shadcn/UI
*   **Infrastructure Clients**:
    *   `kubernetes` (Official Python client)
    *   `google-cloud-sdk`
    *   `datadog`
    *   REST API wrapper for Azion

## Architecture

### 1. Agent Core (Backend)
The backend uses a Multi-Agent architecture orchestrated by a Supervisor (Router).

*   **Supervisor Agent**: Receives user query, analyzes intent, and delegates to the appropriate specialist agent.
*   **Specialist Agents**:
    *   **K8s Specialist**: Has tools to `kubectl get`, `describe`, check logs, etc.
    *   **GCP Specialist**: Can check VM status, GKE clusters, IAM, etc.
    *   **Datadog Specialist**: Queries metrics and monitors.
    *   **Azion Specialist**: Checks edge functions, domains, etc.
*   **Tools Layer**: Each agent is equipped with specific tools (Python functions) to interact with the infrastructure.

### 2. Interface (Frontend)
A modern Chat Interface that not only shows the final answer but also the "Thought Process" (which agent is being called, what tools are being used).

## Roadmap
1.  **Project Setup**: Initialize Monorepo (backend/frontend).
2.  **LLM Abstraction**: Implement the switch between Ollama and Gemini.
3.  **Agent Orchestration**: Set up LangGraph with a Supervisor.
4.  **Tool Implementation**: Create mock/real tools for K8s, GCP, etc. (Start with mocks/read-only for safety).
5.  **Frontend Implementation**: Build the chat UI.
6.  **Integration**: Connect Frontend to Backend.

## Configuration
Environment variables will control credentials and LLM selection (OLLAMA_BASE_URL, GOOGLE_API_KEY).
