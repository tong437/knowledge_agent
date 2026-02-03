#!/usr/bin/env python3
"""
快速测试Web代理功能
"""

import requests
import json
import time

def test_web_proxy():
    """测试Web代理的基本功能"""
    
    base_url = "http://localhost:3000"
    
    print("🧪 测试Web代理功能")
    print("=" * 50)
    
    # 测试1: 检查服务器状态
    print("\n1️⃣ 测试服务器状态...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务器状态: {response.json()}")
        else:
            print(f"❌ 状态检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请先运行: python mcp_web_proxy.py")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    # 测试2: 发送初始化消息
    print("\n2️⃣ 测试MCP初始化...")
    try:
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "Test Client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(
            f"{base_url}/mcp",
            json=init_message,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 初始化成功")
            print(f"   服务器信息: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 初始化失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 初始化错误: {e}")
    
    # 测试3: 列出工具
    print("\n3️⃣ 测试列出工具...")
    try:
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            f"{base_url}/mcp",
            json=tools_message,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            print(f"✅ 找到 {len(tools)} 个工具:")
            for tool in tools[:5]:  # 只显示前5个
                print(f"   - {tool.get('name')}: {tool.get('description', '')[:50]}...")
        else:
            print(f"❌ 列出工具失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 列出工具错误: {e}")
    
    # 测试4: 测试搜索功能
    print("\n4️⃣ 测试知识搜索...")
    try:
        search_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_knowledge",
                "arguments": {
                    "query": "测试",
                    "max_results": 5
                }
            }
        }
        
        response = requests.post(
            f"{base_url}/mcp",
            json=search_message,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 搜索请求成功")
            print(f"   结果: {json.dumps(result.get('result', {}), indent=2, ensure_ascii=False)[:200]}...")
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 搜索错误: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("\n💡 提示:")
    print("   - 在浏览器中打开: http://localhost:3000")
    print("   - 查看API文档: http://localhost:3000/docs")
    print("   - 使用Web客户端进行交互测试")
    
    return True

if __name__ == "__main__":
    print("⏳ 等待2秒让服务器完全启动...")
    time.sleep(2)
    test_web_proxy()