# 需求文档

## 简介

本文档定义了个人知识管理 MCP 服务器的综合改进需求。基于对现有代码库的全面审查，涵盖三大类改进：现有缺陷修复、未实现功能补全、以及推荐的增强功能。项目基于 Python + FastMCP + SQLite + Whoosh 技术栈构建。

## 术语表

- **Knowledge_Agent**：个人知识管理 MCP 服务器系统
- **Storage_Manager**：SQLite 存储管理器，负责知识条目的持久化存储和检索
- **Knowledge_Core**：知识代理核心模块，协调各组件完成业务逻辑
- **MCP_Server**：基于 FastMCP 框架的 MCP 协议服务器
- **MCP_Tools**：通过 MCP 协议暴露的工具函数
- **MCP_Resources**：通过 MCP 协议暴露的只读资源端点
- **MCP_Prompts**：通过 MCP 协议暴露的提示模板
- **Web_Processor**：网页数据源处理器，负责从网页中提取内容
- **Search_Engine**：基于 Whoosh 和 TF-IDF 的搜索引擎
- **Data_Import_Export**：数据导入导出模块
- **Source_Type_Detector**：数据源类型自动检测器
- **Security_Validator**：安全路径验证器，负责文件访问路径和扩展名的安全检查
- **N+1 查询**：一种数据库查询反模式，先查询 ID 列表再逐个查询详情，导致大量冗余查询
- **EARS 模式**：Easy Approach to Requirements Syntax，一种结构化需求编写方法

## 需求

### 需求 1：修复 N+1 查询性能问题

**用户故事：** 作为系统管理员，我希望知识条目的批量查询高效执行，以便在数据量增长时系统仍能保持良好的响应速度。

#### 验收标准

1. WHEN `get_all_knowledge_items()` 被调用时，THE Storage_Manager SHALL 使用 JOIN 查询在单次数据库操作中获取所有知识条目及其关联的分类和标签数据
2. THE Storage_Manager SHALL 避免对每个知识条目单独执行分类查询和标签查询（即消除 N+1 查询模式）
3. WHEN 知识条目数量为 N 时，THE Storage_Manager SHALL 使用不超过 3 次数据库查询完成所有条目及其关联数据的加载（主表查询 + 分类批量查询 + 标签批量查询）
4. THE Storage_Manager SHALL 在批量查询后返回与逐条查询相同的完整 KnowledgeItem 对象列表（包含 categories 和 tags 属性）

### 需求 2：修复内存过滤和统计问题

**用户故事：** 作为开发者，我希望列表查询和统计操作在数据库层面完成过滤和计数，以便减少不必要的内存消耗和数据传输。

#### 验收标准

1. WHEN `list_knowledge_items()` 接收到 category 过滤参数时，THE Storage_Manager SHALL 使用 SQL WHERE 子句在数据库层面完成分类过滤
2. WHEN `list_knowledge_items()` 接收到 tag 过滤参数时，THE Storage_Manager SHALL 使用 SQL WHERE 子句在数据库层面完成标签过滤
3. WHEN `list_knowledge_items()` 接收到 limit 和 offset 参数时，THE Storage_Manager SHALL 使用 SQL LIMIT 和 OFFSET 子句在数据库层面完成分页
4. WHEN `get_statistics()` 被调用时，THE Knowledge_Core SHALL 使用 SQL COUNT 聚合查询获取各类数据的数量，而非加载所有数据到内存后计数
5. THE Storage_Manager SHALL 提供 `query_knowledge_items(category, tag, limit, offset)` 方法支持数据库层面的过滤和分页
6. THE Storage_Manager SHALL 提供 `get_database_stats()` 方法返回各表的记录数量统计

### 需求 3：实现数据源类型自动检测

**用户故事：** 作为用户，我希望在收集知识时选择 "auto" 类型能自动识别数据源的实际类型，以便无需手动指定文件类型。

#### 验收标准

1. WHEN `source_type` 为 "auto" 且 `source_path` 以 `.pdf` 扩展名结尾时，THE Source_Type_Detector SHALL 将其识别为 PDF 类型
2. WHEN `source_type` 为 "auto" 且 `source_path` 以 `.py`、`.js`、`.java`、`.cpp`、`.c`、`.go`、`.rs` 等代码文件扩展名结尾时，THE Source_Type_Detector SHALL 将其识别为 CODE 类型
3. WHEN `source_type` 为 "auto" 且 `source_path` 以 `http://` 或 `https://` 开头时，THE Source_Type_Detector SHALL 将其识别为 WEB 类型
4. WHEN `source_type` 为 "auto" 且 `source_path` 以 `.jpg`、`.jpeg`、`.png`、`.gif`、`.bmp`、`.webp` 等图片扩展名结尾时，THE Source_Type_Detector SHALL 将其识别为 IMAGE 类型
5. WHEN `source_type` 为 "auto" 且 `source_path` 以 `.txt`、`.md`、`.doc`、`.docx` 等文档扩展名结尾时，THE Source_Type_Detector SHALL 将其识别为 DOCUMENT 类型
6. WHEN `source_type` 为 "auto" 且无法根据扩展名或 URL 模式确定类型时，THE Source_Type_Detector SHALL 默认使用 DOCUMENT 类型

### 需求 4：修复封装违规问题

**用户故事：** 作为开发者，我希望 MCP 资源模块通过公开接口访问核心功能，以便维护良好的模块封装性和代码可维护性。

#### 验收标准

1. THE MCP_Resources SHALL 通过 Knowledge_Core 的公开方法访问分类数据，而非直接访问 `_storage_manager` 私有属性
2. THE MCP_Resources SHALL 通过 Knowledge_Core 的公开方法访问标签数据，而非直接访问 `_storage_manager` 私有属性
3. THE MCP_Resources SHALL 通过 Knowledge_Core 的公开方法访问知识图谱数据，而非直接访问 `_storage_manager` 私有属性
4. THE Knowledge_Core SHALL 提供 `get_all_categories()` 公开方法返回所有分类
5. THE Knowledge_Core SHALL 提供 `get_all_tags()` 公开方法返回所有标签
6. THE Knowledge_Core SHALL 提供 `get_knowledge_graph()` 公开方法返回知识图谱的节点和边数据

### 需求 5：修复 SSE 传输参数传递

**用户故事：** 作为运维人员，我希望 SSE 传输方式的 host 和 port 参数能正确传递给 FastMCP，以便可以自定义服务器的监听地址和端口。

#### 验收标准

1. WHEN `start_sse()` 被调用并传入 host 和 port 参数时，THE MCP_Server SHALL 将这些参数传递给 `FastMCP.run()` 方法
2. WHEN `start_sse()` 被调用且未传入 host 和 port 参数时，THE MCP_Server SHALL 使用默认值 `localhost:8000`
3. THE MCP_Server SHALL 从配置文件中读取 SSE 传输方式的 host 和 port 设置作为默认值

### 需求 6：处理空处理器暴露问题

**用户故事：** 作为用户，我希望在使用未实现的数据源类型时获得清晰的错误提示，而非遇到不可预期的运行时错误。

#### 验收标准

1. WHEN 用户通过 `collect_knowledge` 工具提交 "web" 类型的数据源时，THE MCP_Tools SHALL 返回明确的"功能未实现"提示信息，包含该类型当前不可用的说明
2. WHEN 用户通过 `collect_knowledge` 工具提交 "image" 类型的数据源时，THE MCP_Tools SHALL 返回明确的"功能未实现"提示信息
3. THE Knowledge_Core SHALL 在 `_get_processor_for_source()` 方法中对未注册的处理器类型返回描述性的 NotImplementedError，而非返回 None 后在后续流程中报错
4. THE MCP_Tools SHALL 在 `_validate_source_type()` 中区分"已支持"和"已定义但未实现"的数据源类型


### 需求 7：实现 Web 网页处理器

**用户故事：** 作为用户，我希望能够从网页 URL 收集知识，以便将在线文章和文档纳入个人知识库。

#### 验收标准

1. WHEN 提供有效的 HTTP/HTTPS URL 时，THE Web_Processor SHALL 获取网页内容并提取正文文本
2. WHEN 网页包含 HTML 标签时，THE Web_Processor SHALL 清除 HTML 标签并保留纯文本内容
3. WHEN 网页请求超时时，THE Web_Processor SHALL 在配置的超时时间（默认 30 秒）后返回超时错误
4. WHEN 网页返回非 200 状态码时，THE Web_Processor SHALL 返回包含 HTTP 状态码的描述性错误
5. THE Web_Processor SHALL 从网页中提取标题（`<title>` 标签或 `<h1>` 标签）作为知识条目的标题
6. THE Web_Processor SHALL 遵循配置文件中的 `web_scraping` 设置（timeout、max_retries、user_agent）

### 需求 8：实现知识条目更新功能

**用户故事：** 作为用户，我希望能够编辑和更新已有的知识条目，以便在信息变化时保持知识库的准确性。

#### 验收标准

1. THE Storage_Manager SHALL 提供 `update_knowledge_item(item_id, updates)` 方法支持部分字段更新
2. WHEN 更新知识条目的标题或内容时，THE Storage_Manager SHALL 同时更新 `updated_at` 时间戳
3. WHEN 更新不存在的知识条目时，THE Storage_Manager SHALL 返回 False 表示更新失败
4. THE MCP_Tools SHALL 注册 `update_knowledge_item` 工具，接受 item_id 和可选的 title、content、categories、tags 参数
5. WHEN 知识条目内容被更新时，THE Search_Engine SHALL 重新索引该条目以保持搜索结果的准确性

### 需求 9：实现导入合并策略

**用户故事：** 作为用户，我希望在导入知识数据时能选择不同的合并策略，以便灵活处理与现有数据的冲突。

#### 验收标准

1. WHEN `merge_strategy` 为 "skip_existing" 时，THE Data_Import_Export SHALL 跳过 ID 已存在于知识库中的条目
2. WHEN `merge_strategy` 为 "overwrite" 时，THE Data_Import_Export SHALL 用导入数据覆盖 ID 已存在的条目
3. WHEN `merge_strategy` 为 "merge" 时，THE Data_Import_Export SHALL 合并已存在条目的分类和标签（取并集），并保留较新的内容
4. THE Data_Import_Export SHALL 返回导入结果摘要，包含新增条目数、跳过条目数、覆盖条目数和合并条目数
5. IF 导入过程中某个条目处理失败，THEN THE Data_Import_Export SHALL 记录错误并继续处理剩余条目，而非中断整个导入流程

### 需求 10：实现安全路径限制

**用户故事：** 作为系统管理员，我希望配置文件中的安全路径限制能够生效，以便防止未授权的文件访问。

#### 验收标准

1. WHEN 配置文件中 `allowed_paths` 列表非空时，THE Security_Validator SHALL 仅允许访问列表中指定路径及其子路径下的文件
2. WHEN 文件扩展名在 `blocked_extensions` 列表中时，THE Security_Validator SHALL 拒绝处理该文件并返回安全限制错误
3. WHEN `allowed_paths` 列表为空时，THE Security_Validator SHALL 允许访问任意路径（保持向后兼容）
4. THE Security_Validator SHALL 在 `collect_knowledge` 工具处理文件之前执行路径和扩展名验证
5. IF 文件路径包含路径遍历序列（如 `../`）时，THEN THE Security_Validator SHALL 解析为绝对路径后再进行验证

### 需求 11：实现 MCP Prompts 支持

**用户故事：** 作为 AI 助手用户，我希望 MCP 服务器提供预定义的提示模板，以便快速执行常见的知识管理操作。

#### 验收标准

1. THE MCP_Server SHALL 注册至少 3 个 MCP Prompt 模板：知识摘要生成、知识搜索辅助、知识整理建议
2. WHEN 用户调用"知识摘要生成"提示时，THE MCP_Prompts SHALL 接受 item_id 参数并返回包含知识条目内容的摘要生成提示
3. WHEN 用户调用"知识搜索辅助"提示时，THE MCP_Prompts SHALL 接受 topic 参数并返回引导搜索的提示模板
4. WHEN 用户调用"知识整理建议"提示时，THE MCP_Prompts SHALL 返回基于当前知识库状态的整理建议提示
5. THE MCP_Prompts SHALL 通过独立的 `mcp_prompts.py` 模块注册，遵循现有的 `mcp_tools.py` 和 `mcp_resources.py` 的模块组织模式

### 需求 12：实现删除知识条目的 MCP 工具

**用户故事：** 作为用户，我希望能够通过 MCP 工具删除不再需要的知识条目，以便保持知识库的整洁。

#### 验收标准

1. THE MCP_Tools SHALL 注册 `delete_knowledge_item` 工具，接受 `item_id` 参数
2. WHEN 提供有效的 item_id 时，THE MCP_Tools SHALL 调用 Knowledge_Core 删除该知识条目并返回成功响应
3. WHEN 提供不存在的 item_id 时，THE MCP_Tools SHALL 返回"条目未找到"的错误响应
4. WHEN 知识条目被删除时，THE Storage_Manager SHALL 同时删除该条目关联的分类映射、标签映射和关系数据
5. WHEN 知识条目被删除时，THE Search_Engine SHALL 从搜索索引中移除该条目

### 需求 13：实现批量知识收集

**用户故事：** 作为用户，我希望能够一次性处理整个目录中的文件，以便快速批量导入知识。

#### 验收标准

1. THE MCP_Tools SHALL 注册 `batch_collect_knowledge` 工具，接受 `directory_path` 和可选的 `file_pattern`（glob 模式）参数
2. WHEN 提供有效的目录路径时，THE Knowledge_Core SHALL 遍历目录中匹配模式的文件并逐个处理
3. WHEN 批量处理中某个文件处理失败时，THE Knowledge_Core SHALL 记录错误并继续处理剩余文件
4. THE MCP_Tools SHALL 返回批量处理结果摘要，包含成功数量、失败数量和失败文件列表
5. THE Knowledge_Core SHALL 在批量处理前对目录路径执行安全路径验证（复用需求 10 的 Security_Validator）
6. WHEN 目录中包含子目录时，THE Knowledge_Core SHALL 支持通过 `recursive` 参数控制是否递归处理子目录

### 需求 14：搜索建议功能修复

**用户故事：** 作为用户，我希望搜索建议功能能够正常工作，以便在输入搜索词时获得相关的补全建议。

#### 验收标准

1. WHEN 用户输入部分搜索词时，THE Search_Engine SHALL 返回基于已有知识条目标题和内容的搜索建议列表
2. THE Search_Engine SHALL 返回不超过 10 条搜索建议
3. THE MCP_Tools SHALL 注册 `suggest_search` 工具，接受 `partial_query` 参数并返回搜索建议列表
4. WHEN 知识库为空时，THE Search_Engine SHALL 返回空的搜索建议列表
