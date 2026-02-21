import lancedb
from pathlib import Path

from config import DB_PATH, TABLE_NAME


class Database:
    def __init__(self, path) -> None:
        self.db = lancedb.connect(path)
        self._table = self.get_table()

    def get_table(self, table_name: str = TABLE_NAME):
        """Gets table if exists, returns None otherwise"""
        if table_name in self.db.table_names():
            self._table = self.db.open_table(table_name)
            return self._table
        return None

    def save_data(self, table_name, new_documents, files_to_update):
        """Save data, removing old chunks from modified files first"""
        try:
            self._table = self.get_table(table_name)

            if self._table is None:
                self._table = self.db.create_table(name=table_name, data=new_documents)
                self._table.create_fts_index("text")
                print(f"✅ Table created with {len(new_documents)} chunks")
            else:
                for file_path in files_to_update:
                    self._table.delete(f"path = '{file_path}'")
                    print(f"🔄 Deleted old chunks from: {Path(file_path).name}")

                if new_documents:
                    self._table.add(new_documents)
                    print(f"✅ Added {len(new_documents)} chunks")

            return self._table
        except Exception as e:
            print(f"Error saving data: {e}")
            return None

    def semantic_query(self, query_vector, top_k):
        """Vector similarity search"""
        try:
            results = self._table.search(query_vector).limit(top_k).to_list()
            return results
        except Exception as e:
            print(f"Error in semantic query: {e}")
            return []

    def bm25_query(self, query, top_k):
        """Full-text BM25 search"""
        try:
            results = self._table.search(query, query_type="fts").limit(top_k).to_list()
            return results
        except Exception as e:
            print(f"Error in BM25 query: {e}")
            return []

    def get_indexed_files(self):
        """Returns dict of {path: date_indexed} for change detection"""
        try:
            if self._table is None:
                return {}

            df = self._table.to_pandas()
            indexed = {}
            for path in df["path"].unique():
                file_rows = df[df["path"] == path]
                if "date_indexed" in file_rows.columns:
                    indexed[path] = file_rows["date_indexed"].iloc[0]
                else:
                    indexed[path] = 0
            return indexed
        except Exception as e:
            print(f"Error getting indexed files: {e}")
            return {}
