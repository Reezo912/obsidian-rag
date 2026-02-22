import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent
sys.path.append(str(project_root))

from core.db import Database
from core.retrieval import Retriever
from core.embeddings import Embedding
from core.llm import LLM
from config import DB_PATH, EMBED_MODEL_PATH


def build_context(results):
    context = ""
    for r in results:
        context += f"[Source: {r['file']}]\n"
        context += f"{r['text']}\n\n"
    return context




def main():
    db = Database(DB_PATH)
    retriever = Retriever(db)
    embed_model = Embedding(EMBED_MODEL_PATH) 
    local_model = LLM()

    conversation_history = []

    while True:
        query = input("\nWhat do you want to know? write 'exit' to quit\n")
        if query == 'exit':
            break

        query_embed = embed_model.embed_query(query)

        query_response = retriever.hybrid_search(query, query_vector=query_embed)

        context = build_context(query_response)

        answer = local_model.get_answer(query, context, conversation_history)

        conversation_history.append((query, answer))    

        print(answer)


if __name__ == "__main__":
    main()
