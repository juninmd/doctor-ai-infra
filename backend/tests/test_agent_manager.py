import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage
from app.graph import make_specialist

@patch("app.graph.llm")
def test_make_specialist_configuration(mock_llm):
    """
    Verifies that make_specialist creates an agent with the correct system prompt
    and persona configuration.
    """

    # 1. Define Test Data
    test_tools = [MagicMock()]
    test_persona = "Test Persona"
    test_heuristics = "Test Heuristics: Do X, Y, Z."

    # 2. Call the function
    # Note: make_specialist calls create_react_agent, which returns a CompiledGraph.
    # We mock create_react_agent to inspect arguments passed to it.
    with patch("app.graph.create_react_agent") as mock_create_agent:
        mock_graph = MagicMock()
        mock_create_agent.return_value = mock_graph

        agent = make_specialist(test_tools, test_persona, test_heuristics)

        # 3. Verify create_react_agent was called
        mock_create_agent.assert_called_once()

        # Inspect arguments: (llm, tools, prompt=...)
        args, kwargs = mock_create_agent.call_args

        # Verify LLM and Tools
        assert args[0] == mock_llm
        assert args[1] == test_tools

        # Verify System Prompt content
        system_msg = kwargs.get("prompt")
        assert system_msg is not None
        assert "Test Persona" in system_msg
        assert "Test Heuristics: Do X, Y, Z." in system_msg
        assert "Current Year: 2026" in system_msg
        assert "hacker-chic" in system_msg # Tone check

    # 4. Verify return value
    assert agent == mock_graph
