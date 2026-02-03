"""
Pytest configuration and fixtures for knowledge agent tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from knowledge_agent.models import (
    KnowledgeItem, Category, Tag, Relationship, DataSource, SourceType
)
from knowledge_agent.core import KnowledgeAgentCore
from knowledge_agent.storage import SQLiteStorageManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def storage_manager(temp_dir):
    """Create a storage manager instance for testing."""
    db_path = str(temp_dir / "test_knowledge.db")
    manager = SQLiteStorageManager(db_path)
    yield manager
    # Close any open connections
    import gc
    del manager
    gc.collect()


@pytest.fixture
def sample_knowledge_item():
    """Create a sample knowledge item for testing."""
    return KnowledgeItem(
        id="test-item-1",
        title="Test Knowledge Item",
        content="This is a test knowledge item with sample content.",
        source_type=SourceType.DOCUMENT,
        source_path="/test/path/document.txt",
        metadata={"test": True, "created_by": "test_suite"},
    )


@pytest.fixture
def sample_category():
    """Create a sample category for testing."""
    return Category(
        id="test-category-1",
        name="Test Category",
        description="A test category for unit tests",
        confidence=0.9,
    )


@pytest.fixture
def sample_tag():
    """Create a sample tag for testing."""
    return Tag(
        id="test-tag-1",
        name="test",
        color="#ff0000",
        usage_count=5,
    )


@pytest.fixture
def sample_relationship():
    """Create a sample relationship for testing."""
    return Relationship(
        source_id="test-item-1",
        target_id="test-item-2",
        relationship_type=RelationshipType.SIMILAR,
        strength=0.8,
        description="Test relationship between items",
    )


@pytest.fixture
def sample_data_source():
    """Create a sample data source for testing."""
    return DataSource(
        path="/test/path/document.txt",
        source_type=SourceType.DOCUMENT,
        metadata={"size": 1024, "encoding": "utf-8"},
        encoding="utf-8",
    )


@pytest.fixture
def knowledge_agent_core():
    """Create a knowledge agent core instance for testing."""
    config = {
        "storage": {"type": "sqlite", "path": ":memory:"},
        "search": {"type": "simple"},
        "organization": {"type": "basic"},
    }
    return KnowledgeAgentCore(config)


@pytest.fixture
def sample_knowledge_items():
    """Create multiple sample knowledge items for testing."""
    items = []
    for i in range(5):
        item = KnowledgeItem(
            id=f"test-item-{i+1}",
            title=f"Test Item {i+1}",
            content=f"Content for test item {i+1}",
            source_type=SourceType.DOCUMENT,
            source_path=f"/test/path/document{i+1}.txt",
            metadata={"index": i+1},
        )
        items.append(item)
    return items


# Import RelationshipType for the fixture
from knowledge_agent.models.relationship import RelationshipType