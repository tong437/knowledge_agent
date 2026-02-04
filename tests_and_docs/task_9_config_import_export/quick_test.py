"""
任务9快速测试脚本

快速验证配置管理和数据导入导出功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from knowledge_agent.core.config_manager import ConfigManager
from knowledge_agent.core.data_import_export import DataImporter


def test_config_manager():
    """测试配置管理器"""
    print("=" * 60)
    print("测试 1: 配置管理器")
    print("=" * 60)
    
    config_path = Path(__file__).parent / "example_config.yaml"
    
    try:
        # 加载配置
        manager = ConfigManager(config_path)
        print(f"✓ 成功加载配置文件: {config_path}")
        
        # 获取配置
        config = manager.get_config()
        print(f"✓ 版本: {config.version}")
        
        # 获取搜索参数
        search = manager.get_search_parameters()
        print(f"✓ 搜索参数:")
        print(f"  - 最小相关度: {search.min_relevance}")
        print(f"  - 最大结果数: {search.max_results}")
        print(f"  - 语义搜索: {'启用' if search.enable_semantic else '禁用'}")
        
        # 获取自定义规则
        rules = manager.get_classification_rules()
        print(f"✓ 自定义分类规则: {len(rules)} 个")
        for rule in rules[:3]:
            print(f"  - {rule.name}: {rule.category} (优先级: {rule.priority})")
        
        # 验证配置
        errors = manager.validate()
        if errors:
            print(f"✗ 配置验证失败: {errors}")
            return False
        else:
            print(f"✓ 配置验证通过")
        
        print("\n✓ 配置管理器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n✗ 配置管理器测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_data_import():
    """测试数据导入"""
    print("=" * 60)
    print("测试 2: 数据导入")
    print("=" * 60)
    
    data_path = Path(__file__).parent / "example_knowledge_data.json"
    
    try:
        # 导入数据
        importer = DataImporter()
        print(f"正在导入: {data_path}")
        
        data = importer.import_full_database(data_path, validate=True)
        print(f"✓ 数据导入成功")
        
        # 显示统计
        print(f"✓ 数据统计:")
        print(f"  - 知识条目: {len(data['items'])} 个")
        print(f"  - 分类: {len(data['categories'])} 个")
        print(f"  - 标签: {len(data['tags'])} 个")
        print(f"  - 关联关系: {len(data['relationships'])} 个")
        
        # 显示第一个知识条目
        if data['items']:
            item = data['items'][0]
            print(f"\n✓ 第一个知识条目:")
            print(f"  - 标题: {item['title']}")
            print(f"  - ID: {item['id']}")
            print(f"  - 类型: {item['source_type']}")
            print(f"  - 分类: {', '.join(item['categories'])}")
            print(f"  - 标签: {', '.join(item['tags'])}")
        
        print("\n✓ 数据导入测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n✗ 数据导入测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("任务9 - 配置和扩展功能快速测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试配置管理器
    results.append(("配置管理器", test_config_manager()))
    
    # 测试数据导入
    results.append(("数据导入", test_data_import()))
    
    # 显示总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！任务9功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
