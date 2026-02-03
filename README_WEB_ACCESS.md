# 知识管理智能体 - Web访问指南

## 🌐 概述

本指南说明如何通过Web浏览器访问和使用知识管理智能体。

## 📋 问题说明

直接使用SSE模式连接MCP服务器时遇到的问题：
- **错误**: `ValueError: Request validation failed`
- **原因**: MCP的SSE实现需要特定的握手过程和请求格式
- **影响**: 浏览器的EventSource API无法直接连接到MCP SSE端点

## ✅ 解决方案：使用Web代理

我们创建了一个Web代理服务器，它：
1. 使用stdio模式与MCP服务器通信（稳定可靠）
2. 提供标准的HTTP/REST API供Web客户端调用
3. 自动处理MCP协议的复杂性
4. 支持CORS，允许浏览器访问

## 🚀 使用方法

### 方式1：使用Web代理（推荐）

#### 步骤1：启动Web代理服务器
```bash
python mcp_web_proxy.py
```

服务器启动后会显示：
```
🚀 启动MCP Web代理服务器
==================================================
📡 MCP服务器: stdio模式
🌐 Web接口: http://localhost:3000
🔌 WebSocket: ws://localhost:3000/ws
📋 API文档: http://localhost:3000/docs
⚠️  按Ctrl+C停止服务器
==================================================
```

#### 步骤2：打开Web客户端
在浏览器中访问：
```
http://localhost:3000
```

或直接打开本地文件：
```
web_client_example.html
```

#### 步骤3：使用Web界面
1. 点击"连接MCP代理服务器"
2. 点击"初始化MCP"进行协议握手
3. 点击"列出工具"查看可用功能
4. 点击"测试搜索"测试知识搜索功能

### 方式2：使用stdio模式（本地客户端）

适用于AI助手（Claude、Kiro等）：

```bash
# 默认stdio模式
python knowledge_agent_server.py
```

## 🏗️ 架构对比

### Web代理架构（推荐）
```
浏览器 ──HTTP──► Web代理 ──stdio──► MCP服务器
                (FastAPI)         (知识管理智能体)
```

**优点：**
- ✅ 稳定可靠（使用stdio通信）
- ✅ 无CORS问题
- ✅ 标准HTTP API
- ✅ 易于调试
- ✅ 支持多客户端

### 直接SSE架构（有问题）
```
浏览器 ──SSE──► MCP服务器
              (知识管理智能体)
```

**问题：**
- ❌ MCP SSE需要特定握手
- ❌ 浏览器EventSource不兼容
- ❌ 需要复杂的CORS配置
- ❌ 连接验证失败

## 📡 API端点

Web代理提供以下端点：

### 1. 主页
```
GET http://localhost:3000/
```
返回Web客户端界面

### 2. 服务器状态
```
GET http://localhost:3000/status
```
返回：
```json
{
  "status": "running",
  "message": "MCP Web代理正在运行"
}
```

### 3. 发送MCP消息
```
POST http://localhost:3000/mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### 4. WebSocket连接
```
ws://localhost:3000/ws
```
用于实时双向通信

### 5. API文档
```
GET http://localhost:3000/docs
```
自动生成的交互式API文档

## 🔧 配置

### Web代理配置
编辑 `mcp_web_proxy.py` 中的配置：

```python
# 修改端口
uvicorn.run(app, host="localhost", port=3000)

# 修改CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    ...
)
```

### MCP服务器配置
编辑 `knowledge_agent/config.yaml`：

```yaml
server:
  name: "personal-knowledge-agent"
  version: "0.1.0"
```

## 🧪 测试

### 测试Web代理
```bash
# 启动代理
python mcp_web_proxy.py

# 在另一个终端测试
curl http://localhost:3000/status
```

### 测试MCP消息
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

## 📝 MCP消息示例

### 初始化
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "Web Client",
      "version": "1.0.0"
    }
  }
}
```

### 列出工具
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

### 搜索知识
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_knowledge",
    "arguments": {
      "query": "人工智能",
      "max_results": 10
    }
  }
}
```

## 🐛 故障排除

### 问题1：Web代理无法启动
**错误**: `Address already in use`
**解决**: 端口3000被占用，修改端口或关闭占用进程

### 问题2：MCP服务器无法启动
**错误**: `ModuleNotFoundError`
**解决**: 确保已安装所有依赖
```bash
pip install -r requirements.txt
```

### 问题3：浏览器无法连接
**错误**: `Failed to fetch`
**解决**: 
1. 确认Web代理正在运行
2. 检查浏览器控制台错误
3. 确认URL正确（http://localhost:3000）

### 问题4：MCP消息超时
**错误**: `请求超时`
**解决**: 
1. 检查MCP服务器是否正常运行
2. 增加超时时间（在mcp_web_proxy.py中修改）
3. 查看服务器日志

## 📚 相关文件

- `mcp_web_proxy.py` - Web代理服务器
- `web_client_example.html` - Web客户端界面
- `knowledge_agent_server.py` - MCP服务器主程序
- `knowledge_agent/config.yaml` - 配置文件

## 🎯 下一步

1. **完成功能实现** - 实现Task 2-11的功能
2. **增强Web界面** - 添加更多交互功能
3. **添加认证** - 为生产环境添加安全认证
4. **性能优化** - 优化大量数据的处理
5. **部署指南** - 创建生产环境部署文档

## 💡 提示

- Web代理模式是目前最稳定的Web访问方式
- stdio模式适合本地AI助手集成
- SSE模式需要等待MCP协议的进一步完善
- 生产环境建议添加认证和HTTPS支持

## 📞 获取帮助

如有问题，请查看：
1. 服务器日志输出
2. 浏览器开发者工具控制台
3. API文档 (http://localhost:3000/docs)
4. MCP协议规范文档