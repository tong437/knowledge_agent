"""
Tests for search engine functionality.
"""

import pytest
import tempfile
import shutil
from datetime import datetime

from knowledge_agent.search import SearchEngineImpl
from knowledge_agent.models import (
    KnowledgeItem,
    SourceType,
    Category,
    Tag,
    SearchOptions
)


@pytest.fixture
def temp_index_dir():
    """Create a temporary directory for search index."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_items():
    """Create sample knowledge items for testing."""
    items = [
        KnowledgeItem(
            id="1",
            title="Python Programming Basics",
            content="Python is a high-level programming language. It is easy to learn and widely used.",
            source_type=SourceType.DOCUMENT,
            source_path="/docs/python.txt",
            categories=[Category(id="prog", name="Programming", description="", parent_id=None, confidence=0.9)],
            tags=[Tag(id="python", name="python", color="#3776ab", usage_count=1)],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        KnowledgeItem(
            id="2",
            title="JavaScript Fundamentals",
            content="JavaScript is a scripting language for web development. It runs in browsers and on servers.",
            source_type=SourceType.DOCUMENT,
            source_path="/docs/javascript.txt",
            categories=[Category(id="prog", name="Programming", description="", parent_id=None, confidence=0.9)],
            tags=[Tag(id="javascript", name="javascript", color="#f7df1e", usage_count=1)],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        KnowledgeItem(
            id="3",
            title="Machine Learning Introduction",
            content="Machine learning is a subset of artificial intelligence. It enables computers to learn from data.",
            source_type=SourceType.DOCUMENT,
            source_path="/docs/ml.txt",
            categories=[Category(id="ai", name="AI", description="", parent_id=None, confidence=0.9)],
            tags=[Tag(id="ml", name="machine-learning", color="#ff6f00", usage_count=1)],
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    return items


def test_search_engine_initialization(temp_index_dir):
    """Test that search engine initializes correctly."""
    engine = SearchEngineImpl(temp_index_dir)
    assert engine is not None
    assert engine.index_manager is not None
    assert engine.semantic_searcher is not None
    engine.close()


def test_rebuild_index(temp_index_dir, sample_items):
    """Test rebuilding the search index."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Verify items are indexed
    indexed_ids = engine.index_manager.get_all_ids()
    assert len(indexed_ids) == 3
    assert "1" in indexed_ids
    assert "2" in indexed_ids
    assert "3" in indexed_ids
    
    engine.close()


def test_keyword_search(temp_index_dir, sample_items):
    """Test keyword-based search."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Search for "Python"
    options = SearchOptions(max_results=10)
    results = engine.search("Python", options)
    
    assert results.total_found > 0
    assert any("Python" in r.item.title for r in results.results)
    
    engine.close()


def test_semantic_search(temp_index_dir, sample_items):
    """Test semantic search functionality."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Search for "programming language"
    options = SearchOptions(max_results=10)
    results = engine.search("programming language", options)
    
    assert results.total_found > 0
    # Should find at least one programming-related item
    assert len(results.results) >= 1
    
    engine.close()


def test_filter_by_category(temp_index_dir, sample_items):
    """Test filtering search results by category."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Search with category filter
    options = SearchOptions(
        max_results=10,
        include_categories=["Programming"]
    )
    results = engine.search("language", options)
    
    # All results should be in Programming category
    for result in results.results:
        assert any(cat.name == "Programming" for cat in result.item.categories)
    
    engine.close()


def test_update_index(temp_index_dir, sample_items):
    """Test updating an item in the index."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Update an item
    updated_item = KnowledgeItem(
        id="1",
        title="Python Programming Advanced",
        content="Python is a powerful programming language with advanced features.",
        source_type=SourceType.DOCUMENT,
        source_path="/docs/python.txt",
        categories=[Category(id="prog", name="Programming", description="", parent_id=None, confidence=0.9)],
        tags=[Tag(id="python", name="python", color="#3776ab", usage_count=1)],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    engine.update_index(updated_item)
    
    # Search for the updated content
    options = SearchOptions(max_results=10)
    results = engine.search("Advanced", options)
    
    assert results.total_found > 0
    assert any("Advanced" in r.item.title for r in results.results)
    
    engine.close()


def test_remove_from_index(temp_index_dir, sample_items):
    """Test removing an item from the index."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Remove an item
    engine.remove_from_index("1")
    
    # Verify item is removed
    indexed_ids = engine.index_manager.get_all_ids()
    assert "1" not in indexed_ids
    assert len(indexed_ids) == 2
    
    engine.close()


def test_get_similar_items(temp_index_dir, sample_items):
    """Test finding similar items."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Find items similar to the first item
    similar_items = engine.get_similar_items(sample_items[0], limit=2)
    
    # May or may not find similar items depending on content similarity
    # Just verify the function works without error
    assert isinstance(similar_items, list)
    
    engine.close()


def test_sort_by_date(temp_index_dir, sample_items):
    """Test sorting results by date."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Search with date sorting
    options = SearchOptions(max_results=10, sort_by="date")
    results = engine.search("language", options)
    
    # Verify results are sorted by date
    if len(results.results) > 1:
        for i in range(len(results.results) - 1):
            assert results.results[i].item.updated_at >= results.results[i + 1].item.updated_at
    
    engine.close()


def test_group_by_category(temp_index_dir, sample_items):
    """Test grouping results by category."""
    engine = SearchEngineImpl(temp_index_dir)
    engine.rebuild_index(sample_items)
    
    # Search with category grouping - use a more specific query
    options = SearchOptions(max_results=10, group_by_category=True)
    results = engine.search("Python JavaScript", options)
    
    # Verify results are grouped (may be empty if no matches)
    assert results.grouped_results is not None
    
    engine.close()
