#!/usr/bin/env python3
"""
MCP Web代理服务器
将Web请求转换为MCP stdio通信
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import queue
import time

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class MCPStdioProxy:
    """MCP stdio代理，将Web请求转换为MCP stdio通信"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.message_id = 1
        self.pending_requests: Dict[int, queue.Queue] = {}
        self.logger = logging.getLogger("mcp_proxy")
        
    def start_mcp_server(self):
        """启动MCP服务器进程"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, "knowledge_agent_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # 启动读取线程
            threading.Thread(target=self._read_responses, daemon=True).start()
            
            self.logger.info("MCP服务器进程已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动MCP服务器失败: {e}")
            return False
    
    def _read_responses(self):
        """读取MCP服务器响应的线程"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    response = json.loads(line.strip())
                    msg_id = response.get('id')
                    
                    if msg_id and msg_id in self.pending_requests:
                        self.pending_requests[msg_id].put(response)
                    else:
                        self.logger.info(f"收到通知: {response}")
                        
            except Exception as e:
                self.logger.error(f"读取响应错误: {e}")
                break
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息到MCP服务器并等待响应"""
        if not self.process or self.process.poll() is not None:
            raise Exception("MCP服务器未运行")
        
        # 分配消息ID
        if 'id' not in message:
            message['id'] = self.message_id
            self.message_id += 1
        
        msg_id = message['id']
        response_queue = queue.Queue()
        self.pending_requests[msg_id] = response_queue
        
        try:
            # 发送消息
            message_str = json.dumps(message) + '\n'
            self.process.stdin.write(message_str)
            self.process.stdin.flush()
            
            # 等待响应 (超时5秒)
            try:
                response = response_queue.get(timeout=5.0)
                return response
            except queue.Empty:
                raise Exception("请求超时")
                
        finally:
            # 清理
            if msg_id in self.pending_requests:
                del self.pending_requests[msg_id]
    
    def stop(self):
        """停止MCP服务器"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

# 创建FastAPI应用
app = FastAPI(title="MCP Web代理", description="知识管理智能体Web接口")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局MCP代理实例
mcp_proxy = MCPStdioProxy()

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化MCP服务器"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("mcp_proxy")
    
    logger.info("启动MCP Web代理服务器...")
    
    if not mcp_proxy.start_mcp_server():
        logger.error("无法启动MCP服务器")
        return
    
    # 等待MCP服务器启动
    await asyncio.sleep(1)
    
    # 发送初始化消息
    try:
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "MCP Web Proxy",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await mcp_proxy.send_message(init_message)
        logger.info(f"MCP初始化成功: {response}")
        
    except Exception as e:
        logger.error(f"MCP初始化失败: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    mcp_proxy.stop()

@app.get("/", response_class=HTMLResponse)
async def get_web_client():
    """返回Web客户端页面"""
    try:
        with open("web_client_example.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>找不到web_client_example.html文件</h1>", status_code=404)

@app.post("/mcp")
async def send_mcp_message(message: Dict[str, Any]):
    """发送MCP消息"""
    try:
        response = await mcp_proxy.send_message(message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取服务器状态"""
    return {
        "status": "running" if mcp_proxy.process and mcp_proxy.process.poll() is None else "stopped",
        "message": "MCP Web代理正在运行"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时通信"""
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 转发到MCP服务器
            response = await mcp_proxy.send_message(message)
            
            # 发送响应给客户端
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        logging.getLogger("mcp_proxy").error(f"WebSocket错误: {e}")
    finally:
        await websocket.close()

def main():
    """启动Web代理服务器"""
    print("🚀 启动MCP Web代理服务器")
    print("=" * 50)
    print("📡 MCP服务器: stdio模式")
    print("🌐 Web接口: http://localhost:3000")
    print("🔌 WebSocket: ws://localhost:3000/ws")
    print("📋 API文档: http://localhost:3000/docs")
    print("⚠️  按Ctrl+C停止服务器")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host="localhost",
            port=3000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✅ 服务器已停止")

if __name__ == "__main__":
    main()