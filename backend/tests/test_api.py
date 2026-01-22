from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Infrastructure Agent Manager is Running"}

@patch("app.graph.app_graph.invoke")
def test_chat_endpoint(mock_invoke):
    # Mock the graph response
    from langchain_core.messages import AIMessage
    mock_invoke.return_value = {
        "messages": [AIMessage(content="Hello from mock agent")]
    }

    response = client.post("/chat", json={"message": "Hello", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello from mock agent"
    assert len(data["steps"]) == 1
