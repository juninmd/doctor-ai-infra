import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from langchain_core.messages import AIMessage, HumanMessage
from app.state import AgentState

# Mock the LLM before importing graph
with patch("app.llm.ChatOllama") as MockOllama, \
     patch("app.llm.ChatGoogleGenerativeAI") as MockGemini:

    # Setup the mock instance
    mock_llm_instance = MagicMock()

    # IMPORTANT: When used in a LCEL chain (prompt | llm),
    # if the object is a Mock, it might be called via __call__ instead of .invoke
    # so we mock both.

    def mock_response(*args, **kwargs):
        # We can dynamically decide what to return based on input if needed
        # But for now we rely on the test loop setting the return value.
        return mock_llm_instance.invoke.return_value

    mock_llm_instance.side_effect = mock_response
    mock_llm_instance.invoke.side_effect = None # Use return_value

    MockOllama.return_value = mock_llm_instance
    MockGemini.return_value = mock_llm_instance

    from app import graph
    graph.llm = mock_llm_instance

    print("--- Verifying Supervisor Routing Logic ---")

    # 1. Test: User asks about frontend -> Supervisor should pick K8s
    state_1 = {
        "messages": [HumanMessage(content="Why is the frontend crashing?")],
        "next": ""
    }

    # Set the expected response
    mock_llm_instance.invoke.return_value = AIMessage(content="K8s_Specialist")

    result_1 = graph.supervisor_node(state_1)
    print(f"Scenario 1 (Frontend Crash) -> Supervisor routed to: {result_1['next']}")

    if result_1['next'] != "K8s_Specialist":
        print(f"FAILURE: Expected K8s_Specialist. Got: {result_1['next']}")
        sys.exit(1)

    # 2. Test: K8s finds DB error -> Supervisor should pick GCP
    state_2 = {
        "messages": [
            HumanMessage(content="Why is the frontend crashing?"),
            AIMessage(content="I checked the pods. Frontend is crashing. Logs show: ConnectionRefusedError to postgres-db.", name="K8s_Specialist")
        ],
        "next": ""
    }

    mock_llm_instance.invoke.return_value = AIMessage(content="GCP_Specialist")

    result_2 = graph.supervisor_node(state_2)
    print(f"Scenario 2 (DB Error found) -> Supervisor routed to: {result_2['next']}")

    if result_2['next'] != "GCP_Specialist":
        print("FAILURE: Expected GCP_Specialist")
        sys.exit(1)

    # 3. Test: GCP confirms Maintenance -> Supervisor should Finish or Summarize
    state_3 = {
        "messages": [
            HumanMessage(content="Why is the frontend crashing?"),
            AIMessage(content="Logs show ConnectionRefused.", name="K8s_Specialist"),
            AIMessage(content="GCP Cloud SQL is in MAINTENANCE mode.", name="GCP_Specialist")
        ],
        "next": ""
    }

    mock_llm_instance.invoke.return_value = AIMessage(content="FINISH")

    result_3 = graph.supervisor_node(state_3)
    print(f"Scenario 3 (Maintenance Confirmed) -> Supervisor routed to: {result_3['next']}")

    if result_3['next'] != "FINISH":
        print("FAILURE: Expected FINISH")
        sys.exit(1)

    print("\nSUCCESS: Supervisor logic verifies correctly with mocked LLM.")
