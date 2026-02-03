"""
Storage manager interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models import KnowledgeItem, Category, Tag, Relationship


class StorageManager(ABC):
    """
    Abstract base class for knowledge storage and persistence.
    
    Defines the interface for storing, retrieving, and managing
    knowledge items and related data.
    """
    
    @abstractmethod
    def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """
        Save a knowledge item to storage.
        
        Args:
            item: The knowledge item to save
        """
        pass
    
    @abstractmethod
    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """
        Retrieve a knowledge item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            Optional[KnowledgeItem]: The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all_knowledge_items(self) -> List[KnowledgeItem]:
        """
        Retrieve all knowledge items from storage.
        
        Returns:
            List[KnowledgeItem]: List of all stored items
        """
        pass
    
    @abstractmethod
    def delete_knowledge_item(self, item_id: str) -> bool:
        """
        Delete a knowledge item from storage.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def save_category(self, category: Category) -> None:
        """
        Save a category to storage.
        
        Args:
            category: The category to save
        """
        pass
    
    @abstractmethod
    def get_all_categories(self) -> List[Category]:
        """
        Retrieve all categories from storage.
        
        Returns:
            List[Category]: List of all categories
        """
        pass
    
    @abstractmethod
    def save_tag(self, tag: Tag) -> None:
        """
        Save a tag to storage.
        
        Args:
            tag: The tag to save
        """
        pass
    
    @abstractmethod
    def get_all_tags(self) -> List[Tag]:
        """
        Retrieve all tags from storage.
        
        Returns:
            List[Tag]: List of all tags
        """
        pass
    
    @abstractmethod
    def save_relationship(self, relationship: Relationship) -> None:
        """
        Save a relationship to storage.
        
        Args:
            relationship: The relationship to save
        """
        pass
    
    @abstractmethod
    def get_relationships_for_item(self, item_id: str) -> List[Relationship]:
        """
        Get all relationships for a specific knowledge item.
        
        Args:
            item_id: The ID of the item
            
        Returns:
            List[Relationship]: List of relationships involving the item
        """
        pass
    
    @abstractmethod
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export all data in the specified format.
        
        Args:
            format: Export format (json, etc.)
            
        Returns:
            Dict[str, Any]: Exported data
        """
        pass
    
    @abstractmethod
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        Import data from a dictionary.
        
        Args:
            data: Data to import
            
        Returns:
            bool: True if import was successful
        """
        pass