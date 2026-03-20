import pytest
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graph import workflow, app_graph, members

def test_supervisor_double_failure_fallback():
    """
    Verifies that when both the primary structured output call and the fallback
    LLM call fail, the supervisor correctly falls back to the Topology_Specialist.
    """
    from unittest.mock import patch
    from app.graph import supervisor_node
    import json
    from langchain_core.language_models import FakeListChatModel

    state = {"messages": [HumanMessage(content="Random unrecognized issue")]}

    class FakeLLM(FakeListChatModel):
        structured_output_called: bool = False

        def with_structured_output(self, *args, **kwargs):
            self.structured_output_called = True
            # Raise exception to trigger the fallback logic in supervisor
            raise Exception("Structured parsing error")

        def invoke(self, *args, **kwargs):
             # Simulating a total LLM failure that raises an error
             # so the fallback routing logic fails and triggers the ultimate fallback
             raise Exception("LLM Invoke failed")

    fake_llm = FakeLLM(responses=[])

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        # Verify the ultimate fallback routes to Topology_Specialist
        assert result["next"] == "Topology_Specialist"

        # Ensure a system message is appended describing the fallback
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert "Auto-Routing Error" in result["messages"][0].content

def test_supervisor_state_passing():
    """
    Verifies the supervisor correctly processes states with multiple messages.
    """
    from unittest.mock import patch
    from app.graph import supervisor_node
    import json
    from langchain_core.language_models import FakeListChatModel

    state = {
        "messages": [
            HumanMessage(content="System is slow"),
            AIMessage(content="I am looking into this"),
            SystemMessage(content="Some context")
        ]
    }

    llm_output = {"next_agent": "Datadog_Specialist", "reasoning": "Need metrics"}

    class FakeLLM(FakeListChatModel):
        def with_structured_output(self, *args, **kwargs):
            raise Exception("Force fallback")

    fake_llm = FakeLLM(responses=[json.dumps(llm_output)])

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Datadog_Specialist"

def test_supervisor_vague_request_routing():
    """
    Verifies the supervisor correctly routes vague requests like "Help" or "System is slow"
    to Topology_Specialist as explicitly defined in its system prompt instructions.
    """
    from unittest.mock import patch
    from app.graph import supervisor_node
    import json
    from langchain_core.language_models import FakeListChatModel

    # Simulating a vague request where the LLM might be unsure, but should follow instruction #1
    state = {
        "messages": [
            HumanMessage(content="Help, nothing works")
        ]
    }

    # We simulate the LLM following the instruction and routing to Topology_Specialist
    llm_output = {"next_agent": "Topology_Specialist", "reasoning": "Vague request, scanning infrastructure"}

    class FakeLLM(FakeListChatModel):
        def with_structured_output(self, *args, **kwargs):
            raise Exception("Force fallback")

    fake_llm = FakeLLM(responses=[json.dumps(llm_output)])

    with patch("app.graph.llm", fake_llm):
        result = supervisor_node(state)
        assert result["next"] == "Topology_Specialist"
