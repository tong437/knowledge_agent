#!/usr/bin/env python3
"""
一键运行所有任务7的测试
"""

import subprocess
import sys

def run_command(description, command):
    """运行命令并显示结果"""
    print("\n" + "=" * 70)
    print(f"🔍 {description}")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ 成功")
            # 合并stdout和stderr来查找成功标记
            output = result.stdout + result.stderr
            lines = output.split('\n')
            success_lines = [line for line in lines if '✅' in line or 'passed' in line or 'PASSED' in line]
            if success_lines:
                for line in success_lines[:5]:  # 只显示前5行
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ 失败 (退出码: {result.returncode})")
            # 查找实际的错误信息
            output = result.stdout + result.stderr
            error_lines = [line for line in output.split('\n') if 'Error' in line or 'Failed' in line or '❌' in line]
            if error_lines:
                for line in error_lines[:3]:
                    print(f"   {line.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def main():
    """主测试流程"""
    print("=" * 70)
    print("🚀 任务7 - MCP服务器接口测试套件")
    print("=" * 70)
    
    tests = [
        ("1. 运行单元测试", "python -m pytest knowledge_agent/tests/test_mcp_integration.py -v --tb=short"),
        ("2. 测试MCP工具功能", "python test_mcp_tools_manual.py"),
        ("3. 测试MCP资源功能", "python test_mcp_resources_manual.py"),
        ("4. 测试参数验证", "python test_parameter_validation.py"),
        ("5. 测试错误处理", "python test_error_handling.py"),
    ]
    
    results = []
    
    for description, command in tests:
        success = run_command(description, command)
        results.append((description, success))
    
    # 显示总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {description}")
    
    print("\n" + "=" * 70)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！任务7完成！")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
