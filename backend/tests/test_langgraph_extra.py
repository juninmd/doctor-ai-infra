import pytest
from unittest.mock import patch
from langchain_core.messages import HumanMessage
from app.graph import supervisor_node, RouterSchema
import json
from langchain_core.language_models import FakeListChatModel

def _create_mock_llm(next_agent: str, reasoning: str):
    llm_output = {"next_agent": next_agent, "reasoning": reasoning}

    class FakeLLM(FakeListChatModel):
        structured_output_called: bool = False

        def with_structured_output(self, *args, **kwargs):
            self.structured_output_called = True

            # Use inner FakeListChatModel to mock structured output invocation
            class InnerMock:
                def invoke(self, *i_args, **i_kwargs):
                    return RouterSchema(next_agent=next_agent, reasoning=reasoning)

            return InnerMock()

    return FakeLLM(responses=[json.dumps(llm_output)])

def test_supervisor_k8s_routing():
    """
    Verifies the supervisor correctly routes complex log and pod queries (Bits AI style)
    to the K8s_Specialist.
    """
    state = {
        "messages": [
            HumanMessage(content="The payment pod is crashlooping. Analyze the heavy logs and diagnose the service health to see if it's OOMKilled.")
        ]
    }

    fake_llm = _create_mock_llm("K8s_Specialist", "Issue involves pods and logs, routing to K8s_Specialist.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "K8s_Specialist"

def test_supervisor_automation_routing():
    """
    Verifies the supervisor correctly routes requests to execute runbooks (OpsMate / SmythOS style)
    to the Automation_Specialist.
    """
    state = {
        "messages": [
            HumanMessage(content="The service is down. Please execute the restart_service runbook for the payment-gateway in the prod namespace.")
        ]
    }

    fake_llm = _create_mock_llm("Automation_Specialist", "Request requires executing a runbook, routing to Automation_Specialist.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Automation_Specialist"

def test_supervisor_incident_routing():
    """
    Verifies the supervisor correctly routes incident creation and post-mortem requests (IncidentFox style)
    to the Incident_Specialist.
    """
    state = {
        "messages": [
            HumanMessage(content="We just resolved the outage. Please generate a postmortem and build an incident timeline using mermaid format.")
        ]
    }

    fake_llm = _create_mock_llm("Incident_Specialist", "Request involves post-mortem generation and timelines, routing to Incident_Specialist.")

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Incident_Specialist"
