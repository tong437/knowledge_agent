#!/usr/bin/env python3
"""
MCP Server 日志查看器
实时查看和分析日志
"""

import sys
import time
from pathlib import Path
from datetime import datetime


def tail_file(filepath, lines=50):
    """显示文件的最后 N 行"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()
            for line in content[-lines:]:
                print(line.rstrip())
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {filepath}")
        print("   请先启动服务器")
    except Exception as e:
        print(f"❌ 读取日志失败: {e}")


def follow_file(filepath):
    """实时跟踪日志文件（类似 tail -f）"""
    try:
        print(f"📋 实时跟踪日志: {filepath}")
        print("   按 Ctrl+C 停止")
        print("=" * 60)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        print("\n\n✅ 停止跟踪")
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {filepath}")
    except Exception as e:
        print(f"❌ 跟踪日志失败: {e}")


def filter_logs(filepath, level=None, keyword=None):
    """过滤日志"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                # 级别过滤
                if level and f"[{level}]" not in line:
                    continue
                
                # 关键词过滤
                if keyword and keyword.lower() not in line.lower():
                    continue
                
                print(line.rstrip())
                
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {filepath}")
    except Exception as e:
        print(f"❌ 过滤日志失败: {e}")


def show_stats(filepath):
    """显示日志统计"""
    try:
        stats = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'total': 0
        }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stats['total'] += 1
                for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                    if f"[{level}]" in line:
                        stats[level] += 1
                        break
        
        print("=" * 60)
        print("📊 日志统计")
        print("=" * 60)
        print(f"总行数: {stats['total']}")
        print(f"DEBUG:   {stats['DEBUG']}")
        print(f"INFO:    {stats['INFO']}")
        print(f"WARNING: {stats['WARNING']}")
        print(f"ERROR:   {stats['ERROR']}")
        print("=" * 60)
        
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {filepath}")
    except Exception as e:
        print(f"❌ 统计失败: {e}")


def main():
    """主函数"""
    log_file = Path("logs/mcp_server.log")
    
    print("=" * 60)
    print("📋 MCP Server 日志查看器")
    print("=" * 60)
    print()
    
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        print()
        print("请先启动服务器:")
        print("  python knowledge_agent_server.py --transport stdio --log-file logs/mcp_server.log")
        return
    
    print(f"📁 日志文件: {log_file}")
    print(f"📏 文件大小: {log_file.stat().st_size / 1024:.2f} KB")
    print(f"🕐 最后修改: {datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    while True:
        print("选项:")
        print("  1. 查看最后 50 行")
        print("  2. 查看最后 100 行")
        print("  3. 实时跟踪（tail -f）")
        print("  4. 只看 ERROR")
        print("  5. 只看 WARNING")
        print("  6. 搜索关键词")
        print("  7. 显示统计")
        print("  8. 退出")
        print()
        
        choice = input("请选择 (1-8): ").strip()
        print()
        
        if choice == '1':
            tail_file(log_file, 50)
        elif choice == '2':
            tail_file(log_file, 100)
        elif choice == '3':
            follow_file(log_file)
        elif choice == '4':
            filter_logs(log_file, level='ERROR')
        elif choice == '5':
            filter_logs(log_file, level='WARNING')
        elif choice == '6':
            keyword = input("输入搜索关键词: ").strip()
            if keyword:
                filter_logs(log_file, keyword=keyword)
        elif choice == '7':
            show_stats(log_file)
        elif choice == '8':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择")
        
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
