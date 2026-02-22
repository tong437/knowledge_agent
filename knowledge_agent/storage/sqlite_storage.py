"""
SQLite storage manager implementation.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..interfaces.storage_manager import StorageManager
from ..models import KnowledgeItem, Category, Tag, Relationship, RelationshipType, SourceType


logger = logging.getLogger(__name__)


class SQLiteStorageManager(StorageManager):
    """
    SQLite-based storage manager for knowledge items and related data.
    
    Provides persistent storage using SQLite database with proper
    data integrity checks and transaction management.
    """
    
    def __init__(self, db_path: str = "knowledge_agent.db"):
        """
        Initialize the SQLite storage manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._persistent_conn = None
        
        # For :memory: databases, keep a persistent connection
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(db_path, check_same_thread=False)
            self._persistent_conn.execute("PRAGMA foreign_keys = ON")
        
        self._init_database()
    
    def _get_connection(self):
        """Get a database connection (persistent for :memory:, new for file-based)."""
        if self._persistent_conn:
            return self._persistent_conn
        return sqlite3.connect(self.db_path)
    
    def _use_connection(self):
        """Context manager for database connections."""
        if self._persistent_conn:
            # For persistent connections, don't close
            class PersistentConnectionContext:
                def __init__(self, conn):
                    self.conn = conn
                def __enter__(self):
                    return self.conn
                def __exit__(self, *args):
                    self.conn.commit()  # Commit but don't close
            return PersistentConnectionContext(self._persistent_conn)
        else:
            # For file-based, use normal context manager
            return sqlite3.connect(self.db_path)
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self._use_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Knowledge items table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    embedding TEXT
                )
            """)
            
            # Categories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    parent_id TEXT,
                    confidence REAL NOT NULL,
                    FOREIGN KEY (parent_id) REFERENCES categories (id)
                )
            """)
            
            # Tags table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0
                )
            """)
            
            # Relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    description TEXT,
                    FOREIGN KEY (source_id) REFERENCES knowledge_items (id),
                    FOREIGN KEY (target_id) REFERENCES knowledge_items (id),
                    UNIQUE(source_id, target_id, relationship_type)
                )
            """)
            
            # Knowledge item categories junction table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item_categories (
                    knowledge_item_id TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    PRIMARY KEY (knowledge_item_id, category_id),
                    FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
                )
            """)
            
            # Knowledge item tags junction table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item_tags (
                    knowledge_item_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    PRIMARY KEY (knowledge_item_id, tag_id),
                    FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """Save a knowledge item to storage."""
        with self._use_connection() as conn:
            try:
                # Save the main knowledge item
                conn.execute("""
                    INSERT OR REPLACE INTO knowledge_items 
                    (id, title, content, source_type, source_path, metadata, 
                     created_at, updated_at, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.id,
                    item.title,
                    item.content,
                    item.source_type.value,
                    item.source_path,
                    json.dumps(item.metadata),
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    json.dumps(item.embedding) if item.embedding else None
                ))
                
                # Clear existing categories and tags
                conn.execute("DELETE FROM knowledge_item_categories WHERE knowledge_item_id = ?", (item.id,))
                conn.execute("DELETE FROM knowledge_item_tags WHERE knowledge_item_id = ?", (item.id,))
                
                # Save categories
                for category in item.categories:
                    self._save_category_if_not_exists(conn, category)
                    conn.execute("""
                        INSERT OR IGNORE INTO knowledge_item_categories 
                        (knowledge_item_id, category_id) VALUES (?, ?)
                    """, (item.id, category.id))
                
                # Save tags
                for tag in item.tags:
                    self._save_tag_if_not_exists(conn, tag)
                    conn.execute("""
                        INSERT OR IGNORE INTO knowledge_item_tags 
                        (knowledge_item_id, tag_id) VALUES (?, ?)
                    """, (item.id, tag.id))
                
                conn.commit()
                logger.debug(f"Saved knowledge item: {item.id}")
                
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Error saving knowledge item {item.id}: {e}")
                raise
    
    def _save_category_if_not_exists(self, conn: sqlite3.Connection, category: Category) -> None:
        """Save a category if it doesn't already exist."""
        conn.execute("""
            INSERT OR IGNORE INTO categories 
            (id, name, description, parent_id, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (
            category.id,
            category.name,
            category.description,
            category.parent_id,
            category.confidence
        ))
    
    def _save_tag_if_not_exists(self, conn: sqlite3.Connection, tag: Tag) -> None:
        """Save a tag if it doesn't already exist."""
        conn.execute("""
            INSERT OR IGNORE INTO tags 
            (id, name, color, usage_count)
            VALUES (?, ?, ?, ?)
        """, (
            tag.id,
            tag.name,
            tag.color,
            tag.usage_count
        ))
    
    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Retrieve a knowledge item by ID."""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            # Get the main item
            cursor = conn.execute("""
                SELECT * FROM knowledge_items WHERE id = ?
            """, (item_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Get categories
            categories = self._get_categories_for_item(conn, item_id)
            
            # Get tags
            tags = self._get_tags_for_item(conn, item_id)
            
            # Create and return the knowledge item
            return KnowledgeItem(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                source_type=SourceType(row["source_type"]),
                source_path=row["source_path"],
                categories=categories,
                tags=tags,
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                embedding=json.loads(row["embedding"]) if row["embedding"] else None
            )
    
    def _get_categories_for_item(self, conn: sqlite3.Connection, item_id: str) -> List[Category]:
        """Get all categories for a knowledge item."""
        cursor = conn.execute("""
            SELECT c.* FROM categories c
            JOIN knowledge_item_categories kic ON c.id = kic.category_id
            WHERE kic.knowledge_item_id = ?
        """, (item_id,))
        
        categories = []
        for row in cursor.fetchall():
            categories.append(Category(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                parent_id=row["parent_id"],
                confidence=row["confidence"]
            ))
        
        return categories
    
    def _get_tags_for_item(self, conn: sqlite3.Connection, item_id: str) -> List[Tag]:
        """Get all tags for a knowledge item."""
        cursor = conn.execute("""
            SELECT t.* FROM tags t
            JOIN knowledge_item_tags kit ON t.id = kit.tag_id
            WHERE kit.knowledge_item_id = ?
        """, (item_id,))
        
        tags = []
        for row in cursor.fetchall():
            tags.append(Tag(
                id=row["id"],
                name=row["name"],
                color=row["color"],
                usage_count=row["usage_count"]
            ))
        
        return tags
    
    def get_all_knowledge_items(self) -> List[KnowledgeItem]:
        """
        获取存储中的所有知识条目。

        使用批量查询优化，最多执行 3 次数据库查询：
        1. 查询所有主条目
        2. 批量获取所有条目的分类映射
        3. 批量获取所有条目的标签映射
        """
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row

            # 查询 1：获取所有主条目
            cursor = conn.execute("SELECT * FROM knowledge_items")
            rows = cursor.fetchall()

            if not rows:
                return []

            # 查询 2：批量获取所有条目的分类映射
            cat_cursor = conn.execute("""
                SELECT kic.knowledge_item_id, c.id, c.name, c.description,
                       c.parent_id, c.confidence
                FROM knowledge_item_categories kic
                JOIN categories c ON kic.category_id = c.id
            """)
            categories_map: Dict[str, List[Category]] = {}
            for cat_row in cat_cursor.fetchall():
                item_id = cat_row["knowledge_item_id"]
                category = Category(
                    id=cat_row["id"],
                    name=cat_row["name"],
                    description=cat_row["description"],
                    parent_id=cat_row["parent_id"],
                    confidence=cat_row["confidence"]
                )
                categories_map.setdefault(item_id, []).append(category)

            # 查询 3：批量获取所有条目的标签映射
            tag_cursor = conn.execute("""
                SELECT kit.knowledge_item_id, t.id, t.name, t.color,
                       t.usage_count
                FROM knowledge_item_tags kit
                JOIN tags t ON kit.tag_id = t.id
            """)
            tags_map: Dict[str, List[Tag]] = {}
            for tag_row in tag_cursor.fetchall():
                item_id = tag_row["knowledge_item_id"]
                tag = Tag(
                    id=tag_row["id"],
                    name=tag_row["name"],
                    color=tag_row["color"],
                    usage_count=tag_row["usage_count"]
                )
                tags_map.setdefault(item_id, []).append(tag)

            # 组装完整的 KnowledgeItem 对象
            items = []
            for row in rows:
                item = KnowledgeItem(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    source_type=SourceType(row["source_type"]),
                    source_path=row["source_path"],
                    categories=categories_map.get(row["id"], []),
                    tags=tags_map.get(row["id"], []),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None
                )
                items.append(item)

            return items

    def query_knowledge_items(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[KnowledgeItem]:
        """
        按分类、标签过滤并分页查询知识条目。

        使用 SQL WHERE/JOIN 在数据库层面完成过滤和分页，
        并对返回的条目批量加载分类和标签，避免 N+1 查询问题。

        Args:
            category: 按分类名称过滤（精确匹配），为 None 时不过滤
            tag: 按标签名称过滤（精确匹配），为 None 时不过滤
            limit: 每页返回的最大条目数，默认 50
            offset: 分页偏移量，默认 0

        Returns:
            符合条件的 KnowledgeItem 列表，包含完整的 categories 和 tags
        """
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row

            # 构建主查询，根据过滤条件动态添加 JOIN 和 WHERE
            query = "SELECT DISTINCT ki.* FROM knowledge_items ki"
            params: List[Any] = []

            if category:
                query += """
                    JOIN knowledge_item_categories kic ON ki.id = kic.knowledge_item_id
                    JOIN categories c ON kic.category_id = c.id"""

            if tag:
                query += """
                    JOIN knowledge_item_tags kit ON ki.id = kit.knowledge_item_id
                    JOIN tags t ON kit.tag_id = t.id"""

            conditions = []
            if category:
                conditions.append("c.name = ?")
                params.append(category)
            if tag:
                conditions.append("t.name = ?")
                params.append(tag)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return []

            # 收集所有条目 ID，用于批量加载分类和标签
            item_ids = [row["id"] for row in rows]
            placeholders = ",".join(["?"] * len(item_ids))

            # 批量获取这些条目的分类映射
            cat_cursor = conn.execute(f"""
                SELECT kic.knowledge_item_id, c.id, c.name, c.description,
                       c.parent_id, c.confidence
                FROM knowledge_item_categories kic
                JOIN categories c ON kic.category_id = c.id
                WHERE kic.knowledge_item_id IN ({placeholders})
            """, item_ids)
            categories_map: Dict[str, List[Category]] = {}
            for cat_row in cat_cursor.fetchall():
                kid = cat_row["knowledge_item_id"]
                cat_obj = Category(
                    id=cat_row["id"],
                    name=cat_row["name"],
                    description=cat_row["description"],
                    parent_id=cat_row["parent_id"],
                    confidence=cat_row["confidence"]
                )
                categories_map.setdefault(kid, []).append(cat_obj)

            # 批量获取这些条目的标签映射
            tag_cursor = conn.execute(f"""
                SELECT kit.knowledge_item_id, t.id, t.name, t.color,
                       t.usage_count
                FROM knowledge_item_tags kit
                JOIN tags t ON kit.tag_id = t.id
                WHERE kit.knowledge_item_id IN ({placeholders})
            """, item_ids)
            tags_map: Dict[str, List[Tag]] = {}
            for tag_row in tag_cursor.fetchall():
                kid = tag_row["knowledge_item_id"]
                tag_obj = Tag(
                    id=tag_row["id"],
                    name=tag_row["name"],
                    color=tag_row["color"],
                    usage_count=tag_row["usage_count"]
                )
                tags_map.setdefault(kid, []).append(tag_obj)

            # 组装完整的 KnowledgeItem 对象
            items = []
            for row in rows:
                item = KnowledgeItem(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    source_type=SourceType(row["source_type"]),
                    source_path=row["source_path"],
                    categories=categories_map.get(row["id"], []),
                    tags=tags_map.get(row["id"], []),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None
                )
                items.append(item)

            return items

    def delete_knowledge_item(self, item_id: str) -> bool:
        """Delete a knowledge item from storage."""
        with self._use_connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"Deleted knowledge item: {item_id}")
                
                return deleted
                
            except sqlite3.Error as e:
                logger.error(f"Error deleting knowledge item {item_id}: {e}")
                return False
    
    def save_category(self, category: Category) -> None:
        """Save a category to storage."""
        with self._use_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO categories 
                    (id, name, description, parent_id, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    category.id,
                    category.name,
                    category.description,
                    category.parent_id,
                    category.confidence
                ))
                
                conn.commit()
                logger.debug(f"Saved category: {category.id}")
                
            except sqlite3.Error as e:
                logger.error(f"Error saving category {category.id}: {e}")
                raise
    
    def get_all_categories(self) -> List[Category]:
        """Retrieve all categories from storage."""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM categories")
            categories = []
            
            for row in cursor.fetchall():
                categories.append(Category(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    parent_id=row["parent_id"],
                    confidence=row["confidence"]
                ))
            
            return categories
    
    def save_tag(self, tag: Tag) -> None:
        """Save a tag to storage."""
        with self._use_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO tags 
                    (id, name, color, usage_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    tag.id,
                    tag.name,
                    tag.color,
                    tag.usage_count
                ))
                
                conn.commit()
                logger.debug(f"Saved tag: {tag.id}")
                
            except sqlite3.Error as e:
                logger.error(f"Error saving tag {tag.id}: {e}")
                raise
    
    def get_all_tags(self) -> List[Tag]:
        """Retrieve all tags from storage."""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM tags")
            tags = []
            
            for row in cursor.fetchall():
                tags.append(Tag(
                    id=row["id"],
                    name=row["name"],
                    color=row["color"],
                    usage_count=row["usage_count"]
                ))
            
            return tags
    
    def save_relationship(self, relationship: Relationship) -> None:
        """Save a relationship to storage."""
        with self._use_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO relationships 
                    (source_id, target_id, relationship_type, strength, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relationship_type.value,
                    relationship.strength,
                    relationship.description
                ))
                
                conn.commit()
                logger.debug(f"Saved relationship: {relationship.source_id} -> {relationship.target_id}")
                
            except sqlite3.Error as e:
                logger.error(f"Error saving relationship: {e}")
                raise
    
    def get_relationships_for_item(self, item_id: str) -> List[Relationship]:
        """Get all relationships for a specific knowledge item."""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT * FROM relationships 
                WHERE source_id = ? OR target_id = ?
            """, (item_id, item_id))
            
            relationships = []
            for row in cursor.fetchall():
                relationships.append(Relationship(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relationship_type=RelationshipType(row["relationship_type"]),
                    strength=row["strength"],
                    description=row["description"] or ""
                ))
            
            return relationships
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """Export all data in the specified format."""
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}")
        
        data = {
            "knowledge_items": [item.to_dict() for item in self.get_all_knowledge_items()],
            "categories": [cat.to_dict() for cat in self.get_all_categories()],
            "tags": [tag.to_dict() for tag in self.get_all_tags()],
            "relationships": []
        }
        
        # Get all relationships
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM relationships")
            
            for row in cursor.fetchall():
                relationship = Relationship(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relationship_type=RelationshipType(row["relationship_type"]),
                    strength=row["strength"],
                    description=row["description"] or ""
                )
                data["relationships"].append(relationship.to_dict())
        
        data["export_timestamp"] = datetime.now().isoformat()
        return data
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data from a dictionary."""
        try:
            # Import categories first (for foreign key constraints)
            for cat_data in data.get("categories", []):
                category = Category.from_dict(cat_data)
                self.save_category(category)
            
            # Import tags
            for tag_data in data.get("tags", []):
                tag = Tag.from_dict(tag_data)
                self.save_tag(tag)
            
            # Import knowledge items
            for item_data in data.get("knowledge_items", []):
                item = KnowledgeItem.from_dict(item_data)
                self.save_knowledge_item(item)
            
            # Import relationships
            for rel_data in data.get("relationships", []):
                relationship = Relationship.from_dict(rel_data)
                self.save_relationship(relationship)
            
            logger.info("Data import completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self._use_connection() as conn:
            stats = {}
            
            # Count knowledge items
            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_items")
            stats["knowledge_items"] = cursor.fetchone()[0]
            
            # Count categories
            cursor = conn.execute("SELECT COUNT(*) FROM categories")
            stats["categories"] = cursor.fetchone()[0]
            
            # Count tags
            cursor = conn.execute("SELECT COUNT(*) FROM tags")
            stats["tags"] = cursor.fetchone()[0]
            
            # Count relationships
            cursor = conn.execute("SELECT COUNT(*) FROM relationships")
            stats["relationships"] = cursor.fetchone()[0]
            
            return stats
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity and return any issues found."""
        issues = []
        
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            
            # Check for orphaned category references
            cursor = conn.execute("""
                SELECT kic.knowledge_item_id, kic.category_id 
                FROM knowledge_item_categories kic
                LEFT JOIN categories c ON kic.category_id = c.id
                WHERE c.id IS NULL
            """)
            
            orphaned_categories = cursor.fetchall()
            if orphaned_categories:
                issues.append({
                    "type": "orphaned_category_references",
                    "count": len(orphaned_categories),
                    "items": [dict(row) for row in orphaned_categories]
                })
            
            # Check for orphaned tag references
            cursor = conn.execute("""
                SELECT kit.knowledge_item_id, kit.tag_id 
                FROM knowledge_item_tags kit
                LEFT JOIN tags t ON kit.tag_id = t.id
                WHERE t.id IS NULL
            """)
            
            orphaned_tags = cursor.fetchall()
            if orphaned_tags:
                issues.append({
                    "type": "orphaned_tag_references",
                    "count": len(orphaned_tags),
                    "items": [dict(row) for row in orphaned_tags]
                })
            
            # Check for invalid relationships
            cursor = conn.execute("""
                SELECT r.source_id, r.target_id 
                FROM relationships r
                LEFT JOIN knowledge_items ki1 ON r.source_id = ki1.id
                LEFT JOIN knowledge_items ki2 ON r.target_id = ki2.id
                WHERE ki1.id IS NULL OR ki2.id IS NULL
            """)
            
            invalid_relationships = cursor.fetchall()
            if invalid_relationships:
                issues.append({
                    "type": "invalid_relationships",
                    "count": len(invalid_relationships),
                    "items": [dict(row) for row in invalid_relationships]
                })
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "checked_at": datetime.now().isoformat()
        }

    def close(self) -> None:
        """Close the database connection (for persistent connections)."""
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
            logger.info("Closed persistent database connection")
