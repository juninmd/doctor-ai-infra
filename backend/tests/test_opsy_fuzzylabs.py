import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node, RouterSchema
from app.tools.opsy import opsy_backup_and_ticket_failing_pods
from app.tools.fuzzylabs import fuzzylabs_sre_workflow
import json
from langchain_core.language_models import FakeListChatModel

def _create_mock_llm(next_agent: str, reasoning: str):
    llm_output = {"next_agent": next_agent, "reasoning": reasoning}

    class FakeLLM(FakeListChatModel):
        structured_output_called: bool = False

        def with_structured_output(self, *args, **kwargs):
            self.structured_output_called = True

            class InnerMock:
                def invoke(self, *i_args, **i_kwargs):
                    return RouterSchema(next_agent=next_agent, reasoning=reasoning)

            return InnerMock()

    return FakeLLM(responses=[json.dumps(llm_output)])

def test_supervisor_opsy_routing():
    """Verifies the supervisor correctly routes Opsy workflow requests to the Automation_Specialist."""
    state = {
        "messages": [
            HumanMessage(content="Run the Opsy workflow to backup and ticket failing pods.")
        ]
    }

    fake_llm = _create_mock_llm("Automation_Specialist", "Request requires executing the Opsy workflow, routing to Automation_Specialist.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Automation_Specialist"

def test_supervisor_fuzzylabs_routing():
    """Verifies the supervisor correctly routes FuzzyLabs requests to the Incident_Specialist."""
    state = {
        "messages": [
            HumanMessage(content="Use the FuzzyLabs workflow to diagnose the frontend service.")
        ]
    }

    fake_llm = _create_mock_llm("Incident_Specialist", "Request involves the FuzzyLabs workflow, routing to Incident_Specialist.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Incident_Specialist"

@patch("app.tools.opsy.list_k8s_pods", create=True)
@patch("app.tools.opsy.create_issue", create=True)
@patch("app.llm.get_google_sdk_client")
@patch("app.llm.get_llm")
def test_opsy_backup_and_ticket_failing_pods_llm_fallback(mock_get_llm, mock_get_sdk, mock_create_issue, mock_list_pods):
    """Verifies that the Opsy tool falls back to the standard LLM if Gemini SDK fails."""

    # Needs to mock the import from inside the function as it uses local imports
    with patch("app.tools.list_k8s_pods") as mock_local_list_pods, \
         patch("app.tools.create_issue") as mock_local_create_issue:

        mock_local_list_pods.invoke.return_value = "Pod A is CrashLoopBackOff"
        mock_local_create_issue.invoke.return_value = "Issue #123 created."

        # Force SDK to fail
        mock_get_sdk.return_value = None

        # Setup LLM Fallback
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value.content = "Diagnosis: Missing ENV var."
        mock_get_llm.return_value = mock_llm_instance

        result = opsy_backup_and_ticket_failing_pods.invoke({"namespace": "default", "project": "TEST"})

        assert "Diagnosis: Missing ENV var." in result
        assert "Issue #123 created." in result
        assert "datolabs-io/sandbox" in result
        mock_get_llm.assert_called_once()
        mock_llm_instance.invoke.assert_called_once()


@patch("app.llm.get_google_sdk_client")
@patch("app.llm.get_llm")
def test_fuzzylabs_sre_workflow_llm_fallback(mock_get_llm, mock_get_sdk):
    """Verifies that the FuzzyLabs tool falls back to the standard LLM if Gemini SDK fails."""

    with patch("app.tools.get_pod_logs") as mock_logs, \
         patch("app.tools.list_recent_commits") as mock_commits, \
         patch("app.tools.send_slack_notification") as mock_slack:

        mock_logs.invoke.return_value = "Error: Out of Memory"
        mock_commits.invoke.return_value = "Commit 123: Update limits"
        mock_slack.invoke.return_value = "Message sent to #incidents"

        # Force SDK to fail
        mock_get_sdk.return_value = None

        # Setup LLM Fallback
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value.content = "Fuzzy Diagnosis: OOM error due to memory leak."
        mock_get_llm.return_value = mock_llm_instance

        result = fuzzylabs_sre_workflow.invoke({"service_name": "frontend"})

        assert "Fuzzy Diagnosis: OOM error due to memory leak." in result
        assert "Message sent to #incidents" in result
        mock_get_llm.assert_called_once()
        mock_llm_instance.invoke.assert_called_once()
