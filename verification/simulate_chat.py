import sys
import os
from typing import List, Optional, Any

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mocking libraries
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration

# We need to mock get_llm BEFORE importing app.graph because app.graph calls get_llm() at module level.
import app.llm

class SmartMockLLM(BaseChatModel):
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        text = " ".join([str(m.content) for m in messages])

        content = "I don't know."

        # Supervisor Logic (Prompt contains "Who should act next?")
        if "Who should act next?" in text:
            print(f"\n[MockLLM] Acting as Supervisor")

            # Detect state based on conversation history
            has_k8s_acted = "I checked the pods" in text
            has_gcp_acted = "Cloud SQL is currently in maintenance mode" in text

            # 1. User complains about crash -> Call K8s
            if "frontend crashing" in text and not has_k8s_acted:
                print("[MockLLM] Decision: K8s_Specialist")
                content = "K8s_Specialist"

            # 2. K8s found CrashLoop -> Call GCP
            elif "CrashLoopBackOff" in text and not has_gcp_acted:
                 print("[MockLLM] Decision: GCP_Specialist")
                 content = "GCP_Specialist"

            # 3. Done
            else:
                print("[MockLLM] Decision: FINISH")
                content = "FINISH"

        # Specialist Logic
        elif "Kubernetes (K8s)" in text:
            print(f"\n[MockLLM] Acting as K8s Agent")
            content = "I checked the pods. The 'frontend' pod is in CrashLoopBackOff. It seems to be a DB connection error."

        elif "Google Cloud Platform" in text:
             print(f"\n[MockLLM] Acting as GCP Agent")
             content = "I checked GCP. Cloud SQL is currently in maintenance mode. That explains the connection error."

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "smart-mock"

    def bind_tools(self, tools, **kwargs):
        print(f"[MockLLM] Tools bound: {[t.name for t in tools]}")
        return self

# Monkeypatch
def mock_get_llm():
    return SmartMockLLM()

app.llm.get_llm = mock_get_llm

# Now import graph
print("Importing app_graph...")
from app.graph import app_graph

# Run
print("Starting Verification Simulation...")
inputs = {"messages": [HumanMessage(content="Why is my frontend crashing?")]}

try:
    # Run the graph
    result = app_graph.invoke(inputs, config={"recursion_limit": 10})

    print("\n--- Final Messages ---")
    for m in result["messages"]:
        print(f"[{m.type}]: {m.content}")

    print("\nVerification Passed!")
except Exception as e:
    print(f"\nVerification Failed: {e}")
    import traceback
    traceback.print_exc()
