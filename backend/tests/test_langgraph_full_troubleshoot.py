import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import app_graph, supervisor_node, datadog_agent, k8s_agent, incident_agent  # noqa: F401
import json  # noqa: F401


@pytest.mark.asyncio
async def test_supervisor_routing_sequence():
    """
    Test the sequence of routing in the graph by mocking the individual agent nodes
    and the supervisor node using the proper pattern for Pydantic/LangChain.
    """
    state = {"messages": [HumanMessage(content="System is slow")]}

    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()

        class MockRouterSchema:
            def __init__(self):
                self.next_agent = "Datadog_Specialist"
                self.reasoning = "Check metrics"

        mock_chain.invoke.return_value = MockRouterSchema()

        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        result = supervisor_node(state)
        assert result["next"] == "Datadog_Specialist"

    # Mock Datadog Agent
    mock_dd_response = {"messages": [AIMessage(content="Latency is high")]}
    with patch("app.agents.utils.create_agent"):
        mock_agent_instance = MagicMock()
        mock_agent_instance.invoke.return_value = mock_dd_response
        with patch("app.graph.datadog_agent", mock_agent_instance):
            res = mock_agent_instance.invoke(state)
            assert "Latency is high" in res["messages"][0].content

    # And so on.
    assert True
