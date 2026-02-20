from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import uuid

from app.graph import app_graph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from app.rag import initialize_rag
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize RAG Knowledge Base on startup
    try:
        initialize_rag()
    except Exception as e:
        print(f"Warning: Failed to initialize RAG: {e}")
    yield

app = FastAPI(title="Infra Agent Manager", version="1.0", lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    thread_id: Optional[str] = None

class ResumeRequest(BaseModel):
    thread_id: str
    action: str  # "approve" or "deny"

@app.get("/")
def read_root():
    return {"message": "Infrastructure Agent Manager is Running"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Streamed Endpoint to interact with the Agent Graph.
    Returns a stream of JSON events:
    - {"type": "activity", "agent": "AgentName"}
    - {"type": "message", "agent": "AgentName", "content": "..."}
    - {"type": "approval_required", "thread_id": "..."}
    - {"type": "final"}
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Check existing state to avoid duplicating history
    current_state = app_graph.get_state(config)

    messages = []
    # If no state exists, use history + current message
    if not current_state.values:
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Always append the current new message
    messages.append(HumanMessage(content=request.message))
    inputs = {"messages": messages}

    async def event_stream():
        try:
            # Use astream to get updates from the graph
            async for event in app_graph.astream(inputs, config=config):
                for node, output in event.items():
                    # Check if it's the Supervisor routing
                    if node == "Supervisor":
                        next_agent = output.get("next")
                        if next_agent and next_agent != "FINISH":
                            yield json.dumps({"type": "activity", "agent": next_agent}) + "\n"
                        elif next_agent == "FINISH":
                            # We are done.
                            yield json.dumps({"type": "final"}) + "\n"

                    # Check if it's a Specialist acting
                    elif "_Specialist" in node:
                        # output usually contains "messages"
                        msgs = output.get("messages", [])
                        if msgs:
                            if not isinstance(msgs, list):
                                msgs = [msgs]

                            for msg in msgs:
                                # Check for tool calls (Request)
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        yield json.dumps({
                                            "type": "tool_call",
                                            "agent": node,
                                            "tool": tool_call.get('name', 'unknown'),
                                            "args": tool_call.get('args', {})
                                        }) + "\n"

                                # Check for tool outputs (Result)
                                if isinstance(msg, ToolMessage):
                                    yield json.dumps({
                                        "type": "tool_output",
                                        "agent": node,
                                        "tool": msg.name or "unknown",
                                        "content": msg.content
                                    }) + "\n"

                                if msg.content and not isinstance(msg, ToolMessage):
                                    yield json.dumps({
                                        "type": "message",
                                        "agent": node,
                                        "content": msg.content
                                    }) + "\n"

            # After stream ends, check if we are interrupted
            final_state = app_graph.get_state(config)
            if final_state.next:
                # Graph paused (e.g. interrupt_before)
                yield json.dumps({"type": "approval_required", "thread_id": thread_id}) + "\n"
            else:
                yield json.dumps({"type": "final"}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "message", "agent": "System", "content": f"Error: {str(e)}"}) + "\n"
            yield json.dumps({"type": "final"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

@app.post("/chat/resume")
async def resume_chat(request: ResumeRequest):
    """
    Resumes a paused graph execution (e.g. after approval).
    """
    config = {"configurable": {"thread_id": request.thread_id}}

    # If action is 'deny', we update state to skip or cancel
    if request.action == "deny":
        # Inject a denial message as if Automation_Specialist ran
        app_graph.update_state(
            config,
            {"messages": [HumanMessage(content="User denied the action.")]},
            as_node="Automation_Specialist"
        )

    # Resume execution (with None input, as we just want to continue from where we left off)

    async def event_stream():
        try:
            # Resume with None as input
            async for event in app_graph.astream(None, config=config):
                for node, output in event.items():
                    if node == "Supervisor":
                        next_agent = output.get("next")
                        if next_agent and next_agent != "FINISH":
                            yield json.dumps({"type": "activity", "agent": next_agent}) + "\n"
                        elif next_agent == "FINISH":
                            yield json.dumps({"type": "final"}) + "\n"

                    elif "_Specialist" in node:
                        msgs = output.get("messages", [])
                        if msgs:
                            if not isinstance(msgs, list): msgs = [msgs]
                            for msg in msgs:
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        yield json.dumps({
                                            "type": "tool_call",
                                            "agent": node,
                                            "tool": tool_call.get('name', 'unknown'),
                                            "args": tool_call.get('args', {})
                                        }) + "\n"
                                if isinstance(msg, ToolMessage):
                                    yield json.dumps({
                                        "type": "tool_output",
                                        "agent": node,
                                        "tool": msg.name or "unknown",
                                        "content": msg.content
                                    }) + "\n"
                                if msg.content and not isinstance(msg, ToolMessage):
                                    yield json.dumps({
                                        "type": "message",
                                        "agent": node,
                                        "content": msg.content
                                    }) + "\n"

            # Check if finished
            final_state = app_graph.get_state(config)
            if final_state.next:
                 yield json.dumps({"type": "approval_required", "thread_id": request.thread_id}) + "\n"
            else:
                 yield json.dumps({"type": "final"}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "message", "agent": "System", "content": f"Error: {str(e)}"}) + "\n"
            yield json.dumps({"type": "final"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
