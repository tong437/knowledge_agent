#!/usr/bin/env python3
"""
手动测试MCP工具功能
"""

from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.models import KnowledgeItem, SourceType, Category, Tag
from datetime import datetime

# 创建服务器实例
server = KnowledgeMCPServer("test-server")
core = server.knowledge_core

print("=" * 60)
print("测试 1: 创建知识条目")
print("=" * 60)

# 创建测试知识条目
item = KnowledgeItem(
    id="test-001",
    title="Python编程基础",
    content="Python是一种高级编程语言，具有简洁的语法和强大的功能。",
    source_type=SourceType.DOCUMENT,
    source_path="/test/python_basics.txt",
    categories=[],
    tags=[],
    metadata={"author": "测试用户"},
    created_at=datetime.now(),
    updated_at=datetime.now()
)

# 保存到存储
core._storage_manager.save_knowledge_item(item)
print(f"✅ 创建知识条目: {item.id}")

print("\n" + "=" * 60)
print("测试 2: 获取知识条目")
print("=" * 60)

# 测试 get_knowledge_item
retrieved = core.get_knowledge_item("test-001")
if retrieved:
    print(f"✅ 成功获取: {retrieved.title}")
    print(f"   内容: {retrieved.content[:50]}...")
else:
    print("❌ 获取失败")

print("\n" + "=" * 60)
print("测试 3: 列出知识条目")
print("=" * 60)

# 测试 list_knowledge_items
items = core.list_knowledge_items(limit=10)
print(f"✅ 找到 {len(items)} 个知识条目")
for i, item in enumerate(items, 1):
    print(f"   {i}. {item.title}")

print("\n" + "=" * 60)
print("测试 4: 整理知识条目")
print("=" * 60)

# 测试 organize_knowledge
result = core.organize_knowledge(retrieved)
print(f"✅ 整理完成:")
print(f"   分类数量: {len(result['categories'])}")
print(f"   标签数量: {len(result['tags'])}")
print(f"   关联关系: {len(result['relationships'])}")

print("\n" + "=" * 60)
print("测试 5: 获取统计信息")
print("=" * 60)

# 测试 get_statistics
stats = core.get_statistics()
print(f"✅ 知识库统计:")
print(f"   总条目数: {stats['total_items']}")
print(f"   总分类数: {stats['total_categories']}")
print(f"   总标签数: {stats['total_tags']}")
print(f"   总关系数: {stats['total_relationships']}")

print("\n" + "=" * 60)
print("测试 6: 导出数据")
print("=" * 60)

# 测试 export_data
export = core.export_data(format="json")
print(f"✅ 导出成功:")
print(f"   知识条目: {len(export['knowledge_items'])}")
print(f"   分类: {len(export['categories'])}")
print(f"   标签: {len(export['tags'])}")
print(f"   关系: {len(export['relationships'])}")

print("\n" + "=" * 60)
print("测试 7: 过滤和分页")
print("=" * 60)

# 添加分类
category = Category(
    id="cat-001",
    name="编程",
    description="编程相关知识",
    parent_id=None,
    confidence=0.9
)
retrieved.add_category(category)
core._storage_manager.save_knowledge_item(retrieved)

# 测试过滤
filtered = core.list_knowledge_items(category="编程", limit=5)
print(f"✅ 按分类过滤: 找到 {len(filtered)} 个条目")

# 测试分页
page1 = core.list_knowledge_items(limit=2, offset=0)
page2 = core.list_knowledge_items(limit=2, offset=2)
print(f"✅ 分页测试:")
print(f"   第1页: {len(page1)} 个条目")
print(f"   第2页: {len(page2)} 个条目")

print("\n" + "=" * 60)
print("✅ 所有测试完成！")
print("=" * 60)
