# AI SRE Agent: Benchmark & Roadmap (2025)

## 1. Visão Geral
Este documento define os requisitos essenciais ("Must Haves"), as tecnologias mais utilizadas e um benchmark competitivo para Agentes de SRE (Site Reliability Engineering) baseados em IA. O objetivo é guiar a evolução do nosso agente atual.

## 2. O que não pode faltar? (Must Haves)
Com base nas tendências de 2025 (Gartner, Datadog, incident.io), um Agente SRE competente deve possuir:

### A. Observabilidade Contextual e Topológica
*   **O que é:** Não apenas ler logs, mas entender o *mapa* de dependências (ex: Service A chama Service B, que usa DB C).
*   **Por que:** Para diferenciar sintomas de causas raiz.
*   **Nosso Status:** **Alto** (Implementado `trace_service_health` e `generate_topology_diagram` com visualização Mermaid).

### B. Investigação Autônoma (Zero-Touch Triage)
*   **O que é:** Capacidade de buscar logs, correlacionar métricas e eventos sem intervenção humana inicial.
*   **Por que:** Reduz o MTTR (Mean Time to Resolution) drasticamente.
*   **Nosso Status:** Alto (Nossos especialistas de K8s, GCP e Datadog já fazem isso).

### C. Memória de Longo Prazo e Aprendizado (RAG)
*   **O que é:** Capacidade de consultar Post-Mortems passados e Runbooks para sugerir correções baseadas em histórico.
*   **Por que:** Evita "reinventar a roda" em incidentes recorrentes.
*   **Nosso Status:** **Completo** (Implementado via `backend/app/rag.py` usando ChromaDB e Sentence Transformers).

### D. Integração ChatOps (Slack/Teams)
*   **O que é:** O agente deve viver onde o time conversa, não em um dashboard isolado.
*   **Por que:** Colaboração em tempo real.
*   **Nosso Status:** Parcial (Interface Web moderna, integração Slack pendente).

### E. "Human-in-the-loop" para Ações Destrutivas
*   **O que é:** O agente sugere o fix, o humano aprova. Nunca reiniciar produção sem permissão.
*   **Por que:** Segurança e confiança.
*   **Nosso Status:** **Alto/Implementado** (Agentes configurados para solicitar confirmação antes de ações como Purge ou Restart).

---

## 3. Tecnologias Mais Utilizadas (Tech Stack)

| Componente | Padrão da Indústria | Nosso Stack Atual | Veredito |
| :--- | :--- | :--- | :--- |
| **LLM Orchestration** | LangChain / LangGraph / AutoGen | **LangGraph** | ✅ Alinhado |
| **LLM Model** | GPT-4o, Claude 3.5 Sonnet, Llama 3 | **Ollama / Gemini** | ✅ Alinhado (Híbrido) |
| **Vector Database** | Pinecone, Chroma, Weaviate | **ChromaDB** | ✅ Resolvido |
| **Observability** | OpenTelemetry (OTel), Prometheus | **Prometheus (GMP), Datadog** | ✅ Alinhado |
| **Runtime** | Kubernetes | **Kubernetes** | ✅ Alinhado |
| **Context Window** | 128k+ tokens | Depende do modelo | ⚠️ Monitorar |

---

## 4. Benchmark Competitivo

Comparação do nosso agente ("Jules SRE") com líderes de mercado e ferramentas Open Source.

| Funcionalidade | **Datadog Bits** (Commercial) | **K8sGPT** (Open Source) | **Dynatrace Davis** (Causal AI) | **Nosso Agente** (Jules SRE) |
| :--- | :--- | :--- | :--- | :--- |
| **Foco Principal** | Full Stack Observability | Kubernetes Issues | Performance / APM | **Multi-Domain Orchestration** |
| **Raciocínio** | GenAI + Contexto da Plat. | Análise Estática + AI | Determinístico + GenAI | **ReAct (LangGraph)** |
| **Integração Cloud** | Nativa (AWS/GCP/Azure) | Limitada | Nativa | **Alta (Via SDKs)** |
| **Custo** | $$$$ | Grátis (Self-host) | $$$$ | **Baixo (Open/Local)** |
| **Extensibilidade** | Baixa (Ecossistema Fechado) | Média (Plugins) | Baixa | **Alta (Python Code)** |
| **Self-Healing** | Sugestões (Workflows) | Sugestões | Automação Avançada | **Execução de Runbooks** |

---

## 5. Gap Analysis & Roadmap (Próximos Passos)

Para atingir o nível de um "Senior SRE Agent", precisamos focar em:

1.  **Adicionar Memória (Vector Store):**
    *   Implementar ChromaDB ou FAISS.
    *   Indexar `runbooks/` e `incidents/` passados.

2.  **Melhorar a Topologia:**
    *   Criar uma ferramenta `get_service_dependencies` que consulta o Service Catalog para dar contexto ao Supervisor.

3.  **Persistência:**
    *   Mover `INCIDENTS` e `RUNBOOKS` de memória para um banco SQLite ou Postgres.

4.  **Interface de Chat Real:**
    *   Integrar com Slack API ou Discord para simular uma "War Room" real.
