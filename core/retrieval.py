from config import RRF_K, TOP_K_FINAL, TOP_K_SEMANTIC, TOP_K_BM25


class Retriever:
    def __init__(self, db) -> None:
        self.db = db
        self.RRF_K = RRF_K

    def _search_query_semantic(self, query_vector, top_k=TOP_K_SEMANTIC):
        """Search the query into the DB with semantic search"""
        return self.db.semantic_query(query_vector, top_k)

    def _search_bm25(self, query, top_k=TOP_K_BM25):
        return self.db.bm25_query(query, top_k)

    def _rrf_fusion(self, semantic_results, bm25_results):
        """
        Combines semantic and BM25 results.
        Returns combined list sorted by score.
        """

        rrf_scores = {}  # Asociates doc_id with its scoring
        doc_data = {}  # Asociates doc_id with the data

        # Processing of semantic_results
        for rank, result in enumerate(semantic_results):
            doc_id = result["id"]

            score = 1 / (RRF_K + rank + 1)

            rrf_scores[doc_id] = score
            doc_data[doc_id] = result

        # Processing of bm25_results
        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]

            score = 1 / (RRF_K + rank + 1)

            if doc_id in rrf_scores:
                rrf_scores[doc_id] = rrf_scores[doc_id] + score
            else:
                rrf_scores[doc_id] = score

            doc_data[doc_id] = result

        score_list = []
        for doc_id in rrf_scores:
            score = rrf_scores[doc_id]
            score_list.append((doc_id, score))

        score_list.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in score_list:
            result = doc_data[doc_id]
            result["rrf_score"] = score
            results.append((result))

        return results

    def hybrid_search(self, query, query_vector, top_k=TOP_K_FINAL):
        """Full hybrid search: Semantic + BM25 + RFF fusion"""
        semantic = self._search_query_semantic(query_vector)
        bm25 = self._search_bm25(query)
        combined = self._rrf_fusion(semantic, bm25)
        return combined
