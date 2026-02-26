"""
知识组织器接口。
"""

from abc import ABC, abstractmethod
from typing import List
from core.models import KnowledgeItem, Category, Tag, Relationship


class KnowledgeOrganizer(ABC):
    """
    知识组织器的抽象基类。

    定义知识条目的自动分类、标签生成和关系分析接口。
    """

    @abstractmethod
    def classify(self, item: KnowledgeItem) -> List[Category]:
        """
        自动分类知识条目。

        Args:
            item: 待分类的知识条目

        Returns:
            List[Category]: 带置信度分数的分类列表
        """
        pass

    @abstractmethod
    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        为知识条目生成相关标签。

        Args:
            item: 待生成标签的知识条目

        Returns:
            List[Tag]: 生成的标签列表
        """
        pass

    @abstractmethod
    def find_relationships(self, item: KnowledgeItem) -> List[Relationship]:
        """
        发现知识条目与已有条目之间的关系。

        Args:
            item: 待分析关系的知识条目

        Returns:
            List[Relationship]: 发现的关系列表
        """
        pass

    @abstractmethod
    def update_knowledge_graph(self, relationships: List[Relationship]) -> None:
        """
        使用新关系更新知识图谱。

        Args:
            relationships: 待添加到图谱的关系列表
        """
        pass

    @abstractmethod
    def learn_from_user_feedback(self, item: KnowledgeItem,
                                user_categories: List[Category],
                                user_tags: List[Tag]) -> None:
        """
        从用户反馈中学习，改进未来的分类效果。

        Args:
            item: 被修正的知识条目
            user_categories: 用户指定的分类
            user_tags: 用户指定的标签
        """
        pass
