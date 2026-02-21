from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
import hashlib

"""
This script only works for .MD at the moment, since its for my obsidian Vault 

TODO add more data types
"""
### No clase en este script por simplicidad, si en el futuro anado otros tipos de documentos como input, hare una clase.


def generate_chunk_id(filename: str, text: str) -> str:
    """Generate a deterministic ID based on filename and content hash."""
    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    return f"{filename}_{content_hash}"


def chunk_md(content: str, filename: str, filepath: str, mod_date) -> list:
    """Function to genereate chunks out of markdown strings"""
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    )

    chunks = splitter.split_text(content)
    data = []
    for chunk in chunks:
        # Filter empty chunks
        if chunk.page_content.strip():
            data.append(
                {
                    "text": chunk.page_content,
                    "metadata": {
                        "file": filename,
                        "path": str(filepath),
                        "headers": chunk.metadata,
                        "date_modified": mod_date,
                    },
                }
            )
    return data
