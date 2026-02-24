#!/usr/bin/env python3
"""
终止 MCP 服务器进程
"""

import sys
import psutil
import signal


def find_and_kill_server():
    """查找并终止服务器进程"""
    print("=" * 60)
    print("🔍 查找 MCP 服务器进程...")
    print("=" * 60)
    
    found = []
    
    # 查找所有相关进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and 'knowledge_agent_server.py' in ' '.join(cmdline):
                    found.append(proc)
                    print(f"\n✅ 找到进程:")
                    print(f"   PID: {proc.info['pid']}")
                    print(f"   命令: {' '.join(cmdline)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not found:
        print("\n❌ 没有找到运行中的服务器进程")
        return False
    
    # 询问确认
    print("\n" + "=" * 60)
    print(f"找到 {len(found)} 个服务器进程")
    print("=" * 60)
    
    choice = input("\n是否终止这些进程? (y/n): ").strip().lower()
    
    if choice != 'y':
        print("❌ 已取消")
        return False
    
    # 终止进程
    print("\n🛑 正在终止进程...")
    
    for proc in found:
        try:
            pid = proc.info['pid']
            print(f"   终止 PID {pid}...", end=" ")
            
            # 尝试优雅关闭
            proc.terminate()
            
            # 等待进程结束
            try:
                proc.wait(timeout=5)
                print("✅ 已终止")
            except psutil.TimeoutExpired:
                # 强制杀死
                print("⚠️  超时，强制终止...", end=" ")
                proc.kill()
                proc.wait(timeout=2)
                print("✅ 已强制终止")
                
        except psutil.NoSuchProcess:
            print("✅ 进程已结束")
        except psutil.AccessDenied:
            print("❌ 权限不足")
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 服务器已停止")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🛑 MCP 服务器终止工具")
    print("=" * 60)
    print()
    
    try:
        success = find_and_kill_server()
        
        if success:
            print("\n💡 提示:")
            print("   - 日志文件已保留在 logs/ 目录")
            print("   - 数据库文件已保留")
            print("   - 重新启动: 在 ChatboxAI 中发送消息")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
