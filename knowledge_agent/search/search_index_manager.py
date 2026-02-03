"""
Search index manager using Whoosh for full-text search.
"""

import os
from typing import List, Optional
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.query import Query
from whoosh.searching import Results
from whoosh.analysis import StandardAnalyzer, CharsetFilter, RegexTokenizer, LowercaseFilter
from whoosh.support.charset import accent_map
from datetime import datetime

from ..models import KnowledgeItem


class SearchIndexManager:
    """
    Manages the full-text search index using Whoosh.
    
    Provides functionality for creating, updating, and querying
    a search index for knowledge items.
    """
    
    def __init__(self, index_dir: str):
        """
        Initialize the search index manager.
        
        Args:
            index_dir: Directory path for storing the search index
        """
        self.index_dir = index_dir
        self.schema = self._create_schema()
        self.ix = self._get_or_create_index()
    
    def _create_schema(self) -> Schema:
        """
        Create the Whoosh schema for knowledge items.
        
        Returns:
            Schema: The Whoosh schema definition
        """
        # Create an analyzer that supports Chinese and other languages
        # Using character n-grams for better CJK support
        analyzer = RegexTokenizer(r"\w+") | LowercaseFilter() | CharsetFilter(accent_map)
        
        return Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True, field_boost=2.0, analyzer=analyzer),
            content=TEXT(stored=True, analyzer=analyzer),
            source_type=ID(stored=True),
            source_path=TEXT(stored=True),
            categories=KEYWORD(stored=True, commas=True, scorable=True, lowercase=True),
            tags=KEYWORD(stored=True, commas=True, scorable=True, lowercase=True),
            created_at=DATETIME(stored=True),
            updated_at=DATETIME(stored=True),
        )
    
    def _get_or_create_index(self) -> index.Index:
        """
        Get existing index or create a new one.
        
        Returns:
            Index: The Whoosh index object
        """
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
        
        if index.exists_in(self.index_dir):
            return index.open_dir(self.index_dir)
        else:
            return index.create_in(self.index_dir, self.schema)
    
    def add_item(self, item: KnowledgeItem) -> None:
        """
        Add a knowledge item to the search index.
        
        Args:
            item: The knowledge item to index
        """
        writer = self.ix.writer()
        try:
            writer.add_document(
                id=item.id,
                title=item.title,
                content=item.content,
                source_type=item.source_type.value,
                source_path=item.source_path,
                categories=",".join([cat.name for cat in item.categories]),
                tags=",".join([tag.name for tag in item.tags]),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to add item to index: {e}")
    
    def update_item(self, item: KnowledgeItem) -> None:
        """
        Update a knowledge item in the search index.
        
        This removes the old version and adds the new version.
        
        Args:
            item: The knowledge item to update
        """
        writer = self.ix.writer()
        try:
            writer.update_document(
                id=item.id,
                title=item.title,
                content=item.content,
                source_type=item.source_type.value,
                source_path=item.source_path,
                categories=",".join([cat.name for cat in item.categories]),
                tags=",".join([tag.name for tag in item.tags]),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to update item in index: {e}")
    
    def remove_item(self, item_id: str) -> None:
        """
        Remove a knowledge item from the search index.
        
        Args:
            item_id: ID of the item to remove
        """
        writer = self.ix.writer()
        try:
            writer.delete_by_term("id", item_id)
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to remove item from index: {e}")
    
    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        Rebuild the entire search index from scratch.
        
        Args:
            items: List of all knowledge items to index
        """
        # Close and recreate the index
        self.ix.close()
        
        # Recreate the index
        self.ix = index.create_in(self.index_dir, self.schema)
        
        # Add all items
        writer = self.ix.writer()
        try:
            for item in items:
                writer.add_document(
                    id=item.id,
                    title=item.title,
                    content=item.content,
                    source_type=item.source_type.value,
                    source_path=item.source_path,
                    categories=",".join([cat.name for cat in item.categories]),
                    tags=",".join([tag.name for tag in item.tags]),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to rebuild index: {e}")
    
    def search(
        self,
        query_str: str,
        fields: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        Search the index with a query string.
        
        Args:
            query_str: The search query string
            fields: List of fields to search in (default: title and content)
            limit: Maximum number of results to return
            
        Returns:
            List[dict]: List of result dictionaries with stored fields and scores
        """
        if fields is None:
            fields = ["title", "content"]
        
        with self.ix.searcher() as searcher:
            # Use OR parser for better matching with wildcards
            from whoosh.qparser import OrGroup
            parser = MultifieldParser(fields, schema=self.schema, group=OrGroup)
            
            # Add wildcards to improve matching for CJK characters
            # Split query into terms and add wildcards
            terms = query_str.split()
            wildcard_query = " OR ".join([f"*{term}*" for term in terms])
            
            try:
                query = parser.parse(wildcard_query)
            except:
                # Fallback to original query if parsing fails
                query = parser.parse(query_str)
            
            results = searcher.search(query, limit=limit)
            # Return a copy of results with scores that persists after searcher closes
            return [{'score': hit.score, **dict(hit)} for hit in results]
    
    def search_by_field(
        self,
        field: str,
        query_str: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Search a specific field in the index.
        
        Args:
            field: The field name to search
            query_str: The search query string
            limit: Maximum number of results to return
            
        Returns:
            List[dict]: List of result dictionaries with stored fields and scores
        """
        with self.ix.searcher() as searcher:
            parser = QueryParser(field, schema=self.schema)
            
            # Add wildcards for better CJK matching
            terms = query_str.split()
            wildcard_query = " OR ".join([f"*{term}*" for term in terms])
            
            try:
                query = parser.parse(wildcard_query)
            except:
                query = parser.parse(query_str)
            
            results = searcher.search(query, limit=limit)
            # Return a copy of results with scores that persists after searcher closes
            return [{'score': hit.score, **dict(hit)} for hit in results]
    
    def get_all_ids(self) -> List[str]:
        """
        Get all document IDs in the index.
        
        Returns:
            List[str]: List of all document IDs
        """
        with self.ix.searcher() as searcher:
            return [doc["id"] for doc in searcher.all_stored_fields()]
    
    def close(self) -> None:
        """Close the index."""
        if hasattr(self, 'ix') and self.ix is not None:
            self.ix.close()
