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
try:
    local_model = LLM()
except Exception as e:
    print(f"Error initializing local model: {e}")

def build_context(results):
    context = ""
    for r in results:
        context += f"[Source: {r['file']}]\n"
        context += f"{r['text']}\n\n"
    return context


from fastapi.responses import StreamingResponse
import json
import time

# --- PASO 1: Modelos de Entrada ---
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7

# --- PASO 2: El Endpoint de Modelos ---
# Open WebUI llama aquí cuando arranca para saber qué modelos tienes disponibles
@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "RNJ-1", # Este es el nombre que saldrá en el desplegable
                "object": "model",
                "created": 1700000000,
                "owned_by": "reezo"
            }
        ]
    }

# --- PASO 3: El Endpoint de Chat ---
# Le decimos a FastAPI que cuando alguien haga un POST a esta URL, ejecute esta función
@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    
    query = req.messages[-1].content
    query_vector = embed_model.embed_query(query)
    query_response = retriever.hybrid_search(query, query_vector)
    context = build_context(query_response)
    
    # Extraer el historial de conversacion omitiendo el ultimo mensaje (que es la query actual)
    chat_history = []
    for i in range(0, len(req.messages) - 1, 2):
        if req.messages[i].role == "user" and i+1 < len(req.messages):
            user_msg = req.messages[i].content
            bot_msg = req.messages[i+1].content
            chat_history.append((user_msg, bot_msg))
            
    # Función generadora que va devolviendo ('yield') los trocitos de texto uno a uno
    async def generate_stream():
        # Llamamos al modelo con stream=True (nos devuelve un generador)
        answer_generator = local_model.get_answer(query, context, chat_history, stream=True)
        
        for chunk in answer_generator:
            # Open WebUI (y OpenAI) espera que cada trozo llegue en este formato JSON exacto
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
            # FastAPI requiere que los flujos (Server-Sent Events) empiecen por "data: "
            yield f"data: {json.dumps(chunk_data)}\n\n"
            
        # Cuando termina, enviamos el mensaje especial "[DONE]"
        yield "data: [DONE]\n\n"

    # Devolvemos un StreamingResponse en lugar de un diccionario simple
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
