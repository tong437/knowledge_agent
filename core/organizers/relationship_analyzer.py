"""
关系分析器实现，用于发现知识条目之间的关联。
"""

import re
import math
from typing import List, Dict, Set, Tuple
from collections import Counter

from core.models import KnowledgeItem, Relationship, RelationshipType, Category, Tag
from core.interfaces import StorageManager


class RelationshipAnalyzer:
    """
    知识条目关系分析器。

    使用文本相似度算法和内容分析来识别相关条目，
    构建知识图谱。
    """

    def __init__(self, storage_manager: StorageManager, similarity_threshold: float = 0.3):
        self.storage_manager = storage_manager
        self.similarity_threshold = similarity_threshold
        self._knowledge_graph: Dict[str, Set[str]] = {}

    def find_relationships(self, item: KnowledgeItem, max_relationships: int = 10) -> List[Relationship]:
        """
        发现知识条目与已有条目之间的关系。

        Args:
            item: 待分析关系的知识条目
            max_relationships: 返回的最大关系数量

        Returns:
            List[Relationship]: 发现的关系列表
        """
        all_items = self.storage_manager.get_all_knowledge_items()

        other_items = [i for i in all_items if i.id != item.id]

        if not other_items:
            return []

        similarities: List[Tuple[KnowledgeItem, float, RelationshipType]] = []

        for other_item in other_items:
            similarity, rel_type = self._calculate_similarity(item, other_item)

            if similarity >= self.similarity_threshold:
                similarities.append((other_item, similarity, rel_type))

        similarities.sort(key=lambda x: x[1], reverse=True)

        relationships = []
        for other_item, similarity, rel_type in similarities[:max_relationships]:
            relationship = Relationship(
                source_id=item.id,
                target_id=other_item.id,
                relationship_type=rel_type,
                strength=similarity,
                description=self._generate_relationship_description(item, other_item, rel_type)
            )
            relationships.append(relationship)

        return relationships

    def _calculate_similarity(self, item1: KnowledgeItem, item2: KnowledgeItem) -> Tuple[float, RelationshipType]:
        """计算两个知识条目之间的相似度。"""
        content_sim = self._cosine_similarity(item1.content, item2.content)
        title_sim = self._cosine_similarity(item1.title, item2.title)
        category_sim = self._category_similarity(item1.categories, item2.categories)
        tag_sim = self._tag_similarity(item1.tags, item2.tags)

        overall_similarity = (
            content_sim * 0.4 +
            title_sim * 0.2 +
            category_sim * 0.2 +
            tag_sim * 0.2
        )

        rel_type = self._determine_relationship_type(
            content_sim, title_sim, category_sim, tag_sim, item1, item2
        )

        return overall_similarity, rel_type

    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的余弦相似度。"""
        tokens1 = self._tokenize(text1.lower())
        tokens2 = self._tokenize(text2.lower())

        if not tokens1 or not tokens2:
            return 0.0

        tf1 = Counter(tokens1)
        tf2 = Counter(tokens2)

        all_terms = set(tf1.keys()).union(set(tf2.keys()))

        dot_product = sum(tf1.get(term, 0) * tf2.get(term, 0) for term in all_terms)
        magnitude1 = math.sqrt(sum(count ** 2 for count in tf1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in tf2.values()))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _tokenize(self, text: str) -> List[str]:
        """将文本分词。"""
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()

        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can'
        }

        return [t for t in tokens if len(t) > 2 and t not in stop_words]

    def _category_similarity(self, categories1: List[Category], categories2: List[Category]) -> float:
        """基于共享分类计算相似度（Jaccard 系数）。"""
        if not categories1 or not categories2:
            return 0.0

        cat_ids1 = {cat.id for cat in categories1}
        cat_ids2 = {cat.id for cat in categories2}

        intersection = len(cat_ids1.intersection(cat_ids2))
        union = len(cat_ids1.union(cat_ids2))

        if union == 0:
            return 0.0

        return intersection / union

    def _tag_similarity(self, tags1: List[Tag], tags2: List[Tag]) -> float:
        """基于共享标签计算相似度（Jaccard 系数）。"""
        if not tags1 or not tags2:
            return 0.0

        tag_names1 = {tag.name.lower() for tag in tags1}
        tag_names2 = {tag.name.lower() for tag in tags2}

        intersection = len(tag_names1.intersection(tag_names2))
        union = len(tag_names1.union(tag_names2))

        if union == 0:
            return 0.0

        return intersection / union

    def _determine_relationship_type(
        self,
        content_sim: float,
        title_sim: float,
        category_sim: float,
        tag_sim: float,
        item1: KnowledgeItem,
        item2: KnowledgeItem
    ) -> RelationshipType:
        """基于相似度模式判断关系类型。"""
        # 高内容相似度表示相似条目
        if content_sim > 0.7:
            return RelationshipType.SIMILAR

        # 高分类/标签相似度但较低内容相似度表示相关条目
        if (category_sim > 0.5 or tag_sim > 0.5) and content_sim < 0.7:
            return RelationshipType.RELATED

        # 检查内容中是否包含对另一条目的引用
        if self._contains_reference(item1.content, item2.title):
            return RelationshipType.REFERENCES

        # 检查时间关系（一个可能派生自另一个）
        if item1.created_at < item2.created_at and content_sim > 0.4:
            return RelationshipType.DERIVED_FROM

        return RelationshipType.RELATED

    def _contains_reference(self, content: str, title: str) -> bool:
        """检查内容中是否包含对指定标题的引用。"""
        content_lower = content.lower()
        title_lower = title.lower()

        if title_lower in content_lower:
            return True

        # 检查标题中的重要词汇是否出现在内容中
        title_words = [w for w in title_lower.split() if len(w) > 4]
        if len(title_words) >= 2:
            matches = sum(1 for word in title_words if word in content_lower)
            return matches >= len(title_words) * 0.7

        return False

    def _generate_relationship_description(
        self,
        item1: KnowledgeItem,
        item2: KnowledgeItem,
        rel_type: RelationshipType
    ) -> str:
        """生成关系的可读描述。"""
        descriptions = {
            RelationshipType.SIMILAR: f"Similar content to '{item2.title}'",
            RelationshipType.RELATED: f"Related to '{item2.title}'",
            RelationshipType.REFERENCES: f"References '{item2.title}'",
            RelationshipType.DERIVED_FROM: f"Derived from '{item2.title}'",
            RelationshipType.CONTRADICTS: f"Contradicts '{item2.title}'",
            RelationshipType.SUPPORTS: f"Supports '{item2.title}'",
            RelationshipType.CUSTOM: f"Connected to '{item2.title}'",
        }

        return descriptions.get(rel_type, f"Related to '{item2.title}'")

    def update_knowledge_graph(self, relationships: List[Relationship]) -> None:
        """
        使用新关系更新知识图谱。

        Args:
            relationships: 待添加到图谱的关系列表
        """
        for relationship in relationships:
            if relationship.source_id not in self._knowledge_graph:
                self._knowledge_graph[relationship.source_id] = set()

            self._knowledge_graph[relationship.source_id].add(relationship.target_id)

            # 双向关系需要添加反向连接
            if relationship.is_bidirectional():
                if relationship.target_id not in self._knowledge_graph:
                    self._knowledge_graph[relationship.target_id] = set()

                self._knowledge_graph[relationship.target_id].add(relationship.source_id)

            self.storage_manager.save_relationship(relationship)

    def get_related_items(self, item_id: str, max_depth: int = 2) -> List[str]:
        """
        获取与指定条目相关的所有条目（BFS 遍历知识图谱）。

        Args:
            item_id: 起始条目 ID
            max_depth: 图谱遍历的最大深度

        Returns:
            List[str]: 相关条目 ID 列表
        """
        if item_id not in self._knowledge_graph:
            return []

        visited = set()
        to_visit = [(item_id, 0)]
        related = []

        while to_visit:
            current_id, depth = to_visit.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            if current_id != item_id:
                related.append(current_id)

            if current_id in self._knowledge_graph:
                for neighbor_id in self._knowledge_graph[current_id]:
                    if neighbor_id not in visited:
                        to_visit.append((neighbor_id, depth + 1))

        return related

    def find_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """
        发现高度关联的知识条目聚类（连通分量）。

        Args:
            min_cluster_size: 聚类的最小条目数

        Returns:
            List[List[str]]: 聚类列表，每个聚类是条目 ID 列表
        """
        visited = set()
        clusters = []

        for item_id in self._knowledge_graph:
            if item_id in visited:
                continue

            cluster = []
            to_visit = [item_id]

            while to_visit:
                current_id = to_visit.pop(0)

                if current_id in visited:
                    continue

                visited.add(current_id)
                cluster.append(current_id)

                if current_id in self._knowledge_graph:
                    for neighbor_id in self._knowledge_graph[current_id]:
                        if neighbor_id not in visited:
                            to_visit.append(neighbor_id)

            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)

        return clusters
