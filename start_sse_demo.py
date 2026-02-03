#!/usr/bin/env python3
"""
SSE演示启动脚本
"""

import sys
import subprocess
import webbrowser
import time
import os
from pathlib import Path

def main():
    print("🚀 启动知识管理智能体 SSE 演示")
    print("=" * 50)
    
    # 检查文件是否存在
    server_script = Path("knowledge_agent_server.py")
    web_client = Path("web_client_example.html")
    
    if not server_script.exists():
        print("❌ 找不到 knowledge_agent_server.py")
        return
    
    if not web_client.exists():
        print("❌ 找不到 web_client_example.html")
        return
    
    print("✅ 文件检查完成")
    
    try:
        print("\n📡 启动SSE服务器...")
        print("命令: python knowledge_agent_server.py --transport sse")
        print("\n⚠️  注意: 服务器将在前台运行")
        print("⚠️  要停止服务器，请按 Ctrl+C")
        print("\n🌐 服务器启动后，Web客户端将自动打开")
        print("🌐 Web客户端地址: file://" + str(web_client.absolute()))
        
        # 给用户一些时间阅读信息
        print("\n⏳ 3秒后启动服务器...")
        time.sleep(3)
        
        # 在后台打开Web客户端
        webbrowser.open(f"file://{web_client.absolute()}")
        
        # 启动SSE服务器 (这会阻塞)
        subprocess.run([
            sys.executable, 
            "knowledge_agent_server.py", 
            "--transport", "sse"
        ])
        
    except KeyboardInterrupt:
        print("\n\n✅ 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

if __name__ == "__main__":
    main()