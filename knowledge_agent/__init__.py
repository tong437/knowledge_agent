"""
Personal Knowledge Management Agent

A MCP-based intelligent knowledge management system that supports
multi-source knowledge collection, intelligent organization, and semantic search.
"""

__version__ = "0.1.0"
__author__ = "Knowledge Agent Team"

from .models import KnowledgeItem, Category, Tag, Relationship
from .interfaces import DataSourceProcessor, KnowledgeOrganizer, SearchEngine

__all__ = [
    "KnowledgeItem",
    "Category", 
    "Tag",
    "Relationship",
    "DataSourceProcessor",
    "KnowledgeOrganizer", 
    "SearchEngine",
]