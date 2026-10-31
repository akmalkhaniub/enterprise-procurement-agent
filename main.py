import asyncio
import hmac
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

# Import our LangGraph workflow
from agents import graph

app = FastAPI(title="Enterprise Procurement Data API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    session_id: str = "default"


async def authenticate_token(authorization: Optional[str] = Header(None)):
    """Constant-time bearer token authentication backed by PROCUREMENT_API_TOKEN."""
    expected_token = os.environ.get("PROCUREMENT_API_TOKEN", "mock-secret-token")
    expected_header = f"Bearer {expected_token}"
    if not authorization or not hmac.compare_digest(authorization, expected_header):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return True


@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Procurement Agent API", "version": "1.1.0"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, auth: bool = Depends(authenticate_token)):
    """
    Streams the output of the LangGraph supervisor workflow non-blockingly via astream.
    """
    async def event_generator():
        inputs = {"messages": [HumanMessage(content=request.message)]}

        try:
            async for event in graph.astream(inputs, stream_mode="updates"):
                for node_name, state_update in event.items():
                    if "messages" in state_update:
                        msg = state_update["messages"][-1].content
                        if isinstance(msg, list):
                            msg = " ".join([m.get("text", "") for m in msg if m.get("type") == "text" or "text" in m])
                        yield f"data: [{node_name}] {msg}\n\n"
                    elif "next_agent" in state_update:
                        yield f"data: [Supervisor] Routing to {state_update['next_agent']}...\n\n"
        except Exception as exc:
            yield f"data: [Error] {type(exc).__name__}: {exc}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
