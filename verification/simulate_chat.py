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
            has_cicd_acted = "Pipeline for frontend: FAILED" in text
            has_git_acted = "fix: typo in header" in text

            # 1. User complains about build -> Call CI/CD
            if "build fail" in text and not has_cicd_acted:
                print("[MockLLM] Decision: CICD_Specialist")
                content = "CICD_Specialist"

            # 2. CI/CD found failure -> Call Git to check recent commits
            elif "npm run build" in text and not has_git_acted:
                 print("[MockLLM] Decision: Git_Specialist")
                 content = "Git_Specialist"

            # 3. Done
            else:
                print("[MockLLM] Decision: FINISH")
                content = "FINISH"

        # Specialist Logic
        elif "CI/CD Pipelines" in text:
            print(f"\n[MockLLM] Acting as CICD Agent")
            content = "Pipeline for frontend: FAILED. Step 'Build Docker Image' failed. Error: 'npm run build' exited with code 1."

        elif "Git, GitHub" in text:
             print(f"\n[MockLLM] Acting as Git Agent")
             content = "GitHub Org my-org: 5 active repos. Latest commit on 'frontend-repo': 'fix: typo in header' by dev-alex."

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
inputs = {"messages": [HumanMessage(content="Why did the build fail?")]}

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
