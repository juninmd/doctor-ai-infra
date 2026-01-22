from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.graph import app_graph
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="Infra Agent Manager", version="1.0")

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    steps: List[Any] = []

@app.get("/")
def read_root():
    return {"message": "Infrastructure Agent Manager is Running"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to interact with the Agent Graph.
    """
    try:
        # Convert simple history to LangChain messages
        # In a real app, we'd load this from a DB using a session_id
        messages = []
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=request.message))

        inputs = {"messages": messages}

        # Run the graph
        # stream() or invoke()
        # For simplicity in this first pass, we use invoke (blocking)
        # To support "Thought Process" visualization, we need to capture intermediate steps.
        # LangGraph invoke returns the final state.

        final_state = app_graph.invoke(inputs)

        # Extract the final response
        final_messages = final_state["messages"]
        last_message = final_messages[-1]

        # Extract steps (this is a simplification, ideally we stream events)
        # For now, we return the entire message history as "steps" so the UI can parse it
        # or we just return the final text.
        # To show "thoughts", we can look at the messages from the specialized agents.

        return {
            "response": last_message.content,
            "steps": [m.model_dump() for m in final_messages]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
