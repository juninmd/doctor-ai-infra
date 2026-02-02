import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

@patch("app.graph.llm")
def test_full_flow_k8s(mock_llm):
    # Setup mock behavior for structured output
    # The Supervisor now uses llm.with_structured_output(RouterSchema)

    # Strategy: Patch ChatPromptTemplate so we can control the pipe result.
    # This avoids dealing with MagicMock __ror__ ambiguity or complex chain piping.

    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # 1. Setup the Prompt Mock
        mock_prompt_instance = MockPrompt.from_messages.return_value
        # partial() returns self
        mock_prompt_instance.partial.return_value = mock_prompt_instance

        # 2. Setup the Chain Mock
        # When (prompt | llm.with_structured_output) happens, return mock_chain
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        # 3. Setup the Decision Result
        # Create a plain object (not a mock) to hold the data, so property access is simple
        class Decision:
            next_agent = "K8s_Specialist"
            reasoning = "Test reasoning"

        mock_decision = Decision()

        # 4. Configure chain.invoke to return the decision
        mock_chain.invoke.return_value = mock_decision

        # 5. Mock bind_tools for agents (used later in graph compilation if needed)
        mock_llm.bind_tools.return_value = mock_llm

        # 6. Run the test
        from app.graph import supervisor_node
        from app.state import AgentState

        state: AgentState = {
            "messages": [HumanMessage(content="Check my pods")],
            "next": ""
        }

        result = supervisor_node(state)

        # Assert
        assert result["next"] == "K8s_Specialist"
        print("Supervisor correctly routed to K8s_Specialist")
