
import sys
from unittest.mock import MagicMock

# MOCK RAG Engine BEFORE importing backend.main
mock_rag = MagicMock()
mock_rag.rag_engine = MagicMock()
mock_rag.initialize_rag = MagicMock()
sys.modules["app.rag"] = mock_rag
sys.modules["backend.app.rag"] = mock_rag

# Also mock tools that depend on RAG if necessary, but app.rag should be enough if imported as 'app.rag'
# Verify imports in graph.py
# graph.py imports from .tools.incident
# tools/incident.py imports from app.rag

import pytest
import json
import asyncio
from langchain_core.messages import AIMessage, ToolMessage

# Now import main
from backend.main import chat_endpoint, ChatRequest

@pytest.mark.asyncio
async def test_chat_endpoint_streams_tool_output():
    # Setup Mock Graph
    mock_graph = MagicMock()

    # Simulate a sequence of events:
    # 1. Specialist yields a ToolMessage (with JSON) AND an AIMessage (summary)

    tool_output_with_json = "Scan complete.\n```json\n{\"k8s\": \"ok\"}\n```"
    summary_message = "The system is healthy."

    # Mock output from graph.astream
    # It yields a dictionary {NodeName: StateUpdate}
    # StateUpdate has "messages": [ToolMessage, AIMessage]

    mock_node_output = {
        "Topology_Specialist": {
            "messages": [
                ToolMessage(content=tool_output_with_json, tool_call_id="123", name="scan_infrastructure"),
                AIMessage(content=summary_message)
            ]
        }
    }

    # Mock astream to yield this once then finish
    async def mock_astream(input):
        yield mock_node_output
        yield {"Supervisor": {"next": "FINISH"}}

    mock_graph.astream = mock_astream

    # Patch app_graph in main
    with pytest.MonkeyPatch.context() as m:
        m.setattr("backend.main.app_graph", mock_graph)

        request = ChatRequest(message="status")
        response = await chat_endpoint(request)

        # Consume the stream
        events = []
        async for line in response.body_iterator:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        # Verification
        # We expect TWO message events from Topology_Specialist
        # 1. The ToolMessage (containing JSON)
        # 2. The AIMessage (summary)

        messages = [e for e in events if e["type"] == "message" and e["agent"] == "Topology_Specialist"]

        # Check if we got the JSON content
        has_json = any("```json" in m["content"] for m in messages)

        assert has_json, f"The stream did not contain the ToolMessage with the JSON block! Got: {[m['content'] for m in messages]}"
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint_streams_tool_output())
