import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph import supervisor_node
from app.state import AgentState
from app.tools.observability import scan_infrastructure
from app.tools.runbooks import execute_runbook
from app.tools.incident import create_incident

# --- Test 1: Supervisor Smart Routing ---
@patch("app.graph.llm")
def test_supervisor_smart_routing(mock_llm):
    """
    Verifies that the Supervisor routes correctly based on the prompt instructions.
    Since we mock the LLM, we are verifying the *integration* of the prompt and structured output chain.
    """
    # Mocking the chain: prompt | llm.with_structured_output
    # We patch ChatPromptTemplate in app.graph to intercept the chain creation
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # partial() returns the prompt instance
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance

        # prompt | llm returns the chain
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        # Scenario A: Latency -> Azion
        class DecisionAzion:
            next_agent = "Azion_Specialist"
            reasoning = "Latency issues usually start at the edge."

        mock_chain.invoke.return_value = DecisionAzion()

        state = {"messages": [HumanMessage(content="High latency detected")]}
        result = supervisor_node(state)
        assert result["next"] == "Azion_Specialist"

        # Scenario B: Pod -> K8s
        class DecisionK8s:
            next_agent = "K8s_Specialist"
            reasoning = "Pod crash."

        mock_chain.invoke.return_value = DecisionK8s()
        state = {"messages": [HumanMessage(content="My pod is crashing")]}
        result = supervisor_node(state)
        assert result["next"] == "K8s_Specialist"


# --- Test 2: Infrastructure Scan Aggregation ---
@patch("app.tools.list_k8s_pods")
@patch("app.tools.check_gcp_status")
@patch("app.tools.query_gmp_prometheus")
@patch("app.tools.get_active_alerts")
@patch("app.tools.check_azion_edge")
def test_scan_infrastructure_aggregation(mock_azion, mock_alerts, mock_gmp, mock_gcp, mock_k8s):
    """
    Verifies scan_infrastructure collects data from all sources and produces a report.
    """
    # Setup mocks
    mock_k8s.invoke.return_value = "K8s: All Good"
    mock_gcp.invoke.return_value = "GCP: Stable"
    mock_gmp.invoke.return_value = "GMP: Up"
    mock_alerts.invoke.return_value = "No active alerts"
    mock_azion.invoke.return_value = "Azion: Active"

    # Run tool
    result = scan_infrastructure.invoke({})

    # Assertions
    assert "Infrastructure Scan Report" in result
    assert "Kubernetes:" in result
    assert "GCP: Stable" in result
    assert "GMP:" in result
    assert "Datadog:" in result
    assert "Azion:" in result
    # Check for hidden JSON block (Frontend Integration)
    assert "```json" in result

# --- Test 3: Runbook Safety (Dry Run) ---
@patch("app.tools.runbooks.SessionLocal")
def test_execute_runbook_safety(mock_session_local):
    """
    Verifies execute_runbook returns a dry-run message when dry_run=True,
    and actually executes (mocks DB/K8s) when dry_run=False.
    """
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Mock Service and Runbook in DB
    mock_service = MagicMock()
    mock_service.name = "payment-api"
    # Need to match the expected runbook name in the service.runbooks list
    mock_r = MagicMock()
    mock_r.name = "restart_service"
    mock_service.runbooks = [mock_r]

    mock_runbook = MagicMock()
    mock_runbook.name = "restart_service"
    mock_runbook.description = "Restarts pods"

    # Setup side_effect for db.query(Model)
    # This is simplified; usually we need to match the filter logic too
    # But for this unit test, we can just return a mock query object that returns the right thing

    mock_query = MagicMock()
    mock_db.query.return_value = mock_query

    # We use a side effect on filter to return different things based on what we expect
    # But simpler: assume the code calls query(Service) then filter...
    # Let's rely on the fact that the tool calls query(Service) first, then query(Runbook)
    # We can mock the returns in sequence if we want, or just generic valid objects.

    # Actually, the tool does:
    # service = db.query(Service).filter(...).first()
    # runbook = db.query(Runbook).filter(...).first()

    # So filter().first() needs to return:
    # 1. Service
    # 2. Runbook

    mock_query.filter.return_value.first.side_effect = [mock_service, mock_runbook]

    # Case 1: Dry Run
    result = execute_runbook.invoke({
        "runbook_name": "restart_service",
        "target_service": "payment-api",
        "dry_run": True
    })
    assert "[DRY RUN]" in result
    assert "Would execute runbook 'restart_service'" in result

    # Reset side effect for next call
    mock_query.filter.return_value.first.side_effect = [mock_service, mock_runbook]

    # Case 2: Real Run (Mocked K8s)
    with patch("app.tools.runbooks._get_k8s_client") as mock_k8s_client_getter:
        mock_k8s = MagicMock()
        mock_k8s_client_getter.return_value = mock_k8s

        # Mock pod listing
        mock_pod = MagicMock()
        mock_pod.metadata.name = "pod-1"
        mock_k8s.list_namespaced_pod.return_value.items = [mock_pod]

        result = execute_runbook.invoke({
            "runbook_name": "restart_service",
            "target_service": "payment-api",
            "dry_run": False
        })

        # The tool output for restart_service contains "K8s: Deleted X pods"
        assert "K8s: Deleted 1 pods" in result
        mock_k8s.delete_namespaced_pod.assert_called_with("pod-1", "default")


# --- Test 4: Incident Management ---
@patch("app.tools.incident.SessionLocal")
def test_incident_creation(mock_session_local):
    """
    Verifies that creating an incident writes to the DB.
    """
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    result = create_incident.invoke({
        "title": "DB Down",
        "severity": "SEV-1",
        "description": "Database is unreachable"
    })

    assert "Incident created successfully" in result

    # Verify add() was called (for Incident and Event)
    assert mock_db.add.call_count >= 1
    # Verify commit() was called
    mock_db.commit.assert_called()
