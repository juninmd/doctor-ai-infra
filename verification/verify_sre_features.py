import sys
import os
from unittest.mock import MagicMock
from langchain_core.runnables import RunnableLambda

sys.path.append(os.path.join(os.getcwd(), "backend"))

class MockMessage:
    content = "# Post-Mortem Report\n\n**Root Cause:** Redis Cache Failure.\n\n**Action Items:**\n- Scale Redis."

def fake_llm_func(input):
    return MockMessage()

# Mock LLM as a Runnable
mock_llm = RunnableLambda(fake_llm_func)

# We need to inject this into app.tools.incident
import app.tools.incident
import app.llm
app.tools.incident.get_llm = lambda: mock_llm

from app.db import init_db
from app.tools.incident import create_incident, update_incident_status, generate_postmortem
from app.tools.runbooks import get_service_topology, get_service_dependencies
from app.tools.knowledge import search_knowledge_base

def verify():
    print("Initializing DB...")
    init_db()

    print("\n--- 1. Topology Check ---")
    topo = get_service_topology.invoke({"service_name": "payment-api"})
    print(f"Topology:\n{topo}")
    assert "auth-service" in topo

    deps = get_service_dependencies.invoke({"service_name": "payment-api"})
    print(f"Dependencies:\n{deps}")
    assert "payment-db" in deps

    print("\n--- 2. Incident Management ---")
    res = create_incident.invoke({"title": "Payment API High Latency", "severity": "SEV-2", "description": "500 errors and latency > 2s."})
    print(res)
    assert "ID:" in res
    incident_id = res.split("ID: ")[1].strip()

    print("\n--- 3. Knowledge Search ---")
    # Search for "payment"
    search_res = search_knowledge_base.invoke({"query": "payment"})
    print(f"Search Result:\n{search_res}")
    assert "payment-api" in search_res or "Payment API" in search_res

    print("\n--- 4. Post-Mortem Generation ---")
    update_incident_status.invoke({"incident_id": incident_id, "status": "RESOLVED", "update_message": "Restarted service."})

    pm_res = generate_postmortem.invoke({"incident_id": incident_id})
    print(f"PM Result:\n{pm_res}")
    assert "Post-Mortem generated" in pm_res

    print("\n--- Verification Successful ---")

if __name__ == "__main__":
    verify()
