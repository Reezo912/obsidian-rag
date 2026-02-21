import lancedb
from pathlib import Path
from openai import OpenAI
from rank_bm25 import BM25Okapi
import logging
import warnings
from sentence_transformers import SentenceTransformer

"""
Deprecated
"""


VAULT_PATH = Path("/home/reezo/Documents/My-notes/")
DB_PATH = "./data/lancedb"
EMBED_MODEL_PATH = "./models/embedding/"

warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
model = SentenceTransformer(
    "BAAI/bge-large-en-v1.5", cache_folder=EMBED_MODEL_PATH, device="cuda"
)


def load_bm25_index(db):
    """Load documents and create BM25 index"""
    table = db.open_table("notes")
    df = table.to_pandas()

    # Tokenize with a split by spaces
    content = df["text"].tolist()
    tokenized_content = [doc.lower().split() for doc in content]

    bm25 = BM25Okapi(tokenized_content)
    return bm25, df


def search_bm25(query, bm25, df, top_k=5):
    """Search into the db using bm25okapi (lematic search)"""
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Top k index
    top_indices = scores.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        results.append(
            {
                "text": df.iloc[idx]["text"],
                "file": df.iloc[idx]["file"],
                "headers": df.iloc[idx]["headers"],
                "score": scores[idx],
                "source": "bm25",
            }
        )

    return results


def search_query_semantic(query_vector, db, top_k=10):
    table = db.open_table("notes")
    results = table.search(query_vector).limit(top_k).to_list()
    return results


def build_context(results):
    context = ""
    for r in results:
        context += f"[Fuente: {r['file']}]\n"
        context += f"{r['text']}\n\n"
    return context


def rrf_fusion(semantic_results, bm25_results, k=5):
    """
    Combine semantic and BM25 results.
    Returns combined list sorted by score.
    """

    # PASO 1: Dos diccionarios separados (más claro)
    rrf_scores = {}  # doc_id → score
    doc_data = {}  # doc_id → result data

    # PASO 2: Procesar resultados semánticos
    for rank, result in enumerate(semantic_results):
        doc_id = result["file"] + "_" + result["text"][:50]

        # Calcular score RRF
        score = 1 / (k + rank + 1)

        # Acumular score (si ya existe, suma)
        if doc_id in rrf_scores:
            rrf_scores[doc_id] = rrf_scores[doc_id] + score
        else:
            rrf_scores[doc_id] = score

        # Guardar datos del documento
        doc_data[doc_id] = result

    # PASO 3: Procesar resultados BM25 (igual)
    for rank, result in enumerate(bm25_results):
        doc_id = result["file"] + "_" + result["text"][:50]

        score = 1 / (k + rank + 1)

        if doc_id in rrf_scores:
            rrf_scores[doc_id] = rrf_scores[doc_id] + score
        else:
            rrf_scores[doc_id] = score

        doc_data[doc_id] = result

    # PASO 4: Ordenar por score
    # Convertir a lista de tuplas: [(doc_id, score), ...]
    score_list = []
    for doc_id in rrf_scores:
        score = rrf_scores[doc_id]
        score_list.append((doc_id, score))

    # Ordenar por score de mayor a menor
    # Usamos una función normal en vez de lambda
    def get_score(item):
        return item[1]

    score_list.sort(key=get_score, reverse=True)

    # PASO 5: Construir resultado final
    results = []
    for doc_id, score in score_list:
        result = doc_data[doc_id]
        result["rrf_score"] = score
        results.append(result)

    return results


def build_prompt(query, context):
    return f"""
        Use the following context to respond the question, in case of not founding any useful information, respond saying "there is no information available"
        CONTEXT:
        {context}

        QUESTION:   {query}

        ANSWER:
    """


def build_answer(prompt):
    client = OpenAI(api_key="None", base_url="http://127.0.0.1:1234/v1")
    response = client.responses.create(input=prompt, model="essentialai/rnj-1")
    return response.output_text


def main():
    query = input("What do you want to know?  ")
    query_vector = model.encode(query)

    bm25, df = load_bm25_index(db)

    semantic_results = search_query_semantic(query_vector, db, top_k=5)
    bm25_results = search_bm25(query, bm25, df, top_k=5)

    rerank_result = rrf_fusion(semantic_results, bm25_results, k=5)

    context = build_context(rerank_result)

    prompt = build_prompt(query, context)

    answer = build_answer(prompt)

    print("\n=== CONTEXTO RECUPERADO ===")
    for r in rerank_result:
        print(f"📄 {r['file']}: {r['text'][:100]}...")

    print("\n=== RESPUESTA ===")
    print(answer)


if __name__ == "__main__":
    db = lancedb.connect(DB_PATH)
    main()
