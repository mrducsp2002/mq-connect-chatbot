from fastapi import FastAPI
from pydantic import BaseModel
from rag import rag_chain_invoke
from rag_memory import run_llm
from fastapi.responses import HTMLResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Conversation(BaseModel):
    message: str
    
@app.post("/chat")
def chat(req: Conversation): 
    answer = run_llm(req.message)
    return {"answer": answer}


