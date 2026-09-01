from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node
from app.tools.opsmate import opsmate_troubleshooting_workflow
from app.tools.smythos import smythos_unified_resource_manager


from tests.test_langgraph_extra import _create_mock_llm


def test_supervisor_opsmate_routing():
    """Verifies the supervisor correctly routes OpsMate requests."""
    state = {
        "messages": [
            HumanMessage(
                content="Run the OpsMate workflow to diagnose the cluster.")]}

    fake_llm = _create_mock_llm(
        "OpsMate_Specialist",
        "Request requires executing the OpsMate workflow, routing.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "OpsMate_Specialist"


def test_supervisor_smythos_routing():
    """Verifies the supervisor correctly routes SmythOS requests."""
    state = {
        "messages": [
            HumanMessage(
                content="Use the SmythOS manager to read from the VectorDB.")]}

    fake_llm = _create_mock_llm(
        "SmythOS_Specialist",
        "Request involves the SmythOS workflow, routing.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "SmythOS_Specialist"


@patch("app.tools.scan_infrastructure")
@patch("app.tools.list_k8s_pods")
@patch("app.llm.generate_diagnosis")
def test_opsmate_troubleshooting_workflow(
        mock_generate_diagnosis, mock_list_pods, mock_scan_infra):
    """Verifies that the OpsMate workflow returns expected markdown output."""
    mock_scan_infra.invoke.return_value = "Infra is healthy"
    mock_list_pods.invoke.return_value = "No failing pods"
    mock_generate_diagnosis.return_value = "OpsMate Diagnosis: Looks good."

    result = opsmate_troubleshooting_workflow.invoke(
        {"query": "Is everything ok?", "namespace": "default"})

    assert "OpsMate SRE Copilot Analysis" in result
    assert "Is everything ok?" in result
    assert "OpsMate Diagnosis: Looks good." in result


@patch("app.llm.get_llm")
def test_smythos_unified_resource_manager_llm(mock_get_llm):
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value.content = "LLM Response Data"
    mock_get_llm.return_value = mock_llm_instance

    result = smythos_unified_resource_manager.invoke({
        "action": "execute",
        "resource_type": "LLM",
        "resource_name": "TestLLM"
    })

    assert "Response from TestLLM: LLM Response Data" in result


@patch("app.rag.rag_engine")
def test_smythos_unified_resource_manager_vectordb(mock_rag_engine):
    mock_doc = MagicMock()
    mock_doc.page_content = "Document Content"
    mock_rag_engine.search.return_value = [mock_doc]

    result = smythos_unified_resource_manager.invoke({
        "action": "read",
        "resource_type": "VECTORDB",
        "resource_name": "TestDB"
    })

    assert "Search results from TestDB: ['Document Content']" in result
