from langchain_core.tools import tool
from app.db import SessionLocal, Incident, PostMortem
from app.tools.runbooks import RUNBOOKS, SERVICE_CATALOG

@tool
def search_knowledge_base(query: str) -> str:
    """
    Searches the SRE Knowledge Base (Past Incidents, Runbooks, Service Catalog)
    for relevant information.
    Args:
        query: The search terms (e.g., "payment api latency" or "database connection error").
    """
    results = []
    query_lower = query.lower()

    # 1. Search Incidents (DB)
    db = SessionLocal()
    try:
        # Fetch resolved incidents (limit to 20 for performance in this mock)
        incidents = db.query(Incident).filter(Incident.status != 'OPEN').limit(20).all()
        for inc in incidents:
            content = (inc.title + " " + inc.description + " " + (inc.updates or "")).lower()

            # Simple scoring: check if query words are in content
            score = 0
            words = query_lower.split()
            for w in words:
                if w in content:
                    score += 1

            # If match is decent (e.g. all words or 50%+)
            if score >= len(words) * 0.5:
                res_str = f"[Past Incident] {inc.title} (ID: {inc.id}) - {inc.status}"
                if inc.post_mortem:
                    res_str += " [HAS POST-MORTEM]"
                results.append(res_str)

    except Exception as e:
        results.append(f"Error searching DB: {str(e)}")
    finally:
        db.close()

    # 2. Search Runbooks
    for name, desc in RUNBOOKS.items():
        if query_lower in name.lower() or query_lower in desc.lower():
             results.append(f"[Runbook] {name}: {desc}")

    # 3. Search Catalog
    for name, details in SERVICE_CATALOG.items():
        content = str(details).lower()
        if query_lower in name.lower() or query_lower in content:
            results.append(f"[Service] {name}: {details.get('description')} (Owner: {details.get('owner')})")

    if not results:
        return f"No results found for '{query}' in Knowledge Base."

    # Deduplicate and return
    return "\n".join(list(set(results))[:10])
