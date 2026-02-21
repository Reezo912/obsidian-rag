import sys
import os
from pathlib import Path

# Add the project root (parent directory of scripts/) to sys.path
# so Python can find 'core' and 'config'
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent
sys.path.append(str(project_root))

import lancedb
from core.db import Database
from core.embeddings import Embedding
from core.chunking import Chunker

from config import VAULT_PATH, DB_PATH, EMBED_MODEL_PATH, TABLE_NAME


def get_files_with_dates(vault_path: Path) -> dict:
    """Get all .md files with their modification dates."""
    files = {}
    for file in Path(vault_path).rglob("*.md"):
        files[str(file)] = os.path.getmtime(file)
    return files


def main():
    db = Database(DB_PATH)
    indexed_files = db.get_indexed_files()
    current_files = get_files_with_dates(VAULT_PATH)
    
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
            if TABLE_NAME in db.db.table_names():
                table = db.db.open_table(TABLE_NAME)
                table.delete(f"path = '{path}'")

    # 4. Process only what's needed
    if not files_to_process:
        print("\n✅ Everything up to date. Nothing to process.")
        return
    
    print(f"\n🔄 Processing {len(files_to_process)} files...")

    chunker = Chunker()
    documents = chunker.process_files(files_to_process)
    print(f"📄 Extracted {len(documents)} chunks")

    if len(documents) == 0:
        return

    embedder = Embedding(EMBED_MODEL_PATH)
    vectors = embedder.embed_text(documents)

    print(f"🔢 Generated {len(vectors)} vectors")

    for i, doc in enumerate(documents):
        doc["vector"] = vectors[i]

    db.save_data(TABLE_NAME, documents, list(files_to_process.keys()))

    print("\n✅ Sync completed")


if __name__ == "__main__":
    main()
