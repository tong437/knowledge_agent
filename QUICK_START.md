# 🚀 快速开始指南

## 📋 前提条件

- Python 3.10+
- 已安装所有依赖包

```bash
pip install mcp fastapi uvicorn websockets hypothesis pytest
```

## 🎯 三种使用方式

### 方式1：stdio模式（AI助手集成）⭐

**适用场景**: 与Claude Desktop、Kiro等AI助手集成

```bash
# 启动服务器
python knowledge_agent_server.py

# 或指定名称
python knowledge_agent_server.py --name my-agent
```

**配置AI助手**:
在AI助手的配置文件中添加：
```json
{
  "mcpServers": {
    "knowledge-agent": {
      "command": "python",
      "args": ["path/to/knowledge_agent_server.py"]
    }
  }
}
```

---

### 方式2：Web代理模式（浏览器访问）⭐⭐⭐ 推荐

**适用场景**: 通过Web浏览器管理知识

#### 步骤1：启动Web代理
```bash
# Windows
start_web_demo.bat

# 或手动启动
python mcp_web_proxy.py
```

#### 步骤2：打开浏览器
访问: http://localhost:3000

#### 步骤3：使用Web界面
1. 点击"连接MCP代理服务器"
2. 点击"初始化MCP"
3. 开始使用各种功能

#### 步骤4：测试功能（可选）
```bash
# 在另一个终端运行
python test_web_proxy.py
```

---

### 方式3：SSE模式（实验性）⚠️

**注意**: 目前存在兼容性问题，不推荐使用

```bash
python knowledge_agent_server.py --transport sse
```

**已知问题**:
- MCP SSE需要特定握手过程
- 浏览器EventSource API不兼容
- 建议使用Web代理模式替代

---

## 📊 功能对比

| 功能 | stdio | Web代理 | SSE |
|------|-------|---------|-----|
| AI助手集成 | ✅ | ❌ | ❌ |
| 浏览器访问 | ❌ | ✅ | ⚠️ |
| 多客户端 | ❌ | ✅ | ✅ |
| 稳定性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| 易用性 | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| 推荐度 | ⭐⭐⭐ | ⭐⭐⭐ | ❌ |

## 🧪 测试安装

### 运行单元测试
```bash
pytest knowledge_agent/tests/ -v
```

### 测试MCP服务器
```bash
python -c "from knowledge_agent.server import KnowledgeMCPServer; s = KnowledgeMCPServer(); print('✅ 安装成功')"
```

### 测试Web代理
```bash
# 启动代理
python mcp_web_proxy.py

# 在另一个终端测试
python test_web_proxy.py
```

## 📁 项目结构

```
.
├── knowledge_agent/          # 主包
│   ├── models/              # 数据模型
│   ├── interfaces/          # 抽象接口
│   ├── core/                # 核心逻辑
│   ├── server/              # MCP服务器
│   └── tests/               # 测试套件
├── knowledge_agent_server.py # MCP服务器入口
├── mcp_web_proxy.py         # Web代理服务器
├── web_client_example.html  # Web客户端
├── start_web_demo.bat       # Windows启动脚本
└── test_web_proxy.py        # 测试脚本
```

## 🔧 配置

### 服务器配置
编辑 `knowledge_agent/config.yaml`:

```yaml
server:
  name: "personal-knowledge-agent"
  transport:
    default: "stdio"
    sse:
      host: "localhost"
      port: 8000

storage:
  type: "sqlite"
  path: "knowledge_base.db"

search:
  engine: "whoosh"
  max_results: 50
```

### Web代理配置
编辑 `mcp_web_proxy.py`:

```python
# 修改端口
uvicorn.run(app, host="localhost", port=3000)
```

## 📝 使用示例

### 示例1：通过Web界面搜索知识
1. 启动Web代理: `python mcp_web_proxy.py`
2. 打开浏览器: http://localhost:3000
3. 连接服务器
4. 输入搜索词，点击"测试搜索"

### 示例2：通过API调用
```python
import requests

# 搜索知识
response = requests.post(
    "http://localhost:3000/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_knowledge",
            "arguments": {
                "query": "人工智能",
                "max_results": 10
            }
        }
    }
)

print(response.json())
```

### 示例3：与AI助手集成
配置Claude Desktop的`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge-agent": {
      "command": "python",
      "args": ["C:/path/to/knowledge_agent_server.py"],
      "env": {}
    }
  }
}
```

## 🐛 常见问题

### Q1: 无法启动服务器
**A**: 检查Python版本和依赖安装
```bash
python --version  # 应该 >= 3.10
pip list | grep mcp
```

### Q2: Web代理连接失败
**A**: 确认端口未被占用
```bash
netstat -ano | findstr :3000
```

### Q3: MCP消息超时
**A**: 增加超时时间或检查服务器日志

### Q4: 测试失败
**A**: 确保所有依赖已安装
```bash
pip install -r requirements.txt
```

## 📚 下一步

1. ✅ **Task 1完成** - 项目结构和核心接口已建立
2. 🔄 **Task 2** - 实现数据模型和存储层
3. 🔄 **Task 3** - 实现知识收集引擎
4. 🔄 **Task 4-11** - 继续实现其他功能

## 💡 提示

- **推荐使用Web代理模式**进行开发和测试
- **stdio模式**适合与AI助手集成
- **SSE模式**目前不稳定，等待后续改进
- 查看 `README_WEB_ACCESS.md` 了解更多Web访问细节

## 📞 获取帮助

- 查看日志输出
- 检查浏览器控制台
- 访问API文档: http://localhost:3000/docs
- 阅读MCP协议文档

---

**祝使用愉快！** 🎉