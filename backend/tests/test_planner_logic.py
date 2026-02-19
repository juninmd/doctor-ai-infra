import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import supervisor_node, RouterSchema

@patch("app.graph.llm")
def test_supervisor_routes_to_planner(mock_llm):
    # Mock the structured output chain
    mock_chain = MagicMock()
    # Mock decision to route to Planner
    mock_decision = RouterSchema(reasoning="Complex issue, need a plan.", next_agent="Planner_Specialist")
    mock_chain.invoke.return_value = mock_decision

    # Mock the chain creation
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        # Test state
        state = {"messages": [HumanMessage(content="I have a weird latency issue across multiple services. I don't know where to start.")]}

        # Invoke supervisor
        result = supervisor_node(state)

        # Verify
        assert result["next"] == "Planner_Specialist"
