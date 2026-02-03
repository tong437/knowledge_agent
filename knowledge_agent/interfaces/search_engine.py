"""
Search engine interface.
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import SearchResults, SearchOptions, KnowledgeItem


class SearchEngine(ABC):
    """
    Abstract base class for knowledge search functionality.
    
    Defines the interface for semantic search, natural language queries,
    and search result processing.
    """
    
    @abstractmethod
    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        Execute a search query and return results.
        
        Args:
            query: The search query string
            options: Search configuration options
            
        Returns:
            SearchResults: Structured search results with metadata
        """
        pass
    
    @abstractmethod
    def suggest(self, partial_query: str) -> List[str]:
        """
        Provide query suggestions based on partial input.
        
        Args:
            partial_query: Partial query string
            
        Returns:
            List[str]: List of suggested complete queries
        """
        pass
    
    @abstractmethod
    def update_index(self, item: KnowledgeItem) -> None:
        """
        Update the search index with a new or modified knowledge item.
        
        Args:
            item: The knowledge item to index
        """
        pass
    
    @abstractmethod
    def remove_from_index(self, item_id: str) -> None:
        """
        Remove a knowledge item from the search index.
        
        Args:
            item_id: ID of the item to remove
        """
        pass
    
    @abstractmethod
    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        Rebuild the entire search index from scratch.
        
        Args:
            items: List of all knowledge items to index
        """
        pass
    
    @abstractmethod
    def get_similar_items(self, item: KnowledgeItem, limit: int = 10) -> List[KnowledgeItem]:
        """
        Find items similar to the given knowledge item.
        
        Args:
            item: The reference knowledge item
            limit: Maximum number of similar items to return
            
        Returns:
            List[KnowledgeItem]: List of similar items
        """
        pass