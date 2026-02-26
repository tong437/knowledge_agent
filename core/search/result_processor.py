"""
搜索结果处理与排序模块。
"""

from typing import List, Dict
from collections import defaultdict

from core.models import SearchResult, SearchResults, SearchOptions


class ResultProcessor:
    """
    根据多种条件处理和排序搜索结果。

    提供排序、过滤和分组搜索结果的功能。
    """

    @staticmethod
    def sort_results(
        results: List[SearchResult],
        sort_by: str = "relevance"
    ) -> List[SearchResult]:
        """
        按指定条件排序搜索结果。

        Args:
            results: 待排序的搜索结果列表
            sort_by: 排序条件（'relevance'、'date'、'title'）

        Returns:
            排序后的搜索结果列表
        """
        if sort_by == "relevance":
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
        elif sort_by == "date":
            return sorted(results, key=lambda r: r.item.updated_at, reverse=True)
        elif sort_by == "title":
            return sorted(results, key=lambda r: r.item.title.lower())
        else:
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    @staticmethod
    def filter_by_categories(
        results: List[SearchResult],
        include_categories: List[str] = None,
        exclude_categories: List[str] = None
    ) -> List[SearchResult]:
        """
        按分类包含/排除过滤结果。

        Args:
            results: 待过滤的搜索结果列表
            include_categories: 要包含的分类（空表示全部）
            exclude_categories: 要排除的分类

        Returns:
            过滤后的搜索结果列表
        """
        filtered = results

        if include_categories:
            filtered = [
                r for r in filtered
                if any(cat.name in include_categories for cat in r.item.categories)
            ]

        if exclude_categories:
            filtered = [
                r for r in filtered
                if not any(cat.name in exclude_categories for cat in r.item.categories)
            ]

        return filtered

    @staticmethod
    def filter_by_tags(
        results: List[SearchResult],
        include_tags: List[str] = None,
        exclude_tags: List[str] = None
    ) -> List[SearchResult]:
        """
        按标签包含/排除过滤结果。

        Args:
            results: 待过滤的搜索结果列表
            include_tags: 要包含的标签（空表示全部）
            exclude_tags: 要排除的标签

        Returns:
            过滤后的搜索结果列表
        """
        filtered = results

        if include_tags:
            filtered = [
                r for r in filtered
                if any(tag.name in include_tags for tag in r.item.tags)
            ]

        if exclude_tags:
            filtered = [
                r for r in filtered
                if not any(tag.name in exclude_tags for tag in r.item.tags)
            ]

        return filtered

    @staticmethod
    def filter_by_source_types(
        results: List[SearchResult],
        source_types: List[str]
    ) -> List[SearchResult]:
        """
        按来源类型过滤结果。

        Args:
            results: 待过滤的搜索结果列表
            source_types: 要包含的来源类型列表

        Returns:
            过滤后的搜索结果列表
        """
        if not source_types:
            return results

        return [
            r for r in results
            if r.item.source_type.value in source_types
        ]

    @staticmethod
    def filter_by_min_relevance(
        results: List[SearchResult],
        min_relevance: float
    ) -> List[SearchResult]:
        """
        按最低相关度分数过滤结果。

        Args:
            results: 待过滤的搜索结果列表
            min_relevance: 最低相关度阈值（0.0 到 1.0）

        Returns:
            过滤后的搜索结果列表
        """
        return [r for r in results if r.relevance_score >= min_relevance]

    @staticmethod
    def limit_results(
        results: List[SearchResult],
        max_results: int
    ) -> List[SearchResult]:
        """
        限制结果数量。

        Args:
            results: 待限制的搜索结果列表
            max_results: 最大返回结果数

        Returns:
            限制后的搜索结果列表
        """
        return results[:max_results]

    @staticmethod
    def group_by_category(
        results: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """
        按分类对搜索结果进行分组。

        Args:
            results: 待分组的搜索结果列表

        Returns:
            分类名称到结果列表的字典映射
        """
        grouped: Dict[str, List[SearchResult]] = defaultdict(list)

        for result in results:
            if result.item.categories:
                for category in result.item.categories:
                    grouped[category.name].append(result)
            else:
                grouped["Uncategorized"].append(result)

        return dict(grouped)

    @staticmethod
    def group_by_source_type(
        results: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """
        按来源类型对搜索结果进行分组。

        Args:
            results: 待分组的搜索结果列表

        Returns:
            来源类型到结果列表的字典映射
        """
        grouped: Dict[str, List[SearchResult]] = defaultdict(list)

        for result in results:
            source_type = result.item.source_type.value
            grouped[source_type].append(result)

        return dict(grouped)

    @staticmethod
    def apply_options(
        results: List[SearchResult],
        options: SearchOptions
    ) -> SearchResults:
        """
        应用搜索选项来处理和格式化结果。

        Args:
            results: 待处理的搜索结果列表
            options: 要应用的搜索选项

        Returns:
            处理后的 SearchResults 对象
        """
        results = ResultProcessor.filter_by_categories(
            results,
            options.include_categories,
            options.exclude_categories
        )

        results = ResultProcessor.filter_by_tags(
            results,
            options.include_tags,
            options.exclude_tags
        )

        results = ResultProcessor.filter_by_source_types(
            results,
            options.source_types
        )

        results = ResultProcessor.filter_by_min_relevance(
            results,
            options.min_relevance
        )

        results = ResultProcessor.sort_results(results, options.sort_by)

        grouped_results = None
        if options.group_by_category:
            grouped_results = ResultProcessor.group_by_category(results)

        results = ResultProcessor.limit_results(results, options.max_results)

        search_results = SearchResults(
            query="",
            results=results,
            total_found=len(results),
            grouped_results=grouped_results
        )

        return search_results

    @staticmethod
    def merge_results(
        keyword_results: List[SearchResult],
        semantic_results: List[SearchResult],
        keyword_weight: float = 0.5,
        semantic_weight: float = 0.5
    ) -> List[SearchResult]:
        """
        合并关键词搜索和语义搜索结果，使用加权评分。

        Args:
            keyword_results: 关键词搜索结果
            semantic_results: 语义搜索结果
            keyword_weight: 关键词搜索权重（0.0 到 1.0）
            semantic_weight: 语义搜索权重（0.0 到 1.0）

        Returns:
            合并并重新评分的搜索结果列表
        """
        combined_scores: Dict[str, tuple] = {}

        for result in keyword_results:
            item_id = result.item.id
            combined_scores[item_id] = (
                result,
                result.relevance_score * keyword_weight,
                set(result.matched_fields)
            )

        for result in semantic_results:
            item_id = result.item.id
            if item_id in combined_scores:
                existing_result, existing_score, existing_fields = combined_scores[item_id]
                new_score = existing_score + (result.relevance_score * semantic_weight)
                merged_fields = existing_fields.union(set(result.matched_fields))
                combined_scores[item_id] = (existing_result, new_score, merged_fields)
            else:
                combined_scores[item_id] = (
                    result,
                    result.relevance_score * semantic_weight,
                    set(result.matched_fields)
                )

        merged_results = []
        for result, score, fields in combined_scores.values():
            merged_result = SearchResult(
                item=result.item,
                relevance_score=min(score, 1.0),
                matched_fields=list(fields),
                highlights=result.highlights
            )
            merged_results.append(merged_result)

        merged_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return merged_results
