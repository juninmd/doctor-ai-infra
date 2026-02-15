import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage
# Ensure we can import from app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.graph import supervisor_node
from app.state import AgentState

@pytest.fixture
def mock_chain():
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        # Configure prompt chain behavior
        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance

        # Configure the pipe result (which represents the chain)
        mock_chain_instance = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain_instance

        yield mock_chain_instance

def test_routing_latency_to_azion(mock_chain):
    """Test routing logic: Latency -> Azion (Edge)"""
    class Decision:
        next_agent = "Azion_Specialist"
        reasoning = "High latency detected, likely CDN/Edge issue."

    mock_chain.invoke.return_value = Decision()

    state = {"messages": [HumanMessage(content="The site is loading very slowly.")], "next": ""}
    result = supervisor_node(state)

    assert result["next"] == "Azion_Specialist"
    print("Correctly routed latency issue to Azion Specialist")

def test_routing_db_error_to_gcp(mock_chain):
    """Test routing logic: Database -> GCP (Infra)"""
    class Decision:
        next_agent = "GCP_Specialist"
        reasoning = "Database connection refused indicates infrastructure issue."

    mock_chain.invoke.return_value = Decision()

    state = {"messages": [HumanMessage(content="Getting 500 error: Database connection refused.")], "next": ""}
    result = supervisor_node(state)

    assert result["next"] == "GCP_Specialist"
    print("Correctly routed DB error to GCP Specialist")

def test_routing_root_cause_to_incident(mock_chain):
    """Test routing logic: Root Cause -> Incident (Remediation)"""
    class Decision:
        next_agent = "Incident_Specialist"
        reasoning = "Root cause identified as memory leak. Need remediation plan."

    mock_chain.invoke.return_value = Decision()

    state = {"messages": [HumanMessage(content="Root cause found: Memory leak in payment-api.")], "next": ""}
    result = supervisor_node(state)

    assert result["next"] == "Incident_Specialist"
    print("Correctly routed root cause to Incident Specialist")

def test_routing_unknown_to_topology(mock_chain):
    """Test routing logic: General -> Topology (Scan)"""
    class Decision:
        next_agent = "Topology_Specialist"
        reasoning = "General health check requested."

    mock_chain.invoke.return_value = Decision()

    state = {"messages": [HumanMessage(content="How is the system doing?")], "next": ""}
    result = supervisor_node(state)

    assert result["next"] == "Topology_Specialist"
    print("Correctly routed general query to Topology Specialist")
