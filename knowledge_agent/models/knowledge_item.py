"""
Knowledge item data model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .category import Category
from .tag import Tag
from .data_source import SourceType


@dataclass
class KnowledgeItem:
    """
    Represents a single knowledge item in the system.
    
    A knowledge item is the fundamental unit of information storage,
    containing content, metadata, and organizational information.
    """
    
    id: str
    title: str
    content: str
    source_type: SourceType
    source_path: str
    categories: List[Category] = field(default_factory=list)
    tags: List[Tag] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        """Validate the knowledge item after initialization."""
        if not self.id:
            raise ValueError("Knowledge item ID cannot be empty")
        if not self.title:
            raise ValueError("Knowledge item title cannot be empty")
        if not self.content:
            raise ValueError("Knowledge item content cannot be empty")
    
    def add_category(self, category: Category) -> None:
        """Add a category to this knowledge item."""
        if category not in self.categories:
            self.categories.append(category)
            self.updated_at = datetime.now()
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to this knowledge item."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def update_content(self, new_content: str) -> None:
        """Update the content of this knowledge item."""
        if not new_content:
            raise ValueError("Content cannot be empty")
        self.content = new_content
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the knowledge item to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source_type": self.source_type.value,
            "source_path": self.source_path,
            "categories": [cat.to_dict() for cat in self.categories],
            "tags": [tag.to_dict() for tag in self.tags],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "embedding": self.embedding,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeItem":
        """Create a knowledge item from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            source_type=SourceType(data["source_type"]),
            source_path=data["source_path"],
            categories=[Category.from_dict(cat) for cat in data.get("categories", [])],
            tags=[Tag.from_dict(tag) for tag in data.get("tags", [])],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            embedding=data.get("embedding"),
        )