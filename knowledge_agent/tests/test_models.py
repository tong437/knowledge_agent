"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from knowledge_agent.models import (
    KnowledgeItem, Category, Tag, Relationship, DataSource, SourceType
)
from knowledge_agent.models.relationship import RelationshipType


class TestKnowledgeItem:
    """Test cases for KnowledgeItem model."""
    
    def test_create_knowledge_item(self, sample_knowledge_item):
        """Test creating a knowledge item."""
        item = sample_knowledge_item
        assert item.id == "test-item-1"
        assert item.title == "Test Knowledge Item"
        assert item.source_type == SourceType.DOCUMENT
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
    
    def test_knowledge_item_validation(self):
        """Test knowledge item validation."""
        # Test empty ID
        with pytest.raises(ValueError, match="ID cannot be empty"):
            KnowledgeItem(
                id="",
                title="Test",
                content="Content",
                source_type=SourceType.DOCUMENT,
                source_path="/test/path",
            )
        
        # Test empty title
        with pytest.raises(ValueError, match="title cannot be empty"):
            KnowledgeItem(
                id="test-id",
                title="",
                content="Content",
                source_type=SourceType.DOCUMENT,
                source_path="/test/path",
            )
        
        # Test empty content
        with pytest.raises(ValueError, match="content cannot be empty"):
            KnowledgeItem(
                id="test-id",
                title="Test",
                content="",
                source_type=SourceType.DOCUMENT,
                source_path="/test/path",
            )
    
    def test_add_category(self, sample_knowledge_item, sample_category):
        """Test adding a category to a knowledge item."""
        item = sample_knowledge_item
        original_updated = item.updated_at
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        item.add_category(sample_category)
        
        assert sample_category in item.categories
        assert item.updated_at >= original_updated
    
    def test_add_tag(self, sample_knowledge_item, sample_tag):
        """Test adding a tag to a knowledge item."""
        item = sample_knowledge_item
        original_updated = item.updated_at
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        item.add_tag(sample_tag)
        
        assert sample_tag in item.tags
        assert item.updated_at >= original_updated
    
    def test_update_content(self, sample_knowledge_item):
        """Test updating knowledge item content."""
        item = sample_knowledge_item
        original_updated = item.updated_at
        new_content = "Updated content"
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        item.update_content(new_content)
        
        assert item.content == new_content
        assert item.updated_at >= original_updated
    
    def test_to_dict(self, sample_knowledge_item):
        """Test converting knowledge item to dictionary."""
        item = sample_knowledge_item
        data = item.to_dict()
        
        assert data["id"] == item.id
        assert data["title"] == item.title
        assert data["content"] == item.content
        assert data["source_type"] == item.source_type.value
        assert "created_at" in data
        assert "updated_at" in data


class TestCategory:
    """Test cases for Category model."""
    
    def test_create_category(self, sample_category):
        """Test creating a category."""
        category = sample_category
        assert category.id == "test-category-1"
        assert category.name == "Test Category"
        assert category.confidence == 0.9
        assert category.is_root_category()
    
    def test_category_validation(self):
        """Test category validation."""
        # Test invalid confidence
        with pytest.raises(ValueError, match="confidence must be between"):
            Category(
                id="test-id",
                name="Test",
                description="Test description",
                confidence=1.5,
            )
    
    def test_category_equality(self):
        """Test category equality comparison."""
        cat1 = Category(id="test-1", name="Test", description="Test")
        cat2 = Category(id="test-1", name="Different", description="Different")
        cat3 = Category(id="test-2", name="Test", description="Test")
        
        assert cat1 == cat2  # Same ID
        assert cat1 != cat3  # Different ID


class TestTag:
    """Test cases for Tag model."""
    
    def test_create_tag(self, sample_tag):
        """Test creating a tag."""
        tag = sample_tag
        assert tag.id == "test-tag-1"
        assert tag.name == "test"
        assert tag.color == "#ff0000"
        assert tag.usage_count == 5
    
    def test_tag_usage_tracking(self, sample_tag):
        """Test tag usage count tracking."""
        tag = sample_tag
        original_count = tag.usage_count
        
        tag.increment_usage()
        assert tag.usage_count == original_count + 1
        
        tag.decrement_usage()
        assert tag.usage_count == original_count
        
        # Test decrement doesn't go below zero
        tag.usage_count = 0
        tag.decrement_usage()
        assert tag.usage_count == 0


class TestRelationship:
    """Test cases for Relationship model."""
    
    def test_create_relationship(self, sample_relationship):
        """Test creating a relationship."""
        rel = sample_relationship
        assert rel.source_id == "test-item-1"
        assert rel.target_id == "test-item-2"
        assert rel.relationship_type == RelationshipType.SIMILAR
        assert rel.strength == 0.8
    
    def test_relationship_validation(self):
        """Test relationship validation."""
        # Test same source and target
        with pytest.raises(ValueError, match="Source and target cannot be the same"):
            Relationship(
                source_id="test-1",
                target_id="test-1",
                relationship_type=RelationshipType.SIMILAR,
                strength=0.5,
            )
        
        # Test invalid strength
        with pytest.raises(ValueError, match="strength must be between"):
            Relationship(
                source_id="test-1",
                target_id="test-2",
                relationship_type=RelationshipType.SIMILAR,
                strength=1.5,
            )
    
    def test_bidirectional_relationships(self):
        """Test bidirectional relationship handling."""
        rel = Relationship(
            source_id="test-1",
            target_id="test-2",
            relationship_type=RelationshipType.SIMILAR,
            strength=0.8,
        )
        
        assert rel.is_bidirectional()
        
        reverse_rel = rel.reverse()
        assert reverse_rel.source_id == "test-2"
        assert reverse_rel.target_id == "test-1"
        assert reverse_rel.relationship_type == RelationshipType.SIMILAR


class TestDataSource:
    """Test cases for DataSource model."""
    
    def test_create_data_source(self, sample_data_source):
        """Test creating a data source."""
        source = sample_data_source
        assert source.path == "/test/path/document.txt"
        assert source.source_type == SourceType.DOCUMENT
        assert source.encoding == "utf-8"
        assert source.is_valid()
    
    def test_data_source_validation(self):
        """Test data source validation."""
        # Test empty path
        with pytest.raises(ValueError, match="path cannot be empty"):
            DataSource(
                path="",
                source_type=SourceType.DOCUMENT,
                metadata={},
            )