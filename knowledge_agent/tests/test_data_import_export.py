"""
测试数据导入导出功能

验证JSON格式的数据导入导出和数据完整性验证。
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from knowledge_agent.core.data_import_export import (
    DataExporter,
    DataImporter,
    DataExportError,
    DataImportError
)
from knowledge_agent.models.knowledge_item import KnowledgeItem
from knowledge_agent.models.category import Category
from knowledge_agent.models.tag import Tag
from knowledge_agent.models.relationship import Relationship


class TestDataExporter:
    """测试数据导出器"""
    
    def test_export_knowledge_items_basic(self, tmp_path):
        """测试基本的知识条目导出"""
        exporter = DataExporter()
        
        # 创建测试数据
        items = [
            KnowledgeItem(
                id="item1",
                title="Test Item 1",
                content="Content 1",
                source_type="document",
                source_path="/path/to/doc1.txt",
                categories=[Category(id="cat1", name="Category 1", description="", parent_id=None, confidence=0.9)],
                tags=[Tag(id="tag1", name="Tag 1", color="#FF0000", usage_count=1)],
                metadata={"key": "value"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            KnowledgeItem(
                id="item2",
                title="Test Item 2",
                content="Content 2",
                source_type="code",
                source_path="/path/to/code.py",
                categories=[],
                tags=[],
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # 导出
        output_file = tmp_path / "items.json"
        exporter.export_knowledge_items(items, output_file)
        
        # 验证文件存在
        assert output_file.exists()
        
        # 验证内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['version'] == '1.0'
        assert data['item_count'] == 2
        assert len(data['items']) == 2
        assert data['items'][0]['id'] == 'item1'
        assert data['items'][0]['title'] == 'Test Item 1'
        assert data['items'][1]['id'] == 'item2'
    
    def test_export_knowledge_items_without_metadata(self, tmp_path):
        """测试不包含元数据的导出"""
        exporter = DataExporter()
        
        items = [
            KnowledgeItem(
                id="item1",
                title="Test Item",
                content="Content",
                source_type="document",
                source_path="/path/to/doc.txt",
                categories=[],
                tags=[],
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        output_file = tmp_path / "items_no_meta.json"
        exporter.export_knowledge_items(items, output_file, include_metadata=False)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 不应包含时间戳
        assert 'created_at' not in data['items'][0]
        assert 'updated_at' not in data['items'][0]
    
    def test_export_categories(self, tmp_path):
        """测试分类导出"""
        exporter = DataExporter()
        
        categories = [
            Category(id="cat1", name="Category 1", description="Desc 1", parent_id=None, confidence=0.9),
            Category(id="cat2", name="Category 2", description="Desc 2", parent_id="cat1", confidence=0.8)
        ]
        
        output_file = tmp_path / "categories.json"
        exporter.export_categories(categories, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['category_count'] == 2
        assert len(data['categories']) == 2
        assert data['categories'][0]['name'] == 'Category 1'
        assert data['categories'][1]['parent_id'] == 'cat1'
    
    def test_export_tags(self, tmp_path):
        """测试标签导出"""
        exporter = DataExporter()
        
        tags = [
            Tag(id="tag1", name="Python", color="#3776AB", usage_count=10),
            Tag(id="tag2", name="AI", color="#FF6B6B", usage_count=5)
        ]
        
        output_file = tmp_path / "tags.json"
        exporter.export_tags(tags, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['tag_count'] == 2
        assert data['tags'][0]['name'] == 'Python'
        assert data['tags'][1]['usage_count'] == 5
    
    def test_export_relationships(self, tmp_path):
        """测试关联关系导出"""
        exporter = DataExporter()
        
        relationships = [
            Relationship(
                source_id="item1",
                target_id="item2",
                relationship_type="related",
                strength=0.8,
                description="Related items"
            )
        ]
        
        output_file = tmp_path / "relationships.json"
        exporter.export_relationships(relationships, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['relationship_count'] == 1
        assert data['relationships'][0]['source_id'] == 'item1'
        assert data['relationships'][0]['strength'] == 0.8
    
    def test_export_full_database(self, tmp_path):
        """测试完整数据库导出"""
        exporter = DataExporter()
        
        items = [
            KnowledgeItem(
                id="item1",
                title="Item 1",
                content="Content 1",
                source_type="document",
                source_path="/path/to/doc.txt",
                categories=[],
                tags=[],
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        categories = [Category(id="cat1", name="Cat 1", description="", parent_id=None, confidence=0.9)]
        tags = [Tag(id="tag1", name="Tag 1", color="#FF0000", usage_count=1)]
        relationships = [
            Relationship(
                source_id="item1",
                target_id="item2",
                relationship_type="related",
                strength=0.7,
                description="Test"
            )
        ]
        
        output_file = tmp_path / "full_db.json"
        exporter.export_full_database(items, categories, tags, relationships, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'statistics' in data
        assert data['statistics']['item_count'] == 1
        assert data['statistics']['category_count'] == 1
        assert data['statistics']['tag_count'] == 1
        assert data['statistics']['relationship_count'] == 1
        assert 'items' in data
        assert 'categories' in data
        assert 'tags' in data
        assert 'relationships' in data
    
    def test_export_empty_list(self, tmp_path):
        """测试导出空列表"""
        exporter = DataExporter()
        
        output_file = tmp_path / "empty.json"
        exporter.export_knowledge_items([], output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['item_count'] == 0
        assert len(data['items']) == 0


class TestDataImporter:
    """测试数据导入器"""
    
    def test_import_knowledge_items_basic(self, tmp_path):
        """测试基本的知识条目导入"""
        # 创建测试文件
        test_data = {
            'version': '1.0',
            'export_date': datetime.now().isoformat(),
            'item_count': 2,
            'items': [
                {
                    'id': 'item1',
                    'title': 'Test Item 1',
                    'content': 'Content 1',
                    'source_type': 'document',
                    'source_path': '/path/to/doc.txt',
                    'categories': ['Category 1'],
                    'tags': ['Tag 1'],
                    'metadata': {'key': 'value'}
                },
                {
                    'id': 'item2',
                    'title': 'Test Item 2',
                    'content': 'Content 2',
                    'source_type': 'code',
                    'source_path': '/path/to/code.py',
                    'categories': [],
                    'tags': [],
                    'metadata': {}
                }
            ]
        }
        
        input_file = tmp_path / "items.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # 导入
        importer = DataImporter()
        items = importer.import_knowledge_items(input_file)
        
        assert len(items) == 2
        assert items[0]['id'] == 'item1'
        assert items[0]['title'] == 'Test Item 1'
        assert items[1]['id'] == 'item2'
    
    def test_import_categories(self, tmp_path):
        """测试分类导入"""
        test_data = {
            'version': '1.0',
            'category_count': 2,
            'categories': [
                {'id': 'cat1', 'name': 'Category 1', 'description': 'Desc 1', 'parent_id': None, 'confidence': 0.9},
                {'id': 'cat2', 'name': 'Category 2', 'description': 'Desc 2', 'parent_id': 'cat1', 'confidence': 0.8}
            ]
        }
        
        input_file = tmp_path / "categories.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        categories = importer.import_categories(input_file)
        
        assert len(categories) == 2
        assert categories[0]['name'] == 'Category 1'
        assert categories[1]['parent_id'] == 'cat1'
    
    def test_import_tags(self, tmp_path):
        """测试标签导入"""
        test_data = {
            'version': '1.0',
            'tag_count': 2,
            'tags': [
                {'id': 'tag1', 'name': 'Python', 'color': '#3776AB', 'usage_count': 10},
                {'id': 'tag2', 'name': 'AI', 'color': '#FF6B6B', 'usage_count': 5}
            ]
        }
        
        input_file = tmp_path / "tags.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        tags = importer.import_tags(input_file)
        
        assert len(tags) == 2
        assert tags[0]['name'] == 'Python'
        assert tags[1]['usage_count'] == 5
    
    def test_import_relationships(self, tmp_path):
        """测试关联关系导入"""
        test_data = {
            'version': '1.0',
            'relationship_count': 1,
            'relationships': [
                {
                    'source_id': 'item1',
                    'target_id': 'item2',
                    'relationship_type': 'related',
                    'strength': 0.8,
                    'description': 'Related items'
                }
            ]
        }
        
        input_file = tmp_path / "relationships.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        relationships = importer.import_relationships(input_file)
        
        assert len(relationships) == 1
        assert relationships[0]['source_id'] == 'item1'
        assert relationships[0]['strength'] == 0.8
    
    def test_import_full_database(self, tmp_path):
        """测试完整数据库导入"""
        test_data = {
            'version': '1.0',
            'export_date': datetime.now().isoformat(),
            'statistics': {
                'item_count': 1,
                'category_count': 1,
                'tag_count': 1,
                'relationship_count': 1
            },
            'items': [
                {
                    'id': 'item1',
                    'title': 'Item 1',
                    'content': 'Content 1',
                    'source_type': 'document',
                    'source_path': '/path/to/doc.txt',
                    'categories': [],
                    'tags': [],
                    'metadata': {}
                }
            ],
            'categories': [
                {'id': 'cat1', 'name': 'Cat 1', 'description': '', 'parent_id': None, 'confidence': 0.9}
            ],
            'tags': [
                {'id': 'tag1', 'name': 'Tag 1', 'color': '#FF0000', 'usage_count': 1}
            ],
            'relationships': [
                {
                    'source_id': 'item1',
                    'target_id': 'item2',
                    'relationship_type': 'related',
                    'strength': 0.7,
                    'description': 'Test'
                }
            ]
        }
        
        input_file = tmp_path / "full_db.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        data = importer.import_full_database(input_file)
        
        assert 'items' in data
        assert 'categories' in data
        assert 'tags' in data
        assert 'relationships' in data
        assert len(data['items']) == 1
        assert len(data['categories']) == 1
        assert len(data['tags']) == 1
        assert len(data['relationships']) == 1
    
    def test_validate_import_data_valid(self):
        """测试有效数据的验证"""
        importer = DataImporter()
        
        valid_data = {
            'version': '1.0',
            'items': [
                {'id': 'item1', 'title': 'Title', 'content': 'Content'}
            ],
            'categories': [
                {'id': 'cat1', 'name': 'Category'}
            ],
            'tags': [
                {'id': 'tag1', 'name': 'Tag'}
            ],
            'relationships': [
                {'source_id': 'item1', 'target_id': 'item2'}
            ]
        }
        
        errors = importer.validate_import_data(valid_data)
        assert len(errors) == 0
    
    def test_validate_import_data_missing_version(self):
        """测试缺少版本字段的验证"""
        importer = DataImporter()
        
        invalid_data = {
            'items': []
        }
        
        errors = importer.validate_import_data(invalid_data)
        assert len(errors) > 0
        assert any('version' in error for error in errors)
    
    def test_validate_import_data_missing_item_fields(self):
        """测试缺少必需字段的知识条目"""
        importer = DataImporter()
        
        invalid_data = {
            'version': '1.0',
            'items': [
                {'id': 'item1'},  # 缺少 title 和 content
                {'title': 'Title', 'content': 'Content'}  # 缺少 id
            ]
        }
        
        errors = importer.validate_import_data(invalid_data)
        assert len(errors) > 0
        assert any('title' in error for error in errors)
        assert any('content' in error for error in errors)
        assert any('id' in error for error in errors)
    
    def test_validate_import_data_missing_category_fields(self):
        """测试缺少必需字段的分类"""
        importer = DataImporter()
        
        invalid_data = {
            'version': '1.0',
            'categories': [
                {'id': 'cat1'},  # 缺少 name
                {'name': 'Category'}  # 缺少 id
            ]
        }
        
        errors = importer.validate_import_data(invalid_data)
        assert len(errors) > 0
        assert any('name' in error and 'Category' in error for error in errors)
        assert any('id' in error and 'Category' in error for error in errors)
    
    def test_import_nonexistent_file(self):
        """测试导入不存在的文件"""
        importer = DataImporter()
        
        with pytest.raises(DataImportError) as exc_info:
            importer.import_knowledge_items("/nonexistent/file.json")
        
        assert "not found" in str(exc_info.value)
    
    def test_import_invalid_json(self, tmp_path):
        """测试导入无效的JSON文件"""
        input_file = tmp_path / "invalid.json"
        with open(input_file, 'w') as f:
            f.write("{ invalid json }")
        
        importer = DataImporter()
        
        with pytest.raises(DataImportError) as exc_info:
            importer.import_knowledge_items(input_file)
        
        assert "parse JSON" in str(exc_info.value)
    
    def test_import_with_validation_failure(self, tmp_path):
        """测试导入时验证失败"""
        test_data = {
            'version': '1.0',
            'items': [
                {'id': 'item1'}  # 缺少必需字段
            ]
        }
        
        input_file = tmp_path / "invalid_data.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        
        with pytest.raises(DataImportError) as exc_info:
            importer.import_knowledge_items(input_file, validate=True)
        
        assert "validation failed" in str(exc_info.value).lower()
    
    def test_import_without_validation(self, tmp_path):
        """测试跳过验证的导入"""
        test_data = {
            'version': '1.0',
            'items': [
                {'id': 'item1'}  # 缺少必需字段，但跳过验证
            ]
        }
        
        input_file = tmp_path / "data.json"
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        importer = DataImporter()
        items = importer.import_knowledge_items(input_file, validate=False)
        
        # 应该成功导入，即使数据不完整
        assert len(items) == 1
        assert items[0]['id'] == 'item1'


class TestRoundTrip:
    """测试导出后再导入的往返一致性"""
    
    def test_knowledge_items_round_trip(self, tmp_path):
        """测试知识条目的往返一致性"""
        exporter = DataExporter()
        importer = DataImporter()
        
        # 创建原始数据
        original_items = [
            KnowledgeItem(
                id="item1",
                title="Test Item",
                content="Test Content",
                source_type="document",
                source_path="/path/to/doc.txt",
                categories=[Category(id="cat1", name="Category", description="", parent_id=None, confidence=0.9)],
                tags=[Tag(id="tag1", name="Tag", color="#FF0000", usage_count=1)],
                metadata={"key": "value"},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # 导出
        export_file = tmp_path / "export.json"
        exporter.export_knowledge_items(original_items, export_file)
        
        # 导入
        imported_data = importer.import_knowledge_items(export_file)
        
        # 验证一致性
        assert len(imported_data) == len(original_items)
        assert imported_data[0]['id'] == original_items[0].id
        assert imported_data[0]['title'] == original_items[0].title
        assert imported_data[0]['content'] == original_items[0].content
        assert imported_data[0]['source_type'] == original_items[0].source_type
    
    def test_full_database_round_trip(self, tmp_path):
        """测试完整数据库的往返一致性"""
        exporter = DataExporter()
        importer = DataImporter()
        
        # 创建原始数据
        items = [
            KnowledgeItem(
                id="item1",
                title="Item",
                content="Content",
                source_type="document",
                source_path="/path",
                categories=[],
                tags=[],
                metadata={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        categories = [Category(id="cat1", name="Cat", description="", parent_id=None, confidence=0.9)]
        tags = [Tag(id="tag1", name="Tag", color="#FF0000", usage_count=1)]
        relationships = [
            Relationship(
                source_id="item1",
                target_id="item2",
                relationship_type="related",
                strength=0.8,
                description="Test"
            )
        ]
        
        # 导出
        export_file = tmp_path / "full_export.json"
        exporter.export_full_database(items, categories, tags, relationships, export_file)
        
        # 导入
        imported_data = importer.import_full_database(export_file)
        
        # 验证一致性
        assert len(imported_data['items']) == len(items)
        assert len(imported_data['categories']) == len(categories)
        assert len(imported_data['tags']) == len(tags)
        assert len(imported_data['relationships']) == len(relationships)
        
        assert imported_data['items'][0]['id'] == items[0].id
        assert imported_data['categories'][0]['id'] == categories[0].id
        assert imported_data['tags'][0]['id'] == tags[0].id
        assert imported_data['relationships'][0]['source_id'] == relationships[0].source_id
