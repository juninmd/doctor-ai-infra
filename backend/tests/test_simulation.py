import pytest
from app.graph import app_graph

def test_graph_structure():
    """
    Verifies that the LangGraph is correctly constructed and compiled.
    """
    assert app_graph is not None

    # Check for critical nodes
    nodes = app_graph.nodes
    expected_nodes = [
        "Supervisor",
        "K8s_Specialist",
        "GCP_Specialist",
        "Incident_Specialist",
        "Topology_Specialist"
    ]

    for node in expected_nodes:
        assert node in nodes, f"Node {node} missing from graph"

    # Check edges exist (implied by compilation success, but good to know)
    # Accessing edges directly depends on LangGraph internals,
    # but successful compilation is the main check.
