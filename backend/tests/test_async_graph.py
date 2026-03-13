import pytest
import asyncio
from unittest.mock import patch
from langchain_core.messages import HumanMessage
from app.graph import app_graph
from app.state import AgentState

@pytest.mark.asyncio
async def test_async_workflow_astream():
    """
    Verifies that the LangGraph workflow can be executed asynchronously
    using astream.
    """
    state = {
        "messages": [HumanMessage(content="System status")],
        "next": ""
    }

    config = {"configurable": {"thread_id": "test_async_thread"}}

    events = []
    from unittest.mock import patch

    # To test async workflow, we can use a smaller test graph
    # or mock the whole graph's runner instead. But a cleaner way is just to mock the actual LLM
    # so we don't break langgraph's node definition internal structures by patching `app_graph.nodes`.
    from langchain_core.messages import AIMessage

    with patch("langchain_ollama.ChatOllama.ainvoke", return_value=AIMessage(content='{"reasoning": "done", "next_agent": "FINISH"}')), \
         patch("langchain_ollama.ChatOllama.invoke", return_value=AIMessage(content='{"reasoning": "done", "next_agent": "FINISH"}')):

        async for event in app_graph.astream(state, config, stream_mode="values"):
            events.append(event)

    assert len(events) > 0
    # The last event should have messages
    last_event = events[-1]
    assert "messages" in last_event
