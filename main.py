from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage

# Import our LangGraph workflow
from agents import graph

app = FastAPI(title="Enterprise Procurement Data API", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

async def authenticate_token(authorization: Optional[str] = Header(None)):
    """Simple placeholder authentication (matches JD requirement for auth layer)"""
    # In production, this would validate a JWT against an IdP (e.g., AWS Cognito)
    if authorization != "Bearer mock-secret-token":
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return True

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Procurement Agent API"}

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, auth: bool = Depends(authenticate_token)):
    """
    Streams the output of the LangGraph supervisor workflow.
    """
    async def event_generator():
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        # We use aio_stream or stream in an executor to avoid blocking the event loop
        # Since graph.stream is synchronous here, we wrap it
        def run_graph():
            for output in graph.stream(inputs, stream_mode="updates"):
                yield output

        for event in run_graph():
            # Format the output for streaming (Server-Sent Events format)
            for node_name, state_update in event.items():
                if "messages" in state_update:
                    msg = state_update["messages"][-1].content
                    if isinstance(msg, list):
                        msg = " ".join([m.get("text", "") for m in msg if m.get("type") == "text" or "text" in m])
                    yield f"data: [{node_name}] {msg}\n\n"
                elif "next_agent" in state_update:
                    yield f"data: [Supervisor] Routing to {state_update['next_agent']}...\n\n"
            
            # Small sleep to yield control to event loop
            await asyncio.sleep(0.01)
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
