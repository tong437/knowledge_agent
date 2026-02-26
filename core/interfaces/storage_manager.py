"""
存储管理器接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from core.models import KnowledgeItem, Category, Tag, Relationship


class StorageManager(ABC):
    """
    知识存储管理器的抽象基类。

    定义知识条目及相关数据的存储、检索和管理接口。
    """

    @abstractmethod
    def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """
        保存知识条目到存储。

        Args:
            item: 待保存的知识条目
        """
        pass

    @abstractmethod
    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """
        根据 ID 检索知识条目。

        Args:
            item_id: 待检索条目的 ID

        Returns:
            Optional[KnowledgeItem]: 找到则返回条目，否则返回 None
        """
        pass

    @abstractmethod
    def get_all_knowledge_items(self) -> List[KnowledgeItem]:
        """
        检索存储中的所有知识条目。

        Returns:
            List[KnowledgeItem]: 所有已存储条目的列表
        """
        pass

    @abstractmethod
    def update_knowledge_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新知识条目的部分字段。

        支持部分字段更新，自动更新 updated_at 时间戳。

        Args:
            item_id: 知识条目 ID
            updates: 可更新字段字典，支持 title、content、categories、tags

        Returns:
            bool: 更新成功返回 True，条目不存在返回 False
        """
        pass

    @abstractmethod
    def delete_knowledge_item(self, item_id: str) -> bool:
        """
        从存储中删除知识条目。

        Args:
            item_id: 待删除条目的 ID

        Returns:
            bool: 删除成功返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def save_category(self, category: Category) -> None:
        """
        保存分类到存储。

        Args:
            category: 待保存的分类
        """
        pass

    @abstractmethod
    def get_all_categories(self) -> List[Category]:
        """
        检索所有分类。

        Returns:
            List[Category]: 所有分类的列表
        """
        pass

    @abstractmethod
    def save_tag(self, tag: Tag) -> None:
        """
        保存标签到存储。

        Args:
            tag: 待保存的标签
        """
        pass

    @abstractmethod
    def get_all_tags(self) -> List[Tag]:
        """
        检索所有标签。

        Returns:
            List[Tag]: 所有标签的列表
        """
        pass

    @abstractmethod
    def save_relationship(self, relationship: Relationship) -> None:
        """
        保存关系到存储。

        Args:
            relationship: 待保存的关系
        """
        pass

    @abstractmethod
    def get_relationships_for_item(self, item_id: str) -> List[Relationship]:
        """
        获取指定知识条目的所有关系。

        Args:
            item_id: 条目 ID

        Returns:
            List[Relationship]: 涉及该条目的关系列表
        """
        pass

    @abstractmethod
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        以指定格式导出所有数据。

        Args:
            format: 导出格式（json 等）

        Returns:
            Dict[str, Any]: 导出的数据
        """
        pass

    @abstractmethod
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        从字典导入数据。

        Args:
            data: 待导入的数据

        Returns:
            bool: 导入成功返回 True
        """
        pass
