import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph import supervisor_node, app_graph
from app.state import AgentState
import os

# Define a mock schema that matches RouterSchema structure
class MockDecision:
    def __init__(self, next_agent, reasoning="Testing"):
        self.next_agent = next_agent
        self.reasoning = reasoning

@patch("app.graph.llm")
@patch("app.tools.incident.SessionLocal")  # Mock DB for incident creation
def test_complex_troubleshooting(mock_session_local, mock_llm):
    """
    Simulates a full troubleshooting session with mocked Supervisor decisions.
    We force the path: Topology -> Azion -> Incident.
    We let the actual tool logic run (using mocks/safe tools where possible).
    """

    # Setup Mock DB
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # We mock the chain: prompt | llm.with_structured_output(RouterSchema)
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # Setup chain mock
        mock_chain = MagicMock()
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        # Sequence of Supervisor decisions
        mock_chain.invoke.side_effect = [
            MockDecision("Topology_Specialist", "Request is vague, scanning infra."),
            MockDecision("Azion_Specialist", "Topology found latency, checking edge."),
            MockDecision("Incident_Specialist", "Azion found WAF issue, creating incident."),
            MockDecision("FINISH", "Incident created, done.")
        ]

        # We also need to ensure we are using MOCK tools for observability/k8s/etc
        # to avoid real API calls or errors.
        # However, app.graph tools are already loaded.
        # But 'scan_infrastructure' calls tools dynamically.
        # We can patch 'app.tools.list_k8s_pods.invoke' etc because they are functions/attributes.
        # Or better: just let them run. If they are real tools, they might fail without creds.

        # We can use the environment variable USE_REAL_TOOLS=false to ensure safe mocks are used
        # BUT we must reload imports or rely on dynamic imports.
        # `scan_infrastructure` imports `list_k8s_pods` inside the function.
        # So if we patch `app.tools.list_k8s_pods` variable, it works.

        # Let's patch the tools that `scan_infrastructure` uses.
        # Note: We must patch the *Tool Object* in `app.tools`.
        # Since we can't patch `.invoke`, we patch the object itself in the module.

        with patch("app.tools.list_k8s_pods") as mock_k8s, \
             patch("app.tools.check_gcp_status") as mock_gcp, \
             patch("app.tools.query_gmp_prometheus") as mock_gmp, \
             patch("app.tools.get_active_alerts") as mock_dd, \
             patch("app.tools.check_azion_edge") as mock_azion:

            # Configure mocks to return strings (so invoke() works)
            # When the tool is called as tool.invoke(arg), it returns...
            # But the tool object is a StructuredTool.
            # If we replace it with a MagicMock, mock.invoke(...) works.

            mock_k8s.invoke.return_value = "K8s: All Systems Go"
            mock_gcp.invoke.return_value = "GCP: Operational"
            mock_gmp.invoke.return_value = "GMP: Up"
            mock_dd.invoke.return_value = "Datadog: No Alerts"
            mock_azion.invoke.return_value = "Azion: WAF Blocking (Simulated)"

            # Step 1: Supervisor Decision 1
            state = {"messages": [HumanMessage(content="System is slow")]}
            result1 = supervisor_node(state)
            assert result1["next"] == "Topology_Specialist"

            # Step 2: Simulate Topology Execution
            # We can run the actual tool since we patched its dependencies!
            # Import it here to ensure we get the right one
            from app.tools.observability import scan_infrastructure

            # scan_infrastructure calls the tools we patched above.
            scan_res = scan_infrastructure.invoke({})
            assert "Infrastructure Scan Report" in scan_res
            state["messages"].append(SystemMessage(content=scan_res))

            # Step 3: Supervisor Decision 2
            result2 = supervisor_node(state)
            assert result2["next"] == "Azion_Specialist"

            # Step 4: Simulate Azion Execution
            # The Azion_Specialist uses `check_azion_edge`.
            # In the graph, `Azion_Specialist` holds a reference to the tool.
            # That reference is likely the real tool (if imports happened before patch).
            # But we patched `app.tools.check_azion_edge`.
            # If `Azion_Specialist` uses `check_azion_edge` from `app.tools`, and it was imported...

            # Let's just simulate the message since we can't easily change the graph node's internal tool.
            state["messages"].append(SystemMessage(content="Azion: WAF Blocking (Simulated)"))

            # Step 5: Supervisor Decision 3
            result3 = supervisor_node(state)
            assert result3["next"] == "Incident_Specialist"

            # Step 6: Simulate Incident Execution
            # We use create_incident.invoke. We patched SessionLocal so it's safe.
            from app.tools.incident import create_incident

            inc_res = create_incident.invoke({
                "title": "Azion WAF Issue",
                "severity": "High",
                "description": "Blocking legitimate traffic"
            })
            assert "Incident created successfully" in inc_res
            state["messages"].append(SystemMessage(content=inc_res))

            # Step 7: Supervisor Decision 4
            result4 = supervisor_node(state)
            assert result4["next"] == "FINISH"
