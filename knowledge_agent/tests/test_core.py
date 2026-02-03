"""
Unit tests for core knowledge agent functionality.
"""

import pytest
from knowledge_agent.core import KnowledgeAgentCore, KnowledgeAgentError


class TestKnowledgeAgentCore:
    """Test cases for KnowledgeAgentCore."""
    
    def test_create_core(self, knowledge_agent_core):
        """Test creating a knowledge agent core."""
        core = knowledge_agent_core
        assert core is not None
        assert hasattr(core, 'config')
        assert hasattr(core, 'logger')
    
    def test_core_with_config(self):
        """Test creating core with custom configuration."""
        config = {
            "storage": {"type": "sqlite", "path": ":memory:"},
            "search": {"type": "whoosh"},
        }
        core = KnowledgeAgentCore(config)
        assert core.config == config
    
    def test_collect_knowledge_not_implemented(self, knowledge_agent_core, sample_data_source):
        """Test that collect_knowledge raises KnowledgeAgentError with NotImplementedError."""
        core = knowledge_agent_core
        with pytest.raises(KnowledgeAgentError, match="will be implemented in task 3"):
            core.collect_knowledge(sample_data_source)
    
    def test_search_knowledge_not_implemented(self, knowledge_agent_core):
        """Test that search_knowledge raises KnowledgeAgentError with NotImplementedError."""
        core = knowledge_agent_core
        with pytest.raises(KnowledgeAgentError, match="will be implemented in task 6"):
            core.search_knowledge("test query")
    
    def test_organize_knowledge_not_implemented(self, knowledge_agent_core, sample_knowledge_item):
        """Test that organize_knowledge raises KnowledgeAgentError with NotImplementedError."""
        core = knowledge_agent_core
        with pytest.raises(KnowledgeAgentError, match="will be implemented in task 5"):
            core.organize_knowledge(sample_knowledge_item)
    
    def test_get_statistics(self, knowledge_agent_core):
        """Test getting knowledge base statistics."""
        core = knowledge_agent_core
        stats = core.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_items" in stats
        assert "total_categories" in stats
        assert "total_tags" in stats
        assert "total_relationships" in stats
        assert stats["total_items"] == 0  # Empty initially
    
    def test_shutdown(self, knowledge_agent_core):
        """Test shutting down the core."""
        core = knowledge_agent_core
        # Should not raise any exceptions
        core.shutdown()