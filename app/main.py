from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import agent, memory, llm

app = FastAPI(title="Travel Planning Agent")

# allow the demo HTML page (opened as a local file / different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

memory.init_db()


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "model": llm.MODEL}


@app.post("/chat")
def chat(req: ChatRequest):
    return agent.answer(req.session_id, req.message)


@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "messages": memory.get_history(session_id, limit=50)}


@app.post("/warmup")
def warmup():
    load_time = llm.warmup()
    return {"model": llm.MODEL, "load_time_sec": round(load_time, 2)}
