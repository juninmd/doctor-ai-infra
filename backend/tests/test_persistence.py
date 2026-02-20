import pytest
import asyncio
import sys
import importlib
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

@pytest.mark.asyncio
async def test_persistence_interrupt_resume():
    # Setup Config
    thread_id = "test-thread-persistence"
    config = {"configurable": {"thread_id": thread_id}}

    # Create a Mock LLM
    mock_llm = MagicMock()

    # Setup Supervisor Mock behavior on the LLM
    class Decision:
        next_agent = "Automation_Specialist"
        reasoning = "Testing Automation"

    class FinishDecision:
        next_agent = "FINISH"
        reasoning = "Done"

    mock_chain = MagicMock()
    decisions = [Decision(), FinishDecision()]
    mock_chain.invoke.side_effect = decisions
    mock_chain.side_effect = decisions # In case it's coerced to RunnableLambda and called directly

    # mock_llm.with_structured_output returns the chain
    mock_llm.with_structured_output.return_value = mock_chain

    # Use patch context only for get_llm, as reloading will use real ChatPromptTemplate
    with patch("app.llm.get_llm", return_value=mock_llm):

        # Reload app.graph to use the mocked get_llm
        import app.graph
        importlib.reload(app.graph)
        from app.graph import app_graph

        # 1. Start Conversation
        inputs = {"messages": [HumanMessage(content="Please run the cleanup runbook")]}

        print("Starting execution...")
        async for event in app_graph.astream(inputs, config=config):
            pass

        # 2. Verify Interrupt
        state = app_graph.get_state(config)
        print(f"State after first run: {state.next}")
        assert state.next == ('Automation_Specialist',), f"Graph should be paused at Automation_Specialist, got {state.next}"

        # 3. Verify State Persistence
        assert len(state.values["messages"]) >= 1

        # 4. Resume Execution with injected state (Simulating completion/skip)
        # Instead of running the agent (which is hard to mock correctly due to async/bind_tools),
        # we update the state as if the agent ran, which is exactly how 'deny' logic works too.
        print("Resuming execution with injected state...")

        app_graph.update_state(
            config,
            {"messages": [AIMessage(content="Automation Task Complete (Simulated)")]},
            as_node="Automation_Specialist"
        )

        events = []
        # Resume. Since we updated state as Automation_Specialist, it should proceed to Supervisor.
        async for event in app_graph.astream(None, config=config):
            for k, v in event.items():
                events.append(k)

        # 5. Verify Completion
        final_state = app_graph.get_state(config)
        print(f"Final state: {final_state.next}")
        assert final_state.next == (), "Graph should have finished"

        assert "Supervisor" in events, "Supervisor should have executed again"
