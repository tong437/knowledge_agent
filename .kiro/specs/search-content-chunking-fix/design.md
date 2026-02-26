# 搜索内容分块溢出修复设计

## 概述

MCP 工具 `search_knowledge` 在处理大型文档（如整本 PDF 书籍）时，搜索结果中携带了未经有效大小控制的内容，导致上下文窗口溢出、会话异常终止。本修复的核心策略是在搜索结果构建的多个层级引入内容大小控制机制：单分块截断、分块数量限制、结果总大小预算控制，以及分块缺失时的延迟分块恢复。

## 术语表

- **Bug_Condition (C)**：触发缺陷的条件——搜索结果中包含的内容总大小超出安全阈值，或知识项缺少分块数据导致降级路径返回无效结果
- **Property (P)**：期望行为——搜索结果的总内容大小始终在安全上限内，且每个搜索结果都包含有效的分块内容片段
- **Preservation**：现有行为中不应被修改的部分——小型文档的完整返回、正常分块的搜索精度、结果的排序/过滤/分组逻辑
- **`search_knowledge`**：`core/knowledge_agent_core.py` 中的核心搜索方法，构建返回给 MCP 调用方的结果字典
- **`_chunk_search`**：`core/search/search_engine_impl.py` 中的分块搜索路径，返回 `matched_chunks` 和 `context_chunks`
- **`_item_search`**：`core/search/search_engine_impl.py` 中的文档级搜索降级路径
- **`ContentChunker`**：`core/chunking/content_chunker.py` 中的内容分块引擎
- **内容预算（Content Budget）**：单次搜索结果允许返回的最大内容总字符数

## 缺陷详情

### 故障条件

缺陷在以下场景中触发：搜索命中大型文档（内容长度远超常规文本），且满足以下任一条件：(a) 知识项在导入时分块失败，搜索降级为文档级路径，`matched_chunks` 为空；(b) 分块搜索路径返回的分块内容本身过大或分块数量过多，累计内容超出上下文窗口限制；(c) `search_knowledge` 构建结果字典时未对分块内容施加任何大小控制。

**形式化规约：**
```
FUNCTION isBugCondition(searchResult)
  INPUT: searchResult of type SearchResult（包含 item, matched_chunks, context_chunks）
  OUTPUT: boolean

  totalContentSize := len(searchResult.item.content)
  FOR EACH chunk IN searchResult.matched_chunks:
    totalContentSize += len(chunk.content)
  FOR EACH chunk IN searchResult.context_chunks:
    totalContentSize += len(chunk.content)

  hasNoChunks := len(searchResult.matched_chunks) == 0
                 AND len(searchResult.item.content) > SAFE_CONTENT_THRESHOLD

  RETURN totalContentSize > MAX_RESULT_CONTENT_SIZE
         OR hasNoChunks
END FUNCTION
```

### 示例

- 用户搜索"机器学习"，命中一本 500 页 PDF 书籍（content 约 200 万字符），该书导入时分块失败。系统降级为 `_item_search`，返回 `content` 截断为 200 字符，但 `matched_chunks` 为空列表，调用方无法获取任何有效内容片段
- 用户搜索"深度学习"，命中同一本书，分块索引可用但该书被分为 800 个分块。`_chunk_search` 返回 15 个 `matched_chunks`（每个约 1500 字符）加上 30 个 `context_chunks`（每个约 1500 字符），总计约 67,500 字符，超出 MCP 上下文窗口限制
- 用户搜索"Python 基础"，命中一个 3000 字符的普通文本笔记。系统正常返回完整内容，不受影响（非缺陷条件）
- 用户搜索"算法"，命中一本大型 PDF，分块索引中有 5 个匹配分块，每个分块约 1500 字符。总计约 7,500 字符，在安全范围内，正常返回（边界情况）

## 期望行为

### 保持不变的行为

**不变行为：**
- 小型知识项（内容长度在合理范围内，如 < 5000 字符）的搜索结果必须继续完整返回，不受新增大小限制影响
- 正常大小分块（单个分块 < 1500 字符）的搜索结果必须继续完整返回 `matched_chunks` 和 `context_chunks`
- 导入时分块成功的知识项必须继续使用已有分块数据进行搜索，搜索精度和召回率不受影响
- 搜索结果的过滤（分类、标签、来源类型）、排序（相关度、日期、标题）、分组逻辑必须保持不变
- `ResultProcessor` 的所有现有方法行为不变

**范围：**
所有不涉及大型文档内容溢出的搜索场景应完全不受本修复影响，包括：
- 小型文档的搜索和返回
- 正常大小分块的搜索和返回
- 搜索选项的过滤、排序、分组操作
- 非搜索功能（知识收集、导出、导入等）

## 假设的根因

基于代码分析，最可能的问题如下：

1. **`search_knowledge` 结果构建无大小控制**：`knowledge_agent_core.py` 第 460-475 行，构建结果字典时直接调用 `mc.to_dict()` 和 `cc.to_dict()`，未对分块内容施加任何大小限制，也未计算总内容大小
   - `content` 字段仅截断为 200 字符，但 `matched_chunks` 和 `context_chunks` 中的 `content` 完全未截断
   - 多个大分块的内容累加后可轻易超出上下文窗口限制

2. **`_chunk_search` 分块数量无上限**：`search_engine_impl.py` 第 116-223 行，`matched_chunks` 和 `context_chunks` 的数量仅受搜索命中数限制，无独立的分块数量上限
   - 每个 `matched_chunk` 还会加载相邻的 `context_chunks`，进一步放大内容量
   - 一个大型文档可能命中数十个分块，每个分块再加载 2 个上下文分块

3. **`_item_search` 降级路径无分块恢复**：当知识项缺少分块数据时，`_item_search` 返回的 `SearchResult` 中 `matched_chunks` 为空列表，`content` 仅截断为 200 字符，调用方无法获取有效内容
   - 没有延迟分块机制来恢复缺失的分块数据
   - 没有从完整内容中提取相关片段的降级策略

4. **`collect_knowledge` 分块失败无恢复**：`knowledge_agent_core.py` 第 280-287 行，分块异常仅记录警告日志，不重试也不标记，导致该知识项永远没有分块数据

## 正确性属性

Property 1: 故障条件 - 搜索结果内容大小控制

_对于任意_ 搜索结果，当结果中包含的内容总大小（`content` + `matched_chunks` + `context_chunks`）超出安全阈值时，修复后的 `search_knowledge` 方法应当对内容进行截断或裁剪，确保返回给 MCP 调用方的单个结果内容总大小不超过 `MAX_RESULT_CONTENT_SIZE`（建议 30,000 字符），且所有结果的内容总大小不超过 `MAX_TOTAL_CONTENT_SIZE`（建议 100,000 字符）。

**验证需求：2.1, 2.2, 2.3**

Property 2: 故障条件 - 缺失分块的延迟恢复

_对于任意_ 搜索命中的大型知识项，当该知识项缺少分块数据时，修复后的系统应当尝试对该知识项进行延迟分块，或至少从完整内容中提取与查询相关的片段作为 `matched_chunks` 返回，而非返回空的 `matched_chunks`。

**验证需求：2.1, 2.4**

Property 3: 保持不变 - 小型文档完整返回

_对于任意_ 搜索结果，当知识项内容较短（< 5000 字符）且分块大小在正常范围内时，修复后的系统应当产生与修复前完全相同的结果，所有内容完整返回，不被不必要地截断。

**验证需求：3.1, 3.2**

Property 4: 保持不变 - 搜索过滤排序逻辑

_对于任意_ 搜索请求，修复后的系统在过滤（分类、标签、来源类型、最低相关度）、排序（相关度、日期、标题）和分组操作上应当产生与修复前完全相同的结果，内容大小控制不影响结果的选择和排列顺序。

**验证需求：3.3, 3.4**

## 修复实现

### 所需变更

假设根因分析正确：

**文件**：`core/knowledge_agent_core.py`

**方法**：`search_knowledge`

**具体变更**：
1. **引入内容大小常量**：在模块级别定义 `MAX_CHUNK_CONTENT_SIZE = 1500`（单分块最大字符数）、`MAX_MATCHED_CHUNKS = 5`（单结果最大匹配分块数）、`MAX_CONTEXT_CHUNKS = 3`（单结果最大上下文分块数）、`MAX_RESULT_CONTENT_SIZE = 30000`（单结果最大内容总字符数）、`MAX_TOTAL_CONTENT_SIZE = 100000`（所有结果最大内容总字符数）
2. **分块内容截断**：在构建结果字典时，对每个 `matched_chunk` 和 `context_chunk` 的 `content` 字段施加 `MAX_CHUNK_CONTENT_SIZE` 截断
3. **分块数量限制**：对 `matched_chunks` 限制为 `MAX_MATCHED_CHUNKS` 个，对 `context_chunks` 限制为 `MAX_CONTEXT_CHUNKS` 个
4. **结果总大小预算控制**：计算所有结果的内容总大小，超出 `MAX_TOTAL_CONTENT_SIZE` 时停止添加更多结果
5. **`content` 字段截断阈值提升**：将 `content` 截断阈值从 200 字符提升到 2000 字符，为无分块的降级场景提供更多有效内容

**文件**：`core/search/search_engine_impl.py`

**方法**：`_chunk_search`

**具体变更**：
1. **限制每个 item 的 matched_chunks 数量**：在构建 `matched_chunks` 列表时，按分数排序后只取前 N 个
2. **限制 context_chunks 数量**：对每个 item 的 `context_chunks` 总数施加上限

**文件**：`core/knowledge_agent_core.py`

**方法**：`search_knowledge`（延迟分块逻辑）

**具体变更**：
1. **检测缺失分块**：在构建结果字典时，检查 `matched_chunks` 是否为空且 `item.content` 长度超过阈值
2. **延迟分块恢复**：对缺失分块的知识项调用 `ContentChunker.chunk()` 进行即时分块，将分块结果保存到存储层和索引
3. **降级片段提取**：如果延迟分块也失败，从 `item.content` 中提取包含查询关键词的片段作为 `matched_chunks` 返回

## 测试策略

### 验证方法

测试策略分两阶段：首先在未修复代码上复现缺陷（探索性测试），然后验证修复的正确性和行为保持。

### 探索性故障条件检查

**目标**：在实施修复之前，复现缺陷并确认根因分析。如果复现结果与假设不符，需要重新分析。

**测试计划**：构造大型知识项（content > 50,000 字符），模拟分块缺失和分块过多的场景，在未修复代码上运行搜索，观察返回结果的内容大小。

**测试用例**：
1. **大型文档无分块测试**：创建一个 content 为 100,000 字符的知识项，不生成分块数据，执行搜索。预期在未修复代码上 `matched_chunks` 为空，`content` 仅 200 字符（将在未修复代码上失败）
2. **大型文档多分块测试**：创建一个大型知识项并生成 50 个分块（每个 1500 字符），执行搜索命中多个分块。预期在未修复代码上返回所有匹配分块和上下文分块，总内容超出安全阈值（将在未修复代码上失败）
3. **分块内容超大测试**：创建分块内容为 10,000 字符的异常大分块，执行搜索。预期在未修复代码上返回未截断的大分块内容（将在未修复代码上失败）
4. **正常文档基线测试**：创建一个 3000 字符的普通知识项，执行搜索。预期正常返回（在未修复代码上也应通过）

**预期反例**：
- 大型文档搜索结果的总内容大小超出 100,000 字符
- 无分块知识项的搜索结果中 `matched_chunks` 为空列表
- 可能原因：结果构建无大小控制、分块数量无上限、降级路径无恢复机制

### 修复检查

**目标**：验证对于所有触发缺陷条件的输入，修复后的函数产生期望行为。

**伪代码：**
```
FOR ALL searchResult WHERE isBugCondition(searchResult) DO
  result := search_knowledge_fixed(query)
  totalSize := calculateTotalContentSize(result)
  ASSERT totalSize <= MAX_TOTAL_CONTENT_SIZE
  FOR EACH item_result IN result["results"]:
    itemSize := calculateItemContentSize(item_result)
    ASSERT itemSize <= MAX_RESULT_CONTENT_SIZE
    ASSERT len(item_result["matched_chunks"]) <= MAX_MATCHED_CHUNKS
    IF item_result 对应大型知识项且原本无分块:
      ASSERT len(item_result["matched_chunks"]) > 0  // 延迟分块恢复
END FOR
```

### 保持检查

**目标**：验证对于所有不触发缺陷条件的输入，修复后的函数产生与原函数相同的结果。

**伪代码：**
```
FOR ALL searchInput WHERE NOT isBugCondition(searchInput) DO
  ASSERT search_knowledge_original(searchInput) == search_knowledge_fixed(searchInput)
END FOR
```

**测试方法**：推荐使用基于属性的测试（Property-Based Testing）进行保持检查，因为：
- 自动生成大量测试用例覆盖输入域
- 捕获手动单元测试可能遗漏的边界情况
- 对非缺陷输入的行为不变性提供强保证

**测试计划**：先在未修复代码上观察小型文档和正常分块的搜索行为，然后编写基于属性的测试捕获该行为。

**测试用例**：
1. **小型文档保持测试**：观察未修复代码上小型文档（< 5000 字符）的搜索结果，验证修复后结果完全一致
2. **正常分块保持测试**：观察未修复代码上正常大小分块的搜索结果，验证修复后 `matched_chunks` 和 `context_chunks` 内容不变
3. **过滤排序保持测试**：观察未修复代码上各种过滤和排序选项的搜索结果，验证修复后结果顺序和内容一致
4. **分组功能保持测试**：观察未修复代码上分组搜索的结果，验证修复后分组逻辑不变

### 单元测试

- 测试 `search_knowledge` 对大型文档搜索结果的内容截断逻辑
- 测试单分块内容超过 `MAX_CHUNK_CONTENT_SIZE` 时的截断行为
- 测试 `matched_chunks` 和 `context_chunks` 数量限制
- 测试结果总大小预算控制（超出 `MAX_TOTAL_CONTENT_SIZE` 时停止添加结果）
- 测试延迟分块恢复逻辑（无分块知识项的即时分块）
- 测试延迟分块失败时的降级片段提取
- 测试小型文档不受截断影响

### 基于属性的测试

- 生成随机大小的知识项内容（从 100 到 500,000 字符），验证搜索结果总大小始终不超过 `MAX_TOTAL_CONTENT_SIZE`
- 生成随机数量和大小的分块，验证返回的分块数量始终不超过上限
- 生成小型知识项（< 5000 字符），验证修复前后搜索结果完全一致
- 生成各种搜索选项组合，验证过滤、排序、分组逻辑不受影响

### 集成测试

- 测试完整的搜索流程：导入大型 PDF → 分块 → 搜索 → 验证结果大小在安全范围内
- 测试分块失败场景：导入大型 PDF → 模拟分块异常 → 搜索 → 验证延迟分块恢复
- 测试多结果场景：搜索命中多个大型文档 → 验证总内容大小预算控制
- 测试混合场景：搜索同时命中大型和小型文档 → 验证大型文档被截断而小型文档完整返回
