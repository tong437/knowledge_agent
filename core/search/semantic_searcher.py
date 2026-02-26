"""
基于 TF-IDF 和余弦相似度的语义搜索模块。
"""

from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from core.models import KnowledgeItem
from core.models.knowledge_chunk import KnowledgeChunk


class SemanticSearcher:
    """
    使用 TF-IDF 向量化和余弦相似度提供语义搜索能力，
    用于查找相关的知识条目和分块。
    """

    def __init__(self):
        """初始化语义搜索器。"""
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.item_vectors = None
        self.items: List[KnowledgeItem] = []
        self.is_fitted = False
        self.chunk_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.chunk_vectors = None
        self.chunks: List[KnowledgeChunk] = []
        self.is_chunk_fitted: bool = False

    def fit(self, items: List[KnowledgeItem]) -> None:
        """
        对知识条目集合进行向量化拟合。

        Args:
            items: 用于构建语义模型的知识条目列表
        """
        if not items:
            self.is_fitted = False
            return

        self.items = items
        documents = [
            f"{item.title} {item.content}"
            for item in items
        ]

        try:
            self.item_vectors = self.vectorizer.fit_transform(documents)
            self.is_fitted = True
        except ValueError:
            self.is_fitted = False

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        搜索与查询语义相似的知识条目。

        Args:
            query: 搜索查询字符串
            top_k: 最大返回结果数
            min_similarity: 最低相似度阈值（0.0 到 1.0）

        Returns:
            按相关性排序的 (KnowledgeItem, 相似度分数) 元组列表
        """
        if not self.is_fitted or not self.items:
            return []

        try:
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.item_vectors)[0]
            valid_indices = np.where(similarities >= min_similarity)[0]
            sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]

            results = [
                (self.items[idx], float(similarities[idx]))
                for idx in sorted_indices[:top_k]
            ]

            return results
        except Exception:
            return []

    def find_similar_items(
        self,
        item: KnowledgeItem,
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        查找与给定知识条目相似的条目。

        Args:
            item: 参考知识条目
            top_k: 最大返回相似条目数
            min_similarity: 最低相似度阈值（0.0 到 1.0）

        Returns:
            按相关性排序的 (KnowledgeItem, 相似度分数) 元组列表
        """
        if not self.is_fitted or not self.items:
            return []

        try:
            item_idx = None
            for idx, stored_item in enumerate(self.items):
                if stored_item.id == item.id:
                    item_idx = idx
                    break

            if item_idx is None:
                query = f"{item.title} {item.content}"
                return self.search(query, top_k + 1, min_similarity)[1:]

            item_vector = self.item_vectors[item_idx:item_idx+1]
            similarities = cosine_similarity(item_vector, self.item_vectors)[0]
            valid_indices = np.where(similarities >= min_similarity)[0]
            valid_indices = valid_indices[valid_indices != item_idx]
            sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]

            results = [
                (self.items[idx], float(similarities[idx]))
                for idx in sorted_indices[:top_k]
            ]

            return results
        except Exception:
            return []

    def get_query_terms(self, query: str, top_n: int = 10) -> List[str]:
        """
        从查询中提取最重要的词项。

        Args:
            query: 搜索查询字符串
            top_n: 返回的词项数量

        Returns:
            查询中的重要词项列表
        """
        if not self.is_fitted:
            return []

        try:
            query_vector = self.vectorizer.transform([query])
            feature_names = self.vectorizer.get_feature_names_out()
            non_zero_indices = query_vector.nonzero()[1]
            weights = query_vector.data
            sorted_indices = np.argsort(-weights)

            top_terms = [
                feature_names[non_zero_indices[idx]]
                for idx in sorted_indices[:top_n]
            ]

            return top_terms
        except Exception:
            return []

    def update_item(self, item: KnowledgeItem) -> None:
        """
        更新语义模型中的条目，需要重新拟合整个模型。

        Args:
            item: 待更新的知识条目
        """
        for idx, stored_item in enumerate(self.items):
            if stored_item.id == item.id:
                self.items[idx] = item
                break
        else:
            self.items.append(item)

        self.fit(self.items)

    def remove_item(self, item_id: str) -> None:
        """
        从语义模型中移除条目，需要重新拟合整个模型。

        Args:
            item_id: 待移除条目的 ID
        """
        self.items = [item for item in self.items if item.id != item_id]

        if self.items:
            self.fit(self.items)
        else:
            self.is_fitted = False

    def fit_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """
        对分块集合进行向量化拟合。

        Args:
            chunks: 待拟合的知识分块列表
        """
        if not chunks:
            self.is_chunk_fitted = False
            return

        self.chunks = chunks
        documents = [f"{chunk.heading} {chunk.content}" for chunk in chunks]

        try:
            self.chunk_vectors = self.chunk_vectorizer.fit_transform(documents)
            self.is_chunk_fitted = True
        except ValueError:
            self.is_chunk_fitted = False

    def search_chunks(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        在分块级别进行语义搜索。

        Args:
            query: 搜索查询字符串
            top_k: 返回的最大结果数
            min_similarity: 最低相似度阈值（0.0 到 1.0）

        Returns:
            按相关性排序的 (KnowledgeChunk, 相似度分数) 元组列表
        """
        if not self.is_chunk_fitted or not self.chunks:
            return []

        try:
            query_vector = self.chunk_vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.chunk_vectors)[0]
            valid_indices = np.where(similarities >= min_similarity)[0]
            sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]

            results = [
                (self.chunks[idx], float(similarities[idx]))
                for idx in sorted_indices[:top_k]
            ]
            return results
        except Exception:
            return []

    def update_chunks_for_item(self, item_id: str, chunks: List[KnowledgeChunk]) -> None:
        """
        更新指定条目的分块数据，移除旧分块后添加新分块并重新拟合。

        Args:
            item_id: 知识条目 ID
            chunks: 新的分块列表
        """
        self.chunks = [c for c in self.chunks if c.item_id != item_id]
        self.chunks.extend(chunks)
        self.fit_chunks(self.chunks)

    def remove_chunks_for_item(self, item_id: str) -> None:
        """
        移除指定条目的所有分块并重新拟合。

        Args:
            item_id: 知识条目 ID
        """
        self.chunks = [c for c in self.chunks if c.item_id != item_id]
        if self.chunks:
            self.fit_chunks(self.chunks)
        else:
            self.is_chunk_fitted = False
