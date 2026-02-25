# 需求文档

## 简介

当前知识管理系统将每个文档（PDF、代码、网页等）作为一个完整的 KnowledgeItem 存储，搜索时在文档级别进行关键词和 TF-IDF 语义匹配。对于长文档，某个段落包含用户查询的答案，但文档级的向量化和关键词匹配无法精确命中该段落，导致搜索返回 0 结果。

本功能通过引入文档分块（Chunking）机制和两阶段搜索策略，将长文档拆分为语义完整的分块，在分块级别执行搜索，再聚合为文档级结果，从而显著提升长文档的搜索召回率和精确度。

## 术语表

- **Knowledge_Agent**：知识管理智能体系统，负责知识的收集、组织、搜索和管理
- **KnowledgeItem**：知识条目，系统中的基本信息存储单元，对应一个完整的文档
- **KnowledgeChunk**：知识分块，KnowledgeItem 的子单元，表示文档中一个语义完整的片段
- **ContentChunker**：内容分块引擎，负责将文档内容拆分为语义完整的分块
- **SearchEngine**：搜索引擎，负责执行关键词搜索和语义搜索的核心组件
- **SearchIndexManager**：搜索索引管理器，基于 Whoosh 的全文索引管理组件
- **SemanticSearcher**：语义搜索器，基于 TF-IDF 和余弦相似度的语义搜索组件
- **BaseDataSourceProcessor**：数据源处理器基类，负责从各类数据源提取内容并生成 KnowledgeItem
- **SQLiteStorageManager**：SQLite 存储管理器，负责知识条目和相关数据的持久化存储
- **Chunk_Index**：分块索引，Whoosh 全文索引中用于分块级搜索的索引结构
- **Context_Window**：上下文窗口，搜索结果中围绕命中分块加载的相邻分块，用于提供更完整的上下文

## 需求

### 需求 1：KnowledgeChunk 数据模型

**用户故事：** 作为系统开发者，我希望有一个专门的分块数据模型，以便将长文档拆分为可独立索引和搜索的语义片段。

#### 验收标准

1. THE KnowledgeChunk SHALL 包含以下字段：id（唯一标识）、item_id（关联的 KnowledgeItem ID）、chunk_index（分块在文档中的序号）、content（分块文本内容）、heading（分块所属的标题或章节名）、start_position（在原文中的起始位置）、end_position（在原文中的结束位置）、metadata（扩展元数据字典）
2. THE KnowledgeChunk SHALL 与 KnowledgeItem 建立多对一关联关系，通过 item_id 外键引用 knowledge_items 表的 id 字段
3. THE SQLiteStorageManager SHALL 在数据库中创建 knowledge_chunks 表，包含上述所有字段和外键约束
4. WHEN 一个 KnowledgeItem 被删除时，THE SQLiteStorageManager SHALL 级联删除该条目关联的所有 KnowledgeChunk 记录
5. THE KnowledgeChunk SHALL 提供 to_dict 和 from_dict 方法，支持序列化和反序列化
6. FOR ALL 有效的 KnowledgeChunk 对象，序列化后再反序列化 SHALL 产生等价的对象（往返属性）

### 需求 2：内容分块引擎

**用户故事：** 作为系统开发者，我希望有一个智能的内容分块引擎，以便将各类长文档按语义结构拆分为大小适中的分块。

#### 验收标准

1. THE ContentChunker SHALL 支持三级分块策略，按优先级依次为：标题和章节结构分块、段落分块（双换行符分隔）、滑动窗口二次切分
2. THE ContentChunker SHALL 提供可配置的分块阈值参数：min_chunk_size（最小分块大小，默认 100 字符）、max_chunk_size（最大分块大小，默认 1500 字符）、overlap_ratio（重叠比例，默认 0.2）
3. WHEN 文档总长度小于 min_chunk_size 乘以 2 时，THE ContentChunker SHALL 将整个文档作为单个分块返回
4. WHEN 一个分块的长度超过 max_chunk_size 时，THE ContentChunker SHALL 使用滑动窗口策略将该分块二次切分为多个子分块，相邻子分块之间保持 overlap_ratio 比例的重叠
5. THE ContentChunker SHALL 为每个分块记录其在原文中的起始位置和结束位置
6. THE ContentChunker SHALL 为每个分块提取其所属的标题或章节名称（heading 字段）
7. WHEN 分块过程中发生异常时，THE ContentChunker SHALL 将整个文档内容作为单个分块返回，而非抛出异常
8. FOR ALL 非空文档内容，THE ContentChunker SHALL 返回至少一个分块
9. FOR ALL 分块结果，每个分块的 content 字段 SHALL 为非空字符串
10. FOR ALL 分块结果，分块的 chunk_index SHALL 从 0 开始连续递增

### 需求 3：处理器集成分块

**用户故事：** 作为系统开发者，我希望在知识收集流程中自动对文档进行分块，以便所有新导入的文档都能被分块索引。

#### 验收标准

1. WHEN BaseDataSourceProcessor 成功提取文档内容后，THE BaseDataSourceProcessor SHALL 调用 ContentChunker 对内容进行分块
2. WHEN 处理器生成 KnowledgeItem 后，THE Knowledge_Agent SHALL 将分块结果作为 KnowledgeChunk 列表与 KnowledgeItem 一起保存到存储层
3. THE SQLiteStorageManager SHALL 提供批量保存 KnowledgeChunk 的方法，在保存 KnowledgeItem 时同时保存其关联的所有分块
4. WHEN 分块过程失败时，THE BaseDataSourceProcessor SHALL 继续正常处理，将整个文档内容作为单个分块保存

### 需求 4：分块级搜索索引

**用户故事：** 作为系统开发者，我希望搜索索引能够在分块级别建立，以便搜索能够精确命中文档中的特定段落。

#### 验收标准

1. THE SearchIndexManager SHALL 为 KnowledgeChunk 建立独立的 Whoosh 全文索引，索引字段包含 chunk_id、item_id、chunk_index、heading 和 content
2. THE SemanticSearcher SHALL 在分块级别构建 TF-IDF 向量模型，每个分块作为独立的文档参与向量化
3. WHEN 一个新的 KnowledgeItem 及其分块被保存时，THE SearchEngine SHALL 将所有分块添加到 Chunk_Index 中
4. WHEN 一个 KnowledgeItem 被删除时，THE SearchEngine SHALL 从 Chunk_Index 中移除该条目的所有分块
5. WHEN 搜索索引需要重建时，THE SearchEngine SHALL 从存储层加载所有 KnowledgeChunk 并重建 Chunk_Index

### 需求 5：两阶段搜索策略

**用户故事：** 作为用户，我希望搜索能够精确找到长文档中包含答案的段落，同时返回足够的上下文信息。

#### 验收标准

1. WHEN 用户执行搜索查询时，THE SearchEngine SHALL 在第一阶段对 Chunk_Index 执行关键词搜索和 TF-IDF 语义搜索，获取匹配的分块列表
2. WHEN 第一阶段搜索完成后，THE SearchEngine SHALL 在第二阶段按 item_id 对匹配的分块进行分组，取每组中最高分分块的得分作为该文档的相关性得分
3. WHEN 搜索结果包含命中的分块时，THE SearchEngine SHALL 支持加载该分块的相邻分块（前后各一个）作为 Context_Window，提供更完整的上下文
4. THE SearchEngine SHALL 在搜索结果中包含以下信息：KnowledgeItem 的基本信息、命中的 KnowledgeChunk 内容、分块在原文中的位置信息、分块的 heading 信息
5. IF Chunk_Index 为空或不可用，THEN THE SearchEngine SHALL 退化为原有的 KnowledgeItem 级别搜索，保持向后兼容

### 需求 6：搜索结果格式调整

**用户故事：** 作为 MCP 客户端开发者，我希望搜索结果包含分块级别的详细信息，以便向用户展示精确的匹配内容和上下文。

#### 验收标准

1. THE SearchResult SHALL 扩展为包含以下新字段：matched_chunks（命中的分块列表，每个分块包含 chunk_id、content、heading、chunk_index、start_position、end_position）、context_chunks（上下文分块列表）
2. WHEN 搜索结果通过 MCP 工具返回时，THE search_knowledge 工具 SHALL 在每个结果中包含命中的分块内容和位置信息
3. THE SearchResult SHALL 保持与现有 item、relevance_score、matched_fields、highlights 字段的向后兼容
4. WHEN 搜索结果中的 matched_chunks 为空时，THE SearchResult SHALL 退化为仅包含 KnowledgeItem 级别的信息（与当前行为一致）

### 需求 7：短文档兼容性

**用户故事：** 作为用户，我希望短文档的搜索行为保持不变，分块机制不会对短文档的搜索性能和结果产生负面影响。

#### 验收标准

1. WHEN 文档总长度小于 min_chunk_size 乘以 2 时，THE ContentChunker SHALL 将整个文档作为单个分块处理
2. WHEN 短文档作为单个分块被索引时，THE SearchEngine SHALL 对该文档的搜索行为与分块功能引入前保持一致
3. THE Knowledge_Agent SHALL 对所有文档类型（PDF、文本、代码、网页）统一应用分块逻辑，短文档自动退化为单分块模式

### 需求 8：存储层分块管理

**用户故事：** 作为系统开发者，我希望存储层能够高效地管理分块数据，支持按条目查询和批量操作。

#### 验收标准

1. THE SQLiteStorageManager SHALL 提供 save_chunks 方法，支持批量保存一个 KnowledgeItem 的所有分块
2. THE SQLiteStorageManager SHALL 提供 get_chunks_for_item 方法，根据 item_id 查询该条目的所有分块，按 chunk_index 排序返回
3. THE SQLiteStorageManager SHALL 提供 get_chunk_by_id 方法，根据 chunk_id 查询单个分块
4. THE SQLiteStorageManager SHALL 提供 get_adjacent_chunks 方法，根据 item_id 和 chunk_index 查询相邻分块（用于 Context_Window）
5. WHEN 保存分块时，THE SQLiteStorageManager SHALL 先删除该 item_id 的所有旧分块，再插入新分块，确保数据一致性
