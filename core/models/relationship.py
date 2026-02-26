"""
知识条目关系数据模型。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class RelationshipType(Enum):
    """知识条目之间的关系类型。"""

    SIMILAR = "similar"
    RELATED = "related"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    CUSTOM = "custom"


@dataclass
class Relationship:
    """
    知识条目之间的关系，用于构建知识图谱。

    通过类型和强度描述条目间的连接。
    """

    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float
    description: str = ""

    def __post_init__(self):
        if not self.source_id:
            raise ValueError("Source ID cannot be empty")
        if not self.target_id:
            raise ValueError("Target ID cannot be empty")
        if self.source_id == self.target_id:
            raise ValueError("Source and target cannot be the same")
        if not (0.0 <= self.strength <= 1.0):
            raise ValueError("Relationship strength must be between 0.0 and 1.0")

    def is_bidirectional(self) -> bool:
        bidirectional_types = {
            RelationshipType.SIMILAR,
            RelationshipType.RELATED,
            RelationshipType.CONTRADICTS,
        }
        return self.relationship_type in bidirectional_types

    def reverse(self) -> "Relationship":
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
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=RelationshipType(data["relationship_type"]),
            strength=data["strength"],
            description=data.get("description", ""),
        )
