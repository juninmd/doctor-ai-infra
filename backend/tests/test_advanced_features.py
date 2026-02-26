import pytest
from unittest.mock import MagicMock, patch
from app.db import Incident, PostMortem, Runbook, Service
from app.tools.incident import generate_postmortem, generate_runbook_from_incident
from app.tools.observability import correlate_alerts
from app.tools.runbooks import execute_runbook
from app.rag import rag_engine

@pytest.fixture
def mock_google_sdk():
    client = MagicMock()
    client.models.generate_content.return_value.text = "Mocked AI Response"

    # Patch in incident (module-level import)
    p1 = patch("app.tools.incident.get_google_sdk_client", return_value=client)
    # Patch in llm (source of truth, used by runtime imports in observability)
    p2 = patch("app.llm.get_google_sdk_client", return_value=client)

    with p1, p2:
        yield client

@pytest.fixture
def mock_rag():
    with patch("app.tools.incident.rag_engine") as mock:
        yield mock

def test_generate_postmortem_indexing(db_session, mock_google_sdk, mock_rag, mock_llm):
    # 1. Create resolved incident
    inc = Incident(id="inc-123", title="Test Incident", status="RESOLVED", description="Something broke")
    db_session.add(inc)
    db_session.commit()

    # 2. Call generate_postmortem
    result = generate_postmortem.invoke({"incident_id": "inc-123"})
    print(f"DEBUG: generate_postmortem result: {result}")

    # 3. Verify it was saved to DB
    pm = db_session.query(PostMortem).filter_by(incident_id="inc-123").first()
    assert pm is not None
    assert "Mocked AI Response" in pm.content
    assert "Mocked AI Response" in result

    # 4. Verify it was indexed in RAG
    # The tool calls rag_engine.add_documents
    assert mock_rag.add_documents.called
    args, _ = mock_rag.add_documents.call_args
    assert len(args[0]) == 1
    doc = args[0][0]
    assert doc.metadata["type"] == "post_mortem"
    assert doc.metadata["incident_id"] == "inc-123"

def test_generate_runbook_from_incident(db_session, mock_google_sdk, mock_rag, mock_llm):
    # 1. Setup Incident with PostMortem
    inc = Incident(id="inc-456", title="DB Crash", status="RESOLVED")
    pm = PostMortem(incident_id="inc-456", content="Root Cause: Deadlock. Action: Restart DB.")
    db_session.add(inc)
    db_session.add(pm)
    db_session.commit()

    # 2. Call generate_runbook_from_incident
    result = generate_runbook_from_incident.invoke({"incident_id": "inc-456", "runbook_name": "auto_db_restart"})

    # 3. Verify Runbook created
    rb = db_session.query(Runbook).filter_by(name="auto_db_restart").first()
    assert rb is not None
    assert rb.implementation_key == "manual_steps"
    assert "Mocked AI Response" in rb.content
    assert "Successfully created Runbook" in result

def test_correlate_alerts(mock_google_sdk):
    # 1. Call correlate_alerts with input
    alerts = "Alert 1: High CPU. Alert 2: High Latency."
    result = correlate_alerts.invoke({"alerts_input": alerts})

    # 2. Verify AI response
    assert "Alert Correlation Analysis" in result
    assert "Mocked AI Response" in result

def test_execute_runbook_manual(db_session):
    # 1. Create Manual Runbook
    rb = Runbook(
        name="manual_check",
        description="Check logs manually",
        implementation_key="manual_steps",
        content="1. Login to server.\n2. Run tail -f logs"
    )
    svc = Service(name="test-service", owner="me", description="test", tier="1")
    svc.runbooks.append(rb)
    db_session.add(rb)
    db_session.add(svc)
    db_session.commit()

    # 2. Execute Runbook
    result = execute_runbook.invoke({"runbook_name": "manual_check", "target_service": "test-service"})

    # 3. Verify Output
    assert "**Manual Runbook Execution:**" in result
    assert "1. Login to server." in result
