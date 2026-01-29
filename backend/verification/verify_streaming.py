import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import json
import sys
import os

# Add backend to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from langchain_core.messages import AIMessage

client = TestClient(app)

# Mock data
mock_tool_call_msg = AIMessage(
    content="I will check the pods.",
    tool_calls=[{"name": "list_k8s_pods", "args": {"namespace": "default"}, "id": "call_123"}]
)

async def mock_astream(inputs):
    # Yield Supervisor activity
    yield {"Supervisor": {"next": "K8s_Specialist"}}
    # Yield Specialist activity with tool call
    yield {"K8s_Specialist": {"messages": [mock_tool_call_msg]}}
    # Yield Finish
    yield {"Supervisor": {"next": "FINISH"}}

def test_streaming_tool_calls():
    print("Starting streaming test...")
    response = client.post("/chat", json={"message": "check pods"})
    assert response.status_code == 200

    # Read the stream
    lines = response.text.strip().split("\n")
    events = [json.loads(line) for line in lines if line.strip()]

    print(f"Received {len(events)} events.")
    for event in events:
        print(f"Event: {event}")

    # Verify events
    # 1. Activity: K8s_Specialist
    assert events[0]["type"] == "activity"
    assert events[0]["agent"] == "K8s_Specialist"

    # 2. Tool Call
    found_tool_call = False
    for event in events:
        if event["type"] == "tool_call":
            found_tool_call = True
            assert event["agent"] == "K8s_Specialist"
            assert event["tool"] == "list_k8s_pods"
            assert event["args"] == {"namespace": "default"}
            break

    assert found_tool_call, "Tool call event not found in stream"

    # 3. Message
    found_message = False
    for event in events:
        if event["type"] == "message" and event["content"] == "I will check the pods.":
            found_message = True
            break

    assert found_message, "Message event not found in stream"

    # 4. Final
    assert events[-1]["type"] == "final"

if __name__ == "__main__":
    try:
        # We need to run this in a way that patch works.
        with patch("main.app_graph.astream", side_effect=mock_astream):
            test_streaming_tool_calls()
            print("\n✅ Verification Passed: Tool calls are streaming correctly.")
    except AssertionError as e:
        print(f"\n❌ Verification Failed: Assertion Error - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
