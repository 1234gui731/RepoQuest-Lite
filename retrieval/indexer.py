import os

# 强制使用国内 HuggingFace 镜像，防止模型下载卡死
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class HybridIndex:
    def __init__(self, symbols):
        self.symbols = symbols
        self.texts = [f"{s['name']} {s['code']}" for s in symbols]

        # 1. 初始化 BM25 (关键词搜索)
        tokenized_corpus = [self._tokenize(text) for text in self.texts]
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

        # 2. 初始化向量模型 (语义搜索)
        # 使用轻量级模型 all-MiniLM-L6-v2，第一次运行会自动从镜像站下载
        if self.texts:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            # 把代码文本转成向量
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
        # 把用户的查询也转成向量
        query_embedding = self.model.encode([query], show_progress_bar=False)
        # 计算余弦相似度
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(self.symbols[idx], float(similarities[idx])) for idx in top_indices if similarities[idx] > 0.1]

    def search_hybrid(self, query, top_k=3):
        """
        混合检索：简单地把两边的结果合并展示
        （后续我们会用更高级的 RRF 算法，现在先跑通）
        """
        bm25_res = self.search_bm25(query, top_k)
        vector_res = self.search_vector(query, top_k)

        # 按名字去重合并
        seen = set()
        combined = []
        for sym, score in bm25_res + vector_res:
            if sym['name'] not in seen:
                seen.add(sym['name'])
                combined.append((sym, score))
        return combined[:top_k]