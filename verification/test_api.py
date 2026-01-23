import sys
import os
from unittest.mock import MagicMock, patch

# Correct path setup
# We assume this script is run from backend/ or root.
# Let's verify where we are.
# If we are in backend/, sys.path should include current dir.
# If we add backend/ to sys.path, we can import main.

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../backend"))

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from fastapi.testclient import TestClient

# Try importing main (backend/main.py)
# Since we added backend/ to sys.path, 'main' should be importable as a module
try:
    from main import app
    from langchain_core.messages import AIMessage, ToolMessage
except ImportError:
    # Fallback if run differently
    from app.main import app
    from langchain_core.messages import AIMessage, ToolMessage

client = TestClient(app)

def test_chat_endpoint_structure():
    print("Testing /chat endpoint structure...")

    # Mock the graph invocation
    mock_final_state = {
        "messages": [
            AIMessage(content="Thinking...", name="Supervisor"),
            AIMessage(content="", tool_calls=[{"name": "list_k8s_pods", "args": {}, "id": "123"}]),
            ToolMessage(content="[pod-1, pod-2]", tool_call_id="123", name="K8s_Specialist"),
            AIMessage(content="The pods are running.", name="K8s_Specialist")
        ]
    }

    # Patch 'main.app_graph.invoke' because we imported 'app' from 'main'
    # Depending on how main imported it, it might be app.graph.app_graph
    # In backend/main.py: from app.graph import app_graph

    target = "main.app_graph.invoke"

    with patch(target, return_value=mock_final_state):
        response = client.post("/chat", json={
            "message": "Check my pods",
            "history": []
        })

        if response.status_code != 200:
            print(f"Failed: {response.status_code} - {response.text}")

        assert response.status_code == 200
        data = response.json()

        print("Response Data:", data)

        assert "response" in data
        assert data["response"] == "The pods are running."
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) == 4

        # Check tool call preservation
        tool_call_step = data["steps"][1]
        # Pydantic/LangChain dump structure check
        # Tool calls usually appear in 'tool_calls' or 'additional_kwargs' depending on version
        # But our dump is m.model_dump()

        print("Test Passed!")

if __name__ == "__main__":
    test_chat_endpoint_structure()
