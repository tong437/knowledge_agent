"""
MCP 服务器工具和资源集成测试。
"""

import pytest
import json
from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.models import KnowledgeItem, Category, Tag, SourceType
from datetime import datetime


class TestMCPIntegration:
    """MCP 服务器集成测试用例。"""
    
    @pytest.fixture
    def mcp_server(self, tmp_path):
        """创建用于测试的 MCP 服务器实例，使用内存数据库避免文件冲突。"""
        server = KnowledgeMCPServer("test-knowledge-agent")
        # 替换为使用内存数据库的存储管理器，避免与其他测试数据冲突
        from knowledge_agent.storage import SQLiteStorageManager
        memory_storage = SQLiteStorageManager(":memory:")
        server.knowledge_core._storage_manager = memory_storage
        server.knowledge_core._data_import_export = None
        from knowledge_agent.core.data_import_export import DataImportExport
        server.knowledge_core._data_import_export = DataImportExport(memory_storage)
        return server
    
    @pytest.fixture
    def sample_item(self, mcp_server):
        """创建用于测试的示例知识条目。"""
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
        
        # 保存到存储
        if mcp_server.knowledge_core._storage_manager:
            mcp_server.knowledge_core._storage_manager.save_knowledge_item(item)
        
        return item
    
    def test_server_initialization(self, mcp_server):
        """测试 MCP 服务器正确初始化。"""
        assert mcp_server is not None
        assert mcp_server.server_name == "test-knowledge-agent"
        assert mcp_server.knowledge_core is not None
        assert mcp_server.app is not None
    
    def test_get_server_info(self, mcp_server):
        """测试获取服务器信息。"""
        info = mcp_server.get_server_info()
        
        assert info["name"] == "test-knowledge-agent"
        assert "version" in info
        assert "capabilities" in info
        assert info["capabilities"]["knowledge_collection"] is True
        assert info["capabilities"]["semantic_search"] is True
    
    def test_get_knowledge_item_integration(self, mcp_server, sample_item):
        """测试通过核心检索知识条目。"""
        # 通过核心获取条目
        retrieved_item = mcp_server.knowledge_core.get_knowledge_item(sample_item.id)
        
        assert retrieved_item is not None
        assert retrieved_item.id == sample_item.id
        assert retrieved_item.title == sample_item.title
        assert retrieved_item.content == sample_item.content
    
    def test_list_knowledge_items_integration(self, mcp_server, sample_item):
        """测试通过核心列出知识条目。"""
        # 列出条目
        items = mcp_server.knowledge_core.list_knowledge_items(limit=10, offset=0)
        
        assert isinstance(items, list)
        assert len(items) > 0
        assert any(item.id == sample_item.id for item in items)
    
    def test_get_statistics_integration(self, mcp_server, sample_item):
        """测试通过核心获取统计信息。"""
        stats = mcp_server.knowledge_core.get_statistics()
        
        assert "total_items" in stats
        assert "total_categories" in stats
        assert "total_tags" in stats
        assert "total_relationships" in stats
        assert stats["total_items"] >= 1  # 至少包含我们的示例条目
    
    def test_export_import_integration(self, mcp_server, sample_item):
        """测试通过核心导出和导入数据。"""
        # 导出数据
        export_data = mcp_server.knowledge_core.export_data(format="json")
        
        assert "knowledge_items" in export_data
        assert "categories" in export_data
        assert "tags" in export_data
        assert "relationships" in export_data
        assert len(export_data["knowledge_items"]) >= 1
        
        # 验证示例条目在导出数据中
        item_ids = [item["id"] for item in export_data["knowledge_items"]]
        assert sample_item.id in item_ids
    
    def test_organize_knowledge_integration(self, mcp_server, sample_item):
        """测试通过核心组织知识条目。"""
        # 组织条目
        result = mcp_server.knowledge_core.organize_knowledge(sample_item)
        
        assert result is not None
        assert "item_id" in result
        assert result["item_id"] == sample_item.id
        assert "categories" in result
        assert "tags" in result
        assert "relationships" in result
        assert result["success"] is True
    
    def test_error_handling_invalid_item_id(self, mcp_server):
        """测试无效条目 ID 的错误处理。"""
        # 尝试获取不存在的条目
        item = mcp_server.knowledge_core.get_knowledge_item("non-existent-id")
        
        # 不存在的条目应返回 None
        assert item is None
    
    def test_list_with_filters(self, mcp_server, sample_item):
        """测试带过滤条件的列表查询。"""
        # 为示例条目添加分类
        category = Category(
            id="test-cat-1",
            name="Test Category",
            description="A test category",
            parent_id=None,
            confidence=0.9
        )
        sample_item.add_category(category)
        mcp_server.knowledge_core._storage_manager.save_knowledge_item(sample_item)
        
        # 按分类过滤列出条目
        items = mcp_server.knowledge_core.list_knowledge_items(
            category="Test Category",
            limit=10
        )
        
        assert isinstance(items, list)
        # 应找到带有该分类的条目
        assert any(item.id == sample_item.id for item in items)
    
    def test_pagination(self, mcp_server, sample_item):
        """测试 list_knowledge_items 的分页功能。"""
        # 创建多个条目
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
        
        # 测试分页
        page1 = mcp_server.knowledge_core.list_knowledge_items(limit=3, offset=0)
        page2 = mcp_server.knowledge_core.list_knowledge_items(limit=3, offset=3)
        
        assert len(page1) <= 3
        assert len(page2) <= 3
        
        # 不同页应包含不同的条目
        page1_ids = {item.id for item in page1}
        page2_ids = {item.id for item in page2}
        assert page1_ids != page2_ids or len(page2) == 0
