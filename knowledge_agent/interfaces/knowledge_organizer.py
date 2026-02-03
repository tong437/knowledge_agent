"""
Knowledge organizer interface.
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import KnowledgeItem, Category, Tag, Relationship


class KnowledgeOrganizer(ABC):
    """
    Abstract base class for organizing and structuring knowledge.
    
    Defines the interface for automatic classification, tagging,
    and relationship analysis of knowledge items.
    """
    
    @abstractmethod
    def classify(self, item: KnowledgeItem) -> List[Category]:
        """
        Automatically classify a knowledge item.
        
        Args:
            item: The knowledge item to classify
            
        Returns:
            List[Category]: List of assigned categories with confidence scores
        """
        pass
    
    @abstractmethod
    def generate_tags(self, item: KnowledgeItem) -> List[Tag]:
        """
        Generate relevant tags for a knowledge item.
        
        Args:
            item: The knowledge item to generate tags for
            
        Returns:
            List[Tag]: List of generated tags
        """
        pass
    
    @abstractmethod
    def find_relationships(self, item: KnowledgeItem) -> List[Relationship]:
        """
        Find relationships between a knowledge item and existing items.
        
        Args:
            item: The knowledge item to find relationships for
            
        Returns:
            List[Relationship]: List of discovered relationships
        """
        pass
    
    @abstractmethod
    def update_knowledge_graph(self, relationships: List[Relationship]) -> None:
        """
        Update the knowledge graph with new relationships.
        
        Args:
            relationships: List of relationships to add to the graph
        """
        pass
    
    @abstractmethod
    def learn_from_user_feedback(self, item: KnowledgeItem, 
                                user_categories: List[Category],
                                user_tags: List[Tag]) -> None:
        """
        Learn from user corrections to improve future classification.
        
        Args:
            item: The knowledge item that was corrected
            user_categories: Categories assigned by the user
            user_tags: Tags assigned by the user
        """
        pass