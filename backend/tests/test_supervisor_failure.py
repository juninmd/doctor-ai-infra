import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, SystemMessage

@patch("app.graph.llm")
def test_supervisor_failure_fallback(mock_llm):
    # Strategy: Patch ChatPromptTemplate so we can control the pipe result.
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # 1. Setup the Prompt Mock
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance

        # 2. Setup the Chain Mock
        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain

        # 3. Configure chain.invoke to raise an exception
        mock_chain.invoke.side_effect = Exception("Simulated LLM Failure")

        # Ensure fallback chain also fails (so we hit the final safety net)
        # fallback_chain = prompt | llm | parser
        # prompt | llm returns mock_chain.
        # mock_chain | parser needs to return something that raises on invoke.
        # Let's make it return mock_chain itself.
        mock_chain.__or__.return_value = mock_chain

        # 4. Run the test
        from app.graph import supervisor_node
        from app.state import AgentState

        state: AgentState = {
            "messages": [HumanMessage(content="Check system status")],
            "next": ""
        }

        result = supervisor_node(state)

        # Assert
        assert result["next"] == "Topology_Specialist"
        assert "messages" in result
        assert isinstance(result["messages"][0], SystemMessage)
        assert "Simulated LLM Failure" in result["messages"][0].content
        print("Supervisor correctly fell back to Topology_Specialist on error")
