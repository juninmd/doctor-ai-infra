import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node

@pytest.mark.parametrize("query, expected_agent", [
    ("Check pods status", "K8s_Specialist"),
    ("My website is slow", "Azion_Specialist"),
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
    """
    Tests that the Supervisor node correctly processes the decision from the LLM.
    We mock the LLM to return the expected agent, verifying the plumbing works.
    """
    # Mock the chain execution
    # structure: chain = prompt | llm.with_structured_output(RouterSchema)

    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # Setup the mock chain
        mock_chain = MagicMock()

        # Create a mock schema object
        class MockRouterSchema:
            def __init__(self, agent):
                self.next_agent = agent
                self.reasoning = "Test reasoning"

        mock_chain.invoke.return_value = MockRouterSchema(expected_agent)

        # Connect the mock chain to the prompt pipe
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        # Create state
        state = {"messages": [HumanMessage(content=query)]}

        # Run node
        result = supervisor_node(state)

        assert result["next"] == expected_agent

def test_supervisor_fallback_on_error():
    """Tests that Supervisor falls back to Topology_Specialist on LLM error."""
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        # Simulate an error
        mock_chain.invoke.side_effect = Exception("Ollama overload")

        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        state = {"messages": [HumanMessage(content="Break me")]}
        result = supervisor_node(state)

        assert result["next"] == "Topology_Specialist"
        assert "Falling back" in str(result["messages"][0].content)
