from langchain_core.tools import tool
from app.rag import rag_engine

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
