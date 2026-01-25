
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.graph import app_graph as graph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Infrastructure Agent Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "Infra Agent Manager API is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    inputs = {"messages": [HumanMessage(content=request.message)]}

    async def event_generator():
        # Using astream to stream updates from the graph
        async for event in graph.astream(inputs):
            for node_name, state_update in event.items():
                # Notify frontend which agent is working
                yield json.dumps({"type": "activity", "agent": node_name}) + "\n"

                # If the agent produced a message, send it
                if "messages" in state_update:
                    messages = state_update["messages"]
                    if messages:
                        # LangGraph appends messages. Depending on the update,
                        # 'messages' might be the full list or just the new ones if 'messages' key in state is configured with add.
                        # In the provided graph.py, state uses operator.add, so state_update usually contains the delta (the new message).
                        # Let's handle both list or single item just in case.
                        latest = messages[-1] if isinstance(messages, list) else messages

                        content = latest.content if hasattr(latest, "content") else str(latest)
                        role = getattr(latest, "name", "assistant")

                        yield json.dumps({
                            "type": "message",
                            "role": role,
                            "content": content,
                            "agent": node_name
                        }) + "\n"

        # Signal finish
        yield json.dumps({"type": "final"}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
