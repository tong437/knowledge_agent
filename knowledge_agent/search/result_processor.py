"""
Search result processing and ranking functionality.
"""

from typing import List, Dict, Callable
from collections import defaultdict
from datetime import datetime

from ..models import SearchResult, SearchResults, SearchOptions, KnowledgeItem


class ResultProcessor:
    """
    Processes and ranks search results according to various criteria.
    
    Provides functionality for sorting, filtering, and grouping search results.
    """
    
    @staticmethod
    def sort_results(
        results: List[SearchResult],
        sort_by: str = "relevance"
    ) -> List[SearchResult]:
        """
        Sort search results by the specified criterion.
        
        Args:
            results: List of search results to sort
            sort_by: Sorting criterion ('relevance', 'date', 'title')
            
        Returns:
            Sorted list of search results
        """
        if sort_by == "relevance":
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
        elif sort_by == "date":
            return sorted(results, key=lambda r: r.item.updated_at, reverse=True)
        elif sort_by == "title":
            return sorted(results, key=lambda r: r.item.title.lower())
        else:
            # Default to relevance
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
    
    @staticmethod
    def filter_by_categories(
        results: List[SearchResult],
        include_categories: List[str] = None,
        exclude_categories: List[str] = None
    ) -> List[SearchResult]:
        """
        Filter results by category inclusion/exclusion.
        
        Args:
            results: List of search results to filter
            include_categories: Categories to include (empty means all)
            exclude_categories: Categories to exclude
            
        Returns:
            Filtered list of search results
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
        Filter results by tag inclusion/exclusion.
        
        Args:
            results: List of search results to filter
            include_tags: Tags to include (empty means all)
            exclude_tags: Tags to exclude
            
        Returns:
            Filtered list of search results
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
        Filter results by source type.
        
        Args:
            results: List of search results to filter
            source_types: List of source types to include
            
        Returns:
            Filtered list of search results
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
        Filter results by minimum relevance score.
        
        Args:
            results: List of search results to filter
            min_relevance: Minimum relevance threshold (0.0 to 1.0)
            
        Returns:
            Filtered list of search results
        """
        return [r for r in results if r.relevance_score >= min_relevance]
    
    @staticmethod
    def limit_results(
        results: List[SearchResult],
        max_results: int
    ) -> List[SearchResult]:
        """
        Limit the number of results.
        
        Args:
            results: List of search results to limit
            max_results: Maximum number of results to return
            
        Returns:
            Limited list of search results
        """
        return results[:max_results]
    
    @staticmethod
    def group_by_category(
        results: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """
        Group search results by category.
        
        Args:
            results: List of search results to group
            
        Returns:
            Dictionary mapping category names to lists of results
        """
        grouped: Dict[str, List[SearchResult]] = defaultdict(list)
        
        for result in results:
            if result.item.categories:
                # Add to each category the item belongs to
                for category in result.item.categories:
                    grouped[category.name].append(result)
            else:
                # Add to "Uncategorized" if no categories
                grouped["Uncategorized"].append(result)
        
        return dict(grouped)
    
    @staticmethod
    def group_by_source_type(
        results: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """
        Group search results by source type.
        
        Args:
            results: List of search results to group
            
        Returns:
            Dictionary mapping source types to lists of results
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
        Apply search options to process and format results.
        
        Args:
            results: List of search results to process
            options: Search options to apply
            
        Returns:
            Processed SearchResults object
        """
        # Filter by categories
        results = ResultProcessor.filter_by_categories(
            results,
            options.include_categories,
            options.exclude_categories
        )
        
        # Filter by tags
        results = ResultProcessor.filter_by_tags(
            results,
            options.include_tags,
            options.exclude_tags
        )
        
        # Filter by source types
        results = ResultProcessor.filter_by_source_types(
            results,
            options.source_types
        )
        
        # Filter by minimum relevance
        results = ResultProcessor.filter_by_min_relevance(
            results,
            options.min_relevance
        )
        
        # Sort results
        results = ResultProcessor.sort_results(results, options.sort_by)
        
        # Group by category if requested
        grouped_results = None
        if options.group_by_category:
            grouped_results = ResultProcessor.group_by_category(results)
        
        # Limit results
        results = ResultProcessor.limit_results(results, options.max_results)
        
        # Create SearchResults object
        search_results = SearchResults(
            query="",  # Will be set by the search engine
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
        Merge keyword and semantic search results with weighted scoring.
        
        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search
            keyword_weight: Weight for keyword search scores (0.0 to 1.0)
            semantic_weight: Weight for semantic search scores (0.0 to 1.0)
            
        Returns:
            Merged and re-scored list of search results
        """
        # Create a dictionary to track combined scores
        combined_scores: Dict[str, tuple] = {}
        
        # Add keyword results
        for result in keyword_results:
            item_id = result.item.id
            combined_scores[item_id] = (
                result,
                result.relevance_score * keyword_weight,
                set(result.matched_fields)
            )
        
        # Add or merge semantic results
        for result in semantic_results:
            item_id = result.item.id
            if item_id in combined_scores:
                # Merge scores
                existing_result, existing_score, existing_fields = combined_scores[item_id]
                new_score = existing_score + (result.relevance_score * semantic_weight)
                merged_fields = existing_fields.union(set(result.matched_fields))
                combined_scores[item_id] = (existing_result, new_score, merged_fields)
            else:
                # Add new result
                combined_scores[item_id] = (
                    result,
                    result.relevance_score * semantic_weight,
                    set(result.matched_fields)
                )
        
        # Create merged results with updated scores
        merged_results = []
        for result, score, fields in combined_scores.values():
            merged_result = SearchResult(
                item=result.item,
                relevance_score=min(score, 1.0),  # Cap at 1.0
                matched_fields=list(fields),
                highlights=result.highlights
            )
            merged_results.append(merged_result)
        
        # Sort by combined score
        merged_results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return merged_results
