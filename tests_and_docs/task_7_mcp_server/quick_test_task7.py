#!/usr/bin/env python3
"""
快速验证任务7是否完成
"""

import sys

def test_imports():
    """测试1: 验证所有模块可以导入"""
    print("测试1: 验证模块导入...")
    try:
        from knowledge_agent.server import KnowledgeMCPServer
        from knowledge_agent.server.mcp_tools import register_knowledge_tools
        from knowledge_agent.server.mcp_resources import register_knowledge_resources
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_server_creation():
    """测试2: 验证服务器可以创建"""
    print("\n测试2: 验证服务器创建...")
    try:
        from knowledge_agent.server import KnowledgeMCPServer
        server = KnowledgeMCPServer("quick-test")
        print("✅ 服务器创建成功")
        return True
    except Exception as e:
        print(f"❌ 服务器创建失败: {e}")
        return False

def test_core_methods():
    """测试3: 验证核心方法存在"""
    print("\n测试3: 验证核心方法...")
    try:
        from knowledge_agent.server import KnowledgeMCPServer
        server = KnowledgeMCPServer("quick-test")
        core = server.knowledge_core
        
        # 检查所有必需的方法
        methods = [
            'get_knowledge_item',
            'list_knowledge_items',
            'organize_knowledge',
            'export_data',
            'import_data',
            'get_statistics'
        ]
        
        for method in methods:
            if not hasattr(core, method):
                print(f"❌ 缺少方法: {method}")
                return False
        
        print(f"✅ 所有{len(methods)}个核心方法存在")
        return True
    except Exception as e:
        print(f"❌ 方法检查失败: {e}")
        return False

def test_basic_operations():
    """测试4: 验证基本操作"""
    print("\n测试4: 验证基本操作...")
    try:
        from knowledge_agent.server import KnowledgeMCPServer
        from knowledge_agent.models import KnowledgeItem, SourceType
        from datetime import datetime
        
        server = KnowledgeMCPServer("quick-test")
        core = server.knowledge_core
        
        # 创建测试条目
        item = KnowledgeItem(
            id="quick-test-1",
            title="快速测试",
            content="这是一个快速测试条目",
            source_type=SourceType.DOCUMENT,
            source_path="/test/quick.txt",
            categories=[],
            tags=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存
        core._storage_manager.save_knowledge_item(item)
        
        # 获取
        retrieved = core.get_knowledge_item("quick-test-1")
        if not retrieved:
            print("❌ 无法获取保存的条目")
            return False
        
        # 列出
        items = core.list_knowledge_items(limit=10)
        if len(items) == 0:
            print("❌ 列表为空")
            return False
        
        # 统计
        stats = core.get_statistics()
        if stats['total_items'] == 0:
            print("❌ 统计信息错误")
            return False
        
        print("✅ 基本操作正常")
        return True
    except Exception as e:
        print(f"❌ 基本操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mcp_tools():
    """测试5: 验证MCP工具注册"""
    print("\n测试5: 验证MCP工具...")
    try:
        from knowledge_agent.server import KnowledgeMCPServer
        
        server = KnowledgeMCPServer("quick-test")
        
        # 检查服务器信息
        info = server.get_server_info()
        if 'capabilities' not in info:
            print("❌ 服务器信息不完整")
            return False
        
        print(f"✅ MCP工具注册成功")
        print(f"   服务器: {info['name']}")
        print(f"   版本: {info['version']}")
        print(f"   功能数: {len(info['capabilities'])}")
        return True
    except Exception as e:
        print(f"❌ MCP工具检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 任务7快速验证")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_server_creation,
        test_core_methods,
        test_basic_operations,
        test_mcp_tools
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 测试结果")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 任务7验证通过！")
        print("=" * 60)
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
