"""
Relationship data model.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class RelationshipType(Enum):
    """Types of relationships between knowledge items."""
    
    SIMILAR = "similar"           # Content similarity
    RELATED = "related"           # Topical relation
    REFERENCES = "references"     # One references another
    DERIVED_FROM = "derived_from" # One is derived from another
    CONTRADICTS = "contradicts"   # Conflicting information
    SUPPORTS = "supports"         # Supporting evidence
    CUSTOM = "custom"            # User-defined relationship


@dataclass
class Relationship:
    """
    Represents a relationship between two knowledge items.
    
    Relationships help build the knowledge graph by connecting
    related items with typed and weighted connections.
    """
    
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float
    description: str = ""
    
    def __post_init__(self):
        """Validate the relationship after initialization."""
        if not self.source_id:
            raise ValueError("Source ID cannot be empty")
        if not self.target_id:
            raise ValueError("Target ID cannot be empty")
        if self.source_id == self.target_id:
            raise ValueError("Source and target cannot be the same")
        if not (0.0 <= self.strength <= 1.0):
            raise ValueError("Relationship strength must be between 0.0 and 1.0")
    
    def is_bidirectional(self) -> bool:
        """Check if this relationship type is bidirectional."""
        bidirectional_types = {
            RelationshipType.SIMILAR,
            RelationshipType.RELATED,
            RelationshipType.CONTRADICTS,
        }
        return self.relationship_type in bidirectional_types
    
    def reverse(self) -> "Relationship":
        """Create the reverse relationship if bidirectional."""
        if not self.is_bidirectional():
            raise ValueError(f"Cannot reverse {self.relationship_type.value} relationship")
        
        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=self.relationship_type,
            strength=self.strength,
            description=self.description,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the relationship to a dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create a relationship from a dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=RelationshipType(data["relationship_type"]),
            strength=data["strength"],
            description=data.get("description", ""),
        )