# Knowledge Agent MCP Server - 启动指南

## 快速启动

### 1. 启动 MCP 服务器（SSE 模式）

```bash
python start_with_cors_fix.py
```

服务器将在 `http://127.0.0.1:8000` 启动，SSE 端点为 `http://127.0.0.1:8000/sse`

### 2. 使用 MCP Inspector 连接

1. 打开 MCP Inspector: https://inspector.mcp.run
2. 配置连接参数：
   - **Transport Type**: SSE
   - **URL**: `http://127.0.0.1:8000/sse`
   - **Connection Type**: Direct
3. 点击 "Connect"

### 3. 测试功能

#### 收集知识（Collect Knowledge）

测试本地文件：
```json
{
  "source_path": "README.md",
  "source_type": "document"
}
```

测试代码文件：
```json
{
  "source_path": "knowledge_agent_server.py",
  "source_type": "code"
}
```

#### 搜索知识（Search Knowledge）

```json
{
  "query": "knowledge agent",
  "max_results": 10,
  "min_relevance": 0.1
}
```

#### 获取统计信息（Get Statistics）

无需参数，直接调用即可。

## 支持的数据源类型

- **document**: 文档文件（.txt, .md, .doc, .docx）
- **pdf**: PDF 文件
- **code**: 代码文件（.py, .js, .java, .cpp, .c, .ts 等）

注意：web（网页）和 image（图片）类型暂未实现。

## 项目结构

```
.
├── start_with_cors_fix.py          # SSE 服务器启动脚本（带 CORS 支持）
├── knowledge_agent_server.py       # MCP 服务器主程序
├── knowledge_agent/                # 核心代码目录
│   ├── server/                     # MCP 服务器实现
│   ├── core/                       # 核心逻辑
│   ├── processors/                 # 数据处理器
│   ├── storage/                    # 存储管理
│   ├── search/                     # 搜索引擎
│   ├── organizers/                 # 知识组织
│   └── models/                     # 数据模型
├── knowledge_agent.db              # SQLite 数据库
├── search_index/                   # 搜索索引
└── logs/                           # 日志文件

## 常见问题

### Q: 连接 Inspector 时出现 CORS 错误？
A: 确保使用 `start_with_cors_fix.py` 启动服务器，该脚本已配置 CORS 支持。

### Q: 收集知识时报错 "No processor available"？
A: 检查文件类型是否支持，目前仅支持 document、pdf、code 三种类型。

### Q: 如何查看服务器日志？
A: 日志文件保存在 `logs/` 目录下，或查看控制台输出。

## 依赖安装

```bash
pip install -r requirements.txt
```

主要依赖：
- fastmcp: MCP 服务器框架
- starlette: ASGI 框架
- uvicorn: ASGI 服务器
- whoosh: 搜索引擎
- PyPDF2: PDF 处理
