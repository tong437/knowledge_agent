# 实现计划：MCP 综合改进

## 概述

基于需求文档和设计文档，将 14 项改进需求分解为增量式编码任务。任务按依赖关系排序：先完成存储层和核心组件的修改，再扩展 MCP 协议层。所有代码使用 Python，测试使用 pytest + Hypothesis。

## 任务

- [x] 1. 优化 SQLiteStorageManager 存储层（N+1 查询修复、数据库过滤分页、统计查询）
  - [x] 1.1 修复 `get_all_knowledge_items()` 的 N+1 查询问题
    - 修改 `knowledge_agent/storage/sqlite_storage.py`，将逐条查询分类和标签改为 3 次批量查询（主表 + 分类映射 + 标签映射）
    - 在 Python 中按 item_id 分组组装 KnowledgeItem 对象
    - _需求: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 1.2 编写属性测试：批量查询与逐条查询等价性
    - **Property 1: 批量查询与逐条查询等价性**
    - 使用 Hypothesis 生成随机 KnowledgeItem 集合，验证 `get_all_knowledge_items()` 返回结果与逐条 `get_knowledge_item()` 一致
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 1.4**

  - [x] 1.3 实现 `query_knowledge_items()` 数据库层面过滤和分页方法
    - 在 `sqlite_storage.py` 中新增 `query_knowledge_items(category, tag, limit, offset)` 方法
    - 使用 SQL WHERE 子句实现分类和标签过滤，使用 LIMIT/OFFSET 实现分页
    - _需求: 2.1, 2.2, 2.3, 2.5_

  - [ ]* 1.4 编写属性测试：分类和标签过滤正确性
    - **Property 2: 分类和标签过滤正确性**
    - 验证 `query_knowledge_items()` 返回的每个条目都包含指定的分类或标签，且不遗漏符合条件的条目
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 2.1, 2.2**

  - [ ]* 1.5 编写属性测试：分页正确性
    - **Property 3: 分页正确性**
    - 验证 `query_knowledge_items()` 返回结果数量不超过 limit，且与全量查询切片一致
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 2.3**

  - [x] 1.6 实现 `get_database_stats()` 使用 SQL COUNT 聚合查询
    - 在 `sqlite_storage.py` 中新增或修改 `get_database_stats()` 方法，使用 COUNT 聚合查询各表记录数
    - _需求: 2.4, 2.6_

  - [ ]* 1.7 编写属性测试：统计数量一致性
    - **Property 4: 统计数量一致性**
    - 验证 `get_statistics()` 返回的数量与实际存储数据量一致
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 2.4**


- [x] 2. 实现知识条目更新和删除功能（存储层 + 核心层）
  - [x] 2.1 实现 `update_knowledge_item()` 存储层方法
    - 在 `sqlite_storage.py` 中新增 `update_knowledge_item(item_id, updates)` 方法
    - 支持 title、content、categories、tags 的部分字段更新
    - 自动更新 `updated_at` 时间戳，条目不存在时返回 False
    - _需求: 8.1, 8.2, 8.3_

  - [ ]* 2.2 编写属性测试：知识条目部分更新正确性
    - **Property 11: 知识条目部分更新正确性**
    - 验证更新后被更新字段反映新值，未更新字段保持不变，updated_at 时间戳递增
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 8.1, 8.2**

  - [x] 2.3 实现删除知识条目的存储层方法（级联删除）
    - 在 `sqlite_storage.py` 中确保 `delete_knowledge_item(item_id)` 同时删除关联的分类映射、标签映射和关系数据
    - 条目不存在时返回 False
    - _需求: 12.4_

  - [ ]* 2.4 编写属性测试：不存在条目的操作安全性
    - **Property 12: 不存在条目的操作安全性**
    - 验证对不存在的 item_id 调用 update 返回 False，调用 delete 返回 False
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 8.3, 12.3**

  - [ ]* 2.5 编写属性测试：删除操作级联清除
    - **Property 21: 删除操作级联清除**
    - 验证删除后关联的分类映射、标签映射和关系数据也被清除
    - 测试文件：`knowledge_agent/tests/test_storage_properties.py`
    - **验证: 需求 12.2, 12.4**

- [x] 3. 检查点 - 存储层验证
  - 确保所有存储层测试通过，如有问题请向用户确认。


- [x] 4. 实现新增核心组件（SourceTypeDetector、SecurityValidator）
  - [x] 4.1 创建 `SourceTypeDetector` 数据源类型自动检测器
    - 新建 `knowledge_agent/core/source_type_detector.py`
    - 实现扩展名到 SourceType 的映射表和 `detect()` 静态方法
    - 检测优先级：URL 模式 > 文件扩展名 > 默认 DOCUMENT
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 4.2 编写属性测试：数据源类型检测确定性
    - **Property 5: 数据源类型检测确定性**
    - 使用 Hypothesis 生成随机文件路径，验证已知扩展名映射正确、URL 映射到 WEB、未知扩展名默认 DOCUMENT、同一路径多次调用结果一致
    - 测试文件：`knowledge_agent/tests/test_source_type_detector.py`
    - **验证: 需求 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

  - [x] 4.3 创建 `SecurityValidator` 安全路径验证器
    - 新建 `knowledge_agent/core/security_validator.py`
    - 实现 `validate_path()` 方法：解析绝对路径、检查扩展名黑名单、检查 allowed_paths 范围
    - allowed_paths 为空时允许任意路径
    - _需求: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 4.4 编写属性测试：安全路径验证——允许路径限制
    - **Property 17: 安全路径验证——允许路径限制**
    - 验证非空 allowed_paths 下，不在允许范围内的路径返回 False
    - 测试文件：`knowledge_agent/tests/test_security_validator.py`
    - **验证: 需求 10.1**

  - [ ]* 4.5 编写属性测试：安全路径验证——扩展名黑名单
    - **Property 18: 安全路径验证——扩展名黑名单**
    - 验证扩展名在 blocked_extensions 中的路径返回 False
    - 测试文件：`knowledge_agent/tests/test_security_validator.py`
    - **验证: 需求 10.2**

  - [ ]* 4.6 编写属性测试：路径遍历规范化
    - **Property 19: 路径遍历规范化**
    - 验证包含 `../` 的路径解析为绝对路径后验证结果与等价绝对路径一致
    - 测试文件：`knowledge_agent/tests/test_security_validator.py`
    - **验证: 需求 10.5**


- [x] 5. 实现 WebProcessor 网页处理器
  - [x] 5.1 实现 `WebProcessor` 类
    - 修改 `knowledge_agent/processors/web_processor.py`，实现完整的网页处理器
    - 使用 `urllib.request` 获取网页，`html.parser` 解析 HTML（或项目已有的 requests/beautifulsoup4）
    - 实现 `_extract_content()`（清除 HTML 标签）、`_extract_title()`（提取 title/h1）、`validate()`（验证 URL 格式）
    - 读取 config.yaml 中的 `web_scraping` 配置（timeout、max_retries、user_agent）
    - _需求: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 5.2 编写属性测试：HTML 标签清除
    - **Property 9: HTML 标签清除**
    - 使用 Hypothesis 生成随机 HTML 字符串，验证处理后不包含任何 `<...>` 标签
    - 测试文件：`knowledge_agent/tests/test_web_processor.py`
    - **验证: 需求 7.2**

  - [ ]* 5.3 编写属性测试：HTML 标题提取
    - **Property 10: HTML 标题提取**
    - 验证包含 `<title>` 或 `<h1>` 标签的 HTML 能正确提取标题文本
    - 测试文件：`knowledge_agent/tests/test_web_processor.py`
    - **验证: 需求 7.5**

- [ ] 6. 检查点 - 核心组件验证
  - 确保 SourceTypeDetector、SecurityValidator、WebProcessor 的所有测试通过，如有问题请向用户确认。


- [x] 7. 扩展 KnowledgeAgentCore 核心层（封装修复、公开接口、业务逻辑）
  - [x] 7.1 添加公开接口方法（修复封装违规）
    - 在 `knowledge_agent/core/knowledge_agent_core.py` 中新增 `get_all_categories()`、`get_all_tags()`、`get_knowledge_graph()` 公开方法
    - 这些方法委托给 `_storage_manager` 的对应方法
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 7.2 编写属性测试：公开接口数据完整性
    - **Property 6: 公开接口数据完整性**
    - 验证通过公开接口返回的分类和标签数据包含所有已存入的数据
    - 测试文件：`knowledge_agent/tests/test_core_properties.py`
    - **验证: 需求 4.4, 4.5**

  - [ ]* 7.3 编写属性测试：知识图谱节点与边一致性
    - **Property 7: 知识图谱节点与边一致性**
    - 验证节点数等于知识条目数，每条边的 source 和 target 对应存在的节点
    - 测试文件：`knowledge_agent/tests/test_core_properties.py`
    - **验证: 需求 4.6**

  - [x] 7.4 修改 `list_knowledge_items()` 委托给存储层的 `query_knowledge_items()`
    - 修改 `knowledge_agent_core.py` 中的 `list_knowledge_items()` 方法，使用存储层的数据库过滤分页
    - _需求: 2.1, 2.2, 2.3_

  - [x] 7.5 修改 `get_statistics()` 使用 SQL COUNT 聚合查询
    - 修改 `knowledge_agent_core.py` 中的 `get_statistics()` 方法，调用 `get_database_stats()` 替代加载全部数据
    - _需求: 2.4_

  - [x] 7.6 修改 `_get_processor_for_source()` 对未注册处理器抛出 NotImplementedError
    - 修改 `knowledge_agent_core.py`，未注册类型抛出描述性 `NotImplementedError` 而非返回 None
    - _需求: 6.3_

  - [ ]* 7.7 编写属性测试：未注册处理器抛出异常
    - **Property 8: 未注册处理器抛出异常**
    - 验证未注册的 SourceType 调用 `_get_processor_for_source()` 抛出 NotImplementedError
    - 测试文件：`knowledge_agent/tests/test_core_properties.py`
    - **验证: 需求 6.3**

  - [x] 7.8 实现核心层的 `update_knowledge_item()` 和 `delete_knowledge_item()` 方法
    - 在 `knowledge_agent_core.py` 中新增更新和删除方法
    - 更新时调用存储层更新 + 搜索引擎重新索引
    - 删除时调用存储层删除 + 搜索引擎移除索引
    - _需求: 8.1, 8.4, 8.5, 12.2, 12.4, 12.5_

  - [x] 7.9 实现核心层的 `batch_collect_knowledge()` 批量收集方法
    - 在 `knowledge_agent_core.py` 中新增批量收集方法
    - 遍历目录匹配文件，逐个处理，单文件失败不中断
    - 处理前调用 SecurityValidator 验证目录路径
    - 支持 `recursive` 参数控制是否递归子目录
    - _需求: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ]* 7.10 编写属性测试：批量收集文件匹配与计数不变量
    - **Property 22: 批量收集文件匹配与计数不变量**
    - 验证 `success_count + failure_count` 等于匹配文件总数，recursive 参数控制子目录包含
    - 测试文件：`knowledge_agent/tests/test_core_properties.py`
    - **验证: 需求 13.2, 13.4, 13.6**


- [ ] 8. 检查点 - 核心层验证
  - 确保 KnowledgeAgentCore 的所有公开接口、更新/删除、批量收集功能测试通过，如有问题请向用户确认。

- [x] 9. 实现导入合并策略
  - [x] 9.1 修改 `DataImportExport` 支持三种合并策略
    - 修改 `knowledge_agent/core/data_import_export.py` 中的 `import_from_json()` 方法
    - 实现 `skip_existing`、`overwrite`、`merge` 三种策略
    - merge 策略：分类和标签取并集，保留较新内容
    - 返回 ImportResult 摘要（new_count、skipped_count、overwritten_count、merged_count、error_count）
    - 单条目失败时记录错误并继续处理
    - _需求: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 9.2 编写属性测试：skip_existing 策略保持已有数据不变
    - **Property 13: skip_existing 策略保持已有数据不变**
    - 验证使用 skip_existing 导入后，已存在条目的内容、分类和标签与导入前一致
    - 测试文件：`knowledge_agent/tests/test_import_properties.py`
    - **验证: 需求 9.1**

  - [ ]* 9.3 编写属性测试：overwrite 策略覆盖已有数据
    - **Property 14: overwrite 策略覆盖已有数据**
    - 验证使用 overwrite 导入后，已存在条目的内容与导入数据一致
    - 测试文件：`knowledge_agent/tests/test_import_properties.py`
    - **验证: 需求 9.2**

  - [ ]* 9.4 编写属性测试：merge 策略分类标签取并集
    - **Property 15: merge 策略分类标签取并集**
    - 验证使用 merge 导入后，分类和标签为原数据与导入数据的并集
    - 测试文件：`knowledge_agent/tests/test_import_properties.py`
    - **验证: 需求 9.3**

  - [ ]* 9.5 编写属性测试：导入结果摘要计数不变量
    - **Property 16: 导入结果摘要计数不变量**
    - 验证 `new_count + skipped_count + overwritten_count + merged_count + error_count` 等于导入总条目数
    - 测试文件：`knowledge_agent/tests/test_import_properties.py`
    - **验证: 需求 9.4**


- [x] 10. 修复 MCP Resources 封装违规和 SSE 参数传递
  - [x] 10.1 修复 `mcp_resources.py` 中的封装违规
    - 修改 `knowledge_agent/server/mcp_resources.py`，将所有 `knowledge_core._storage_manager.xxx()` 调用替换为 `knowledge_core.get_all_categories()`、`knowledge_core.get_all_tags()`、`knowledge_core.get_knowledge_graph()` 等公开接口
    - _需求: 4.1, 4.2, 4.3_

  - [x] 10.2 修复 SSE 传输参数传递
    - 修改 `knowledge_agent/server/knowledge_mcp_server.py` 中的 `start_sse()` 方法
    - 将 host 和 port 参数正确传递给 `FastMCP.run()`
    - 从配置文件读取默认值，未配置时使用 `localhost:8000`
    - _需求: 5.1, 5.2, 5.3_

- [x] 11. 扩展 MCP Tools（更新、删除、批量收集、搜索建议、空处理器提示）
  - [x] 11.1 修改 `mcp_tools.py` 处理空处理器暴露问题
    - 在 `knowledge_agent/server/mcp_tools.py` 中添加 `_validate_source_type()` 逻辑
    - 区分"已支持"和"已定义但未实现"的数据源类型
    - 对 web、image 等未实现类型返回明确的"功能未实现"提示
    - _需求: 6.1, 6.2, 6.4_

  - [x] 11.2 注册 `update_knowledge_item` MCP 工具
    - 在 `mcp_tools.py` 中注册更新工具，接受 item_id 和可选的 title、content、categories、tags 参数
    - 调用 `knowledge_core.update_knowledge_item()` 并返回结果
    - _需求: 8.4_

  - [x] 11.3 注册 `delete_knowledge_item` MCP 工具
    - 在 `mcp_tools.py` 中注册删除工具，接受 item_id 参数
    - 调用 `knowledge_core.delete_knowledge_item()` 并返回结果
    - 不存在的 item_id 返回"条目未找到"错误响应
    - _需求: 12.1, 12.2, 12.3_

  - [x] 11.4 注册 `batch_collect_knowledge` MCP 工具
    - 在 `mcp_tools.py` 中注册批量收集工具，接受 directory_path、file_pattern、recursive 参数
    - 调用 `knowledge_core.batch_collect_knowledge()` 并返回结果摘要
    - _需求: 13.1, 13.4_

  - [x] 11.5 注册 `suggest_search` MCP 工具并修复搜索建议功能
    - 在 `mcp_tools.py` 中注册搜索建议工具，接受 partial_query 参数
    - 修改 `knowledge_agent/search/search_engine_impl.py` 中的 `suggest()` 方法，基于 Whoosh 索引前缀匹配返回建议
    - 返回不超过 10 条建议，知识库为空时返回空列表
    - _需求: 14.1, 14.2, 14.3, 14.4_

  - [ ]* 11.6 编写属性测试：搜索建议数量上限
    - **Property 23: 搜索建议数量上限**
    - 验证 `suggest()` 返回的建议列表长度不超过 10
    - 测试文件：`knowledge_agent/tests/test_search_properties.py`
    - **验证: 需求 14.2**


- [x] 12. 实现 MCP Prompts 支持
  - [x] 12.1 创建 `mcp_prompts.py` 模块并注册提示模板
    - 新建 `knowledge_agent/server/mcp_prompts.py`
    - 实现 `register_knowledge_prompts(app, knowledge_core)` 函数
    - 注册 3 个提示模板：`summarize_knowledge`（知识摘要生成）、`search_assistant`（知识搜索辅助）、`organize_suggestions`（知识整理建议）
    - _需求: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 12.2 在 `knowledge_mcp_server.py` 中集成 MCP Prompts 注册
    - 修改 `knowledge_agent/server/knowledge_mcp_server.py`，调用 `register_knowledge_prompts()` 注册提示模板
    - _需求: 11.5_

  - [ ]* 12.3 编写属性测试：提示模板包含输入参数
    - **Property 20: 提示模板包含输入参数**
    - 验证 `summarize_knowledge(item_id)` 返回的提示包含条目内容，`search_assistant(topic)` 返回的提示包含 topic 文本
    - 测试文件：`knowledge_agent/tests/test_mcp_prompts.py`
    - **验证: 需求 11.2, 11.3**

- [x] 13. 集成 SourceTypeDetector 和 SecurityValidator 到业务流程
  - [x] 13.1 在 `collect_knowledge` 工具中集成 SourceTypeDetector
    - 修改 `mcp_tools.py` 中的 `collect_knowledge` 工具
    - 当 source_type 为 "auto" 时调用 `SourceTypeDetector.detect()` 自动检测类型
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 13.2 在 `collect_knowledge` 工具中集成 SecurityValidator
    - 修改 `mcp_tools.py`，在处理文件前调用 `SecurityValidator.validate_path()` 验证路径安全性
    - 从配置文件读取 `allowed_paths` 和 `blocked_extensions` 设置
    - _需求: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 13.3 在 WebProcessor 中注册到处理器注册表
    - 修改 `knowledge_agent_core.py` 中的处理器注册逻辑，将 WebProcessor 注册为 WEB 类型的处理器
    - _需求: 7.1_

- [x] 14. 检查点 - MCP 协议层验证
  - 确保所有 MCP Tools、Resources、Prompts 功能正常，SourceTypeDetector 和 SecurityValidator 集成正确，如有问题请向用户确认。

- [x] 15. 最终检查点 - 全量测试验证
  - 运行全部测试套件（`pytest knowledge_agent/tests/`），确保所有单元测试和属性测试通过
  - 确认所有 14 项需求的验收标准均已覆盖
  - 如有问题请向用户确认

## 说明

- 标记 `*` 的子任务为可选测试任务，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保可追溯性
- 属性测试使用 Hypothesis 库，每个属性对应设计文档中的一个正确性属性
- 检查点任务用于增量验证，确保每个阶段的代码质量
- 单元测试和属性测试互补：属性测试验证通用不变量，单元测试验证具体边界条件
