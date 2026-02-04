"""
数据导入功能演示脚本

演示如何使用DataImporter导入知识库数据
"""

import json
from pathlib import Path
from datetime import datetime

from knowledge_agent.core.data_import_export import DataImporter, DataExporter
from knowledge_agent.models.knowledge_item import KnowledgeItem
from knowledge_agent.models.category import Category
from knowledge_agent.models.tag import Tag
from knowledge_agent.models.relationship import Relationship


def create_sample_export_file():
    """创建示例导出文件用于测试导入"""
    print("=" * 60)
    print("步骤 1: 创建示例数据文件")
    print("=" * 60)
    
    # 创建示例数据
    sample_items = [
        KnowledgeItem(
            id="item_001",
            title="Python编程基础",
            content="Python是一种高级编程语言，具有简洁的语法和强大的功能。适合初学者学习，也适合专业开发。",
            source_type="document",
            source_path="/docs/python_basics.md",
            categories=[
                Category(id="cat_001", name="编程", description="编程相关知识", parent_id=None, confidence=0.95)
            ],
            tags=[
                Tag(id="tag_001", name="Python", color="#3776AB", usage_count=10),
                Tag(id="tag_002", name="编程语言", color="#FF6B6B", usage_count=5)
            ],
            metadata={"difficulty": "beginner", "language": "zh-CN"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        KnowledgeItem(
            id="item_002",
            title="机器学习入门",
            content="机器学习是人工智能的一个分支，通过算法让计算机从数据中学习模式。常见算法包括线性回归、决策树、神经网络等。",
            source_type="document",
            source_path="/docs/ml_intro.md",
            categories=[
                Category(id="cat_002", name="人工智能", description="AI相关知识", parent_id=None, confidence=0.92)
            ],
            tags=[
                Tag(id="tag_003", name="机器学习", color="#4CAF50", usage_count=15),
                Tag(id="tag_004", name="AI", color="#2196F3", usage_count=20)
            ],
            metadata={"difficulty": "intermediate", "language": "zh-CN"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        KnowledgeItem(
            id="item_003",
            title="数据结构与算法",
            content="数据结构是计算机存储、组织数据的方式。常见的数据结构包括数组、链表、栈、队列、树、图等。算法是解决问题的步骤。",
            source_type="document",
            source_path="/docs/data_structures.md",
            categories=[
                Category(id="cat_001", name="编程", description="编程相关知识", parent_id=None, confidence=0.90)
            ],
            tags=[
                Tag(id="tag_005", name="数据结构", color="#9C27B0", usage_count=8),
                Tag(id="tag_006", name="算法", color="#FF9800", usage_count=12)
            ],
            metadata={"difficulty": "intermediate", "language": "zh-CN"},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    sample_categories = [
        Category(id="cat_001", name="编程", description="编程相关知识", parent_id=None, confidence=0.95),
        Category(id="cat_002", name="人工智能", description="AI相关知识", parent_id=None, confidence=0.92),
        Category(id="cat_003", name="数据科学", description="数据科学相关知识", parent_id=None, confidence=0.88)
    ]
    
    sample_tags = [
        Tag(id="tag_001", name="Python", color="#3776AB", usage_count=10),
        Tag(id="tag_002", name="编程语言", color="#FF6B6B", usage_count=5),
        Tag(id="tag_003", name="机器学习", color="#4CAF50", usage_count=15),
        Tag(id="tag_004", name="AI", color="#2196F3", usage_count=20),
        Tag(id="tag_005", name="数据结构", color="#9C27B0", usage_count=8),
        Tag(id="tag_006", name="算法", color="#FF9800", usage_count=12)
    ]
    
    sample_relationships = [
        Relationship(
            source_id="item_001",
            target_id="item_003",
            relationship_type="related",
            strength=0.75,
            description="Python编程需要数据结构知识"
        ),
        Relationship(
            source_id="item_002",
            target_id="item_001",
            relationship_type="prerequisite",
            strength=0.85,
            description="机器学习需要Python基础"
        )
    ]
    
    # 导出数据
    exporter = DataExporter()
    export_path = Path("sample_knowledge_export.json")
    
    exporter.export_full_database(
        items=sample_items,
        categories=sample_categories,
        tags=sample_tags,
        relationships=sample_relationships,
        output_path=export_path
    )
    
    print(f"✓ 已创建示例数据文件: {export_path}")
    print(f"  - 知识条目: {len(sample_items)} 个")
    print(f"  - 分类: {len(sample_categories)} 个")
    print(f"  - 标签: {len(sample_tags)} 个")
    print(f"  - 关联关系: {len(sample_relationships)} 个")
    print()
    
    return export_path


def test_import_full_database(import_path):
    """测试导入完整数据库"""
    print("=" * 60)
    print("步骤 2: 导入完整数据库")
    print("=" * 60)
    
    importer = DataImporter()
    
    # 导入数据
    print(f"正在从 {import_path} 导入数据...")
    data = importer.import_full_database(import_path, validate=True)
    
    print(f"✓ 导入成功！")
    print()
    
    # 显示导入的数据统计
    print("导入数据统计:")
    print(f"  - 知识条目: {len(data['items'])} 个")
    print(f"  - 分类: {len(data['categories'])} 个")
    print(f"  - 标签: {len(data['tags'])} 个")
    print(f"  - 关联关系: {len(data['relationships'])} 个")
    print()
    
    return data


def display_imported_items(data):
    """显示导入的知识条目详情"""
    print("=" * 60)
    print("步骤 3: 查看导入的知识条目")
    print("=" * 60)
    
    for idx, item in enumerate(data['items'], 1):
        print(f"\n知识条目 {idx}:")
        print(f"  ID: {item['id']}")
        print(f"  标题: {item['title']}")
        print(f"  内容: {item['content'][:50]}..." if len(item['content']) > 50 else f"  内容: {item['content']}")
        print(f"  来源类型: {item['source_type']}")
        print(f"  来源路径: {item['source_path']}")
        print(f"  分类: {', '.join(item['categories'])}")
        print(f"  标签: {', '.join(item['tags'])}")
        print(f"  元数据: {item['metadata']}")


def display_imported_categories(data):
    """显示导入的分类"""
    print("\n" + "=" * 60)
    print("步骤 4: 查看导入的分类")
    print("=" * 60)
    
    for idx, cat in enumerate(data['categories'], 1):
        print(f"\n分类 {idx}:")
        print(f"  ID: {cat['id']}")
        print(f"  名称: {cat['name']}")
        print(f"  描述: {cat['description']}")
        print(f"  父分类ID: {cat['parent_id']}")
        print(f"  置信度: {cat['confidence']}")


def display_imported_tags(data):
    """显示导入的标签"""
    print("\n" + "=" * 60)
    print("步骤 5: 查看导入的标签")
    print("=" * 60)
    
    for idx, tag in enumerate(data['tags'], 1):
        print(f"\n标签 {idx}:")
        print(f"  ID: {tag['id']}")
        print(f"  名称: {tag['name']}")
        print(f"  颜色: {tag['color']}")
        print(f"  使用次数: {tag['usage_count']}")


def display_imported_relationships(data):
    """显示导入的关联关系"""
    print("\n" + "=" * 60)
    print("步骤 6: 查看导入的关联关系")
    print("=" * 60)
    
    for idx, rel in enumerate(data['relationships'], 1):
        print(f"\n关联关系 {idx}:")
        print(f"  源ID: {rel['source_id']}")
        print(f"  目标ID: {rel['target_id']}")
        print(f"  关系类型: {rel['relationship_type']}")
        print(f"  强度: {rel['strength']}")
        print(f"  描述: {rel['description']}")


def test_import_individual_files():
    """测试导入单独的文件"""
    print("\n" + "=" * 60)
    print("步骤 7: 测试导入单独的数据文件")
    print("=" * 60)
    
    # 创建单独的导出文件
    exporter = DataExporter()
    importer = DataImporter()
    
    # 测试知识条目导入
    items = [
        KnowledgeItem(
            id="test_001",
            title="测试条目",
            content="这是一个测试知识条目",
            source_type="document",
            source_path="/test.txt",
            categories=[],
            tags=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    items_path = Path("test_items_only.json")
    exporter.export_knowledge_items(items, items_path)
    
    print(f"\n✓ 创建了单独的知识条目文件: {items_path}")
    
    imported_items = importer.import_knowledge_items(items_path)
    print(f"✓ 成功导入 {len(imported_items)} 个知识条目")
    print(f"  第一个条目标题: {imported_items[0]['title']}")
    
    # 清理测试文件
    items_path.unlink()
    print(f"✓ 已清理测试文件")


def test_validation():
    """测试数据验证功能"""
    print("\n" + "=" * 60)
    print("步骤 8: 测试数据验证功能")
    print("=" * 60)
    
    # 创建无效数据
    invalid_data = {
        'version': '1.0',
        'items': [
            {'id': 'item1'},  # 缺少必需字段
            {'title': 'Test', 'content': 'Content'}  # 缺少id
        ]
    }
    
    invalid_path = Path("invalid_data.json")
    with open(invalid_path, 'w', encoding='utf-8') as f:
        json.dump(invalid_data, f)
    
    print(f"✓ 创建了包含无效数据的文件: {invalid_path}")
    
    importer = DataImporter()
    
    # 测试验证
    try:
        importer.import_knowledge_items(invalid_path, validate=True)
        print("✗ 验证失败：应该检测到错误但没有")
    except Exception as e:
        print(f"✓ 验证成功检测到错误:")
        print(f"  错误信息: {str(e)[:100]}...")
    
    # 清理测试文件
    invalid_path.unlink()
    print(f"✓ 已清理测试文件")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("知识管理智能体 - 数据导入功能演示")
    print("=" * 60)
    print()
    
    try:
        # 1. 创建示例数据文件
        export_path = create_sample_export_file()
        
        # 2. 导入完整数据库
        data = test_import_full_database(export_path)
        
        # 3. 显示导入的数据
        display_imported_items(data)
        display_imported_categories(data)
        display_imported_tags(data)
        display_imported_relationships(data)
        
        # 4. 测试单独文件导入
        test_import_individual_files()
        
        # 5. 测试数据验证
        test_validation()
        
        # 清理示例文件
        print("\n" + "=" * 60)
        print("清理测试文件")
        print("=" * 60)
        export_path.unlink()
        print(f"✓ 已删除示例文件: {export_path}")
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n所有导入功能测试通过！✓")
        
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
