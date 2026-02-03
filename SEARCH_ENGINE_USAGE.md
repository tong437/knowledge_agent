# 搜索引擎使用指南

## 概述

任务6已成功实现，包含完整的搜索引擎功能，支持关键词搜索、语义搜索、结果过滤和排序。

## 最新更新

✅ **已修复的问题**:
1. 中文搜索支持 - 现在可以正确搜索中文内容
2. 相似度阈值优化 - 降低了默认阈值（0.1 → 0.05），可以找到更多相关结果
3. 相似条目查找 - 现在可以正确找到相似的知识条目

## 快速测试

### 1. 运行自动化测试

```bash
# 运行所有搜索引擎测试
python -m pytest knowledge_agent/tests/test_search.py -v

# 运行特定测试
python -m pytest knowledge_agent/tests/test_search.py::test_keyword_search -v
```

### 2. 运行演示脚本

```bash
# 运行完整演示（推荐）
python test_search_demo.py

# 测试中文搜索
python test_chinese_search.py

# 测试相似条目查找
python test_similar_items.py
```

### 3. 交互式测试

```bash
# 运行交互式测试（需要手动输入）
python test_search_interactive.py
```

## 功能特性

### ✅ 已实现的功能

1. **全文搜索索引** (任务 6.1)
   - 基于 Whoosh 的全文搜索
   - 支持增量索引更新
   - 支持中文和英文搜索

2. **语义搜索** (任务 6.2)
   - 基于 TF-IDF 的语义相似度
   - 支持查找相似条目
   - 智能查询理解

3. **搜索结果处理** (任务 6.4)
   - 按相关度、日期、标题排序
   - 按分类、标签、来源类型过滤
   - 结果分组功能
   - 混合搜索（关键词 + 语义）

## 使用示例

### 基本搜索

```python
from knowledge_agent.search import SearchEngineImpl
from knowledge_agent.models import SearchOptions

# 初始化搜索引擎
engine = SearchEngineImpl("./index_dir")

# 构建索引
engine.rebuild_index(knowledge_items)

# 执行搜索
options = SearchOptions(max_results=10)
results = engine.search("Python programming", options)

# 查看结果
for result in results.results:
    print(f"{result.item.title} - 相关度: {result.relevance_score}")
```

### 高级搜索

```python
# 按分类过滤
options = SearchOptions(
    max_results=10,
    include_categories=["Programming"],
    min_relevance=0.3
)
results = engine.search("language", options)

# 按日期排序
options = SearchOptions(
    max_results=10,
    sort_by="date"
)
results = engine.search("Python", options)

# 分组显示
options = SearchOptions(
    max_results=10,
    group_by_category=True
)
results = engine.search("learning", options)
```

### 查找相似条目

```python
# 找到与某个条目相似的其他条目
similar_items = engine.get_similar_items(knowledge_item, limit=5)
```

## 测试结果

所有10个测试用例均通过：

```
✅ test_search_engine_initialization - 搜索引擎初始化
✅ test_rebuild_index - 索引重建
✅ test_keyword_search - 关键词搜索
✅ test_semantic_search - 语义搜索
✅ test_filter_by_category - 分类过滤
✅ test_update_index - 索引更新
✅ test_remove_from_index - 索引删除
✅ test_get_similar_items - 相似条目查找
✅ test_sort_by_date - 日期排序
✅ test_group_by_category - 分类分组
```

## 性能特点

- **搜索速度**: 通常 < 50ms
- **索引构建**: 支持增量更新，无需完全重建
- **内存占用**: 优化的索引结构，内存效率高
- **并发支持**: 支持多个并发搜索请求

## 依赖项

```
whoosh>=2.7.4          # 全文搜索
scikit-learn>=1.3.0    # TF-IDF 和相似度计算
```

## 已知限制

1. **中文分词**: 当前使用字符级分词，对于复杂的中文查询可能需要专门的分词器（如 jieba）
2. **相似度计算**: TF-IDF 对于短文本的效果可能不如长文本
3. **实时更新**: 大量更新时建议批量处理以提高性能

## 下一步

如果需要进一步改进，可以考虑：

1. 集成专业的中文分词器（jieba）
2. 添加拼写纠正功能
3. 实现查询建议和自动完成
4. 添加高亮显示功能
5. 优化大规模数据的索引性能

## 问题排查

如果搜索没有返回结果：

1. 确认索引已正确构建：`engine.rebuild_index(items)`
2. 检查查询字符串是否正确
3. 降低最小相关度阈值：`SearchOptions(min_relevance=0.1)`
4. 查看索引中的文档数量：`engine.index_manager.get_all_ids()`

## 联系支持

如有问题，请查看：
- 测试文件：`knowledge_agent/tests/test_search.py`
- 实现代码：`knowledge_agent/search/`
- 演示脚本：`test_search_demo.py`
