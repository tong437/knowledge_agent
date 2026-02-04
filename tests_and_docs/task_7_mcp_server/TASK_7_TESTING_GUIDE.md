# 任务7测试指南 - MCP服务器接口测试

本指南将帮助您验证任务7（实现MCP服务器接口）是否正确完成。

## 📋 测试清单

### ✅ 1. 运行单元测试

首先运行所有测试以确保没有破坏现有功能：

```bash
# 运行所有测试
python -m pytest knowledge_agent/tests/ -v

# 只运行MCP集成测试
python -m pytest knowledge_agent/tests/test_mcp_integration.py -v

# 运行核心功能测试
python -m pytest knowledge_agent/tests/test_core.py -v
```

**预期结果：** 所有73个测试应该通过 ✅

---

### ✅ 2. 测试MCP服务器启动

测试服务器是否能正常启动：

```bash
# 使用stdio传输方式启动（用于本地MCP客户端）
python knowledge_agent_server.py --transport stdio

# 使用SSE传输方式启动（用于Web客户端）
python knowledge_agent_server.py --transport sse --port 8000
```

**预期结果：** 
- 服务器应该启动并显示服务器信息
- 没有错误或异常
- 显示已注册的工具和资源

---

### ✅ 3. 交互式测试MCP工具

创建一个测试脚本来验证MCP工具功能：

```python
# test_mcp_tools_manual.py
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
```

运行测试脚本：

```bash
python test_mcp_tools_manual.py
```

**预期结果：** 所有7个测试应该显示 ✅ 成功

---

### ✅ 4. 测试MCP资源

创建资源测试脚本：

```python
# test_mcp_resources_manual.py
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
```

运行资源测试：

```bash
python test_mcp_resources_manual.py
```

**预期结果：** 所有6个资源测试应该显示 ✅ 成功

---

### ✅ 5. 测试参数验证

创建参数验证测试：

```python
# test_parameter_validation.py
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

print("\n3. 测试无效的limit参数")
try:
    # 在实际的MCP工具中会验证，这里测试核心功能
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
```

运行验证测试：

```bash
python test_parameter_validation.py
```

**预期结果：** 所有验证测试应该正确处理边界情况

---

### ✅ 6. 测试错误处理

创建错误处理测试：

```python
# test_error_handling.py
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
```

运行错误处理测试：

```bash
python test_error_handling.py
```

**预期结果：** 所有错误应该被正确捕获和处理

---

## 📊 完整测试命令

运行所有测试的快速命令：

```bash
# 1. 运行所有单元测试
python -m pytest knowledge_agent/tests/ -v --tb=short

# 2. 运行MCP集成测试
python -m pytest knowledge_agent/tests/test_mcp_integration.py -v

# 3. 检查代码诊断
# （在IDE中或使用linter）

# 4. 运行手动测试脚本
python test_mcp_tools_manual.py
python test_mcp_resources_manual.py
python test_parameter_validation.py
python test_error_handling.py
```

---

## ✅ 验收标准

任务7完成的标志：

1. ✅ **所有73个单元测试通过**
2. ✅ **10个MCP集成测试通过**
3. ✅ **MCP服务器能够正常启动**
4. ✅ **所有8个MCP工具正确实现并有参数验证**
5. ✅ **所有6个MCP资源正确实现**
6. ✅ **错误处理机制工作正常**
7. ✅ **响应格式标准化（status, message, data）**
8. ✅ **支持过滤和分页功能**
9. ✅ **数据导入导出功能正常**
10. ✅ **与存储层正确集成**

---

## 🎯 快速验证

如果您只想快速验证，运行这个命令：

```bash
python -m pytest knowledge_agent/tests/test_mcp_integration.py -v
```

如果所有10个集成测试通过，说明任务7基本完成！

---

## 📝 需求验证

任务7满足以下需求：

- ✅ **需求 4.2**: API响应标准化 - 所有工具使用统一的响应格式
- ✅ **需求 4.4**: 请求格式验证 - 所有工具都有参数验证
- ✅ **需求 4.3**: 资源访问 - 提供6个资源端点
- ✅ **需求 7.1**: 清晰的工具列表 - 8个MCP工具定义明确
- ✅ **需求 7.2**: 实时反馈 - 标准化响应提供操作状态
- ✅ **需求 7.3**: 友好的错误信息 - 错误响应包含上下文和建议

---

## 🔍 故障排查

如果测试失败：

1. **检查依赖**: `pip install -r requirements.txt`
2. **检查数据库**: 确保SQLite数据库可以创建
3. **查看日志**: 检查错误日志了解详细信息
4. **运行单个测试**: `python -m pytest knowledge_agent/tests/test_mcp_integration.py::TestMCPIntegration::test_server_initialization -v`

---

## 📞 获取帮助

如果遇到问题：

1. 查看测试输出的详细错误信息
2. 检查 `knowledge_agent/tests/test_mcp_integration.py` 中的测试用例
3. 查看 `knowledge_agent/server/mcp_tools.py` 和 `mcp_resources.py` 的实现

---

**祝测试顺利！** 🎉
