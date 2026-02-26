"""
分类数据模型。
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Category:
    """
    知识分类，用于组织知识条目。

    支持层级结构（通过 parent_id）和自动分类的置信度评分。
    """

    id: str
    name: str
    description: str
    parent_id: Optional[str] = None
    confidence: float = 1.0

    def __post_init__(self):
        if not self.id:
            raise ValueError("Category ID cannot be empty")
        if not self.name:
            raise ValueError("Category name cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Category confidence must be between 0.0 and 1.0")

    def is_root_category(self) -> bool:
        return self.parent_id is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            parent_id=data.get("parent_id"),
            confidence=data.get("confidence", 1.0),
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Category):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
