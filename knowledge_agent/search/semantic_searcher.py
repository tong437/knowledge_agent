"""
Semantic search functionality using TF-IDF and cosine similarity.
"""

from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..models import KnowledgeItem
from ..models.knowledge_chunk import KnowledgeChunk


class SemanticSearcher:
    """
    Provides semantic search capabilities using TF-IDF vectorization
    and cosine similarity for finding relevant knowledge items.
    """
    
    def __init__(self):
        """Initialize the semantic searcher."""
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
        Fit the vectorizer on a collection of knowledge items.
        
        Args:
            items: List of knowledge items to build the semantic model from
        """
        if not items:
            self.is_fitted = False
            return
        
        self.items = items
        
        # Combine title and content for better semantic understanding
        documents = [
            f"{item.title} {item.content}"
            for item in items
        ]
        
        try:
            self.item_vectors = self.vectorizer.fit_transform(documents)
            self.is_fitted = True
        except ValueError:
            # Handle case where all documents are empty or invalid
            self.is_fitted = False
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Search for knowledge items semantically similar to the query.
        
        Args:
            query: The search query string
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of tuples (KnowledgeItem, similarity_score) sorted by relevance
        """
        if not self.is_fitted or not self.items:
            return []
        
        try:
            # Transform the query using the fitted vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity between query and all items
            similarities = cosine_similarity(query_vector, self.item_vectors)[0]
            
            # Get indices of items above the minimum similarity threshold
            valid_indices = np.where(similarities >= min_similarity)[0]
            
            # Sort by similarity score in descending order
            sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]
            
            # Return top_k results
            results = [
                (self.items[idx], float(similarities[idx]))
                for idx in sorted_indices[:top_k]
            ]
            
            return results
        except Exception:
            # Return empty results if search fails
            return []
    
    def find_similar_items(
        self,
        item: KnowledgeItem,
        top_k: int = 10,
        min_similarity: float = 0.05
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Find items similar to a given knowledge item.
        
        Args:
            item: The reference knowledge item
            top_k: Maximum number of similar items to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of tuples (KnowledgeItem, similarity_score) sorted by relevance
        """
        if not self.is_fitted or not self.items:
            return []
        
        try:
            # Find the index of the given item
            item_idx = None
            for idx, stored_item in enumerate(self.items):
                if stored_item.id == item.id:
                    item_idx = idx
                    break
            
            if item_idx is None:
                # Item not in the collection, search by content
                query = f"{item.title} {item.content}"
                return self.search(query, top_k + 1, min_similarity)[1:]  # Exclude the item itself
            
            # Get the item's vector
            item_vector = self.item_vectors[item_idx:item_idx+1]
            
            # Calculate cosine similarity with all other items
            similarities = cosine_similarity(item_vector, self.item_vectors)[0]
            
            # Get indices of items above the minimum similarity threshold
            valid_indices = np.where(similarities >= min_similarity)[0]
            
            # Exclude the item itself
            valid_indices = valid_indices[valid_indices != item_idx]
            
            # Sort by similarity score in descending order
            sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]
            
            # Return top_k results
            results = [
                (self.items[idx], float(similarities[idx]))
                for idx in sorted_indices[:top_k]
            ]
            
            return results
        except Exception:
            # Return empty results if search fails
            return []
    
    def get_query_terms(self, query: str, top_n: int = 10) -> List[str]:
        """
        Extract the most important terms from a query.
        
        Args:
            query: The search query string
            top_n: Number of top terms to return
            
        Returns:
            List of important terms from the query
        """
        if not self.is_fitted:
            return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get non-zero features and their weights
            non_zero_indices = query_vector.nonzero()[1]
            weights = query_vector.data
            
            # Sort by weight
            sorted_indices = np.argsort(-weights)
            
            # Get top terms
            top_terms = [
                feature_names[non_zero_indices[idx]]
                for idx in sorted_indices[:top_n]
            ]
            
            return top_terms
        except Exception:
            return []
    
    def update_item(self, item: KnowledgeItem) -> None:
        """
        Update an item in the semantic model.
        
        This requires refitting the entire model.
        
        Args:
            item: The knowledge item to update
        """
        # Find and update the item
        for idx, stored_item in enumerate(self.items):
            if stored_item.id == item.id:
                self.items[idx] = item
                break
        else:
            # Item not found, add it
            self.items.append(item)
        
        # Refit the model
        self.fit(self.items)
    
    def remove_item(self, item_id: str) -> None:
        """
        Remove an item from the semantic model.
        
        This requires refitting the entire model.
        
        Args:
            item_id: ID of the item to remove
        """
        self.items = [item for item in self.items if item.id != item_id]
        
        # Refit the model
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
        更新指定 item 的分块数据，移除旧分块后添加新分块并重新拟合。

        Args:
            item_id: 知识条目 ID
            chunks: 新的分块列表
        """
        self.chunks = [c for c in self.chunks if c.item_id != item_id]
        self.chunks.extend(chunks)
        self.fit_chunks(self.chunks)

    def remove_chunks_for_item(self, item_id: str) -> None:
        """
        移除指定 item 的所有分块并重新拟合。

        Args:
            item_id: 知识条目 ID
        """
        self.chunks = [c for c in self.chunks if c.item_id != item_id]
        if self.chunks:
            self.fit_chunks(self.chunks)
        else:
            self.is_chunk_fitted = False
