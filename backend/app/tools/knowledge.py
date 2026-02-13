from langchain_core.tools import tool
from app.rag import rag_engine
from app.db import SessionLocal, Service, Runbook
import datetime

@tool
def search_knowledge_base(query: str) -> str:
    """
    Searches the SRE Knowledge Base (Past Incidents, Runbooks, Service Catalog)
    for relevant information using Semantic Search (RAG).

    Args:
        query: The search terms (e.g., "payment api latency" or "database connection error").
    """
    try:
        results = rag_engine.search(query, k=5)

        if not results:
            return f"No relevant information found for '{query}' in the Knowledge Base."

        formatted_results = []
        for doc in results:
            meta = doc.metadata
            source_type = meta.get("type", "unknown").upper()

            # Format based on type for better readability
            if source_type == "RUNBOOK":
                header = f"[{source_type}] {meta.get('name')}"
            elif source_type == "SERVICE":
                header = f"[{source_type}] {meta.get('name')}"
            elif source_type == "INCIDENT":
                header = f"[{source_type}] ID: {meta.get('id')}"
            else:
                header = f"[{source_type}]"

            formatted_results.append(f"{header}\n{doc.page_content}\n")

        return "\n---\n".join(formatted_results)

    except Exception as e:
        return f"Error searching Knowledge Base: {str(e)}"

@tool
def generate_service_catalog_docs() -> str:
    """
    Generates a comprehensive Markdown documentation of the Service Catalog.
    Includes Services, Dependencies, Ownership, and Linked Runbooks.
    Useful for onboarding or system auditing.
    """
    db = SessionLocal()
    try:
        services = db.query(Service).all()

        md = ["# 📖 Service Catalog Documentation"]
        md.append(f"Generated at: {datetime.datetime.now().isoformat()}\n")

        if not services:
            return "Service Catalog is empty. Please bootstrap first."

        for s in services:
            md.append(f"## 🏗️ {s.name}")
            md.append(f"- **Owner:** {s.owner}")
            md.append(f"- **Tier:** {s.tier}")
            md.append(f"- **Description:** {s.description}")
            if s.telemetry_url:
                md.append(f"- **Telemetry:** [Link]({s.telemetry_url})")

            # Dependencies
            deps = [d.name for d in s.dependencies]
            if deps:
                md.append(f"\n### Dependencies")
                for d in deps:
                    md.append(f"- {d}")
            else:
                md.append("\n*No dependencies.*")

            # Runbooks
            if s.runbooks:
                md.append(f"\n### 📚 Available Runbooks")
                for r in s.runbooks:
                    md.append(f"- **{r.name}**: {r.description}")

            md.append("\n---\n")

        return "\n".join(md)
    except Exception as e:
        return f"Error generating docs: {e}"
    finally:
        db.close()
