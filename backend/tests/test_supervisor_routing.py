import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node

@pytest.mark.parametrize("query, expected_agent", [
    ("Check pods status", "K8s_Specialist"),
    ("My website is slow", "Traefik_Specialist"),
    ("Database connection refused", "GCP_Specialist"),
    ("High latency in backend", "Datadog_Specialist"),
    ("Fix this bug in main.py", "Code_Specialist"),
    ("Deploy to production failed", "CICD_Specialist"),
    ("Create an incident for this outage", "Incident_Specialist"),
    ("Scan for vulnerabilities", "Security_Specialist"),
    ("What services call the payment API?", "Topology_Specialist"),
    ("Execute the restart runbook", "Automation_Specialist"),
])
def test_supervisor_routing_logic(query, expected_agent):
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        class MockRouterSchema:
            def __init__(self, agent):
                self.next_agent = agent
                self.reasoning = "Test"
        mock_chain.invoke.return_value = MockRouterSchema(expected_agent)
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        state = {"messages": [HumanMessage(content=query)]}
        result = supervisor_node(state)
        assert result["next"] == expected_agent

def test_supervisor_fallback_on_error():
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("error")
        mock_chain.__or__.return_value = mock_chain
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain
        state = {"messages": [HumanMessage(content="Break")]}
        result = supervisor_node(state)
        assert result["next"] == "Topology_Specialist"
