from pathlib import Path

# Paths
VAULT_PATH = Path("/home/reezo/Documents/My-notes/")
BASE_PATH = Path(__file__).parent.resolve()
DB_PATH = BASE_PATH / "data" / "lancedb"
EMBED_MODEL_PATH = BASE_PATH / "models" / "embedding"

TABLE_NAME = "obsidian_notes"

# Models
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
LLM_MODEL = "essentialai/rnj-1"
LLM_BASE_URL = "http://127.0.0.1:1234/v1"

DEVICE_EMBED = "cuda"

# Search parameters
TOP_K_SEMANTIC = 50
TOP_K_BM25 = 50
RRF_K = 60
TOP_K_FINAL = 5
