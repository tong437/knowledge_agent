#!/usr/bin/env python3
"""
测试错误处理功能
"""

from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.core.exceptions import KnowledgeAgentError

server = KnowledgeMCPServer("test-server")
core = server.knowledge_core

print("=" * 60)
print("测试错误处理")
print("=" * 60)

print("\n1. 测试导出无效格式")
try:
    result = core.export_data(format="invalid_format")
    print("❌ 应该抛出异常")
except KnowledgeAgentError as e:
    print(f"✅ 正确捕获异常: {e}")

print("\n2. 测试导入无效数据")
try:
    result = core.import_data("not a dict")
    print("❌ 应该抛出异常")
except KnowledgeAgentError as e:
    print(f"✅ 正确捕获异常: {e}")

print("\n3. 测试获取不存在的条目")
result = core.get_knowledge_item("definitely-does-not-exist")
if result is None:
    print("✅ 正确返回None而不是抛出异常")

print("\n" + "=" * 60)
print("✅ 错误处理测试完成！")
print("=" * 60)
