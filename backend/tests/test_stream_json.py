
import sys
from unittest.mock import MagicMock

# MOCK RAG Engine BEFORE importing main
mock_rag = MagicMock()
mock_rag.rag_engine = MagicMock()
mock_rag.initialize_rag = MagicMock()
sys.modules["app.rag"] = mock_rag

import pytest
import json
import asyncio
from langchain_core.messages import AIMessage, ToolMessage

# Now import main
from main import chat_endpoint, ChatRequest

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
        m.setattr("main.app_graph", mock_graph)

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
        # We expect two types of events from Topology_Specialist
        # 1. The ToolOutput (containing JSON)
        # 2. The Message (summary)

        tool_outputs = [e for e in events if e["type"] == "tool_output" and e["agent"] == "Topology_Specialist"]
        messages = [e for e in events if e["type"] == "message" and e["agent"] == "Topology_Specialist"]

        # Check if we got the JSON content in tool_output
        has_json = any("```json" in t["content"] for t in tool_outputs)

        assert has_json, f"The stream did not contain the ToolOutput with the JSON block! Got: {tool_outputs}"
        assert len(messages) == 1, f"Expected 1 summary message, got {len(messages)}"

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint_streams_tool_output())
