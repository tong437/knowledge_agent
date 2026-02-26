"""
统一知识组织器实现。
"""

from typing import List

from core.models import KnowledgeItem, Category, Tag, Relationship
from core.interfaces import KnowledgeOrganizer, StorageManager
from .auto_classifier import AutoClassifier
from .tag_generator import TagGenerator
from .relationship_analyzer import RelationshipAnalyzer


class KnowledgeOrganizerImpl(KnowledgeOrganizer):
    """
    知识组织器接口的统一实现。

    将自动分类、标签生成和关系分析整合为
    一个完整的知识组织系统。
    """

    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.classifier = AutoClassifier(storage_manager)
        self.tag_generator = TagGenerator(storage_manager)
        self.relationship_analyzer = RelationshipAnalyzer(storage_manager)

    def classify(self, item: KnowledgeItem) -> List[Category]:
        """
        自动分类知识条目。

        Args:
            item: 待分类的知识条目

        Returns:
            List[Category]: 带置信度分数的分类列表
        """
        return self.classifier.classify(item)

    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        为知识条目生成相关标签。

        Args:
            item: 待生成标签的知识条目

        Returns:
            List[Tag]: 生成的标签列表
        """
        return self.tag_generator.generate_tags(item)

    def find_relationships(self, item: KnowledgeItem) -> List[Relationship]:
        """
        发现知识条目与已有条目之间的关系。

        Args:
            item: 待分析关系的知识条目

        Returns:
            List[Relationship]: 发现的关系列表
        """
        return self.relationship_analyzer.find_relationships(item)

    def update_knowledge_graph(self, relationships: List[Relationship]) -> None:
        """
        使用新关系更新知识图谱。

        Args:
            relationships: 待添加到图谱的关系列表
        """
        self.relationship_analyzer.update_knowledge_graph(relationships)

    def learn_from_user_feedback(
        self,
        item: KnowledgeItem,
        user_categories: List[Category],
        user_tags: List[Tag]
    ) -> None:
        """
        从用户反馈中学习，改进未来的分类效果。

        Args:
            item: 被修正的知识条目
            user_categories: 用户指定的分类
            user_tags: 用户指定的标签
        """
        self.classifier.learn_from_feedback(item, user_categories)

        item.categories = user_categories
        item.tags = user_tags

        self.storage_manager.save_knowledge_item(item)

    def organize_item(self, item: KnowledgeItem) -> KnowledgeItem:
        """
        完整组织一个知识条目（分类、打标签、发现关系）。

        Args:
            item: 待组织的知识条目

        Returns:
            KnowledgeItem: 已组织的条目（包含分类、标签和关系）
        """
        categories = self.classify(item)
        for category in categories:
            item.add_category(category)

        tags = self.generate_tags(item)
        for tag in tags:
            item.add_tag(tag)

        self.storage_manager.save_knowledge_item(item)

        relationships = self.find_relationships(item)
        self.update_knowledge_graph(relationships)

        return item
