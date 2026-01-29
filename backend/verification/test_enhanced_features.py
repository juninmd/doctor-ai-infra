import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

# Set MOCK env var BEFORE importing tools that depend on it
os.environ["USE_REAL_TOOLS"] = "false"

from app.tools.incident import create_incident, log_incident_event, build_incident_timeline
# Import directly from mocks to ensure we test the mock logic regardless of env vars/import caching
from app.tools.mocks import trace_service_health

def test_incident_flow():
    print("--- Testing Incident Flow ---")
    # 1. Create Incident
    res = create_incident.invoke({"title": "Frontend Crash", "severity": "SEV-1", "description": "Users seeing 500s"})
    print(f"Create: {res}")
    # Extract ID. Output format: "Incident created successfully. ID: XXXXXXXX"
    try:
        incident_id = res.split("ID: ")[1].strip()
    except:
        print("Failed to parse ID")
        return

    # 2. Log Hypothesis
    res = log_incident_event.invoke({
        "incident_id": incident_id,
        "event_type": "Hypothesis",
        "content": "Database connection failure causing crash loop.",
        "source": "K8s_Specialist"
    })
    print(f"Log 1: {res}")

    # 3. Log Evidence
    res = log_incident_event.invoke({
        "incident_id": incident_id,
        "event_type": "Evidence",
        "content": "Logs show 'ConnectionRefusedError: POST https://postgres-db:5432'",
        "source": "K8s_Specialist"
    })
    print(f"Log 2: {res}")

    # 4. Build Timeline
    timeline = build_incident_timeline.invoke({"incident_id": incident_id})
    print(f"\nTimeline Preview:\n{timeline}")

    assert "Frontend Crash" in timeline
    assert "Database connection failure" in timeline
    assert "ConnectionRefusedError" in timeline

def test_tracing():
    print("\n--- Testing Service Tracing ---")
    # 1. Trace Frontend
    # This should use the mock implementation in mocks.py because USE_REAL_TOOLS=false
    trace = trace_service_health.invoke({"service_name": "frontend-web", "depth": 1})
    print(f"Trace:\n{trace}")

    assert "Root: frontend-web" in trace
    # The mock output for frontend should include crash info
    assert "CrashLoopBackOff" in trace or "Database connection failed" in trace

if __name__ == "__main__":
    test_incident_flow()
    test_tracing()
