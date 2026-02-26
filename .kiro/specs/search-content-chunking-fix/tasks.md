# 实现计划

- [x] 1. 编写缺陷条件探索测试
  - **Property 1: Fault Condition** - 搜索结果内容大小失控
  - **CRITICAL**: 此测试必须在未修复代码上失败——失败即确认缺陷存在
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: 此测试编码了期望行为——修复后测试通过即验证修复正确性
  - **GOAL**: 产生反例，证明缺陷存在
  - **Scoped PBT Approach**: 针对确定性缺陷，将属性范围限定到具体的失败场景以确保可复现
  - 安装 hypothesis 库：在 pyproject.toml 的 dev 依赖中添加 `hypothesis>=6.0.0`，运行 `uv sync`
  - 创建测试文件 `tests/test_search_content_size.py`
  - 使用 hypothesis 的 `@given` 策略生成随机内容大小（50,000 ~ 500,000 字符）的知识项
  - 场景 A（无分块降级）：创建大型知识项但不生成分块数据，执行搜索，断言 `matched_chunks` 不为空（从设计文档故障条件：`hasNoChunks AND item.content > SAFE_CONTENT_THRESHOLD`）
  - 场景 B（分块内容溢出）：创建大型知识项并生成 50+ 个分块（每个约 1500 字符），执行搜索命中多个分块，断言单结果内容总大小 <= 30,000 字符且所有结果总大小 <= 100,000 字符（从设计文档故障条件：`totalContentSize > MAX_RESULT_CONTENT_SIZE`）
  - 场景 C（单分块超大）：创建分块内容为 10,000+ 字符的异常大分块，执行搜索，断言返回的分块内容已被截断
  - 在未修复代码上运行测试
  - **EXPECTED OUTCOME**: 测试失败（这是正确的——证明缺陷存在）
  - 记录发现的反例以理解根因
  - 当测试编写完成、运行完毕且失败已记录后，标记任务完成
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 编写保持性属性测试（在实施修复之前）
  - **Property 2: Preservation** - 小型文档和正常分块行为不变
  - **IMPORTANT**: 遵循观察优先方法论
  - 创建测试文件 `tests/test_search_preservation.py`
  - 观察：在未修复代码上，小型文档（< 5000 字符）的搜索结果完整返回，content 字段包含完整内容或 200 字符截断
  - 观察：在未修复代码上，正常大小分块（< 1500 字符）的 `matched_chunks` 和 `context_chunks` 内容完整返回
  - 观察：在未修复代码上，过滤（分类、标签）、排序（relevance、date、title）、分组操作的结果顺序和内容
  - 使用 hypothesis 生成小型知识项（100 ~ 5000 字符），验证修复前后搜索结果一致
  - 编写属性测试：对所有非缺陷条件输入（`NOT isBugCondition`），`search_knowledge` 的返回结果结构和内容不变
  - 编写属性测试：对各种 SearchOptions 组合（sort_by、include_categories、include_tags、group_by_category），过滤排序分组逻辑不受影响
  - 在未修复代码上运行测试
  - **EXPECTED OUTCOME**: 测试通过（确认基线行为已捕获）
  - 当测试编写完成、运行完毕且在未修复代码上通过后，标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. 修复搜索内容分块溢出缺陷

  - [x] 3.1 在 `core/knowledge_agent_core.py` 中引入内容大小常量和结果构建截断逻辑
    - 在模块级别定义常量：`MAX_CHUNK_CONTENT_SIZE = 1500`、`MAX_MATCHED_CHUNKS = 5`、`MAX_CONTEXT_CHUNKS = 3`、`MAX_RESULT_CONTENT_SIZE = 30000`、`MAX_TOTAL_CONTENT_SIZE = 100000`、`CONTENT_TRUNCATION_THRESHOLD = 2000`
    - 修改 `search_knowledge` 方法中的结果构建逻辑：
      - 将 `content` 截断阈值从 200 字符提升到 `CONTENT_TRUNCATION_THRESHOLD`（2000 字符）
      - 对 `matched_chunks` 列表限制为 `MAX_MATCHED_CHUNKS` 个
      - 对 `context_chunks` 列表限制为 `MAX_CONTEXT_CHUNKS` 个
      - 对每个分块的 `content` 字段施加 `MAX_CHUNK_CONTENT_SIZE` 截断
      - 计算单结果内容总大小，超出 `MAX_RESULT_CONTENT_SIZE` 时停止添加分块
      - 计算所有结果的内容总大小，超出 `MAX_TOTAL_CONTENT_SIZE` 时停止添加更多结果
    - _Bug_Condition: isBugCondition(searchResult) where totalContentSize > MAX_RESULT_CONTENT_SIZE OR (hasNoChunks AND item.content > SAFE_CONTENT_THRESHOLD)_
    - _Expected_Behavior: 单结果内容总大小 <= MAX_RESULT_CONTENT_SIZE，所有结果总大小 <= MAX_TOTAL_CONTENT_SIZE_
    - _Preservation: 小型文档（< 5000 字符）和正常分块（< 1500 字符）的搜索结果不受影响_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 在 `core/search/search_engine_impl.py` 的 `_chunk_search` 中限制分块数量
    - 修改 `_chunk_search` 方法：
      - 在构建 `matched_chunks` 列表时，按分数排序后只取前 N 个（引入 `MAX_MATCHED_CHUNKS_PER_ITEM` 常量）
      - 对每个 item 的 `context_chunks` 总数施加上限（引入 `MAX_CONTEXT_CHUNKS_PER_ITEM` 常量）
    - _Bug_Condition: 大型文档命中数十个分块，每个分块再加载上下文分块，内容量无上限_
    - _Expected_Behavior: 每个 item 的 matched_chunks 和 context_chunks 数量受控_
    - _Preservation: 正常搜索场景中分块数量本身就在限制范围内，不受影响_
    - _Requirements: 2.2_

  - [x] 3.3 在 `core/knowledge_agent_core.py` 的 `search_knowledge` 中实现延迟分块恢复逻辑
    - 在结果构建循环中，检测 `matched_chunks` 为空且 `item.content` 长度超过 `CONTENT_TRUNCATION_THRESHOLD` 的情况
    - 对缺失分块的知识项调用 `ContentChunker.chunk()` 进行即时分块
    - 将分块结果保存到存储层（`storage_manager.save_chunks`）和搜索索引（`search_engine.update_chunk_index`）
    - 如果延迟分块也失败，从 `item.content` 中提取包含查询关键词的片段作为 `matched_chunks` 返回
    - _Bug_Condition: hasNoChunks AND item.content > SAFE_CONTENT_THRESHOLD，降级路径返回空 matched_chunks_
    - _Expected_Behavior: 缺失分块的知识项通过延迟分块恢复，返回有效的 matched_chunks_
    - _Preservation: 已有分块数据的知识项不触发延迟分块逻辑_
    - _Requirements: 2.1, 2.4_

  - [x] 3.4 验证缺陷条件探索测试现在通过
    - **Property 1: Expected Behavior** - 搜索结果内容大小控制
    - **IMPORTANT**: 重新运行任务 1 中的同一测试——不要编写新测试
    - 任务 1 的测试编码了期望行为
    - 当此测试通过时，确认期望行为已满足
    - 运行任务 1 中的缺陷条件探索测试
    - **EXPECTED OUTCOME**: 测试通过（确认缺陷已修复）
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 验证保持性测试仍然通过
    - **Property 2: Preservation** - 小型文档和正常分块行为不变
    - **IMPORTANT**: 重新运行任务 2 中的同一测试——不要编写新测试
    - 运行任务 2 中的保持性属性测试
    - **EXPECTED OUTCOME**: 测试通过（确认无回归）
    - 确认修复后所有测试仍然通过（无回归）

- [x] 4. 检查点 - 确保所有测试通过
  - 运行完整测试套件：`pytest tests/ -v`
  - 确保所有测试通过，如有问题请询问用户
