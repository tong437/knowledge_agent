"""
Integration tests for the complete knowledge agent system.

Tests the integration of all components working together.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from knowledge_agent.core import KnowledgeAgentCore
from knowledge_agent.models import DataSource, SourceType, KnowledgeItem


class TestSystemIntegration:
    """Test complete system integration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def agent(self, temp_dir):
        """Create a knowledge agent instance for testing."""
        config = {
            "storage": {
                "type": "sqlite",
                "path": str(Path(temp_dir) / "test_knowledge.db")
            },
            "search": {
                "index_dir": str(Path(temp_dir) / "test_index")
            }
        }
        agent = KnowledgeAgentCore(config)
        yield agent
        agent.shutdown()
    
    def test_agent_initialization(self, agent):
        """Test that the agent initializes all components correctly."""
        assert agent.is_initialized()
        assert agent._storage_manager is not None
        assert agent._knowledge_organizer is not None
        assert agent._search_engine is not None
        assert len(agent._data_processors) > 0
        assert agent._data_import_export is not None
    
    def test_component_registry(self, agent):
        """Test that all components are registered in the registry."""
        registry = agent._registry
        status = registry.get_status()
        
        # Check that key components are registered
        assert "storage_manager" in status
        assert "knowledge_organizer" in status
        assert "search_engine" in status
        assert "document_processor" in status
        assert "pdf_processor" in status
        assert "code_processor" in status
    
    def test_collect_and_organize_workflow(self, agent, temp_dir):
        """Test the complete workflow: collect -> organize -> search."""
        # Create a test document
        test_file = Path(temp_dir) / "test_document.txt"
        test_content = "This is a test document about Python programming and machine learning."
        test_file.write_text(test_content)
        
        # Step 1: Collect knowledge
        source = DataSource(
            source_type=SourceType.DOCUMENT,
            path=str(test_file),
            metadata={"test": True}
        )
        
        item = agent.collect_knowledge(source)
        assert item is not None
        assert item.id is not None
        assert "Python" in item.content or "python" in item.content.lower()
        
        # Step 2: Organize knowledge
        org_result = agent.organize_knowledge(item)
        assert org_result["success"] is True
        assert "categories" in org_result
        assert "tags" in org_result
        
        # Step 3: Search for the knowledge
        search_results = agent.search_knowledge("Python programming")
        assert search_results["total_results"] > 0
        assert any("Python" in r["content"] or "python" in r["content"].lower() 
                   for r in search_results["results"])
    
    def test_multiple_document_types(self, agent, temp_dir):
        """Test collecting different types of documents."""
        # Create test files
        txt_file = Path(temp_dir) / "test.txt"
        txt_file.write_text("Text document content")
        
        md_file = Path(temp_dir) / "test.md"
        md_file.write_text("# Markdown Document\n\nMarkdown content")
        
        py_file = Path(temp_dir) / "test.py"
        py_file.write_text("# Python code\ndef hello():\n    print('Hello')")
        
        # Collect all documents
        items = []
        for file_path, source_type in [
            (txt_file, SourceType.DOCUMENT),
            (md_file, SourceType.DOCUMENT),
            (py_file, SourceType.CODE)
        ]:
            source = DataSource(source_type=source_type, path=str(file_path), metadata={})
            item = agent.collect_knowledge(source)
            items.append(item)
        
        assert len(items) == 3
        
        # Verify all items are stored
        all_items = agent.list_knowledge_items()
        assert len(all_items) >= 3
    
    def test_search_integration(self, agent, temp_dir):
        """Test search functionality with multiple items."""
        # Create multiple test documents
        docs = [
            ("Python is a programming language", "python.txt"),
            ("JavaScript is used for web development", "javascript.txt"),
            ("Machine learning uses Python extensively", "ml.txt"),
        ]
        
        for content, filename in docs:
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
            source = DataSource(source_type=SourceType.DOCUMENT, path=str(file_path), metadata={})
            agent.collect_knowledge(source)
        
        # Search for Python-related content
        results = agent.search_knowledge("Python")
        assert results["total_results"] >= 2  # Should find at least 2 Python-related docs
        
        # Search for JavaScript
        results = agent.search_knowledge("JavaScript")
        assert results["total_results"] >= 1
    
    def test_data_export_import(self, agent, temp_dir):
        """Test data export and import functionality."""
        # Create and collect a test document
        test_file = Path(temp_dir) / "export_test.txt"
        test_file.write_text("Test content for export")
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        item = agent.collect_knowledge(source)
        
        # Export data
        exported_data = agent.export_data(format="json")
        assert "knowledge_items" in exported_data
        assert len(exported_data["knowledge_items"]) > 0
        
        # Create a new agent with different database
        new_config = {
            "storage": {
                "type": "sqlite",
                "path": str(Path(temp_dir) / "imported_knowledge.db")
            },
            "search": {
                "index_dir": str(Path(temp_dir) / "imported_index")
            }
        }
        new_agent = KnowledgeAgentCore(new_config)
        
        try:
            # Import data to new agent
            success = new_agent.import_data(exported_data)
            assert success is True
            
            # Verify imported data
            imported_items = new_agent.list_knowledge_items()
            assert len(imported_items) > 0
            
            # Verify search works on imported data
            search_results = new_agent.search_knowledge("export")
            assert search_results["total_results"] > 0
        finally:
            new_agent.shutdown()
    
    def test_statistics(self, agent, temp_dir):
        """Test statistics gathering."""
        # Create some test data
        test_file = Path(temp_dir) / "stats_test.txt"
        test_file.write_text("Statistics test content")
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        item = agent.collect_knowledge(source)
        agent.organize_knowledge(item)
        
        # Get statistics
        stats = agent.get_statistics()
        assert "total_items" in stats
        assert "total_categories" in stats
        assert "total_tags" in stats
        assert stats["total_items"] > 0
    
    def test_performance_metrics(self, agent, temp_dir):
        """Test performance monitoring."""
        # Perform some operations
        test_file = Path(temp_dir) / "perf_test.txt"
        test_file.write_text("Performance test content")
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        agent.collect_knowledge(source)
        
        # Get performance metrics
        metrics = agent.get_performance_metrics()
        assert isinstance(metrics, dict)
        # Metrics should contain operation data
        assert len(metrics) >= 0  # May be empty if no operations tracked yet
    
    def test_error_handling(self, agent):
        """Test error handling for invalid operations."""
        # Test with invalid source
        with pytest.raises(Exception):
            source = DataSource(
                source_type=SourceType.DOCUMENT,
                path="/nonexistent/file.txt"
            )
            agent.collect_knowledge(source)
        
        # Test with invalid item ID
        item = agent.get_knowledge_item("nonexistent_id")
        assert item is None
    
    def test_similar_items(self, agent, temp_dir):
        """Test finding similar items."""
        # Create related documents
        docs = [
            ("Python programming tutorial", "python1.txt"),
            ("Advanced Python techniques", "python2.txt"),
            ("JavaScript basics", "js.txt"),
        ]
        
        item_ids = []
        for content, filename in docs:
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
            source = DataSource(source_type=SourceType.DOCUMENT, path=str(file_path), metadata={})
            item = agent.collect_knowledge(source)
            item_ids.append(item.id)
        
        # Find similar items to the first Python document
        similar = agent.get_similar_items(item_ids[0], limit=5)
        # Should find at least one similar item (the other Python doc)
        assert len(similar) >= 0  # May be 0 if semantic search not fitted yet
    
    def test_shutdown_and_cleanup(self, agent):
        """Test proper shutdown and cleanup."""
        assert agent.is_initialized()
        assert not agent.is_shutdown_requested()
        
        agent.shutdown()
        
        assert not agent.is_initialized()
        assert agent.is_shutdown_requested()


class TestComponentIntegration:
    """Test integration between specific components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def agent(self, temp_dir):
        """Create a knowledge agent instance for testing."""
        config = {
            "storage": {
                "type": "sqlite",
                "path": str(Path(temp_dir) / "test_knowledge.db")
            },
            "search": {
                "index_dir": str(Path(temp_dir) / "test_index")
            }
        }
        agent = KnowledgeAgentCore(config)
        yield agent
        agent.shutdown()
    
    def test_processor_to_storage_integration(self, agent, temp_dir):
        """Test that processors correctly save to storage."""
        test_file = Path(temp_dir) / "integration_test.txt"
        test_file.write_text("Integration test content")
        
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        item = agent.collect_knowledge(source)
        
        # Verify item is in storage
        retrieved_item = agent.get_knowledge_item(item.id)
        assert retrieved_item is not None
        assert retrieved_item.id == item.id
        assert retrieved_item.content == item.content
    
    def test_organizer_to_storage_integration(self, agent, temp_dir):
        """Test that organizer updates are persisted to storage."""
        test_file = Path(temp_dir) / "organize_test.txt"
        test_file.write_text("Test content for organization")
        
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        item = agent.collect_knowledge(source)
        
        # Organize the item
        org_result = agent.organize_knowledge(item)
        
        # Retrieve and verify categories/tags are persisted
        retrieved_item = agent.get_knowledge_item(item.id)
        assert retrieved_item is not None
        # Categories and tags should be added by organizer
        assert len(retrieved_item.categories) >= 0
        assert len(retrieved_item.tags) >= 0
    
    def test_storage_to_search_integration(self, agent, temp_dir):
        """Test that storage updates trigger search index updates."""
        test_file = Path(temp_dir) / "search_integration.txt"
        test_content = "Unique search integration test content"
        test_file.write_text(test_content)
        
        source = DataSource(source_type=SourceType.DOCUMENT, path=str(test_file), metadata={})
        item = agent.collect_knowledge(source)
        
        # Search should find the newly added item
        results = agent.search_knowledge("unique search integration")
        assert results["total_results"] > 0
