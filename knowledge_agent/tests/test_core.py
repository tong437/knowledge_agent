"""
知识代理核心功能单元测试。
"""

import pytest
from knowledge_agent.core import KnowledgeAgentCore, KnowledgeAgentError


class TestKnowledgeAgentCore:
    """KnowledgeAgentCore 测试用例。"""
    
    def test_create_core(self, knowledge_agent_core):
        """测试创建知识代理核心。"""
        core = knowledge_agent_core
        assert core is not None
        assert hasattr(core, 'config')
        assert hasattr(core, 'logger')
    
    def test_core_with_config(self):
        """测试使用自定义配置创建核心。"""
        config = {
            "storage": {"type": "sqlite", "path": ":memory:"},
            "search": {"type": "whoosh"},
        }
        core = KnowledgeAgentCore(config)
        assert core.config == config
    
    def test_collect_knowledge_invalid_source(self, knowledge_agent_core, sample_data_source):
        """测试传入不存在的文件路径时，collect_knowledge 应抛出 KnowledgeAgentError。"""
        core = knowledge_agent_core
        # 使用一个不存在的文件路径，验证会失败
        sample_data_source.path = "/nonexistent/path/does_not_exist.txt"
        with pytest.raises(KnowledgeAgentError):
            core.collect_knowledge(sample_data_source)
    
    def test_search_knowledge_empty_results(self, knowledge_agent_core):
        """测试在空知识库中搜索时，应返回包含空结果的字典。"""
        core = knowledge_agent_core
        result = core.search_knowledge("test query")
        assert isinstance(result, dict)
        assert "results" in result
    
    def test_organize_knowledge(self, knowledge_agent_core, sample_knowledge_item):
        """测试组织知识条目。"""
        core = knowledge_agent_core
        
        # 先保存条目
        if core._storage_manager:
            core._storage_manager.save_knowledge_item(sample_knowledge_item)
        
        # 组织条目
        result = core.organize_knowledge(sample_knowledge_item)
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "categories" in result
        assert "tags" in result
        assert "relationships" in result
        assert result["item_id"] == sample_knowledge_item.id
    
    def test_get_statistics(self, knowledge_agent_core):
        """测试获取知识库统计信息。"""
        core = knowledge_agent_core
        stats = core.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_items" in stats
        assert "total_categories" in stats
        assert "total_tags" in stats
        assert "total_relationships" in stats
        assert stats["total_items"] == 0  # 初始为空
    
    def test_shutdown(self, knowledge_agent_core):
        """测试关闭核心。"""
        core = knowledge_agent_core
        # 不应抛出任何异常
        core.shutdown()
