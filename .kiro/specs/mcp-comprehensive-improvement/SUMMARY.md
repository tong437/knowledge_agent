# MCP 综合改进说明

## 概述

本次 Spec 对个人知识管理 MCP 服务器进行了一次系统性的综合改进，覆盖 14 项需求，涉及缺陷修复、功能补全和架构增强三大类。技术栈为 Python 3.10+ / FastMCP / SQLite / Whoosh。

全部 15 个任务已完成，123 个测试全部通过。

## 改进分类

### 一、缺陷修复（5 项）

| 需求 | 问题描述 | 修复方案 |
|------|---------|---------|
| N+1 查询性能问题 | `get_all_knowledge_items()` 对每个条目单独查询分类和标签，数据量大时性能急剧下降 | 改为 3 次批量查询（主表 + 分类映射 + 标签映射），在 Python 中按 item_id 分组组装 |
| 内存过滤和统计 | `list_knowledge_items()` 加载全部数据到内存后过滤；`get_statistics()` 加载全部数据后计数 | 新增 `query_knowledge_items()` 使用 SQL WHERE/LIMIT/OFFSET 数据库层面过滤分页；`get_database_stats()` 使用 COUNT 聚合查询 |
| 封装违规 | `mcp_resources.py` 直接访问 `knowledge_core._storage_manager` 私有属性 | 在 KnowledgeAgentCore 中新增 `get_all_categories()`、`get_all_tags()`、`get_knowledge_graph()` 公开接口，资源模块改为通过公开接口访问 |
| SSE 参数传递 | `start_sse()` 的 host 和 port 参数未传递给 `FastMCP.run()` | 将参数正确传递给 `FastMCP.run(transport="sse", host=host, port=port)` |
| 空处理器暴露 | 用户提交未实现类型（如 image）时遇到不可预期的运行时错误 | 区分"已支持"和"已定义但未实现"的类型，未实现类型返回明确的提示信息；未注册处理器抛出描述性 `NotImplementedError` |

### 二、功能补全（7 项）

| 需求 | 功能描述 | 实现要点 |
|------|---------|---------|
| 数据源类型自动检测 | source_type 为 "auto" 时自动识别文件类型 | 新增 `SourceTypeDetector`，检测优先级：URL 模式 → 文件扩展名 → 默认 DOCUMENT，支持 20+ 种扩展名映射 |
| Web 网页处理器 | 从网页 URL 收集知识 | 实现 `WebProcessor`，使用 `urllib.request` 获取网页、`html.parser` 解析 HTML，支持标题提取、标签清除、超时重试 |
| 知识条目更新 | 编辑已有知识条目 | 存储层 `update_knowledge_item()` 支持部分字段更新，自动更新时间戳；核心层更新后自动重新索引搜索引擎 |
| 知识条目删除 | 删除不需要的条目 | 存储层级联删除关联的分类映射、标签映射和关系数据；核心层同步移除搜索索引 |
| 导入合并策略 | 导入数据时灵活处理冲突 | 支持 skip_existing（跳过）、overwrite（覆盖）、merge（合并，分类标签取并集）三种策略，返回详细的导入结果摘要 |
| 批量知识收集 | 一次性处理整个目录 | `batch_collect_knowledge()` 支持 glob 模式匹配、递归子目录、单文件失败不中断，处理前执行安全路径验证 |
| 搜索建议 | 输入时获得补全建议 | 基于 Whoosh 索引前缀匹配，返回不超过 10 条建议 |

### 三、架构增强（2 项）

| 需求 | 增强描述 | 实现要点 |
|------|---------|---------|
| 安全路径限制 | 防止未授权的文件访问 | 新增 `SecurityValidator`，支持 allowed_paths 白名单、blocked_extensions 黑名单、路径遍历防护（`../` 规范化），集成到 `collect_knowledge` 和 `batch_collect_knowledge` 流程 |
| MCP Prompts 支持 | 为 LLM 提供预定义提示模板 | 新增 `mcp_prompts.py`，注册 3 个提示模板：知识摘要生成（summarize_knowledge）、搜索辅助（search_assistant）、整理建议（organize_suggestions） |

## 修改文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `knowledge_agent/core/source_type_detector.py` | 数据源类型自动检测器 |
| `knowledge_agent/core/security_validator.py` | 安全路径验证器 |
| `knowledge_agent/server/mcp_prompts.py` | MCP 提示模板注册模块 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `knowledge_agent/storage/sqlite_storage.py` | N+1 查询修复、新增 `query_knowledge_items()`、`get_database_stats()`、`update_knowledge_item()`、删除级联 |
| `knowledge_agent/core/knowledge_agent_core.py` | 新增公开接口、更新/删除方法、批量收集、统计优化、注册 WebProcessor |
| `knowledge_agent/core/data_import_export.py` | 实现三种合并策略的 `import_from_json()`，修复方法名 `store_knowledge_item` → `save_knowledge_item` |
| `knowledge_agent/server/mcp_tools.py` | 新增 4 个 MCP 工具（update、delete、batch_collect、suggest_search），集成 SourceTypeDetector 和 SecurityValidator |
| `knowledge_agent/server/mcp_resources.py` | 封装修复，改为通过公开接口访问数据 |
| `knowledge_agent/server/knowledge_mcp_server.py` | SSE 参数传递修复、集成 MCP Prompts 注册 |
| `knowledge_agent/search/search_engine_impl.py` | 搜索建议功能，基于 Whoosh 前缀匹配 |
| `knowledge_agent/processors/__init__.py` | 导出 WebProcessor |
| `knowledge_agent/processors/web_processor.py` | 完整实现网页处理器 |
| `knowledge_agent/tests/test_core.py` | 更新过时的占位符测试 |
| `knowledge_agent/tests/test_mcp_integration.py` | 修复数据库隔离问题 |

## MCP 工具和资源变更

### 新增 MCP 工具

| 工具名称 | 参数 | 功能 |
|---------|------|------|
| `update_knowledge_item` | item_id, title?, content?, categories?, tags? | 部分更新知识条目 |
| `delete_knowledge_item` | item_id | 删除知识条目及关联数据 |
| `batch_collect_knowledge` | directory_path, file_pattern?, recursive? | 批量收集目录中的知识 |
| `suggest_search` | partial_query | 搜索自动补全建议 |

### 新增 MCP 提示模板

| 模板名称 | 参数 | 功能 |
|---------|------|------|
| `summarize_knowledge` | item_id | 生成知识条目的结构化摘要 |
| `search_assistant` | topic | 搜索知识库并综合分析结果 |
| `organize_suggestions` | 无 | 基于统计数据提供整理建议 |

### 增强的 MCP 工具

| 工具名称 | 增强内容 |
|---------|---------|
| `collect_knowledge` | source_type="auto" 时自动检测类型；处理文件前执行安全路径验证 |

## 测试覆盖

全量测试 123 个，全部通过。覆盖存储层、核心层、处理器层、搜索层、MCP 协议层和集成测试。
