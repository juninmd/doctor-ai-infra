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
    """
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        # Scenario A: Latency -> Traefik
        class DecisionTraefik:
            next_agent = "Traefik_Specialist"
            reasoning = "Latency issues usually start at ingress/routing."

        mock_chain.invoke.return_value = DecisionTraefik()

        state = {"messages": [HumanMessage(content="High latency detected")]}
        result = supervisor_node(state)
        assert result["next"] == "Traefik_Specialist"

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
@patch("app.tools.check_traefik_health")
def test_scan_infrastructure_aggregation(mock_traefik, mock_alerts, mock_gmp, mock_gcp, mock_k8s):
    """
    Verifies scan_infrastructure collects data from all sources and produces a report.
    """
    mock_k8s.invoke.return_value = "K8s: All Good"
    mock_gcp.invoke.return_value = "GCP: Stable"
    mock_gmp.invoke.return_value = "GMP: Up"
    mock_alerts.invoke.return_value = "No active alerts"
    mock_traefik.invoke.return_value = "🟢 Traefik: Active"

    result = scan_infrastructure.invoke({})

    assert "Infrastructure Scan Report" in result
    assert "Kubernetes:" in result
    assert "GCP: Stable" in result
    assert "GMP:" in result
    assert "Datadog:" in result
    assert "Traefik:" in result
    assert "```json" in result

# --- Test 3: Runbook Safety (Dry Run) ---
@patch("app.tools.runbooks.SessionLocal")
def test_execute_runbook_safety(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_service = MagicMock()
    mock_service.name = "payment-api"
    mock_r = MagicMock()
    mock_r.name = "restart_service"
    mock_service.runbooks = [mock_r]
    mock_runbook = MagicMock()
    mock_runbook.name = "restart_service"
    mock_runbook.description = "Restarts pods"
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.side_effect = [mock_service, mock_runbook]

    result = execute_runbook.invoke({
        "runbook_name": "restart_service",
        "target_service": "payment-api",
        "dry_run": True
    })
    assert "[DRY RUN]" in result
    assert "Would execute runbook 'restart_service'" in result

    mock_query.filter.return_value.first.side_effect = [mock_service, mock_runbook]
    with patch("app.tools.runbooks._get_k8s_client") as mock_k8s_client_getter:
        mock_k8s = MagicMock()
        mock_k8s_client_getter.return_value = mock_k8s
        mock_pod = MagicMock()
        mock_pod.metadata.name = "pod-1"
        mock_k8s.list_namespaced_pod.return_value.items = [mock_pod]

        result = execute_runbook.invoke({
            "runbook_name": "restart_service",
            "target_service": "payment-api",
            "dry_run": False
        })
        assert "K8s: Deleted 1 pods" in result
        mock_k8s.delete_namespaced_pod.assert_called_with("pod-1", "default")


# --- Test 4: Incident Management ---
@patch("app.tools.incident.SessionLocal")
def test_incident_creation(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    result = create_incident.invoke({
        "title": "DB Down",
        "severity": "SEV-1",
        "description": "Database is unreachable"
    })
    assert "Incident created successfully" in result
    assert mock_db.add.call_count >= 1
    mock_db.commit.assert_called()
