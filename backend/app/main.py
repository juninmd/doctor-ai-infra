
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.agents.supervisor import build_graph
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

class ChatResponse(BaseModel):
    response: str
    history: list

# Initialize the graph
graph = build_graph()

@app.get("/")
def read_root():
    return {"message": "Infra Agent Manager API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        inputs = {"messages": [HumanMessage(content=request.message)]}
        result = graph.invoke(inputs)

        # Extract the final response
        messages = result["messages"]
        last_message = messages[-1].content if messages else "No response generated."

        # Serialize history for frontend (simplified)
        # Map "human" role to "user" for the frontend
        history = []
        for m in messages:
            role = getattr(m, "name", m.type)
            if role == "human":
                role = "user"
            history.append({"role": role, "content": m.content})

        return ChatResponse(response=last_message, history=history)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
