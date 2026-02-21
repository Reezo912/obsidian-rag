import lancedb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter
import hashlib
import os

from config import VAULT_PATH, DB_PATH, EMBED_MODEL_PATH


def generate_chunk_id(filename: str, text: str) -> str:
    """Generate a deterministic ID based on filename and content hash."""
    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    return f"{filename}_{content_hash}"


def get_files_with_dates(vault_path: Path) -> dict:
    """Get all .md files with their modification dates."""
    files = {}
    for file in Path(vault_path).rglob("*.md"):
        files[str(file)] = os.path.getmtime(file)
    return files


def get_indexed_files(db) -> dict:
    """Get already indexed files with their indexed dates."""
    if "notes" not in db.list_tables():
        return {}

    table = db.open_table("notes")
    df = table.to_pandas()

    indexed = {}
    for path in df["path"].unique():
        file_rows = df[df["path"] == path]
        if "date_indexed" in file_rows.columns:
            indexed[path] = file_rows["date_indexed"].iloc[0]
        else:
            indexed[path] = 0
    return indexed


def extract_data_md(files_to_process: dict) -> list:
    """Extract chunks only from specified files."""
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    )
    data = []
    for file_path, mod_date in files_to_process.items():
        file = Path(file_path)
        content = file.read_text(encoding="utf-8")
        chunks = splitter.split_text(content)

        for chunk in chunks:
            # Filter empty chunks
            if chunk.page_content.strip():
                data.append(
                    {
                        "text": chunk.page_content,
                        "metadata": {
                            "file": file.name,
                            "path": str(file),
                            "headers": chunk.metadata,
                            "date_modified": mod_date,
                        },
                    }
                )
    return data


def load_and_embed(raw_data: list):
    """Load embedding model and generate vectors for all chunks."""
    if not raw_data:
        return []

    try:
        model = SentenceTransformer(
            "BAAI/bge-large-en-v1.5", cache_folder=EMBED_MODEL_PATH
        )
    except Exception as e:
        print(f"Error loading the model: {e}")
        return []

    texts = [chunk["text"] for chunk in raw_data]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings


def combine_vector_metadata(raw_data: list, vectors) -> list:
    """Combine vectors with metadata into documents ready for DB."""
    documents = []
    for i, chunk in enumerate(raw_data):
        documents.append(
            {
                "text": chunk["text"],
                "vector": vectors[i],
                "file": chunk["metadata"]["file"],
                "path": chunk["metadata"]["path"],
                "headers": str(chunk["metadata"]["headers"]),
                "id": generate_chunk_id(chunk["metadata"]["file"], chunk["text"]),
                "date_indexed": chunk["metadata"]["date_modified"],
            }
        )
    return documents


def save_data(db, new_documents: list, files_to_update: list):
    """Save data, removing old chunks from modified files first."""

    if "notes" in db.table_names():
        table = db.open_table("notes")

        # Delete old chunks from files being updated
        for file_path in files_to_update:
            table.delete(f"path = '{file_path}'")
            print(f"🔄 Deleted old chunks from: {Path(file_path).name}")

        # Add new chunks
        if new_documents:
            table.add(new_documents)
            print(f"✅ Added {len(new_documents)} chunks")
    else:
        table = db.create_table("notes", data=new_documents)
        print(f"✅ Table created with {len(new_documents)} chunks")

    return table


def main():
    db = lancedb.connect(DB_PATH)

    # 1. Get current state
    current_files = get_files_with_dates(VAULT_PATH)
    indexed_files = get_indexed_files(db)

    print(f"📁 Files in vault: {len(current_files)}")
    print(f"📊 Indexed files: {len(indexed_files)}")

    # 2. Detect changes
    files_to_process = {}

    for path, mod_date in current_files.items():
        if path not in indexed_files:
            # New file
            files_to_process[path] = mod_date
            print(f"🆕 New: {Path(path).name}")
        elif mod_date > indexed_files[path]:
            # Modified file
            files_to_process[path] = mod_date
            print(f"📝 Modified: {Path(path).name}")

    # 3. Detect deleted files
    for path in indexed_files:
        if path not in current_files:
            print(f"🗑️ Deleted: {Path(path).name}")
            if "notes" in db.table_names():
                table = db.open_table("notes")
                table.delete(f"path = '{path}'")

    # 4. Process only what's needed
    if not files_to_process:
        print("\n✅ Everything up to date. Nothing to process.")
        return

    print(f"\n🔄 Processing {len(files_to_process)} files...")

    raw_data = extract_data_md(files_to_process)
    print(f"📄 Extracted {len(raw_data)} chunks")

    vectors = load_and_embed(raw_data)
    if len(vectors) == 0:
        return
    print(f"🔢 Generated {len(vectors)} vectors")

    documents = combine_vector_metadata(raw_data, vectors)
    save_data(db, documents, files_to_process.keys())

    print("\n✅ Sync completed")


if __name__ == "__main__":
    main()

