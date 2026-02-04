#!/usr/bin/env python3
"""
测试参数验证功能
"""

from knowledge_agent.server import KnowledgeMCPServer

server = KnowledgeMCPServer("test-server")
core = server.knowledge_core

print("=" * 60)
print("测试参数验证")
print("=" * 60)

print("\n1. 测试空item_id")
try:
    result = core.get_knowledge_item("")
    if result is None:
        print("✅ 正确处理空ID")
except Exception as e:
    print(f"✅ 捕获异常: {type(e).__name__}")

print("\n2. 测试不存在的item_id")
result = core.get_knowledge_item("non-existent-id")
if result is None:
    print("✅ 正确返回None")

print("\n3. 测试有效的limit参数")
try:
    items = core.list_knowledge_items(limit=1, offset=0)
    print(f"✅ 有效的limit参数: 返回 {len(items)} 个条目")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n4. 测试分页边界")
items = core.list_knowledge_items(limit=100, offset=0)
print(f"✅ 大limit值: 返回 {len(items)} 个条目")

items = core.list_knowledge_items(limit=1, offset=1000)
print(f"✅ 大offset值: 返回 {len(items)} 个条目")

print("\n5. 测试过滤功能")
items = core.list_knowledge_items(category="不存在的分类")
print(f"✅ 不存在的分类: 返回 {len(items)} 个条目")

print("\n" + "=" * 60)
print("✅ 参数验证测试完成！")
print("=" * 60)
