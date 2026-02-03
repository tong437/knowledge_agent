"""
Unit tests for storage layer functionality.

Tests data persistence, retrieval, and data integrity validation
as specified in Requirements 5.1 and 5.3.
"""

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from knowledge_agent.storage.sqlite_storage import SQLiteStorageManager
from knowledge_agent.models import (
    KnowledgeItem, Category, Tag, Relationship, SourceType
)
from knowledge_agent.models.relationship import RelationshipType


class TestSQLiteStorageManager:
    """Test cases for SQLiteStorageManager."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file path."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup - try multiple times for Windows file locking
        import time
        for _ in range(3):
            try:
                if os.path.exists(path):
                    os.unlink(path)
                break
            except PermissionError:
                time.sleep(0.1)
    
    @pytest.fixture
    def storage_manager(self, temp_db_path):
        """Create a storage manager with temporary database."""
        manager = SQLiteStorageManager(temp_db_path)
        yield manager
        # Explicitly close any open connections
        # SQLite connections are closed when context managers exit,
        # but we'll add a small delay to ensure cleanup
        import time
        time.sleep(0.05)
    
    @pytest.fixture
    def sample_item(self):
        """Create a sample knowledge item."""
        return KnowledgeItem(
            id="test-item-1",
            title="Test Knowledge Item",
            content="This is test content for the knowledge item.",
            source_type=SourceType.DOCUMENT,
            source_path="/test/path/document.txt",
            metadata={"author": "test", "version": 1},
        )
    
    @pytest.fixture
    def sample_category(self):
        """Create a sample category."""
        return Category(
            id="cat-1",
            name="Test Category",
            description="A test category",
            confidence=0.85,
        )
    
    @pytest.fixture
    def sample_tag(self):
        """Create a sample tag."""
        return Tag(
            id="tag-1",
            name="test-tag",
            color="#ff0000",
            usage_count=0,
        )
    
    # Test: Data Persistence (Requirement 5.1)
    
    def test_save_and_retrieve_knowledge_item(self, storage_manager, sample_item):
        """Test saving and retrieving a knowledge item."""
        # Save the item
        storage_manager.save_knowledge_item(sample_item)
        
        # Retrieve the item
        retrieved = storage_manager.get_knowledge_item(sample_item.id)
        
        # Verify all fields match
        assert retrieved is not None
        assert retrieved.id == sample_item.id
        assert retrieved.title == sample_item.title
        assert retrieved.content == sample_item.content
        assert retrieved.source_type == sample_item.source_type
        assert retrieved.source_path == sample_item.source_path
        assert retrieved.metadata == sample_item.metadata
    
    def test_save_knowledge_item_with_categories(self, storage_manager, sample_item, sample_category):
        """Test saving a knowledge item with categories."""
        sample_item.add_category(sample_category)
        storage_manager.save_knowledge_item(sample_item)
        
        retrieved = storage_manager.get_knowledge_item(sample_item.id)
        
        assert len(retrieved.categories) == 1
        assert retrieved.categories[0].id == sample_category.id
        assert retrieved.categories[0].name == sample_category.name
    
    def test_save_knowledge_item_with_tags(self, storage_manager, sample_item, sample_tag):
        """Test saving a knowledge item with tags."""
        sample_item.add_tag(sample_tag)
        storage_manager.save_knowledge_item(sample_item)
        
        retrieved = storage_manager.get_knowledge_item(sample_item.id)
        
        assert len(retrieved.tags) == 1
        assert retrieved.tags[0].id == sample_tag.id
        assert retrieved.tags[0].name == sample_tag.name
    
    def test_update_existing_knowledge_item(self, storage_manager, sample_item):
        """Test updating an existing knowledge item."""
        # Save initial version
        storage_manager.save_knowledge_item(sample_item)
        
        # Update the item
        sample_item.update_content("Updated content")
        storage_manager.save_knowledge_item(sample_item)
        
        # Retrieve and verify
        retrieved = storage_manager.get_knowledge_item(sample_item.id)
        assert retrieved.content == "Updated content"
    
    def test_get_nonexistent_knowledge_item(self, storage_manager):
        """Test retrieving a non-existent knowledge item returns None."""
        retrieved = storage_manager.get_knowledge_item("nonexistent-id")
        assert retrieved is None
    
    def test_get_all_knowledge_items(self, storage_manager):
        """Test retrieving all knowledge items."""
        # Create and save multiple items
        items = []
        for i in range(3):
            item = KnowledgeItem(
                id=f"item-{i}",
                title=f"Item {i}",
                content=f"Content {i}",
                source_type=SourceType.DOCUMENT,
                source_path=f"/path/{i}.txt",
            )
            items.append(item)
            storage_manager.save_knowledge_item(item)
        
        # Retrieve all items
        all_items = storage_manager.get_all_knowledge_items()
        
        assert len(all_items) == 3
        item_ids = {item.id for item in all_items}
        assert item_ids == {"item-0", "item-1", "item-2"}
    
    def test_delete_knowledge_item(self, storage_manager, sample_item):
        """Test deleting a knowledge item."""
        # Save the item
        storage_manager.save_knowledge_item(sample_item)
        
        # Verify it exists
        assert storage_manager.get_knowledge_item(sample_item.id) is not None
        
        # Delete the item
        result = storage_manager.delete_knowledge_item(sample_item.id)
        assert result is True
        
        # Verify it's gone
        assert storage_manager.get_knowledge_item(sample_item.id) is None
    
    def test_delete_nonexistent_item(self, storage_manager):
        """Test deleting a non-existent item returns False."""
        result = storage_manager.delete_knowledge_item("nonexistent-id")
        assert result is False
    
    # Test: Category Management
    
    def test_save_and_retrieve_category(self, storage_manager, sample_category):
        """Test saving and retrieving categories."""
        storage_manager.save_category(sample_category)
        
        categories = storage_manager.get_all_categories()
        assert len(categories) == 1
        assert categories[0].id == sample_category.id
        assert categories[0].name == sample_category.name
    
    def test_save_category_with_parent(self, storage_manager):
        """Test saving categories with parent-child relationships."""
        parent = Category(
            id="parent-cat",
            name="Parent Category",
            description="Parent",
            confidence=0.9,
        )
        child = Category(
            id="child-cat",
            name="Child Category",
            description="Child",
            parent_id="parent-cat",
            confidence=0.8,
        )
        
        storage_manager.save_category(parent)
        storage_manager.save_category(child)
        
        categories = storage_manager.get_all_categories()
        assert len(categories) == 2
        
        child_cat = next(c for c in categories if c.id == "child-cat")
        assert child_cat.parent_id == "parent-cat"
    
    # Test: Tag Management
    
    def test_save_and_retrieve_tag(self, storage_manager, sample_tag):
        """Test saving and retrieving tags."""
        storage_manager.save_tag(sample_tag)
        
        tags = storage_manager.get_all_tags()
        assert len(tags) == 1
        assert tags[0].id == sample_tag.id
        assert tags[0].name == sample_tag.name
        assert tags[0].color == sample_tag.color
    
    def test_update_tag_usage_count(self, storage_manager, sample_tag):
        """Test updating tag usage count."""
        storage_manager.save_tag(sample_tag)
        
        # Update usage count
        sample_tag.increment_usage()
        storage_manager.save_tag(sample_tag)
        
        tags = storage_manager.get_all_tags()
        assert tags[0].usage_count == 1
    
    # Test: Relationship Management
    
    def test_save_and_retrieve_relationship(self, storage_manager):
        """Test saving and retrieving relationships."""
        # Create two items
        item1 = KnowledgeItem(
            id="item-1",
            title="Item 1",
            content="Content 1",
            source_type=SourceType.DOCUMENT,
            source_path="/path/1.txt",
        )
        item2 = KnowledgeItem(
            id="item-2",
            title="Item 2",
            content="Content 2",
            source_type=SourceType.DOCUMENT,
            source_path="/path/2.txt",
        )
        
        storage_manager.save_knowledge_item(item1)
        storage_manager.save_knowledge_item(item2)
        
        # Create relationship
        relationship = Relationship(
            source_id="item-1",
            target_id="item-2",
            relationship_type=RelationshipType.SIMILAR,
            strength=0.75,
            description="Test relationship",
        )
        
        storage_manager.save_relationship(relationship)
        
        # Retrieve relationships
        relationships = storage_manager.get_relationships_for_item("item-1")
        assert len(relationships) == 1
        assert relationships[0].source_id == "item-1"
        assert relationships[0].target_id == "item-2"
        assert relationships[0].strength == 0.75
    
    def test_get_relationships_bidirectional(self, storage_manager):
        """Test retrieving relationships works for both source and target."""
        # Create items and relationship
        item1 = KnowledgeItem(
            id="item-1",
            title="Item 1",
            content="Content 1",
            source_type=SourceType.DOCUMENT,
            source_path="/path/1.txt",
        )
        item2 = KnowledgeItem(
            id="item-2",
            title="Item 2",
            content="Content 2",
            source_type=SourceType.DOCUMENT,
            source_path="/path/2.txt",
        )
        
        storage_manager.save_knowledge_item(item1)
        storage_manager.save_knowledge_item(item2)
        
        relationship = Relationship(
            source_id="item-1",
            target_id="item-2",
            relationship_type=RelationshipType.RELATED,
            strength=0.8,
        )
        
        storage_manager.save_relationship(relationship)
        
        # Should be found when querying either item
        rels_from_item1 = storage_manager.get_relationships_for_item("item-1")
        rels_from_item2 = storage_manager.get_relationships_for_item("item-2")
        
        assert len(rels_from_item1) == 1
        assert len(rels_from_item2) == 1
    
    # Test: Data Export/Import (Requirement 5.3)
    
    def test_export_data(self, storage_manager, sample_item, sample_category, sample_tag):
        """Test exporting all data."""
        # Add some data
        sample_item.add_category(sample_category)
        sample_item.add_tag(sample_tag)
        storage_manager.save_knowledge_item(sample_item)
        
        # Export data
        exported = storage_manager.export_data()
        
        assert "knowledge_items" in exported
        assert "categories" in exported
        assert "tags" in exported
        assert "relationships" in exported
        assert "export_timestamp" in exported
        
        assert len(exported["knowledge_items"]) == 1
        assert len(exported["categories"]) == 1
        assert len(exported["tags"]) == 1
    
    def test_import_data(self, storage_manager):
        """Test importing data."""
        # Create test data
        data = {
            "categories": [
                {
                    "id": "cat-1",
                    "name": "Category 1",
                    "description": "Test category",
                    "parent_id": None,
                    "confidence": 0.9,
                }
            ],
            "tags": [
                {
                    "id": "tag-1",
                    "name": "test",
                    "color": "#ff0000",
                    "usage_count": 0,
                }
            ],
            "knowledge_items": [
                {
                    "id": "item-1",
                    "title": "Test Item",
                    "content": "Test content",
                    "source_type": "document",
                    "source_path": "/test/path.txt",
                    "categories": [
                        {
                            "id": "cat-1",
                            "name": "Category 1",
                            "description": "Test category",
                            "parent_id": None,
                            "confidence": 0.9,
                        }
                    ],
                    "tags": [
                        {
                            "id": "tag-1",
                            "name": "test",
                            "color": "#ff0000",
                            "usage_count": 0,
                        }
                    ],
                    "metadata": {},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "embedding": None,
                }
            ],
            "relationships": [],
        }
        
        # Import data
        result = storage_manager.import_data(data)
        assert result is True
        
        # Verify imported data
        items = storage_manager.get_all_knowledge_items()
        assert len(items) == 1
        assert items[0].id == "item-1"
        
        categories = storage_manager.get_all_categories()
        assert len(categories) == 1
        
        tags = storage_manager.get_all_tags()
        assert len(tags) == 1
    
    def test_export_import_roundtrip(self, storage_manager, temp_db_path):
        """Test that export followed by import preserves data."""
        # Create and save test data
        item = KnowledgeItem(
            id="roundtrip-item",
            title="Roundtrip Test",
            content="Testing roundtrip",
            source_type=SourceType.DOCUMENT,
            source_path="/test/roundtrip.txt",
            metadata={"test": "roundtrip"},
        )
        
        category = Category(
            id="roundtrip-cat",
            name="Roundtrip Category",
            description="Test",
            confidence=0.95,
        )
        
        item.add_category(category)
        storage_manager.save_knowledge_item(item)
        
        # Export data
        exported = storage_manager.export_data()
        
        # Create new storage manager with different database
        fd, new_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        try:
            new_storage = SQLiteStorageManager(new_db_path)
            
            # Import data
            new_storage.import_data(exported)
            
            # Verify data
            retrieved = new_storage.get_knowledge_item("roundtrip-item")
            assert retrieved is not None
            assert retrieved.title == item.title
            assert retrieved.content == item.content
            assert len(retrieved.categories) == 1
            assert retrieved.categories[0].id == category.id
            
            # Clean up the new storage manager
            del new_storage
        finally:
            # Wait a bit for Windows to release the file
            import time
            time.sleep(0.1)
            # Try to delete with retries
            for _ in range(3):
                try:
                    if os.path.exists(new_db_path):
                        os.unlink(new_db_path)
                    break
                except PermissionError:
                    time.sleep(0.1)
    
    # Test: Data Integrity (Requirement 5.3)
    
    def test_check_data_integrity_clean_database(self, storage_manager):
        """Test data integrity check on clean database."""
        integrity = storage_manager.check_data_integrity()
        
        assert "has_issues" in integrity
        assert "issues" in integrity
        assert "checked_at" in integrity
        assert integrity["has_issues"] is False
        assert len(integrity["issues"]) == 0
    
    def test_database_stats(self, storage_manager, sample_item):
        """Test getting database statistics."""
        # Initially empty
        stats = storage_manager.get_database_stats()
        assert stats["knowledge_items"] == 0
        assert stats["categories"] == 0
        assert stats["tags"] == 0
        assert stats["relationships"] == 0
        
        # Add an item
        storage_manager.save_knowledge_item(sample_item)
        
        stats = storage_manager.get_database_stats()
        assert stats["knowledge_items"] == 1
    
    def test_save_with_embedding(self, storage_manager):
        """Test saving and retrieving knowledge item with embedding."""
        item = KnowledgeItem(
            id="item-with-embedding",
            title="Item with Embedding",
            content="Content",
            source_type=SourceType.DOCUMENT,
            source_path="/test/path.txt",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        )
        
        storage_manager.save_knowledge_item(item)
        retrieved = storage_manager.get_knowledge_item(item.id)
        
        assert retrieved.embedding is not None
        assert len(retrieved.embedding) == 5
        assert retrieved.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    def test_cascade_delete_removes_associations(self, storage_manager, sample_item, sample_category, sample_tag):
        """Test that deleting an item removes its category and tag associations."""
        # Add item with category and tag
        sample_item.add_category(sample_category)
        sample_item.add_tag(sample_tag)
        storage_manager.save_knowledge_item(sample_item)
        
        # Verify associations exist
        retrieved = storage_manager.get_knowledge_item(sample_item.id)
        assert len(retrieved.categories) == 1
        assert len(retrieved.tags) == 1
        
        # Delete the item
        storage_manager.delete_knowledge_item(sample_item.id)
        
        # Categories and tags should still exist
        categories = storage_manager.get_all_categories()
        tags = storage_manager.get_all_tags()
        assert len(categories) == 1
        assert len(tags) == 1
        
        # But the item should be gone
        assert storage_manager.get_knowledge_item(sample_item.id) is None
    
    def test_multiple_items_same_category(self, storage_manager, sample_category):
        """Test multiple items can share the same category."""
        item1 = KnowledgeItem(
            id="item-1",
            title="Item 1",
            content="Content 1",
            source_type=SourceType.DOCUMENT,
            source_path="/path/1.txt",
        )
        item2 = KnowledgeItem(
            id="item-2",
            title="Item 2",
            content="Content 2",
            source_type=SourceType.DOCUMENT,
            source_path="/path/2.txt",
        )
        
        item1.add_category(sample_category)
        item2.add_category(sample_category)
        
        storage_manager.save_knowledge_item(item1)
        storage_manager.save_knowledge_item(item2)
        
        # Both items should have the category
        retrieved1 = storage_manager.get_knowledge_item("item-1")
        retrieved2 = storage_manager.get_knowledge_item("item-2")
        
        assert len(retrieved1.categories) == 1
        assert len(retrieved2.categories) == 1
        assert retrieved1.categories[0].id == sample_category.id
        assert retrieved2.categories[0].id == sample_category.id
        
        # But only one category should exist in the database
        categories = storage_manager.get_all_categories()
        assert len(categories) == 1
