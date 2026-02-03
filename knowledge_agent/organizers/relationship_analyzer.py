"""
Relationship analyzer implementation for finding connections between knowledge items.
"""

import re
import math
from typing import List, Dict, Set, Tuple
from collections import Counter

from ..models import KnowledgeItem, Relationship, RelationshipType, Category, Tag
from ..interfaces import StorageManager


class RelationshipAnalyzer:
    """
    Analyzer for discovering relationships between knowledge items.
    
    Uses text similarity algorithms and content analysis to identify
    related items and build the knowledge graph.
    """
    
    def __init__(self, storage_manager: StorageManager, similarity_threshold: float = 0.3):
        """
        Initialize the relationship analyzer.
        
        Args:
            storage_manager: Storage manager for accessing knowledge items
            similarity_threshold: Minimum similarity score for creating relationships
        """
        self.storage_manager = storage_manager
        self.similarity_threshold = similarity_threshold
        self._knowledge_graph: Dict[str, Set[str]] = {}
    
    def find_relationships(self, item: KnowledgeItem, max_relationships: int = 10) -> List[Relationship]:
        """
        Find relationships between a knowledge item and existing items.
        
        Args:
            item: The knowledge item to find relationships for
            max_relationships: Maximum number of relationships to return
            
        Returns:
            List[Relationship]: List of discovered relationships
        """
        all_items = self.storage_manager.get_all_knowledge_items()
        
        # Filter out the item itself
        other_items = [i for i in all_items if i.id != item.id]
        
        if not other_items:
            return []
        
        # Calculate similarities with all other items
        similarities: List[Tuple[KnowledgeItem, float, RelationshipType]] = []
        
        for other_item in other_items:
            similarity, rel_type = self._calculate_similarity(item, other_item)
            
            if similarity >= self.similarity_threshold:
                similarities.append((other_item, similarity, rel_type))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Create relationships for top matches
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
        """
        Calculate similarity between two knowledge items.
        
        Args:
            item1: First knowledge item
            item2: Second knowledge item
            
        Returns:
            Tuple[float, RelationshipType]: Similarity score and relationship type
        """
        # Calculate different types of similarity
        content_sim = self._cosine_similarity(item1.content, item2.content)
        title_sim = self._cosine_similarity(item1.title, item2.title)
        category_sim = self._category_similarity(item1.categories, item2.categories)
        tag_sim = self._tag_similarity(item1.tags, item2.tags)
        
        # Weighted combination
        overall_similarity = (
            content_sim * 0.4 +
            title_sim * 0.2 +
            category_sim * 0.2 +
            tag_sim * 0.2
        )
        
        # Determine relationship type based on similarity patterns
        rel_type = self._determine_relationship_type(
            content_sim, title_sim, category_sim, tag_sim, item1, item2
        )
        
        return overall_similarity, rel_type
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Cosine similarity score between 0.0 and 1.0
        """
        # Tokenize and create term frequency vectors
        tokens1 = self._tokenize(text1.lower())
        tokens2 = self._tokenize(text2.lower())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Create term frequency dictionaries
        tf1 = Counter(tokens1)
        tf2 = Counter(tokens2)
        
        # Get all unique terms
        all_terms = set(tf1.keys()).union(set(tf2.keys()))
        
        # Calculate dot product and magnitudes
        dot_product = sum(tf1.get(term, 0) * tf2.get(term, 0) for term in all_terms)
        magnitude1 = math.sqrt(sum(count ** 2 for count in tf1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in tf2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        # Remove special characters and split
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()
        
        # Remove stop words and short tokens
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can'
        }
        
        return [t for t in tokens if len(t) > 2 and t not in stop_words]
    
    def _category_similarity(self, categories1: List[Category], categories2: List[Category]) -> float:
        """
        Calculate similarity based on shared categories.
        
        Args:
            categories1: Categories of first item
            categories2: Categories of second item
            
        Returns:
            float: Category similarity score between 0.0 and 1.0
        """
        if not categories1 or not categories2:
            return 0.0
        
        # Get category IDs
        cat_ids1 = {cat.id for cat in categories1}
        cat_ids2 = {cat.id for cat in categories2}
        
        # Calculate Jaccard similarity
        intersection = len(cat_ids1.intersection(cat_ids2))
        union = len(cat_ids1.union(cat_ids2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _tag_similarity(self, tags1: List[Tag], tags2: List[Tag]) -> float:
        """
        Calculate similarity based on shared tags.
        
        Args:
            tags1: Tags of first item
            tags2: Tags of second item
            
        Returns:
            float: Tag similarity score between 0.0 and 1.0
        """
        if not tags1 or not tags2:
            return 0.0
        
        # Get tag names (case-insensitive)
        tag_names1 = {tag.name.lower() for tag in tags1}
        tag_names2 = {tag.name.lower() for tag in tags2}
        
        # Calculate Jaccard similarity
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
        """
        Determine the type of relationship based on similarity patterns.
        
        Args:
            content_sim: Content similarity score
            title_sim: Title similarity score
            category_sim: Category similarity score
            tag_sim: Tag similarity score
            item1: First knowledge item
            item2: Second knowledge item
            
        Returns:
            RelationshipType: The determined relationship type
        """
        # High content similarity suggests similar items
        if content_sim > 0.7:
            return RelationshipType.SIMILAR
        
        # High category/tag similarity but lower content similarity suggests related items
        if (category_sim > 0.5 or tag_sim > 0.5) and content_sim < 0.7:
            return RelationshipType.RELATED
        
        # Check for reference patterns in content
        if self._contains_reference(item1.content, item2.title):
            return RelationshipType.REFERENCES
        
        # Check for temporal relationship (one derived from another)
        if item1.created_at < item2.created_at and content_sim > 0.4:
            return RelationshipType.DERIVED_FROM
        
        # Default to related
        return RelationshipType.RELATED
    
    def _contains_reference(self, content: str, title: str) -> bool:
        """
        Check if content contains a reference to a title.
        
        Args:
            content: Content to search in
            title: Title to search for
            
        Returns:
            bool: True if reference is found
        """
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Check for direct mention
        if title_lower in content_lower:
            return True
        
        # Check for significant words from title
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
        """
        Generate a human-readable description of the relationship.
        
        Args:
            item1: First knowledge item
            item2: Second knowledge item
            rel_type: Type of relationship
            
        Returns:
            str: Description of the relationship
        """
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
        Update the knowledge graph with new relationships.
        
        Args:
            relationships: List of relationships to add to the graph
        """
        for relationship in relationships:
            # Add to graph structure
            if relationship.source_id not in self._knowledge_graph:
                self._knowledge_graph[relationship.source_id] = set()
            
            self._knowledge_graph[relationship.source_id].add(relationship.target_id)
            
            # If bidirectional, add reverse connection
            if relationship.is_bidirectional():
                if relationship.target_id not in self._knowledge_graph:
                    self._knowledge_graph[relationship.target_id] = set()
                
                self._knowledge_graph[relationship.target_id].add(relationship.source_id)
            
            # Save to storage
            self.storage_manager.save_relationship(relationship)
    
    def get_related_items(self, item_id: str, max_depth: int = 2) -> List[str]:
        """
        Get all items related to a given item up to a certain depth.
        
        Args:
            item_id: ID of the item to start from
            max_depth: Maximum depth to traverse in the graph
            
        Returns:
            List[str]: List of related item IDs
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
            
            # Add neighbors to visit
            if current_id in self._knowledge_graph:
                for neighbor_id in self._knowledge_graph[current_id]:
                    if neighbor_id not in visited:
                        to_visit.append((neighbor_id, depth + 1))
        
        return related
    
    def find_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """
        Find clusters of highly related knowledge items.
        
        Args:
            min_cluster_size: Minimum number of items in a cluster
            
        Returns:
            List[List[str]]: List of clusters (each cluster is a list of item IDs)
        """
        visited = set()
        clusters = []
        
        for item_id in self._knowledge_graph:
            if item_id in visited:
                continue
            
            # Perform BFS to find connected component
            cluster = []
            to_visit = [item_id]
            
            while to_visit:
                current_id = to_visit.pop(0)
                
                if current_id in visited:
                    continue
                
                visited.add(current_id)
                cluster.append(current_id)
                
                # Add neighbors
                if current_id in self._knowledge_graph:
                    for neighbor_id in self._knowledge_graph[current_id]:
                        if neighbor_id not in visited:
                            to_visit.append(neighbor_id)
            
            # Only keep clusters above minimum size
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
        
        return clusters
