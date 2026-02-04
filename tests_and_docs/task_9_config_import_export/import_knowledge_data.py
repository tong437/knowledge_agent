"""
知识数据导入工具

使用方法:
    python import_knowledge_data.py <json文件路径>

示例:
    python import_knowledge_data.py my_knowledge.json
"""

import sys
import json
from pathlib import Path
from knowledge_agent.core.data_import_export import DataImporter, DataImportError


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def import_and_display(file_path):
    """导入并显示数据"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"✗ 错误: 文件不存在 - {file_path}")
        return False
    
    print_header("知识数据导入工具")
    print(f"文件路径: {file_path}")
    print()
    
    try:
        importer = DataImporter()
        
        # 先验证数据
        print("正在验证数据...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        errors = importer.validate_import_data(data)
        
        if errors:
            print(f"✗ 数据验证失败，发现 {len(errors)} 个错误:")
            for error in errors[:5]:  # 只显示前5个错误
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... 还有 {len(errors) - 5} 个错误")
            print()
            
            response = input("是否继续导入（跳过验证）？(y/n): ")
            if response.lower() != 'y':
                print("已取消导入")
                return False
            
            validate = False
        else:
            print("✓ 数据验证通过")
            validate = True
        
        # 导入数据
        print("\n正在导入数据...")
        imported_data = importer.import_full_database(file_path, validate=validate)
        
        print_header("导入成功！")
        
        # 显示统计信息
        print("\n数据统计:")
        print(f"  知识条目: {len(imported_data['items'])} 个")
        print(f"  分类: {len(imported_data['categories'])} 个")
        print(f"  标签: {len(imported_data['tags'])} 个")
        print(f"  关联关系: {len(imported_data['relationships'])} 个")
        
        # 显示知识条目预览
        if imported_data['items']:
            print_header("知识条目预览（前3个）")
            for idx, item in enumerate(imported_data['items'][:3], 1):
                print(f"\n{idx}. {item['title']}")
                print(f"   ID: {item['id']}")
                print(f"   类型: {item['source_type']}")
                content_preview = item['content'][:80] + "..." if len(item['content']) > 80 else item['content']
                print(f"   内容: {content_preview}")
                if item['categories']:
                    print(f"   分类: {', '.join(item['categories'])}")
                if item['tags']:
                    print(f"   标签: {', '.join(item['tags'])}")
        
        # 显示分类预览
        if imported_data['categories']:
            print_header("分类列表")
            for cat in imported_data['categories']:
                print(f"  - {cat['name']}: {cat['description']}")
        
        # 显示标签预览
        if imported_data['tags']:
            print_header("标签列表")
            tag_names = [tag['name'] for tag in imported_data['tags']]
            print(f"  {', '.join(tag_names)}")
        
        # 显示关联关系预览
        if imported_data['relationships']:
            print_header("关联关系")
            for rel in imported_data['relationships']:
                print(f"  {rel['source_id']} --[{rel['relationship_type']}]--> {rel['target_id']}")
                print(f"    强度: {rel['strength']}, 描述: {rel['description']}")
        
        print_header("导入完成")
        print("\n提示: 导入的数据已加载到内存中。")
        print("如需将数据保存到数据库，请使用存储管理器的相关功能。")
        
        return True
        
    except DataImportError as e:
        print(f"\n✗ 导入失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON解析失败: {e}")
        print("请确保文件是有效的JSON格式")
        return False
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage():
    """显示使用说明"""
    print("""
知识数据导入工具
================

使用方法:
    python import_knowledge_data.py <json文件路径>

示例:
    python import_knowledge_data.py my_knowledge.json
    python import_knowledge_data.py data/export_2024.json

支持的数据格式:
    - 完整数据库导出文件（包含items, categories, tags, relationships）
    - 单独的知识条目文件
    - 单独的分类文件
    - 单独的标签文件
    - 单独的关联关系文件

数据文件示例结构:
{
    "version": "1.0",
    "export_date": "2024-01-01T00:00:00",
    "items": [
        {
            "id": "item1",
            "title": "标题",
            "content": "内容",
            "source_type": "document",
            "source_path": "/path/to/file",
            "categories": ["分类1"],
            "tags": ["标签1", "标签2"],
            "metadata": {}
        }
    ],
    "categories": [...],
    "tags": [...],
    "relationships": [...]
}
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if file_path in ['-h', '--help', 'help']:
        show_usage()
        sys.exit(0)
    
    success = import_and_display(file_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
