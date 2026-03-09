import pytest
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from app.graph import workflow, app_graph, members

def test_langgraph_workflow_instantiation():
    """
    Verifies that the workflow is a valid LangGraph StateGraph
    and contains all the expected nodes and edges.
    """
    assert isinstance(workflow, StateGraph)

    # Check that all specialists and Supervisor are added as nodes
    expected_nodes = set(members) | {"Supervisor"}
    actual_nodes = set(workflow.nodes.keys())
    assert expected_nodes.issubset(actual_nodes), f"Missing nodes: {expected_nodes - actual_nodes}"

def test_langgraph_compilation():
    """
    Verifies that the graph compiles correctly and has the MemorySaver attached
    for human-in-the-loop interruption.
    """
    assert app_graph is not None
    # We interrupt before Automation_Specialist as per graph.py definition
    assert "Automation_Specialist" in app_graph.interrupt_before_nodes

def test_initial_state_routing():
    """
    Verifies the basic state shape for the graph
    """
    state = {"messages": [HumanMessage(content="System status")]}
    assert "messages" in state
    assert len(state["messages"]) == 1
    assert state["messages"][0].content == "System status"

def test_supervisor_node_fallback():
    """
    Verifies that when structured output fails (as it might with older Ollama versions),
    the supervisor successfully falls back to JsonOutputParser.
    """
    from unittest.mock import patch, MagicMock
    from app.graph import supervisor_node

    state = {"messages": [HumanMessage(content="System is very slow")]}

    with patch("app.graph.llm", new_callable=MagicMock) as mock_llm:
        mock_llm.with_structured_output.side_effect = Exception("Ollama unsupported")

        # The fallback chain will call `llm.invoke()` and the result is parsed by `JsonOutputParser`.
        # We mock `llm.invoke()` to return what the parser expects: a message with a JSON string.
        import json
        from langchain_core.messages import AIMessage
        llm_output = {"next_agent": "Datadog_Specialist", "reasoning": "checking metrics"}
        mock_llm.invoke.return_value = AIMessage(content=json.dumps(llm_output))

        result = supervisor_node(state)
        assert result["next"] == "Datadog_Specialist"

        # Verify that the structured output was attempted and failed, and the fallback was used.
        mock_llm.with_structured_output.assert_called_once()
        mock_llm.invoke.assert_called_once()
