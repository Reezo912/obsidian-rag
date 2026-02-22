import sys
import os
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent
sys.path.append(str(project_root))

from config import DB_PATH, EMBED_MODEL_PATH
from core.db import Database
from core.retrieval import Retriever
from core.embeddings import Embedding
from core.llm import LLM



app = FastAPI(title="Obsidian RAG API")

db = Database(DB_PATH)
retriever = Retriever(db)
embed_model = Embedding(EMBED_MODEL_PATH)
local_model = LLM()

def build_context(results):
    context = ""
    for r in results:
        context += f"[Source: {r['file']}]\n"
        context += f"{r['text']}\n\n"
    return context


from fastapi.responses import StreamingResponse
import json
import time

# Input models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7

# Check available models
@app.get("/v1/models")
async def get_models():
    try:
        models = local_model.client.models.list().data
        model_list = []
        for m in models:
            model_list.append({
                "id": m.id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "lm-studio"
            })
    except Exception:
        model_list = [
            {
                "id": "Not connected to LM Studio",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "error"
            }
        ]

    return {
        "object": "list",
        "data": model_list
    }

# Chat endpoint
@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    
    query = req.messages[-1].content
    query_vector = embed_model.embed_query(query)
    query_response = retriever.hybrid_search(query, query_vector)
    context = build_context(query_response)
    
    # Extract conversation history omitting the last message (which is the current query)
    chat_history = []
    for i in range(0, len(req.messages) - 1, 2):
        if req.messages[i].role == "user" and i+1 < len(req.messages):
            user_msg = req.messages[i].content
            bot_msg = req.messages[i+1].content
            chat_history.append((user_msg, bot_msg))
            
    # Generator function that yields text chunks one by one
    async def generate_stream():
        # Call the model with stream=True (returns a generator)
        # Important: Pass req.model to use the one selected in the dropdown
        answer_generator = local_model.get_answer(query, context, chat_history, requested_model=req.model, stream=True)
        
        for chunk in answer_generator:
            # Open WebUI (and OpenAI) expects each chunk to arrive in this exact JSON format
            chunk_data = {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk},
                        "finish_reason": None
                    }
                ]
            }
            # FastAPI requires that streams (Server-Sent Events) start with "data: "
            yield f"data: {json.dumps(chunk_data)}\n\n"
            
        # When it finishes, send the special message "[DONE]"
        yield "data: [DONE]\n\n"

    # Return a StreamingResponse instead of a simple dictionary
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
