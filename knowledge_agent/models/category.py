"""
Category data model.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Category:
    """
    Represents a knowledge category for organizing knowledge items.
    
    Categories can be hierarchical with parent-child relationships
    and include confidence scores for automatic classification.
    """
    
    id: str
    name: str
    description: str
    parent_id: Optional[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate the category after initialization."""
        if not self.id:
            raise ValueError("Category ID cannot be empty")
        if not self.name:
            raise ValueError("Category name cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Category confidence must be between 0.0 and 1.0")
    
    def is_root_category(self) -> bool:
        """Check if this is a root category (no parent)."""
        return self.parent_id is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the category to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        """Create a category from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            parent_id=data.get("parent_id"),
            confidence=data.get("confidence", 1.0),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on category ID."""
        if not isinstance(other, Category):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on category ID."""
        return hash(self.id)