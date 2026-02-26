"""
自动标签生成器实现。
"""

import uuid
import re
from typing import List, Dict, Set, Tuple
from collections import Counter

from core.models import KnowledgeItem, Tag, Category
from core.interfaces import StorageManager


class TagGenerator:
    """
    知识条目自动标签生成器。

    基于内容分析、分类信息和关键词提取，
    生成带权重和相关性的标签。
    """

    def __init__(self, storage_manager: StorageManager, max_tags: int = 10):
        self.storage_manager = storage_manager
        self.max_tags = max_tags
        self._tag_cache: Dict[str, Tag] = {}
        self._load_existing_tags()

    def _load_existing_tags(self) -> None:
        """从存储中加载已有标签到缓存。"""
        try:
            existing_tags = self.storage_manager.get_all_tags()
            for tag in existing_tags:
                self._tag_cache[tag.name.lower()] = tag
        except Exception:
            self._tag_cache = {}

    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        为知识条目生成相关标签。

        Args:
            item: 待生成标签的知识条目

        Returns:
            List[Tag]: 生成的标签列表
        """
        content_tags = self._extract_tags_from_content(item.content)
        title_tags = self._extract_tags_from_content(item.title)
        category_tags = self._extract_tags_from_categories(item.categories)

        # 合并并加权标签
        tag_weights: Dict[str, float] = {}

        # 标题标签权重更高
        for tag, weight in title_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight * 2.0

        for tag, weight in content_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight

        # 分类衍生标签中等权重
        for tag, weight in category_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight * 1.5

        sorted_tags = sorted(tag_weights.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:self.max_tags]

        result_tags = []
        for tag_name, weight in top_tags:
            tag = self._get_or_create_tag(tag_name)
            result_tags.append(tag)

        return result_tags

    def _extract_tags_from_content(self, text: str) -> List[Tuple[str, float]]:
        """从文本内容中提取候选标签。"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()

        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'when', 'where', 'which', 'who', 'how', 'why'
        }

        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]

        token_counts = Counter(tokens)

        total_tokens = len(tokens)
        if total_tokens == 0:
            return []

        # 提取二元词组
        bigrams = []
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            if tokens[i] not in stop_words and tokens[i+1] not in stop_words:
                bigrams.append(bigram)

        bigram_counts = Counter(bigrams)

        tag_candidates = []

        for token, count in token_counts.most_common(20):
            if count > 1 or (count == 1 and len(token) > 5):
                weight = count / total_tokens
                tag_candidates.append((token, weight))

        for bigram, count in bigram_counts.most_common(10):
            if count > 1:
                weight = (count / len(bigrams)) * 1.5
                tag_candidates.append((bigram, weight))

        return tag_candidates

    def _extract_tags_from_categories(self, categories: List[Category]) -> List[Tuple[str, float]]:
        """从已分配的分类中提取标签。"""
        tags = []

        for category in categories:
            tag_name = category.name.lower()
            weight = category.confidence
            tags.append((tag_name, weight))

            desc_words = category.description.lower().split()
            for word in desc_words:
                if len(word) > 4:
                    tags.append((word, weight * 0.5))

        return tags

    def _get_or_create_tag(self, tag_name: str) -> Tag:
        """获取已有标签或创建新标签。"""
        tag_name_lower = tag_name.lower()

        if tag_name_lower in self._tag_cache:
            tag = self._tag_cache[tag_name_lower]
            tag.increment_usage()
            self.storage_manager.save_tag(tag)
            return tag

        tag_id = f"tag_{uuid.uuid4().hex[:12]}"
        tag = Tag(
            id=tag_id,
            name=tag_name,
            color=self._assign_color(tag_name),
            usage_count=1
        )

        self.storage_manager.save_tag(tag)
        self._tag_cache[tag_name_lower] = tag

        return tag

    def _assign_color(self, tag_name: str) -> str:
        """基于标签名称哈希分配颜色。"""
        color_palette = [
            "#007bff",  # Blue
            "#28a745",  # Green
            "#dc3545",  # Red
            "#ffc107",  # Yellow
            "#17a2b8",  # Cyan
            "#6610f2",  # Purple
            "#e83e8c",  # Pink
            "#fd7e14",  # Orange
            "#20c997",  # Teal
            "#6c757d",  # Gray
        ]

        hash_value = sum(ord(c) for c in tag_name)
        color_index = hash_value % len(color_palette)

        return color_palette[color_index]

    def calculate_tag_relevance(self, tag: Tag, item: KnowledgeItem) -> float:
        """
        计算标签与知识条目的相关性。

        综合考虑标签在标题和内容中的出现频率。

        Args:
            tag: 待评估的标签
            item: 知识条目

        Returns:
            float: 0.0 到 1.0 之间的相关性分数
        """
        text = f"{item.title} {item.content}".lower()
        tag_name = tag.name.lower()

        occurrences = text.count(tag_name)

        if occurrences == 0:
            return 0.0

        in_title = tag_name in item.title.lower()
        title_bonus = 0.3 if in_title else 0.0

        words = text.split()
        frequency_score = min(1.0, occurrences / len(words) * 100)

        relevance = (frequency_score * 0.7) + title_bonus

        return min(1.0, relevance)

    def merge_similar_tags(self, threshold: float = 0.8) -> Dict[str, str]:
        """
        识别并合并相似标签。

        Args:
            threshold: 合并的相似度阈值（0.0 到 1.0）

        Returns:
            Dict[str, str]: 旧标签名到新标签名的映射
        """
        tags = list(self._tag_cache.values())
        merge_map = {}

        for i, tag1 in enumerate(tags):
            for tag2 in tags[i+1:]:
                similarity = self._calculate_tag_similarity(tag1.name, tag2.name)

                if similarity >= threshold:
                    if tag1.usage_count >= tag2.usage_count:
                        merge_map[tag2.name] = tag1.name
                    else:
                        merge_map[tag1.name] = tag2.name

        return merge_map

    def _calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """计算两个标签名称的相似度。"""
        tag1 = tag1.lower()
        tag2 = tag2.lower()

        if tag1 == tag2:
            return 1.0

        if tag1 in tag2 or tag2 in tag1:
            return 0.9

        # 基于字符集的 Jaccard 相似度
        set1 = set(tag1)
        set2 = set(tag2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union
