import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class HybridIndex:
    def __init__(self, symbols):
        self.symbols = symbols
        self.texts = [f"{s['name']} {s['code']}" for s in symbols]

        tokenized_corpus = [self._tokenize(text) for text in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

        if self.texts:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings = self.model.encode(self.texts, show_progress_bar=False)
        else:
            self.model = None
            self.embeddings = None

    def _tokenize(self, text):
        return text.lower().split()

    def search_bm25(self, query, top_k=3):
        if not self.bm25: return []
        scores = self.bm25.get_scores(self._tokenize(query))
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.symbols[idx], float(scores[idx])) for idx in top_indices if scores[idx] > 0]

    def search_vector(self, query, top_k=3):
        if self.embeddings is None: return []
        query_embedding = self.model.encode([query], show_progress_bar=False)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(self.symbols[idx], float(similarities[idx])) for idx in top_indices if similarities[idx] > 0.1]

    def search_hybrid(self, query, top_k=3, k=60):
        """使用 RRF (Reciprocal Rank Fusion) 算法融合两路检索结果"""
        if not self.bm25 or self.embeddings is None:
            return []

        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_ranked_indices = np.argsort(bm25_scores)[::-1]

        query_embedding = self.model.encode([query], show_progress_bar=False)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        vector_ranked_indices = np.argsort(similarities)[::-1]

        rrf_scores = {}
        for rank, idx in enumerate(bm25_ranked_indices):
            if bm25_scores[idx] > 0:
                rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank + 1)

        for rank, idx in enumerate(vector_ranked_indices):
            if similarities[idx] > 0.2:
                rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank + 1)

        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in sorted_items[:top_k]:
            results.append((self.symbols[idx], float(score)))
        return results