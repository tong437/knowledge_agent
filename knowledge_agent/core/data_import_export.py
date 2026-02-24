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
from knowledge_agent.models.data_source import SourceType
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



class DataImportExport:
    """
    统一的数据导入导出接口。

    提供知识数据导入和导出的统一接口，
    与存储管理器集成实现无缝数据传输。
    """
    
    def __init__(self, storage_manager):
        """
        初始化数据导入导出处理器。
        
        Args:
            storage_manager: 用于数据访问的存储管理器实例
        """
        self.storage_manager = storage_manager
        self.exporter = DataExporter()
        self.importer = DataImporter()
    
    def export_to_json(self) -> Dict[str, Any]:
        """
        将所有知识数据导出为 JSON 格式。
        
        Returns:
            包含所有导出数据的字典
        """
        # 从存储中获取所有数据
        items = self.storage_manager.get_all_knowledge_items()
        categories = self.storage_manager.get_all_categories()
        tags = self.storage_manager.get_all_tags()
        
        # 获取所有关系
        relationships = []
        for item in items:
            item_relationships = self.storage_manager.get_relationships_for_item(item.id)
            relationships.extend(item_relationships)
        
        # 转换为字典
        items_data = []
        for item in items:
            item_dict = {
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'source_type': item.source_type.value if hasattr(item.source_type, 'value') else str(item.source_type),
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
                'relationship_type': rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type),
                'strength': rel.strength,
                'description': rel.description
            }
            for rel in relationships
        ]
        
        return {
            'version': '1.0',
            'export_date': datetime.now().isoformat(),
            'knowledge_items': items_data,
            'categories': categories_data,
            'tags': tags_data,
            'relationships': relationships_data
        }
    
    def import_from_json(
        self, data: Dict[str, Any], merge_strategy: str = "skip_existing"
    ) -> Dict[str, Any]:
        """
        从 JSON 格式导入知识数据，支持三种合并策略。

        Args:
            data: 包含待导入数据的字典
            merge_strategy: 合并策略，可选值：
                - "skip_existing"：已存在的条目跳过（默认）
                - "overwrite"：已存在的条目用导入数据完全覆盖
                - "merge"：已存在的条目合并分类和标签（取并集），内容保留较新的

        Returns:
            导入结果摘要字典，包含 new_count、skipped_count、
            overwritten_count、merged_count、error_count、errors

        Raises:
            DataImportError: 合并策略参数非法或数据验证失败时抛出
        """
        # 验证合并策略参数
        valid_strategies = ("skip_existing", "overwrite", "merge")
        if merge_strategy not in valid_strategies:
            raise DataImportError(
                f"Invalid merge_strategy '{merge_strategy}', "
                f"must be one of: {', '.join(valid_strategies)}"
            )

        # 验证导入数据格式
        errors = self.importer.validate_import_data(data)
        if errors:
            raise DataImportError(f"Data validation failed: {'; '.join(errors)}")

        # 初始化结果摘要
        result = {
            "new_count": 0,
            "skipped_count": 0,
            "overwritten_count": 0,
            "merged_count": 0,
            "error_count": 0,
            "errors": [],
        }

        # 获取导入条目列表，兼容 knowledge_items 和 items 两种键名
        items_data = data.get("knowledge_items", data.get("items", []))

        for item_data in items_data:
            try:
                item_id = item_data.get("id", "")
                if not item_id:
                    result["error_count"] += 1
                    result["errors"].append("Item missing 'id' field")
                    continue

                # 检查条目是否已存在
                existing_item = self.storage_manager.get_knowledge_item(item_id)

                if existing_item is None:
                    # 新条目：构造 KnowledgeItem 并存储
                    new_item = self._build_knowledge_item(item_data)
                    self.storage_manager.save_knowledge_item(new_item)
                    result["new_count"] += 1
                elif merge_strategy == "skip_existing":
                    result["skipped_count"] += 1
                elif merge_strategy == "overwrite":
                    # 用导入数据完全覆盖已有条目
                    updates = self._build_overwrite_updates(item_data)
                    self.storage_manager.update_knowledge_item(item_id, updates)
                    result["overwritten_count"] += 1
                elif merge_strategy == "merge":
                    # 合并：分类和标签取并集，内容保留较新的
                    updates = self._build_merge_updates(item_data, existing_item)
                    self.storage_manager.update_knowledge_item(item_id, updates)
                    result["merged_count"] += 1

            except Exception as e:
                result["error_count"] += 1
                item_id_str = item_data.get("id", "unknown")
                result["errors"].append(
                    f"Failed to process item '{item_id_str}': {e}"
                )

        return result

    def _parse_source_type(self, value: Any) -> SourceType:
        """
        将字符串或其他值转换为 SourceType 枚举。

        Args:
            value: 源类型值，可以是字符串或 SourceType 枚举

        Returns:
            对应的 SourceType 枚举值
        """
        if isinstance(value, SourceType):
            return value
        try:
            return SourceType(value)
        except (ValueError, KeyError):
            return SourceType.UNKNOWN

    def _build_knowledge_item(self, item_data: Dict[str, Any]) -> KnowledgeItem:
        """
        从字典数据构造 KnowledgeItem 对象。

        Args:
            item_data: 条目数据字典

        Returns:
            构造好的 KnowledgeItem 实例
        """
        # 解析分类列表
        categories = []
        for cat_data in item_data.get("categories", []):
            if isinstance(cat_data, dict):
                categories.append(Category.from_dict(cat_data))
            elif isinstance(cat_data, str):
                # 兼容仅存储分类名称的格式
                categories.append(Category(id=cat_data, name=cat_data, description=""))

        # 解析标签列表
        tags = []
        for tag_data in item_data.get("tags", []):
            if isinstance(tag_data, dict):
                tags.append(Tag.from_dict(tag_data))
            elif isinstance(tag_data, str):
                # 兼容仅存储标签名称的格式
                tags.append(Tag(id=tag_data, name=tag_data))

        # 解析时间戳
        created_at = datetime.now()
        if "created_at" in item_data and item_data["created_at"]:
            try:
                created_at = datetime.fromisoformat(item_data["created_at"])
            except (ValueError, TypeError):
                pass

        updated_at = datetime.now()
        if "updated_at" in item_data and item_data["updated_at"]:
            try:
                updated_at = datetime.fromisoformat(item_data["updated_at"])
            except (ValueError, TypeError):
                pass

        return KnowledgeItem(
            id=item_data["id"],
            title=item_data.get("title", ""),
            content=item_data.get("content", ""),
            source_type=self._parse_source_type(item_data.get("source_type", "unknown")),
            source_path=item_data.get("source_path", ""),
            categories=categories,
            tags=tags,
            metadata=item_data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            embedding=item_data.get("embedding"),
        )

    def _build_overwrite_updates(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建覆盖模式的更新字典，用导入数据完全替换所有字段。

        Args:
            item_data: 导入的条目数据字典

        Returns:
            用于 update_knowledge_item 的更新字典
        """
        updates: Dict[str, Any] = {}

        if "title" in item_data:
            updates["title"] = item_data["title"]
        if "content" in item_data:
            updates["content"] = item_data["content"]
        if "source_type" in item_data:
            updates["source_type"] = self._parse_source_type(item_data["source_type"])
        if "source_path" in item_data:
            updates["source_path"] = item_data["source_path"]
        if "metadata" in item_data:
            updates["metadata"] = item_data["metadata"]
        if "embedding" in item_data:
            updates["embedding"] = item_data["embedding"]

        # 解析分类
        if "categories" in item_data:
            categories = []
            for cat_data in item_data["categories"]:
                if isinstance(cat_data, dict):
                    categories.append(Category.from_dict(cat_data))
                elif isinstance(cat_data, str):
                    categories.append(Category(id=cat_data, name=cat_data, description=""))
            updates["categories"] = categories

        # 解析标签
        if "tags" in item_data:
            tags = []
            for tag_data in item_data["tags"]:
                if isinstance(tag_data, dict):
                    tags.append(Tag.from_dict(tag_data))
                elif isinstance(tag_data, str):
                    tags.append(Tag(id=tag_data, name=tag_data))
            updates["tags"] = tags

        # 更新时间戳
        updates["updated_at"] = datetime.now()

        return updates

    def _build_merge_updates(
        self, item_data: Dict[str, Any], existing_item: KnowledgeItem
    ) -> Dict[str, Any]:
        """
        构建合并模式的更新字典。

        合并规则：
        - 分类和标签取并集
        - 内容保留较新的（比较 updated_at）

        Args:
            item_data: 导入的条目数据字典
            existing_item: 已存在的知识条目

        Returns:
            用于 update_knowledge_item 的更新字典
        """
        updates: Dict[str, Any] = {}

        # 解析导入数据的 updated_at
        import_updated_at = None
        if "updated_at" in item_data and item_data["updated_at"]:
            try:
                import_updated_at = datetime.fromisoformat(item_data["updated_at"])
            except (ValueError, TypeError):
                pass

        # 比较时间戳，决定是否更新内容字段
        import_is_newer = (
            import_updated_at is not None
            and import_updated_at > existing_item.updated_at
        )

        if import_is_newer:
            # 导入数据较新，更新内容相关字段
            if "title" in item_data:
                updates["title"] = item_data["title"]
            if "content" in item_data:
                updates["content"] = item_data["content"]
            if "source_type" in item_data:
                updates["source_type"] = self._parse_source_type(item_data["source_type"])
            if "source_path" in item_data:
                updates["source_path"] = item_data["source_path"]
            if "metadata" in item_data:
                updates["metadata"] = item_data["metadata"]

        # 合并分类（取并集，基于 ID 去重）
        if "categories" in item_data:
            existing_cat_ids = {cat.id for cat in existing_item.categories}
            merged_categories = list(existing_item.categories)
            for cat_data in item_data["categories"]:
                if isinstance(cat_data, dict):
                    cat = Category.from_dict(cat_data)
                elif isinstance(cat_data, str):
                    cat = Category(id=cat_data, name=cat_data, description="")
                else:
                    continue
                if cat.id not in existing_cat_ids:
                    merged_categories.append(cat)
                    existing_cat_ids.add(cat.id)
            updates["categories"] = merged_categories

        # 合并标签（取并集，基于 ID 去重）
        if "tags" in item_data:
            existing_tag_ids = {tag.id for tag in existing_item.tags}
            merged_tags = list(existing_item.tags)
            for tag_data in item_data["tags"]:
                if isinstance(tag_data, dict):
                    tag = Tag.from_dict(tag_data)
                elif isinstance(tag_data, str):
                    tag = Tag(id=tag_data, name=tag_data)
                else:
                    continue
                if tag.id not in existing_tag_ids:
                    merged_tags.append(tag)
                    existing_tag_ids.add(tag.id)
            updates["tags"] = merged_tags

        # 更新时间戳
        updates["updated_at"] = datetime.now()

        return updates

