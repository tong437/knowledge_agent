"""
数据导入导出模块

支持JSON格式的知识数据导入导出，实现数据完整性验证。
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict

from knowledge_agent.models.knowledge_item import KnowledgeItem
from knowledge_agent.models.category import Category
from knowledge_agent.models.tag import Tag
from knowledge_agent.models.relationship import Relationship
from knowledge_agent.core.exceptions import KnowledgeAgentError


class DataExportError(KnowledgeAgentError):
    """数据导出错误"""
    pass


class DataImportError(KnowledgeAgentError):
    """数据导入错误"""
    pass


class DataExporter:
    """数据导出器
    
    支持将知识库数据导出为JSON格式，包括知识条目、分类、标签和关联关系。
    """
    
    def __init__(self):
        """初始化数据导出器"""
        pass
    
    def export_knowledge_items(
        self,
        items: List[KnowledgeItem],
        output_path: Union[str, Path],
        include_metadata: bool = True
    ) -> None:
        """导出知识条目到JSON文件
        
        Args:
            items: 知识条目列表
            output_path: 输出文件路径
            include_metadata: 是否包含元数据（创建时间、更新时间等）
            
        Raises:
            DataExportError: 导出失败
        """
        try:
            output_path = Path(output_path)
            
            # 转换为可序列化的字典
            items_data = []
            for item in items:
                item_dict = {
                    'id': item.id,
                    'title': item.title,
                    'content': item.content,
                    'source_type': item.source_type,
                    'source_path': item.source_path,
                    'categories': [cat.name for cat in item.categories],
                    'tags': [tag.name for tag in item.tags],
                    'metadata': item.metadata
                }
                
                if include_metadata:
                    item_dict['created_at'] = item.created_at.isoformat() if item.created_at else None
                    item_dict['updated_at'] = item.updated_at.isoformat() if item.updated_at else None
                
                items_data.append(item_dict)
            
            # 创建导出数据结构
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'item_count': len(items),
                'items': items_data
            }
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DataExportError(f"Failed to export knowledge items: {e}")
    
    def export_categories(
        self,
        categories: List[Category],
        output_path: Union[str, Path]
    ) -> None:
        """导出分类到JSON文件
        
        Args:
            categories: 分类列表
            output_path: 输出文件路径
            
        Raises:
            DataExportError: 导出失败
        """
        try:
            output_path = Path(output_path)
            
            categories_data = []
            for cat in categories:
                cat_dict = {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'parent_id': cat.parent_id,
                    'confidence': cat.confidence
                }
                categories_data.append(cat_dict)
            
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'category_count': len(categories),
                'categories': categories_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DataExportError(f"Failed to export categories: {e}")
    
    def export_tags(
        self,
        tags: List[Tag],
        output_path: Union[str, Path]
    ) -> None:
        """导出标签到JSON文件
        
        Args:
            tags: 标签列表
            output_path: 输出文件路径
            
        Raises:
            DataExportError: 导出失败
        """
        try:
            output_path = Path(output_path)
            
            tags_data = []
            for tag in tags:
                tag_dict = {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'usage_count': tag.usage_count
                }
                tags_data.append(tag_dict)
            
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'tag_count': len(tags),
                'tags': tags_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DataExportError(f"Failed to export tags: {e}")
    
    def export_relationships(
        self,
        relationships: List[Relationship],
        output_path: Union[str, Path]
    ) -> None:
        """导出关联关系到JSON文件
        
        Args:
            relationships: 关联关系列表
            output_path: 输出文件路径
            
        Raises:
            DataExportError: 导出失败
        """
        try:
            output_path = Path(output_path)
            
            relationships_data = []
            for rel in relationships:
                rel_dict = {
                    'source_id': rel.source_id,
                    'target_id': rel.target_id,
                    'relationship_type': rel.relationship_type,
                    'strength': rel.strength,
                    'description': rel.description
                }
                relationships_data.append(rel_dict)
            
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'relationship_count': len(relationships),
                'relationships': relationships_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DataExportError(f"Failed to export relationships: {e}")
    
    def export_full_database(
        self,
        items: List[KnowledgeItem],
        categories: List[Category],
        tags: List[Tag],
        relationships: List[Relationship],
        output_path: Union[str, Path]
    ) -> None:
        """导出完整数据库到单个JSON文件
        
        Args:
            items: 知识条目列表
            categories: 分类列表
            tags: 标签列表
            relationships: 关联关系列表
            output_path: 输出文件路径
            
        Raises:
            DataExportError: 导出失败
        """
        try:
            output_path = Path(output_path)
            
            # 转换所有数据
            items_data = []
            for item in items:
                item_dict = {
                    'id': item.id,
                    'title': item.title,
                    'content': item.content,
                    'source_type': item.source_type,
                    'source_path': item.source_path,
                    'categories': [cat.name for cat in item.categories],
                    'tags': [tag.name for tag in item.tags],
                    'metadata': item.metadata,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None
                }
                items_data.append(item_dict)
            
            categories_data = [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'parent_id': cat.parent_id,
                    'confidence': cat.confidence
                }
                for cat in categories
            ]
            
            tags_data = [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'usage_count': tag.usage_count
                }
                for tag in tags
            ]
            
            relationships_data = [
                {
                    'source_id': rel.source_id,
                    'target_id': rel.target_id,
                    'relationship_type': rel.relationship_type,
                    'strength': rel.strength,
                    'description': rel.description
                }
                for rel in relationships
            ]
            
            # 创建完整导出数据
            export_data = {
                'version': '1.0',
                'export_date': datetime.now().isoformat(),
                'statistics': {
                    'item_count': len(items),
                    'category_count': len(categories),
                    'tag_count': len(tags),
                    'relationship_count': len(relationships)
                },
                'items': items_data,
                'categories': categories_data,
                'tags': tags_data,
                'relationships': relationships_data
            }
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise DataExportError(f"Failed to export full database: {e}")


class DataImporter:
    """数据导入器
    
    支持从JSON格式导入知识库数据，实现数据完整性验证。
    """
    
    def __init__(self):
        """初始化数据导入器"""
        pass
    
    def validate_import_data(self, data: Dict[str, Any]) -> List[str]:
        """验证导入数据的完整性
        
        Args:
            data: 导入的数据字典
            
        Returns:
            List[str]: 验证错误列表，如果为空则数据有效
        """
        errors = []
        
        # 检查版本
        if 'version' not in data:
            errors.append("Missing 'version' field")
        
        # 检查必需字段
        if 'items' in data:
            for idx, item in enumerate(data['items']):
                if 'id' not in item:
                    errors.append(f"Item {idx}: missing 'id' field")
                if 'title' not in item:
                    errors.append(f"Item {idx}: missing 'title' field")
                if 'content' not in item:
                    errors.append(f"Item {idx}: missing 'content' field")
        
        if 'categories' in data:
            for idx, cat in enumerate(data['categories']):
                if 'id' not in cat:
                    errors.append(f"Category {idx}: missing 'id' field")
                if 'name' not in cat:
                    errors.append(f"Category {idx}: missing 'name' field")
        
        if 'tags' in data:
            for idx, tag in enumerate(data['tags']):
                if 'id' not in tag:
                    errors.append(f"Tag {idx}: missing 'id' field")
                if 'name' not in tag:
                    errors.append(f"Tag {idx}: missing 'name' field")
        
        if 'relationships' in data:
            for idx, rel in enumerate(data['relationships']):
                if 'source_id' not in rel:
                    errors.append(f"Relationship {idx}: missing 'source_id' field")
                if 'target_id' not in rel:
                    errors.append(f"Relationship {idx}: missing 'target_id' field")
        
        return errors
    
    def import_knowledge_items(
        self,
        input_path: Union[str, Path],
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """从JSON文件导入知识条目
        
        Args:
            input_path: 输入文件路径
            validate: 是否验证数据完整性
            
        Returns:
            List[Dict[str, Any]]: 导入的知识条目数据列表
            
        Raises:
            DataImportError: 导入失败或数据验证失败
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                raise DataImportError(f"Import file not found: {input_path}")
            
            # 读取文件
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据
            if validate:
                errors = self.validate_import_data(data)
                if errors:
                    raise DataImportError(f"Data validation failed: {'; '.join(errors)}")
            
            # 返回知识条目数据
            return data.get('items', [])
            
        except json.JSONDecodeError as e:
            raise DataImportError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            if isinstance(e, DataImportError):
                raise
            raise DataImportError(f"Failed to import knowledge items: {e}")
    
    def import_categories(
        self,
        input_path: Union[str, Path],
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """从JSON文件导入分类
        
        Args:
            input_path: 输入文件路径
            validate: 是否验证数据完整性
            
        Returns:
            List[Dict[str, Any]]: 导入的分类数据列表
            
        Raises:
            DataImportError: 导入失败或数据验证失败
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                raise DataImportError(f"Import file not found: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate:
                errors = self.validate_import_data(data)
                if errors:
                    raise DataImportError(f"Data validation failed: {'; '.join(errors)}")
            
            return data.get('categories', [])
            
        except json.JSONDecodeError as e:
            raise DataImportError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            if isinstance(e, DataImportError):
                raise
            raise DataImportError(f"Failed to import categories: {e}")
    
    def import_tags(
        self,
        input_path: Union[str, Path],
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """从JSON文件导入标签
        
        Args:
            input_path: 输入文件路径
            validate: 是否验证数据完整性
            
        Returns:
            List[Dict[str, Any]]: 导入的标签数据列表
            
        Raises:
            DataImportError: 导入失败或数据验证失败
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                raise DataImportError(f"Import file not found: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate:
                errors = self.validate_import_data(data)
                if errors:
                    raise DataImportError(f"Data validation failed: {'; '.join(errors)}")
            
            return data.get('tags', [])
            
        except json.JSONDecodeError as e:
            raise DataImportError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            if isinstance(e, DataImportError):
                raise
            raise DataImportError(f"Failed to import tags: {e}")
    
    def import_relationships(
        self,
        input_path: Union[str, Path],
        validate: bool = True
    ) -> List[Dict[str, Any]]:
        """从JSON文件导入关联关系
        
        Args:
            input_path: 输入文件路径
            validate: 是否验证数据完整性
            
        Returns:
            List[Dict[str, Any]]: 导入的关联关系数据列表
            
        Raises:
            DataImportError: 导入失败或数据验证失败
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                raise DataImportError(f"Import file not found: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate:
                errors = self.validate_import_data(data)
                if errors:
                    raise DataImportError(f"Data validation failed: {'; '.join(errors)}")
            
            return data.get('relationships', [])
            
        except json.JSONDecodeError as e:
            raise DataImportError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            if isinstance(e, DataImportError):
                raise
            raise DataImportError(f"Failed to import relationships: {e}")
    
    def import_full_database(
        self,
        input_path: Union[str, Path],
        validate: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """从单个JSON文件导入完整数据库
        
        Args:
            input_path: 输入文件路径
            validate: 是否验证数据完整性
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 包含所有数据的字典
                - 'items': 知识条目列表
                - 'categories': 分类列表
                - 'tags': 标签列表
                - 'relationships': 关联关系列表
            
        Raises:
            DataImportError: 导入失败或数据验证失败
        """
        try:
            input_path = Path(input_path)
            
            if not input_path.exists():
                raise DataImportError(f"Import file not found: {input_path}")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate:
                errors = self.validate_import_data(data)
                if errors:
                    raise DataImportError(f"Data validation failed: {'; '.join(errors)}")
            
            return {
                'items': data.get('items', []),
                'categories': data.get('categories', []),
                'tags': data.get('tags', []),
                'relationships': data.get('relationships', [])
            }
            
        except json.JSONDecodeError as e:
            raise DataImportError(f"Failed to parse JSON file: {e}")
        except Exception as e:
            if isinstance(e, DataImportError):
                raise
            raise DataImportError(f"Failed to import full database: {e}")
