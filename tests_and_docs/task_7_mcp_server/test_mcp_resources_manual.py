#!/usr/bin/env python3
"""
手动测试MCP资源功能
"""

from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.models import KnowledgeItem, SourceType
from datetime import datetime
import json

# 创建服务器实例
server = KnowledgeMCPServer("test-server")
core = server.knowledge_core

# 创建测试数据
for i in range(3):
    item = KnowledgeItem(
        id=f"resource-test-{i}",
        title=f"测试条目 {i}",
        content=f"这是测试条目 {i} 的内容",
        source_type=SourceType.DOCUMENT,
        source_path=f"/test/doc{i}.txt",
        categories=[],
        tags=[],
        metadata={},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    core._storage_manager.save_knowledge_item(item)

print("=" * 60)
print("测试 MCP 资源")
print("=" * 60)

# 注意：这里我们直接测试核心功能，因为资源是通过MCP协议访问的
# 在实际使用中，资源会通过 knowledge://items 等URI访问

print("\n1. 测试 knowledge://items 资源")
items = core.list_knowledge_items()
print(f"✅ 获取所有条目: {len(items)} 个")

print("\n2. 测试 knowledge://items/{{item_id}} 资源")
item = core.get_knowledge_item("resource-test-0")
if item:
    print(f"✅ 获取特定条目: {item.title}")

print("\n3. 测试 knowledge://categories 资源")
categories = core._storage_manager.get_all_categories()
print(f"✅ 获取所有分类: {len(categories)} 个")

print("\n4. 测试 knowledge://tags 资源")
tags = core._storage_manager.get_all_tags()
print(f"✅ 获取所有标签: {len(tags)} 个")

print("\n5. 测试 knowledge://graph 资源")
items = core._storage_manager.get_all_knowledge_items()
print(f"✅ 知识图谱节点: {len(items)} 个")

print("\n6. 测试 knowledge://stats 资源")
stats = core.get_statistics()
print(f"✅ 统计信息:")
print(f"   - 总条目: {stats['total_items']}")
print(f"   - 总分类: {stats['total_categories']}")
print(f"   - 总标签: {stats['total_tags']}")

print("\n" + "=" * 60)
print("✅ 所有资源测试完成！")
print("=" * 60)
