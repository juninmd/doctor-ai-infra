from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock, MagicMock
import json

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Infrastructure Agent Manager is Running"}

@patch("app.graph.app_graph.astream")
def test_chat_endpoint_stream(mock_astream):
    # Mock the generator
    async def mock_generator(inputs):
        # Simulate Supervisor routing
        yield {"Supervisor": {"next": "K8s_Specialist"}}
        # Simulate Specialist response
        from langchain_core.messages import AIMessage
        yield {"K8s_Specialist": {"messages": [AIMessage(content="Checking pods...")]}}
        # Simulate Supervisor finish
        yield {"Supervisor": {"next": "FINISH"}}

    mock_astream.side_effect = mock_generator

    response = client.post("/chat", json={"message": "Hello", "history": []})
    assert response.status_code == 200

    # Read the stream lines
    lines = list(response.iter_lines())
    assert len(lines) > 0

    # Parse lines
    events = [json.loads(line) for line in lines if line]

    # Check for activity type
    assert any(e.get("type") == "activity" and e.get("agent") == "K8s_Specialist" for e in events)
    # Check for message type
    assert any(e.get("type") == "message" and e.get("content") == "Checking pods..." for e in events)
    # Check for final type
    assert any(e.get("type") == "final" for e in events)
