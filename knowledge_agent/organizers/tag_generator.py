"""
Tag generator implementation for automatic tag generation.
"""

import uuid
import re
from typing import List, Dict, Set, Tuple
from collections import Counter

from ..models import KnowledgeItem, Tag, Category
from ..interfaces import StorageManager


class TagGenerator:
    """
    Automatic tag generator for knowledge items.
    
    Generates relevant tags based on content analysis, categories,
    and keyword extraction with weight and relevance calculation.
    """
    
    def __init__(self, storage_manager: StorageManager, max_tags: int = 10):
        """
        Initialize the tag generator.
        
        Args:
            storage_manager: Storage manager for accessing existing tags
            max_tags: Maximum number of tags to generate per item
        """
        self.storage_manager = storage_manager
        self.max_tags = max_tags
        self._tag_cache: Dict[str, Tag] = {}
        self._load_existing_tags()
    
    def _load_existing_tags(self) -> None:
        """Load existing tags from storage into cache."""
        try:
            existing_tags = self.storage_manager.get_all_tags()
            for tag in existing_tags:
                self._tag_cache[tag.name.lower()] = tag
        except Exception as e:
            # If storage is not ready or empty, just start with empty cache
            self._tag_cache = {}
    
    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        Generate relevant tags for a knowledge item.
        
        Args:
            item: The knowledge item to generate tags for
            
        Returns:
            List[Tag]: List of generated tags with relevance
        """
        # Extract candidate tags from different sources
        content_tags = self._extract_tags_from_content(item.content)
        title_tags = self._extract_tags_from_content(item.title)
        category_tags = self._extract_tags_from_categories(item.categories)
        
        # Combine and weight tags
        tag_weights: Dict[str, float] = {}
        
        # Title tags have higher weight
        for tag, weight in title_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight * 2.0
        
        # Content tags
        for tag, weight in content_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight
        
        # Category-derived tags have medium weight
        for tag, weight in category_tags:
            tag_weights[tag] = tag_weights.get(tag, 0.0) + weight * 1.5
        
        # Sort by weight and select top tags
        sorted_tags = sorted(tag_weights.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:self.max_tags]
        
        # Create or retrieve Tag objects
        result_tags = []
        for tag_name, weight in top_tags:
            tag = self._get_or_create_tag(tag_name)
            result_tags.append(tag)
        
        return result_tags
    
    def _extract_tags_from_content(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract potential tags from text content.
        
        Args:
            text: Text to extract tags from
            
        Returns:
            List[Tuple[str, float]]: List of (tag_name, weight) tuples
        """
        # Tokenize and clean text
        text = text.lower()
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()
        
        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'when', 'where', 'which', 'who', 'how', 'why'
        }
        
        # Filter tokens
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Calculate TF scores
        total_tokens = len(tokens)
        if total_tokens == 0:
            return []
        
        # Extract multi-word phrases (bigrams)
        bigrams = []
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            if tokens[i] not in stop_words and tokens[i+1] not in stop_words:
                bigrams.append(bigram)
        
        bigram_counts = Counter(bigrams)
        
        # Combine single words and bigrams
        tag_candidates = []
        
        # Add significant single-word tags
        for token, count in token_counts.most_common(20):
            if count > 1 or (count == 1 and len(token) > 5):
                weight = count / total_tokens
                tag_candidates.append((token, weight))
        
        # Add significant bigrams
        for bigram, count in bigram_counts.most_common(10):
            if count > 1:
                weight = (count / len(bigrams)) * 1.5  # Bigrams get bonus weight
                tag_candidates.append((bigram, weight))
        
        return tag_candidates
    
    def _extract_tags_from_categories(self, categories: List[Category]) -> List[Tuple[str, float]]:
        """
        Extract tags from assigned categories.
        
        Args:
            categories: List of categories assigned to the item
            
        Returns:
            List[Tuple[str, float]]: List of (tag_name, weight) tuples
        """
        tags = []
        
        for category in categories:
            # Use category name as a tag
            tag_name = category.name.lower()
            weight = category.confidence
            tags.append((tag_name, weight))
            
            # Extract keywords from category description
            desc_words = category.description.lower().split()
            for word in desc_words:
                if len(word) > 4:  # Only meaningful words
                    tags.append((word, weight * 0.5))
        
        return tags
    
    def _get_or_create_tag(self, tag_name: str) -> Tag:
        """
        Get an existing tag or create a new one.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            Tag: The tag object
        """
        tag_name_lower = tag_name.lower()
        
        # Check cache first
        if tag_name_lower in self._tag_cache:
            tag = self._tag_cache[tag_name_lower]
            tag.increment_usage()
            self.storage_manager.save_tag(tag)
            return tag
        
        # Create new tag
        tag_id = f"tag_{uuid.uuid4().hex[:12]}"
        tag = Tag(
            id=tag_id,
            name=tag_name,
            color=self._assign_color(tag_name),
            usage_count=1
        )
        
        # Save to storage and cache
        self.storage_manager.save_tag(tag)
        self._tag_cache[tag_name_lower] = tag
        
        return tag
    
    def _assign_color(self, tag_name: str) -> str:
        """
        Assign a color to a tag based on its name.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            str: Hex color code
        """
        # Simple hash-based color assignment
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
        
        # Use hash of tag name to select color
        hash_value = sum(ord(c) for c in tag_name)
        color_index = hash_value % len(color_palette)
        
        return color_palette[color_index]
    
    def calculate_tag_relevance(self, tag: Tag, item: KnowledgeItem) -> float:
        """
        Calculate the relevance of a tag to a knowledge item.
        
        Args:
            tag: The tag to evaluate
            item: The knowledge item
            
        Returns:
            float: Relevance score between 0.0 and 1.0
        """
        text = f"{item.title} {item.content}".lower()
        tag_name = tag.name.lower()
        
        # Count occurrences
        occurrences = text.count(tag_name)
        
        # Calculate relevance based on frequency and position
        if occurrences == 0:
            return 0.0
        
        # Check if tag appears in title (higher relevance)
        in_title = tag_name in item.title.lower()
        title_bonus = 0.3 if in_title else 0.0
        
        # Calculate frequency score
        words = text.split()
        frequency_score = min(1.0, occurrences / len(words) * 100)
        
        # Combine scores
        relevance = (frequency_score * 0.7) + title_bonus
        
        return min(1.0, relevance)
    
    def merge_similar_tags(self, threshold: float = 0.8) -> Dict[str, str]:
        """
        Identify and merge similar tags.
        
        Args:
            threshold: Similarity threshold for merging (0.0 to 1.0)
            
        Returns:
            Dict[str, str]: Mapping of old tag names to new tag names
        """
        tags = list(self._tag_cache.values())
        merge_map = {}
        
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i+1:]:
                similarity = self._calculate_tag_similarity(tag1.name, tag2.name)
                
                if similarity >= threshold:
                    # Merge into the tag with higher usage
                    if tag1.usage_count >= tag2.usage_count:
                        merge_map[tag2.name] = tag1.name
                    else:
                        merge_map[tag1.name] = tag2.name
        
        return merge_map
    
    def _calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """
        Calculate similarity between two tag names.
        
        Args:
            tag1: First tag name
            tag2: Second tag name
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        tag1 = tag1.lower()
        tag2 = tag2.lower()
        
        # Exact match
        if tag1 == tag2:
            return 1.0
        
        # One contains the other
        if tag1 in tag2 or tag2 in tag1:
            return 0.9
        
        # Calculate Jaccard similarity on character sets
        set1 = set(tag1)
        set2 = set(tag2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
