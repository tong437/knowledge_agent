"""
Unified knowledge organizer implementation.
"""

from typing import List

from ..models import KnowledgeItem, Category, Tag, Relationship
from ..interfaces import KnowledgeOrganizer, StorageManager
from .auto_classifier import AutoClassifier
from .tag_generator import TagGenerator
from .relationship_analyzer import RelationshipAnalyzer


class KnowledgeOrganizerImpl(KnowledgeOrganizer):
    """
    Unified implementation of the knowledge organizer interface.
    
    Combines auto classification, tag generation, and relationship
    analysis into a single cohesive knowledge organization system.
    """
    
    def __init__(self, storage_manager: StorageManager):
        """
        Initialize the knowledge organizer.
        
        Args:
            storage_manager: Storage manager for data persistence
        """
        self.storage_manager = storage_manager
        self.classifier = AutoClassifier(storage_manager)
        self.tag_generator = TagGenerator(storage_manager)
        self.relationship_analyzer = RelationshipAnalyzer(storage_manager)
    
    def classify(self, item: KnowledgeItem) -> List[Category]:
        """
        Automatically classify a knowledge item.
        
        Args:
            item: The knowledge item to classify
            
        Returns:
            List[Category]: List of assigned categories with confidence scores
        """
        return self.classifier.classify(item)
    
    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        Generate relevant tags for a knowledge item.
        
        Args:
            item: The knowledge item to generate tags for
            
        Returns:
            List[Tag]: List of generated tags
        """
        return self.tag_generator.generate_tags(item)
    
    def find_relationships(self, item: KnowledgeItem) -> List[Relationship]:
        """
        Find relationships between a knowledge item and existing items.
        
        Args:
            item: The knowledge item to find relationships for
            
        Returns:
            List[Relationship]: List of discovered relationships
        """
        return self.relationship_analyzer.find_relationships(item)
    
    def update_knowledge_graph(self, relationships: List[Relationship]) -> None:
        """
        Update the knowledge graph with new relationships.
        
        Args:
            relationships: List of relationships to add to the graph
        """
        self.relationship_analyzer.update_knowledge_graph(relationships)
    
    def learn_from_user_feedback(
        self,
        item: KnowledgeItem,
        user_categories: List[Category],
        user_tags: List[Tag]
    ) -> None:
        """
        Learn from user corrections to improve future classification.
        
        Args:
            item: The knowledge item that was corrected
            user_categories: Categories assigned by the user
            user_tags: Tags assigned by the user
        """
        # Update classifier with user feedback
        self.classifier.learn_from_feedback(item, user_categories)
        
        # Update item with user-provided categories and tags
        item.categories = user_categories
        item.tags = user_tags
        
        # Save updated item
        self.storage_manager.save_knowledge_item(item)
    
    def organize_item(self, item: KnowledgeItem) -> KnowledgeItem:
        """
        Fully organize a knowledge item (classify, tag, and find relationships).
        
        Args:
            item: The knowledge item to organize
            
        Returns:
            KnowledgeItem: The organized item with categories, tags, and relationships
        """
        # Classify the item
        categories = self.classify(item)
        for category in categories:
            item.add_category(category)
        
        # Generate tags
        tags = self.generate_tags(item)
        for tag in tags:
            item.add_tag(tag)
        
        # Save the organized item
        self.storage_manager.save_knowledge_item(item)
        
        # Find and save relationships
        relationships = self.find_relationships(item)
        self.update_knowledge_graph(relationships)
        
        return item
