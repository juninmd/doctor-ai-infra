import pytest
from app.tools.incident import (
    create_incident,
    log_incident_event,
    update_incident_status,
    generate_postmortem,
    generate_remediation_plan,
    list_incidents
)
from app.db import Incident

def test_create_incident(db_session):
    # Tools are StructuredTool objects, verify usage via .invoke
    result = create_incident.invoke({"title": "Database Slow", "severity": "SEV-2", "description": "High latency on primary DB"})
    assert "Incident created successfully" in result

    inc = db_session.query(Incident).first()
    assert inc.title == "Database Slow"
    assert inc.severity == "SEV-2"
    assert inc.status == "OPEN"

def test_incident_workflow(db_session, mock_llm, mock_rag_engine, mock_google_sdk):
    # 1. Create
    res = create_incident.invoke({"title": "API Down", "severity": "SEV-1", "description": "500 errors on /api/v1"})
    # Extract ID (format: "Incident created successfully. ID: XXXXXXXX")
    inc_id = res.split("ID: ")[1].strip()

    # 2. Log Event
    log_res = log_incident_event.invoke({"incident_id": inc_id, "event_type": "Hypothesis", "content": "DB connection pool exhausted", "source": "Human"})
    assert "Logged 'Hypothesis'" in log_res

    # 3. Update Status
    upd_res = update_incident_status.invoke({"incident_id": inc_id, "status": "INVESTIGATING", "update_message": "Checking logs"})
    assert "updated to INVESTIGATING" in upd_res

    # 4. Generate Remediation Plan (Mocked AI)
    # This should use the mock_google_sdk fixture
    plan = generate_remediation_plan.invoke({"incident_context": "Connection refused to Postgres"})
    assert "Generated Remediation Plan" in plan

    # 5. Generate Postmortem (Mocked AI + RAG)
    pm_res = generate_postmortem.invoke({"incident_id": inc_id})
    assert "Post-Mortem generated" in pm_res

    # Verify DB state
    inc = db_session.query(Incident).filter(Incident.id == inc_id).first()
    assert inc.post_mortem is not None
    assert "Mocked Gemini Response" in inc.post_mortem.content

def test_list_incidents(db_session):
    create_incident.invoke({"title": "Inc 1", "severity": "SEV-3", "description": "Minor issue"})
    create_incident.invoke({"title": "Inc 2", "severity": "SEV-1", "description": "Major issue"})

    res = list_incidents.invoke({})
    assert "Inc 1" in res
    assert "Inc 2" in res
