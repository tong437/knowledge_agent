"""
Integration tests for MCP server tools and resources.
"""

import pytest
import json
from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.models import KnowledgeItem, Category, Tag, SourceType
from datetime import datetime


class TestMCPIntegration:
    """Test cases for MCP server integration."""
    
    @pytest.fixture
    def mcp_server(self):
        """Create an MCP server instance for testing."""
        server = KnowledgeMCPServer("test-knowledge-agent")
        return server
    
    @pytest.fixture
    def sample_item(self, mcp_server):
        """Create a sample knowledge item for testing."""
        item = KnowledgeItem(
            id="test-item-1",
            title="Test Knowledge Item",
            content="This is a test knowledge item for MCP integration testing.",
            source_type=SourceType.DOCUMENT,
            source_path="/test/path/document.txt",
            categories=[],
            tags=[],
            metadata={"test": True},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to storage
        if mcp_server.knowledge_core._storage_manager:
            mcp_server.knowledge_core._storage_manager.save_knowledge_item(item)
        
        return item
    
    def test_server_initialization(self, mcp_server):
        """Test that MCP server initializes correctly."""
        assert mcp_server is not None
        assert mcp_server.server_name == "test-knowledge-agent"
        assert mcp_server.knowledge_core is not None
        assert mcp_server.app is not None
    
    def test_get_server_info(self, mcp_server):
        """Test getting server information."""
        info = mcp_server.get_server_info()
        
        assert info["name"] == "test-knowledge-agent"
        assert "version" in info
        assert "capabilities" in info
        assert info["capabilities"]["knowledge_collection"] is True
        assert info["capabilities"]["semantic_search"] is True
    
    def test_get_knowledge_item_integration(self, mcp_server, sample_item):
        """Test retrieving a knowledge item through the core."""
        # Get the item through the core
        retrieved_item = mcp_server.knowledge_core.get_knowledge_item(sample_item.id)
        
        assert retrieved_item is not None
        assert retrieved_item.id == sample_item.id
        assert retrieved_item.title == sample_item.title
        assert retrieved_item.content == sample_item.content
    
    def test_list_knowledge_items_integration(self, mcp_server, sample_item):
        """Test listing knowledge items through the core."""
        # List items
        items = mcp_server.knowledge_core.list_knowledge_items(limit=10, offset=0)
        
        assert isinstance(items, list)
        assert len(items) > 0
        assert any(item.id == sample_item.id for item in items)
    
    def test_get_statistics_integration(self, mcp_server, sample_item):
        """Test getting statistics through the core."""
        stats = mcp_server.knowledge_core.get_statistics()
        
        assert "total_items" in stats
        assert "total_categories" in stats
        assert "total_tags" in stats
        assert "total_relationships" in stats
        assert stats["total_items"] >= 1  # At least our sample item
    
    def test_export_import_integration(self, mcp_server, sample_item):
        """Test exporting and importing data through the core."""
        # Export data
        export_data = mcp_server.knowledge_core.export_data(format="json")
        
        assert "knowledge_items" in export_data
        assert "categories" in export_data
        assert "tags" in export_data
        assert "relationships" in export_data
        assert len(export_data["knowledge_items"]) >= 1
        
        # Verify our sample item is in the export
        item_ids = [item["id"] for item in export_data["knowledge_items"]]
        assert sample_item.id in item_ids
    
    def test_organize_knowledge_integration(self, mcp_server, sample_item):
        """Test organizing a knowledge item through the core."""
        # Organize the item
        result = mcp_server.knowledge_core.organize_knowledge(sample_item)
        
        assert result is not None
        assert "item_id" in result
        assert result["item_id"] == sample_item.id
        assert "categories" in result
        assert "tags" in result
        assert "relationships" in result
        assert result["success"] is True
    
    def test_error_handling_invalid_item_id(self, mcp_server):
        """Test error handling for invalid item ID."""
        # Try to get a non-existent item
        item = mcp_server.knowledge_core.get_knowledge_item("non-existent-id")
        
        # Should return None for non-existent items
        assert item is None
    
    def test_list_with_filters(self, mcp_server, sample_item):
        """Test listing items with filters."""
        # Add a category to the sample item
        category = Category(
            id="test-cat-1",
            name="Test Category",
            description="A test category",
            parent_id=None,
            confidence=0.9
        )
        sample_item.add_category(category)
        mcp_server.knowledge_core._storage_manager.save_knowledge_item(sample_item)
        
        # List items filtered by category
        items = mcp_server.knowledge_core.list_knowledge_items(
            category="Test Category",
            limit=10
        )
        
        assert isinstance(items, list)
        # Should find our item with the category
        assert any(item.id == sample_item.id for item in items)
    
    def test_pagination(self, mcp_server, sample_item):
        """Test pagination in list_knowledge_items."""
        # Create multiple items
        for i in range(5):
            item = KnowledgeItem(
                id=f"test-item-{i+2}",
                title=f"Test Item {i+2}",
                content=f"Content {i+2}",
                source_type=SourceType.DOCUMENT,
                source_path=f"/test/path/doc{i+2}.txt",
                categories=[],
                tags=[],
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            mcp_server.knowledge_core._storage_manager.save_knowledge_item(item)
        
        # Test pagination
        page1 = mcp_server.knowledge_core.list_knowledge_items(limit=3, offset=0)
        page2 = mcp_server.knowledge_core.list_knowledge_items(limit=3, offset=3)
        
        assert len(page1) <= 3
        assert len(page2) <= 3
        
        # Pages should have different items
        page1_ids = {item.id for item in page1}
        page2_ids = {item.id for item in page2}
        assert page1_ids != page2_ids or len(page2) == 0
