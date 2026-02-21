from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
import hashlib


class Chunker:
    """
    Funny name hehe
    This class is in charge of chuncking texts, rn it only supports markdown files
    """
    def __init__(self):
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )

    def _generate_chunk_id(self, filename: str, text: str) -> str:
        """Generate a deterministic ID based on filename and content hash"""
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        return f"{filename}_{content_hash}"

    def process_files(self, files_to_process: dict) -> list:
        """Read files, chunk them, return flat DB-ready documents (without vectors)"""
        documents = []
        for file_path, mod_date in files_to_process.items():
            file = Path(file_path)
            content = file.read_text(encoding="utf-8")
            chunks = self.splitter.split_text(content)

            for chunk in chunks:
                if chunk.page_content.strip():
                    documents.append({
                        "text": chunk.page_content,
                        "file": file.name,
                        "path": str(file),
                        "headers": str(chunk.metadata),
                        "id": self._generate_chunk_id(file.name, chunk.page_content),
                        "date_indexed": mod_date,
                    })
        return documents