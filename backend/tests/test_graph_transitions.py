import pytest
from unittest.mock import patch
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node

def test_supervisor_routes_to_k8s_specialist():
    """
    Test that the supervisor_node routes to the K8s_Specialist
    when the query mentions pods, containers, or large log analysis.
    """
    state = {"messages": [HumanMessage(content="My pod is crashing, can you analyze the logs?")]}

    with patch("app.graph.llm") as mock_llm:
        mock_chain = mock_llm.with_structured_output.return_value
        class MockDecision:
            next_agent = "K8s_Specialist"
            reasoning = "Test reasoning"

        mock_chain.invoke.return_value = MockDecision()

        # We need to test the fallback path as well, so if with_structured_output raises, we catch it
        mock_llm.with_structured_output.side_effect = Exception("Not supported")

        # Mock the whole fallback chain
        with patch("app.graph.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_chain_fallback = mock_prompt.return_value.partial.return_value.__or__.return_value.__or__.return_value
            mock_chain_fallback.invoke.return_value = {"next_agent": "K8s_Specialist", "reasoning": "testing"}
            result = supervisor_node(state)
            assert result["next"] == "K8s_Specialist"

def test_supervisor_routes_to_gcp_specialist():
    """
    Test that the supervisor_node routes to the GCP_Specialist
    when the query is about Cloud/VMs, SQL, GMP, or Cost.
    """
    state = {"messages": [HumanMessage(content="What is the estimated cost of our GCP infrastructure?")]}

    with patch("app.graph.llm") as mock_llm:
        mock_llm.with_structured_output.side_effect = Exception("Not supported")

        # Mock the whole fallback chain
        with patch("app.graph.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_chain_fallback = mock_prompt.return_value.partial.return_value.__or__.return_value.__or__.return_value
            mock_chain_fallback.invoke.return_value = {"next_agent": "GCP_Specialist", "reasoning": "testing"}
            result = supervisor_node(state)
            assert result["next"] == "GCP_Specialist"

def test_supervisor_routes_to_finish():
    """
    Test that the supervisor_node routes to FINISH
    when the task is complete.
    """
    state = {"messages": [HumanMessage(content="Thanks, that fixed the issue!")]}

    with patch("app.graph.llm") as mock_llm:
        mock_llm.with_structured_output.side_effect = Exception("Not supported")

        # Mock the whole fallback chain
        with patch("app.graph.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_chain_fallback = mock_prompt.return_value.partial.return_value.__or__.return_value.__or__.return_value
            mock_chain_fallback.invoke.return_value = {"next_agent": "FINISH", "reasoning": "testing"}
            result = supervisor_node(state)
            assert result["next"] == "FINISH"
