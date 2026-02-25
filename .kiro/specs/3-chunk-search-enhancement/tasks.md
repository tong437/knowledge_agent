# 实施计划：文档分块与两阶段搜索增强

## 概述

按依赖关系逐步实现文档分块机制和两阶段搜索策略。从底层数据模型开始，逐层向上构建存储层、分块引擎、搜索索引、搜索引擎改造，最终集成到核心流程和 MCP 工具层。

## 任务

- [x] 1. 新增 KnowledgeChunk 数据模型和 MatchedChunk 模型
  - [x] 1.1 创建 `knowledge_agent/models/knowledge_chunk.py`，实现 KnowledgeChunk dataclass
    - 包含字段：id、item_id、chunk_index、content、heading、start_position、end_position、metadata
    - 实现 `to_dict()` 和 `from_dict()` 方法
    - id 默认使用 `uuid.uuid4()` 生成
    - metadata 默认为空字典
    - _需求：1.1, 1.5, 1.6_

  - [x] 1.2 扩展 `knowledge_agent/models/search_result.py`，新增 MatchedChunk dataclass
    - 包含字段：chunk_id、content、heading、chunk_index、start_position、end_position、score
    - 实现 `to_dict()` 方法
    - 在 SearchResult 中新增 `matched_chunks: List[MatchedChunk]` 和 `context_chunks: List[MatchedChunk]` 字段（默认空列表）
    - 扩展 SearchResult.to_dict() 包含新字段的序列化
    - _需求：6.1, 6.3, 6.4_

  - [x] 1.3 更新 `knowledge_agent/models/__init__.py`，导出 KnowledgeChunk 和 MatchedChunk
    - _需求：1.1_

  - [ ]* 1.4 为 KnowledgeChunk 编写单元测试
    - 测试 to_dict/from_dict 往返一致性
    - 测试默认值和边界情况
    - _需求：1.5, 1.6_

- [x] 2. 扩展 SQLiteStorageManager 支持分块 CRUD
  - [x] 2.1 在 `knowledge_agent/storage/sqlite_storage.py` 的 `_init_database` 方法中新增 `knowledge_chunks` 表
    - 创建表结构：id、item_id、chunk_index、content、heading、start_position、end_position、metadata
    - 添加外键约束 `FOREIGN KEY (item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE`
    - 创建索引 `idx_chunks_item_id` 和 `idx_chunks_item_chunk`
    - 确保启用 `PRAGMA foreign_keys = ON`
    - _需求：1.3, 1.4_

  - [x] 2.2 在 SQLiteStorageManager 中实现分块 CRUD 方法
    - `save_chunks(item_id, chunks)`：先删除旧分块再批量插入新分块
    - `get_chunks_for_item(item_id)`：按 chunk_index 排序返回
    - `get_chunk_by_id(chunk_id)`：根据 ID 查询单个分块
    - `get_adjacent_chunks(item_id, chunk_index)`：查询前后相邻分块
    - _需求：8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 2.3 为存储层分块方法编写单元测试
    - 测试 save_chunks 的先删后插逻辑
    - 测试 get_chunks_for_item 的排序
    - 测试 get_adjacent_chunks 的边界情况（首尾分块）
    - 测试级联删除（删除 KnowledgeItem 后分块自动清理）
    - _需求：1.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 3. 检查点 - 确保数据模型和存储层测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [x] 4. 实现 ContentChunker 分块引擎
  - [x] 4.1 创建 `knowledge_agent/chunking/__init__.py` 和 `knowledge_agent/chunking/content_chunker.py`
    - 实现 ChunkConfig dataclass（min_chunk_size=100, max_chunk_size=1500, overlap_ratio=0.2）
    - 实现 ContentChunker 类及 `chunk(content, title)` 主方法
    - 实现三级分块策略：`_split_by_headings`（Markdown # 标题）→ `_split_by_paragraphs`（双换行符）→ `_sliding_window_split`（超长文本二次切分）
    - 短文档（长度 < min_chunk_size * 2）直接作为单分块返回
    - 异常时退化为单分块返回
    - 每个分块记录 start_position、end_position、heading
    - chunk_index 从 0 连续递增
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [ ]* 4.2 为 ContentChunker 编写单元测试
    - 测试短文档退化为单分块
    - 测试标题分块策略
    - 测试段落分块策略
    - 测试滑动窗口二次切分
    - 测试异常退化
    - 测试空内容和边界情况
    - _需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

- [-] 5. 扩展 SearchIndexManager 支持分块级 Whoosh 索引
  - [-] 5.1 在 `knowledge_agent/search/search_index_manager.py` 中新增分块索引功能
    - 定义分块索引 Schema（chunk_id、item_id、chunk_index、heading、content）
    - 分块索引存储在 `{index_dir}/chunks/` 子目录
    - 实现 `add_chunks(chunks)`：批量添加分块到索引
    - 实现 `remove_chunks_for_item(item_id)`：移除指定条目的所有分块
    - 实现 `search_chunks(query_str, limit)`：在分块索引上执行搜索
    - 实现 `rebuild_chunk_index(chunks)`：重建分块索引
    - 实现 `has_chunk_index()`：检查分块索引是否可用
    - _需求：4.1, 4.3, 4.4, 4.5_

  - [ ]* 5.2 为分块索引方法编写单元测试
    - 测试分块的添加、搜索、删除
    - 测试索引重建
    - 测试 has_chunk_index 判断
    - _需求：4.1, 4.3, 4.4, 4.5_

- [-] 6. 扩展 SemanticSearcher 支持分块级 TF-IDF
  - [x] 6.1 在 `knowledge_agent/search/semantic_searcher.py` 中新增分块语义搜索功能
    - 新增属性：chunk_vectorizer、chunk_vectors、chunks 列表、is_chunk_fitted
    - 实现 `fit_chunks(chunks)`：对分块列表构建 TF-IDF 模型
    - 实现 `search_chunks(query, top_k, min_similarity)`：分块级语义搜索
    - 实现 `update_chunks_for_item(item_id, chunks)`：更新指定条目的分块（移除旧的、添加新的、重新拟合）
    - 实现 `remove_chunks_for_item(item_id)`：移除指定条目的分块并重新拟合
    - _需求：4.2_

  - [ ]* 6.2 为分块语义搜索编写单元测试
    - 测试 fit_chunks 和 search_chunks
    - 测试 update_chunks_for_item 和 remove_chunks_for_item
    - _需求：4.2_

- [ ] 7. 检查点 - 确保分块引擎和搜索索引扩展测试通过
  - 确保所有测试通过，如有问题请向用户确认。

- [ ] 8. 改造 SearchEngineImpl 实现两阶段搜索
  - [ ] 8.1 在 `knowledge_agent/search/search_engine_impl.py` 中实现两阶段搜索
    - 将现有 `search()` 方法的逻辑重命名为 `_item_search()`
    - 新增 `_chunk_search()` 方法实现两阶段搜索：
      - 阶段1：在分块索引上执行关键词搜索 + TF-IDF 语义搜索，合并分块结果
      - 阶段2：按 item_id 分组，取每组最高分作为文档得分，加载上下文窗口
    - 改造 `search()` 方法：优先尝试分块搜索，分块索引不可用时降级为文档级搜索
    - 新增 `update_chunk_index(item_id, chunks)` 方法
    - 新增 `remove_chunks_from_index(item_id)` 方法
    - 新增 `rebuild_chunk_index(chunks)` 方法
    - 需要注入 SQLiteStorageManager 引用以加载上下文分块和通过 item_id 获取 KnowledgeItem
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 8.2 为两阶段搜索编写单元测试
    - 测试分块搜索的两阶段流程
    - 测试降级为文档级搜索
    - 测试上下文窗口加载
    - 测试分块索引为空时的行为
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 7.2_

- [ ] 9. 集成分块逻辑到 KnowledgeAgentCore
  - [ ] 9.1 修改 `knowledge_agent/core/knowledge_agent_core.py`
    - 在 `collect_knowledge()` 中：处理器生成 KnowledgeItem 后，调用 ContentChunker 分块，保存分块到存储层，更新分块索引
    - 在 `delete_knowledge_item()` 中：删除时同步清理分块索引（数据库级联删除自动清理存储层）
    - 在 `_initialize_components()` 中：初始化 ContentChunker，将 storage_manager 注入 SearchEngineImpl
    - 在 `rebuild_index` 相关逻辑中：加载所有分块并重建分块索引
    - _需求：3.1, 3.2, 3.3, 3.4_

  - [ ]* 9.2 为核心集成逻辑编写单元测试
    - 测试 collect_knowledge 流程中分块的生成和保存
    - 测试 delete_knowledge_item 流程中分块索引的清理
    - 测试分块失败时的降级处理（整个文档作为单分块）
    - _需求：3.1, 3.2, 3.3, 3.4, 7.1, 7.3_

- [ ] 10. 扩展 MCP 工具层搜索结果格式
  - [ ] 10.1 修改 `knowledge_agent/server/mcp_tools.py` 中的 search_knowledge 工具
    - 在搜索结果格式化中包含 matched_chunks 和 context_chunks 信息
    - 每个 matched_chunk 包含 chunk_id、content、heading、chunk_index、start_position、end_position
    - 保持向后兼容：matched_chunks 为空时不影响现有输出格式
    - _需求：6.1, 6.2, 6.3, 6.4_

  - [ ]* 10.2 为 MCP 搜索结果格式编写单元测试
    - 测试包含分块信息的搜索结果格式
    - 测试无分块时的向后兼容
    - _需求：6.1, 6.2, 6.3, 6.4_

- [ ] 11. 最终检查点 - 确保所有测试通过
  - 运行完整测试套件，确保所有测试通过，如有问题请向用户确认。

## 说明

- 标记 `*` 的子任务为可选测试任务，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保需求可追溯
- 检查点任务用于阶段性验证，确保增量开发的正确性
- 所有代码使用 Python 实现，测试使用 pytest 框架
