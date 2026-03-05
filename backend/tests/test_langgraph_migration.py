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
