"""
Main search engine implementation.
"""

import time
from typing import List, Optional
from ..interfaces import SearchEngine
from ..models import (
    KnowledgeItem,
    SearchResult,
    SearchResults,
    SearchOptions
)
from .search_index_manager import SearchIndexManager
from .semantic_searcher import SemanticSearcher
from .result_processor import ResultProcessor


class SearchEngineImpl(SearchEngine):
    """
    Complete search engine implementation combining keyword and semantic search.
    
    Integrates full-text indexing with Whoosh and semantic search with TF-IDF
    to provide comprehensive search capabilities.
    """
    
    def __init__(self, index_dir: str):
        """
        Initialize the search engine.
        
        Args:
            index_dir: Directory path for storing the search index
        """
        self.index_manager = SearchIndexManager(index_dir)
        self.semantic_searcher = SemanticSearcher()
        self.result_processor = ResultProcessor()
    
    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        Execute a search query and return results.
        
        Combines keyword search (via Whoosh) and semantic search (via TF-IDF)
        for comprehensive results.
        
        Args:
            query: The search query string
            options: Search configuration options
            
        Returns:
            SearchResults: Structured search results with metadata
        """
        start_time = time.time()
        
        # Perform keyword search
        keyword_results = self._keyword_search(query, options.max_results * 2)
        
        # Perform semantic search if the model is fitted
        semantic_results = []
        if self.semantic_searcher.is_fitted:
            semantic_results = self._semantic_search(query, options.max_results * 2)
        
        # Merge results
        if keyword_results and semantic_results:
            merged_results = self.result_processor.merge_results(
                keyword_results,
                semantic_results,
                keyword_weight=0.6,
                semantic_weight=0.4
            )
        elif keyword_results:
            merged_results = keyword_results
        elif semantic_results:
            merged_results = semantic_results
        else:
            merged_results = []
        
        # Apply options (filtering, sorting, grouping)
        search_results = self.result_processor.apply_options(merged_results, options)
        
        # Set query and timing
        search_results.query = query
        search_results.search_time_ms = (time.time() - start_time) * 1000
        
        return search_results
    
    def _keyword_search(
        self,
        query: str,
        limit: int
    ) -> List[SearchResult]:
        """
        Perform keyword-based search using Whoosh.
        
        Args:
            query: The search query string
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            # Search the index
            whoosh_results = self.index_manager.search(query, limit=limit)
            
            # Convert to SearchResult objects
            results = []
            for hit in whoosh_results:
                # Reconstruct the knowledge item from stored fields
                item = self._reconstruct_item_from_hit(hit)
                if item:
                    # Get the score from Whoosh (already included in hit dict)
                    # Normalize score to 0-1 range (Whoosh scores can vary)
                    raw_score = hit.get('score', 0.0)
                    relevance_score = min(raw_score / 10.0, 1.0) if raw_score > 0 else 0.5
                    
                    result = SearchResult(
                        item=item,
                        relevance_score=relevance_score,
                        matched_fields=['title', 'content'],
                        highlights=[]
                    )
                    results.append(result)
            
            return results
        except Exception:
            return []
    
    def _semantic_search(
        self,
        query: str,
        limit: int
    ) -> List[SearchResult]:
        """
        Perform semantic search using TF-IDF.
        
        Args:
            query: The search query string
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            # Search using semantic searcher
            semantic_results = self.semantic_searcher.search(
                query,
                top_k=limit,
                min_similarity=0.05  # 降低阈值以获得更多结果
            )
            
            # Convert to SearchResult objects
            results = []
            for item, similarity in semantic_results:
                result = SearchResult(
                    item=item,
                    relevance_score=similarity,
                    matched_fields=['semantic'],
                    highlights=[]
                )
                results.append(result)
            
            return results
        except Exception:
            return []
    
    def _reconstruct_item_from_hit(self, hit: dict) -> Optional[KnowledgeItem]:
        """
        Reconstruct a KnowledgeItem from a Whoosh search hit.
        
        Note: This is a simplified reconstruction. In a real system,
        you would fetch the complete item from the storage layer.
        
        Args:
            hit: Dictionary containing stored fields from Whoosh
            
        Returns:
            KnowledgeItem or None if reconstruction fails
        """
        try:
            from ..models import SourceType, Category, Tag
            from datetime import datetime
            
            # Parse categories
            categories = []
            if hit.get('categories'):
                cat_names = hit['categories'].split(',')
                categories = [
                    Category(id=name, name=name, description="", parent_id=None, confidence=1.0)
                    for name in cat_names if name
                ]
            
            # Parse tags
            tags = []
            if hit.get('tags'):
                tag_names = hit['tags'].split(',')
                tags = [
                    Tag(id=name, name=name, color="#000000", usage_count=1)
                    for name in tag_names if name
                ]
            
            # Create knowledge item
            item = KnowledgeItem(
                id=hit['id'],
                title=hit['title'],
                content=hit['content'],
                source_type=SourceType(hit['source_type']),
                source_path=hit['source_path'],
                categories=categories,
                tags=tags,
                metadata={},
                created_at=hit.get('created_at', datetime.now()),
                updated_at=hit.get('updated_at', datetime.now()),
                embedding=None
            )
            
            return item
        except Exception:
            return None
    
    def suggest(self, partial_query: str) -> List[str]:
        """
        Provide query suggestions based on partial input.
        
        Args:
            partial_query: Partial query string
            
        Returns:
            List[str]: List of suggested complete queries
        """
        # Simple implementation: extract important terms from the semantic model
        if self.semantic_searcher.is_fitted:
            terms = self.semantic_searcher.get_query_terms(partial_query, top_n=5)
            return terms
        return []
    
    def update_index(self, item: KnowledgeItem) -> None:
        """
        Update the search index with a new or modified knowledge item.
        
        Args:
            item: The knowledge item to index
        """
        # Update keyword index
        self.index_manager.update_item(item)
        
        # Update semantic model
        self.semantic_searcher.update_item(item)
    
    def remove_from_index(self, item_id: str) -> None:
        """
        Remove a knowledge item from the search index.
        
        Args:
            item_id: ID of the item to remove
        """
        # Remove from keyword index
        self.index_manager.remove_item(item_id)
        
        # Remove from semantic model
        self.semantic_searcher.remove_item(item_id)
    
    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        Rebuild the entire search index from scratch.
        
        Args:
            items: List of all knowledge items to index
        """
        # Rebuild keyword index
        self.index_manager.rebuild_index(items)
        
        # Rebuild semantic model
        self.semantic_searcher.fit(items)
    
    def get_similar_items(
        self,
        item: KnowledgeItem,
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """
        Find items similar to the given knowledge item.
        
        Args:
            item: The reference knowledge item
            limit: Maximum number of similar items to return
            
        Returns:
            List[KnowledgeItem]: List of similar items
        """
        if not self.semantic_searcher.is_fitted:
            return []
        
        # Use semantic search to find similar items
        similar_results = self.semantic_searcher.find_similar_items(
            item,
            top_k=limit,
            min_similarity=0.05  # 降低阈值以获得更多相似结果
        )
        
        return [item for item, _ in similar_results]
    
    def close(self) -> None:
        """Close the search engine and release resources."""
        self.index_manager.close()
