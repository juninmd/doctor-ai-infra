from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio

from app.graph import app_graph
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="Infra Agent Manager", version="1.0")

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

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
    - {"type": "final"}
    """

    # Convert simple history to LangChain messages
    messages = []
    for msg in request.history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=request.message))
    inputs = {"messages": messages}

    async def event_stream():
        try:
            # Use astream to get updates from the graph
            async for event in app_graph.astream(inputs):
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
                            # It could be a single message or list
                            if isinstance(msgs, list):
                                content = msgs[-1].content
                            else:
                                content = msgs.content

                            yield json.dumps({
                                "type": "message",
                                "agent": node,
                                "content": content
                            }) + "\n"

        except Exception as e:
            yield json.dumps({"type": "message", "agent": "System", "content": f"Error: {str(e)}"}) + "\n"
            yield json.dumps({"type": "final"}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
