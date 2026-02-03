"""
Tag data model.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Tag:
    """
    Represents a tag for labeling and organizing knowledge items.
    
    Tags provide a flexible way to categorize and filter knowledge
    with usage tracking and visual customization.
    """
    
    id: str
    name: str
    color: str = "#007bff"  # Default blue color
    usage_count: int = 0
    
    def __post_init__(self):
        """Validate the tag after initialization."""
        if not self.id:
            raise ValueError("Tag ID cannot be empty")
        if not self.name:
            raise ValueError("Tag name cannot be empty")
        if self.usage_count < 0:
            raise ValueError("Tag usage count cannot be negative")
    
    def increment_usage(self) -> None:
        """Increment the usage count for this tag."""
        self.usage_count += 1
    
    def decrement_usage(self) -> None:
        """Decrement the usage count for this tag."""
        if self.usage_count > 0:
            self.usage_count -= 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the tag to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "usage_count": self.usage_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        """Create a tag from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            color=data.get("color", "#007bff"),
            usage_count=data.get("usage_count", 0),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on tag ID."""
        if not isinstance(other, Tag):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on tag ID."""
        return hash(self.id)