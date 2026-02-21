from sentence_transformers import SentenceTransformer
from config import DEVICE_EMBED


class Embedding:
    def __init__(self, embed_path) -> None:
        self.path = embed_path
        self.model = self._load_model()

    def _load_model(self):
        try:
            return SentenceTransformer(
                "BAAI/bge-large-en-v1.5", cache_folder=self.path, device=DEVICE_EMBED
            )
        except Exception as e:
            print("Error loading embedding model: ", e)
            return None

    def embed_text(self, batch):
        if not batch:
            return []
        texts = [chunk["text"] for chunk in batch]
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings

    def embed_query(self, query):
        embed_query = self.model.encode(query)
        return embed_query
