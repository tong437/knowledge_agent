# 个人知识管理智能体 - 架构文档

## 📖 项目简介

个人知识管理智能体（Personal Knowledge Agent）是一个基于 MCP（Model Context Protocol）协议的智能知识管理系统。它能够自动收集、组织、搜索和管理来自多种数据源的知识内容，为用户提供统一的知识库管理能力。

## 🎯 核心功能

### 1. 知识收集（Knowledge Collection）
- 支持多种数据源类型：文档（.txt, .md, .doc, .docx）、PDF、代码文件、网页
- 自动检测数据源类型
- 提取关键信息和元数据
- 批量收集功能

### 2. 智能搜索（Intelligent Search）
- 基于 Whoosh 的全文搜索引擎
- 语义搜索能力
- 相关性评分和排序
- 支持多条件过滤

### 3. 知识组织（Knowledge Organization）
- 自动分类：根据内容自动归类
- 智能标签：自动生成相关标签
- 关系发现：分析知识项之间的关联
- 分类体系管理

### 4. 数据管理（Data Management）
- SQLite 持久化存储
- 数据导入/导出（JSON 格式）
- 统计信息和性能指标
- 错误追踪和监控

### 5. MCP 协议支持
- 标准 MCP 工具接口
- stdio 传输（AI 助手集成）
- SSE 传输（Web 客户端）
- 资源和提示词管理

## 🏗️ 组件架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  MCP Tools   │  │  Resources   │  │   Prompts    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Knowledge Agent Core                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Component Registry  │  Config Manager  │  Security  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Processors  │  │  Organizers  │  │    Search    │      │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │      │
│  │  │Document│  │  │  │Classify│  │  │  │ Whoosh │  │      │
│  │  │  PDF   │  │  │  │  Tag   │  │  │  │Semantic│  │      │
│  │  │  Code  │  │  │  │Relation│  │  │  │ Index  │  │      │
│  │  │  Web   │  │  │  └────────┘  │  │  └────────┘  │      │
│  │  └────────┘  │  └──────────────┘  └──────────────┘      │
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Storage    │  │    Models    │  │  Interfaces  │      │
│  │  (SQLite)    │  │ KnowledgeItem│  │   Abstract   │      │
│  │              │  │   Category   │  │   Classes    │      │
│  │              │  │     Tag      │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 📦 模块说明

### server/ - MCP 服务器层
- `knowledge_mcp_server.py`: MCP 服务器主类
- `mcp_tools.py`: MCP 工具注册和实现
- `mcp_resources.py`: MCP 资源管理
- `mcp_prompts.py`: MCP 提示词定义

### core/ - 核心业务层
- `knowledge_agent_core.py`: 核心协调器
- `component_registry.py`: 组件注册和依赖注入
- `config_manager.py`: 配置管理
- `security_validator.py`: 安全验证
- `source_type_detector.py`: 数据源类型检测
- `data_import_export.py`: 数据导入导出
- `logging_config.py`: 日志和监控配置
- `exceptions.py`: 自定义异常

### processors/ - 数据处理层
- `base_processor.py`: 处理器基类
- `document_processor.py`: 文档处理器
- `pdf_processor.py`: PDF 处理器
- `code_processor.py`: 代码文件处理器
- `web_processor.py`: 网页处理器

### organizers/ - 知识组织层
- `knowledge_organizer_impl.py`: 组织器实现
- `auto_classifier.py`: 自动分类器
- `tag_generator.py`: 标签生成器
- `relationship_analyzer.py`: 关系分析器

### search/ - 搜索引擎层
- `search_engine_impl.py`: 搜索引擎实现
- `search_index_manager.py`: 索引管理
- `semantic_searcher.py`: 语义搜索
- `result_processor.py`: 结果处理

### storage/ - 存储层
- `sqlite_storage.py`: SQLite 存储实现

### models/ - 数据模型层
- `knowledge_item.py`: 知识项模型
- `data_source.py`: 数据源模型
- `category.py`: 分类模型
- `tag.py`: 标签模型
- `relationship.py`: 关系模型
- `search_result.py`: 搜索结果模型

### interfaces/ - 接口定义层
- `data_source_processor.py`: 数据源处理器接口
- `knowledge_organizer.py`: 知识组织器接口
- `search_engine.py`: 搜索引擎接口
- `storage_manager.py`: 存储管理器接口

## 🔧 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 协议层 | FastMCP | MCP 协议实现框架 |
| Web 层 | Starlette + Uvicorn | ASGI Web 框架和服务器 |
| 业务层 | Python 3.10+ | 核心业务逻辑 |
| 搜索层 | Whoosh | 纯 Python 全文搜索引擎 |
| 存储层 | SQLite | 轻量级关系数据库 |
| 文档处理 | PyPDF2 | PDF 文件解析 |
| 测试框架 | Pytest + Hypothesis | 单元测试和属性测试 |

## 🔄 数据流

### 知识收集流程
```
用户请求 → MCP Tool → Core → Security Validator
                                      ↓
                              Source Type Detector
                                      ↓
                              Processor (Document/PDF/Code/Web)
                                      ↓
                              Knowledge Item 创建
                                      ↓
                              Storage Manager 保存
                                      ↓
                              Search Index 更新
                                      ↓
                              返回结果
```

### 知识搜索流程
```
搜索请求 → MCP Tool → Core → Search Engine
                                    ↓
                            Whoosh Index 查询
                                    ↓
                            Semantic Searcher（可选）
                                    ↓
                            Result Processor 排序
                                    ↓
                            返回搜索结果
```

### 知识组织流程
```
组织请求 → MCP Tool → Core → Knowledge Organizer
                                    ↓
                            Auto Classifier 分类
                                    ↓
                            Tag Generator 标签
                                    ↓
                            Relationship Analyzer 关系
                                    ↓
                            Storage Manager 更新
                                    ↓
                            返回组织结果
```

## 🎨 设计模式

1. **依赖注入**: 通过 ComponentRegistry 管理组件依赖
2. **策略模式**: 不同数据源使用不同的 Processor 策略
3. **工厂模式**: 动态创建处理器和组织器
4. **单例模式**: ConfigManager 和 ComponentRegistry
5. **装饰器模式**: 性能监控和错误追踪装饰器
6. **接口隔离**: 清晰的接口定义层

## 🔐 安全特性

- 路径访问控制：限制可访问的目录
- 文件类型验证：阻止危险文件扩展名
- 输入验证：严格的参数验证
- 错误处理：统一的异常处理机制

## 📊 监控和日志

- 结构化日志输出
- 性能指标追踪
- 错误统计和分析
- 系统信息记录

## 🚀 部署模式

### 1. stdio 模式（AI 助手集成）
```bash
python knowledge_agent_server.py --transport stdio
```
适用于 Claude Desktop、Kiro 等 AI 助手

### 2. SSE 模式（Web 客户端）
```bash
python knowledge_agent_server.py --transport sse --host localhost --port 8000
```
适用于浏览器和 Web 应用

## 📈 扩展性

系统设计支持以下扩展：

1. **新数据源类型**: 实现 DataSourceProcessor 接口
2. **新存储后端**: 实现 StorageManager 接口
3. **新搜索引擎**: 实现 SearchEngine 接口
4. **新组织策略**: 扩展 KnowledgeOrganizer
5. **新传输协议**: FastMCP 支持多种传输方式

## 🧪 测试覆盖

- 单元测试：各组件独立测试
- 集成测试：组件协作测试
- MCP 集成测试：协议兼容性测试
- 属性测试：使用 Hypothesis 进行模糊测试

## 📝 配置管理

配置文件 `config.yaml` 支持：
- 服务器配置（名称、版本、传输方式）
- 存储配置（类型、路径、备份）
- 搜索配置（引擎、索引路径、结果数）
- 组织配置（自动分类、标签、关系）
- 处理配置（文件大小、编码、超时）
- 日志配置（级别、格式、文件）
- 性能配置（缓存、批处理、线程）
- 安全配置（认证、路径限制）

## 🎯 未来规划

- [ ] 支持更多数据源类型（图片、音频、视频）
- [ ] 增强语义搜索能力（向量数据库）
- [ ] 知识图谱可视化
- [ ] 多用户支持和权限管理
- [ ] 云存储集成
- [ ] 移动端应用
- [ ] AI 辅助知识总结和问答
