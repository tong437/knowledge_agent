# Personal Knowledge Agent - MCP Server

个人知识管理代理，基于 MCP (Model Context Protocol) 协议实现。

## 功能特性

- 📚 **知识收集**: 支持文档、PDF、代码文件的知识提取
- 🔍 **智能搜索**: 基于 Whoosh 的全文搜索和语义搜索
- 🏷️ **自动组织**: 自动分类、标签生成、关系发现
- 💾 **数据管理**: SQLite 存储，支持导入导出
- 🔌 **MCP 协议**: 标准 MCP 接口，支持 SSE 传输

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python start_with_cors_fix.py
```

服务器将在 `http://127.0.0.1:8000` 启动。

### 3. 使用 MCP Inspector 测试

1. 访问 https://inspector.mcp.run
2. 配置连接：
   - Transport Type: **SSE**
   - URL: `http://127.0.0.1:8000/sse`
   - Connection Type: **Direct**
3. 连接并测试工具

详细使用说明请查看 [START_GUIDE.md](START_GUIDE.md)

## MCP 工具列表

| 工具名称 | 功能描述 |
|---------|---------|
| `collect_knowledge` | 从数据源收集知识 |
| `search_knowledge` | 搜索知识库 |
| `organize_knowledge` | 组织知识项（分类、标签、关系） |
| `get_knowledge_item` | 获取指定知识项 |
| `list_knowledge_items` | 列出知识项 |
| `export_knowledge` | 导出知识数据 |
| `import_knowledge` | 导入知识数据 |
| `get_statistics` | 获取统计信息 |
| `get_performance_metrics` | 获取性能指标 |
| `get_error_summary` | 获取错误摘要 |

## 支持的数据源类型

- **document**: 文本文档（.txt, .md, .doc, .docx）
- **pdf**: PDF 文件
- **code**: 代码文件（.py, .js, .java, .cpp, .c, .ts 等）

## 项目结构

```
knowledge_agent/
├── server/          # MCP 服务器实现
├── core/            # 核心业务逻辑
├── processors/      # 数据源处理器
├── storage/         # 存储管理
├── search/          # 搜索引擎
├── organizers/      # 知识组织
├── models/          # 数据模型
├── interfaces/      # 接口定义
└── tests/           # 测试代码
```

## 技术栈

- **MCP 框架**: FastMCP
- **Web 框架**: Starlette + Uvicorn
- **数据库**: SQLite
- **搜索引擎**: Whoosh
- **PDF 处理**: PyPDF2
- **测试框架**: Pytest

## 开发文档

- [需求文档](.kiro/specs/personal-knowledge-agent/requirements.md)
- [设计文档](.kiro/specs/personal-knowledge-agent/design.md)
- [任务列表](.kiro/specs/personal-knowledge-agent/tasks.md)

## 许可证

MIT License
