# 📚 Obsidian RAG

> ⚠️ **Work in Progress** — Modular refactor in progress. Breaking changes expected.

Local-first RAG system for chatting with your [Obsidian](https://obsidian.md/) notes. Hybrid search (semantic + BM25), RRF fusion, and LLM-powered answers — all running on your machine.

## Features

- 🔒 **100% Local** — No cloud dependencies, your notes stay private
- 🔍 **Hybrid Search** — Combines vector similarity (dense) with full-text search (BM25)
- 🔀 **RRF Fusion** — Reciprocal Rank Fusion to merge results from both search methods
- 📎 **Source Citations** — Every answer references the original note
- ⚡ **GPU Accelerated** — Optimized for NVIDIA GPUs

## Tech Stack

| Component | Technology |
|-----------|------------|
| Vector DB | [LanceDB](https://lancedb.github.io/lancedb/) (embedded, serverless) |
| Embeddings | [bge-large-en-v1.5](https://huggingface.co/BAAI/bge-large-en-v1.5) (1024 dims) |
| Full-text Search | LanceDB native FTS (BM25) |
| LLM | [RNJ-1 8B](https://www.essential.ai/) via [LM Studio](https://lmstudio.ai/) |
| Chunking | LangChain `MarkdownHeaderTextSplitter` |

## Project Structure

```
obsidian-rag/
├── config.py              # Centralized configuration
├── core/
│   ├── db.py              # LanceDB wrapper (vector + FTS search)
│   ├── chunking.py        # Markdown splitting & chunk ID generation
│   ├── embeddings.py      # Embedding model wrapper
│   ├── retrieval.py       # Hybrid search + RRF fusion
│   └── llm.py             # LLM client (LM Studio)
├── scripts/
│   ├── ingest.py          # Ingestion pipeline (change detection)
│   └── query.py           # CLI query interface
├── data/
│   └── lancedb/           # Vector database (gitignored)
└── models/
    └── embedding/         # Cached model weights (gitignored)
```

## Setup

```bash
# 1. Clone
git clone https://github.com/<your-user>/obsidian-rag.git
cd obsidian-rag

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
# Edit config.py — set VAULT_PATH to your Obsidian vault location

# 4. Start LM Studio with RNJ-1 (or any compatible model)

# 5. Ingest your notes
python scripts/ingest.py

# 6. Query
python scripts/query.py
```

## How It Works

```
User Query
    │
    ▼
┌──────────┐
│ Embed    │──► Query Vector
│ Query    │
└──────────┘
    │
    ├──► Vector Search (Top 50)
    │
    ├──► BM25 Search (Top 50)
    │
    ▼
┌──────────┐
│ RRF      │──► Combined Top Results
│ Fusion   │
└──────────┘
    │
    ▼
┌──────────┐
│ LLM      │──► Answer with Citations
└──────────┘
```

## Roadmap

- [x] Ingestion pipeline with change detection
- [x] Hybrid search (vector + BM25)
- [x] RRF fusion
- [x] LLM integration
- [ ] Cross-encoder re-ranking
- [ ] Confidence threshold filtering
- [ ] File watcher (auto-sync on changes)
- [ ] FastAPI endpoint
- [ ] Open WebUI integration

## License

MIT
