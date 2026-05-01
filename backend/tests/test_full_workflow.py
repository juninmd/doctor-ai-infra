import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph import supervisor_node, app_graph
from app.state import AgentState
import os

class MockDecision:
    def __init__(self, next_agent, reasoning="Testing"):
        self.next_agent = next_agent
        self.reasoning = reasoning

@patch("app.graph.llm")
@patch("app.tools.incident.SessionLocal")
def test_complex_troubleshooting(mock_session_local, mock_llm):
    """
    Simulates a full troubleshooting session with mocked Supervisor decisions.
    We force the path: Topology -> Traefik -> Incident.
    """
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        mock_chain.invoke.side_effect = [
            MockDecision("Topology_Specialist", "Request is vague, scanning infra."),
            MockDecision("Traefik_Specialist", "Topology found latency, checking ingress."),
            MockDecision("Incident_Specialist", "Traefik found routing issue, creating incident."),
            MockDecision("FINISH", "Incident created, done.")
        ]

        with patch("app.tools.list_k8s_pods") as mock_k8s, \
             patch("app.tools.check_gcp_status") as mock_gcp, \
             patch("app.tools.query_gmp_prometheus") as mock_gmp, \
             patch("app.tools.get_active_alerts") as mock_dd, \
             patch("app.tools.check_traefik_health") as mock_traefik:

            mock_k8s.invoke.return_value = "K8s: All Systems Go"
            mock_gcp.invoke.return_value = "GCP: Operational"
            mock_gmp.invoke.return_value = "GMP: Up"
            mock_dd.invoke.return_value = "Datadog: No Alerts"
            mock_traefik.invoke.return_value = "🟢 Traefik: Active"

            state = {"messages": [HumanMessage(content="System is slow")]}
            result1 = supervisor_node(state)
            assert result1["next"] == "Topology_Specialist"

            from app.tools.observability import scan_infrastructure
            scan_res = scan_infrastructure.invoke({})
            assert "Infrastructure Scan Report" in scan_res
            state["messages"].append(SystemMessage(content=scan_res))

            result2 = supervisor_node(state)
            assert result2["next"] == "Traefik_Specialist"

            state["messages"].append(SystemMessage(content="Traefik: Backend Service Unreachable (Simulated)"))

            result3 = supervisor_node(state)
            assert result3["next"] == "Incident_Specialist"

            from app.tools.incident import create_incident
            inc_res = create_incident.invoke({
                "title": "Traefik Ingress Issue",
                "severity": "High",
                "description": "Backend unreachable"
            })
            assert "Incident created successfully" in inc_res
            state["messages"].append(SystemMessage(content=inc_res))

            result4 = supervisor_node(state)
            assert result4["next"] == "FINISH"
