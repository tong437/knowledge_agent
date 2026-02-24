# ChatboxAI MCP 配置指南

## 📋 配置文件

在 ChatboxAI 的 MCP 配置中添加以下内容：

```json
{
  "mcpServers": {
    "knowledge-agent": {
      "command": "python",
      "args": [
        "D:/Study/人工智能/结业项目/U2025011_莫XX_U20250222_张XX/YA_MCPServer_DeepReport/knowledge_agent_server.py",
        "--transport",
        "stdio",
        "--log-file",
        "logs/mcp_server.log",
        "--log-level",
        "INFO"
      ],
      "cwd": "D:/Study/人工智能/结业项目/U2025011_莫XX_U20250222_张XX/YA_MCPServer_DeepReport"
    }
  }
}
```

## 📊 日志位置

日志文件会保存在：
```
D:/Study/人工智能/结业项目/U2025011_莫XX_U20250222_张XX/YA_MCPServer_DeepReport/logs/mcp_server.log
```

## 🔍 查看日志的方法

### 方法1：使用 Python 日志查看器（推荐）⭐⭐⭐

```bash
python view_logs.py
```

功能：
- 查看最后 N 行
- 实时跟踪（tail -f）
- 按级别过滤（ERROR、WARNING）
- 关键词搜索
- 统计信息

### 方法2：使用批处理脚本

```bash
view_logs.bat
```

### 方法3：直接查看文件

使用任何文本编辑器打开：
```
logs/mcp_server.log
```

推荐编辑器：
- VS Code
- Notepad++
- Sublime Text

### 方法4：使用命令行

```bash
# 查看最后 50 行
powershell -Command "Get-Content logs/mcp_server.log -Tail 50"

# 实时跟踪
powershell -Command "Get-Content logs/mcp_server.log -Wait -Tail 20"

# 搜索错误
findstr /i "error" logs\mcp_server.log

# 搜索特定操作
findstr /i "batch_collect" logs\mcp_server.log
```

## 📝 日志级别说明

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认）
- **WARNING**: 警告信息
- **ERROR**: 错误信息

修改日志级别：
```json
"args": [
  "...",
  "--log-level",
  "DEBUG"  // 改为 DEBUG 查看更详细的信息
]
```

## 🔧 故障排查

### 问题1：日志文件不存在

**原因**：服务器还没有启动过

**解决**：
1. 在 ChatboxAI 中发送一条消息
2. 等待服务器启动
3. 检查 `logs/` 目录

### 问题2：日志文件为空

**原因**：日志级别设置过高

**解决**：
将 `--log-level` 改为 `INFO` 或 `DEBUG`

### 问题3：找不到日志文件

**原因**：工作目录不正确

**解决**：
确保配置中的 `cwd` 路径正确

## 💡 日志分析技巧

### 查看批量收集操作

```bash
findstr /i "batch_collect" logs\mcp_server.log
```

### 查看所有错误

```bash
findstr /i "[ERROR]" logs\mcp_server.log
```

### 查看特定时间段

使用 Python 脚本：
```python
python view_logs.py
# 选择 6 (搜索关键词)
# 输入时间: 2025-02-24
```

### 统计操作次数

```bash
findstr /i "collect_knowledge" logs\mcp_server.log | find /c /v ""
```

## 📚 日志示例

正常的日志输出：
```
[2025-02-24T10:30:15] [INFO] [knowledge_agent.core] Batch collecting knowledge from: D:/Study/大创项目
[2025-02-24T10:30:16] [INFO] [knowledge_agent.core] Batch collection completed: 5 succeeded, 0 failed
```

错误日志：
```
[2025-02-24T10:30:15] [ERROR] [knowledge_agent.core] Failed to process file: example.pdf
Exception: FileNotFoundError: File not found
```

## 🎯 演示时的日志监控

在录制演示视频时，可以：

1. **开两个窗口**：
   - 窗口1：ChatboxAI 对话
   - 窗口2：实时日志 `python view_logs.py` → 选择 3

2. **录制后分析**：
   - 使用日志统计功能
   - 展示成功率
   - 显示处理时间

3. **故障演示**：
   - 故意触发错误
   - 展示错误日志
   - 演示如何排查
