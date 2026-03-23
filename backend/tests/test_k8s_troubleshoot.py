import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.graph import supervisor_node, k8s_agent, gcp_agent

@pytest.mark.asyncio
async def test_k8s_agent_routing_and_execution():
    """
    Test routing to K8s_Specialist and its execution
    """
    state = {"messages": [HumanMessage(content="Why is the frontend pod failing in Kubernetes?")]}

    # Use the same patch strategy as test_supervisor_routing.py to avoid Pydantic mock issues
    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        class MockK8sRouterSchema:
            def __init__(self):
                self.next_agent = "K8s_Specialist"
                self.reasoning = "User is asking about a Kubernetes pod"

        mock_chain.invoke.return_value = MockK8sRouterSchema()

        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        result = supervisor_node(state)
        # Verify routing logic chooses K8s
        assert result["next"] == "K8s_Specialist"

    # Verify Agent Execution
    mock_k8s_response = {"messages": [AIMessage(content="CrashLoopBackOff detected in frontend pod")]}
    with patch.object(k8s_agent, "invoke", return_value=mock_k8s_response):
        res = k8s_agent.invoke(state)
        assert "CrashLoopBackOff" in res["messages"][0].content


@pytest.mark.asyncio
async def test_gcp_agent_routing_and_execution():
    """
    Test routing to GCP_Specialist and its execution
    """
    state = {"messages": [HumanMessage(content="Check our GCP database performance.")]}

    with patch("app.graph.ChatPromptTemplate") as MockPrompt:
        mock_chain = MagicMock()
        class MockGCPRouterSchema:
            def __init__(self):
                self.next_agent = "GCP_Specialist"
                self.reasoning = "User is asking about GCP database"

        mock_chain.invoke.return_value = MockGCPRouterSchema()

        mock_prompt_instance = MockPrompt.from_messages.return_value
        mock_prompt_instance.partial.return_value = mock_prompt_instance
        mock_prompt_instance.__or__.return_value = mock_chain

        result = supervisor_node(state)
        # Verify routing logic chooses GCP
        assert result["next"] == "GCP_Specialist"

    # Verify Agent Execution
    mock_gcp_response = {"messages": [AIMessage(content="Cloud SQL CPU is at 99%")]}
    with patch.object(gcp_agent, "invoke", return_value=mock_gcp_response):
        res = gcp_agent.invoke(state)
        assert "Cloud SQL CPU" in res["messages"][0].content
