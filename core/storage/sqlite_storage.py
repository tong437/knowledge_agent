"""
SQLite 存储管理器实现。
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.interfaces.storage_manager import StorageManager
from core.models import (
    KnowledgeItem, Category, Tag, Relationship,
    RelationshipType, SourceType, KnowledgeChunk,
)
from modules.YA_Common.utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteStorageManager(StorageManager):
    """
    基于 SQLite 的知识存储管理器。

    使用 SQLite 数据库提供持久化存储，支持数据完整性检查和事务管理。
    """

    def __init__(self, db_path: str = "knowledge_agent.db"):
        self.db_path = db_path
        self._persistent_conn = None

        # 内存数据库使用持久连接
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(db_path, check_same_thread=False)
            self._persistent_conn.execute("PRAGMA foreign_keys = ON")

        self._init_database()

    def _get_connection(self):
        """获取数据库连接（内存数据库返回持久连接，文件数据库返回新连接）。"""
        if self._persistent_conn:
            return self._persistent_conn
        return sqlite3.connect(self.db_path)

    def _use_connection(self):
        """数据库连接的上下文管理器。"""
        if self._persistent_conn:
            class PersistentConnectionContext:
                def __init__(self, conn):
                    self.conn = conn
                def __enter__(self):
                    return self.conn
                def __exit__(self, *args):
                    self.conn.commit()
            return PersistentConnectionContext(self._persistent_conn)
        else:
            return sqlite3.connect(self.db_path)

    def _init_database(self) -> None:
        """初始化数据库表结构。"""
        with self._use_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")

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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL,
                    usage_count INTEGER NOT NULL DEFAULT 0
                )
            """)

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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item_categories (
                    knowledge_item_id TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    PRIMARY KEY (knowledge_item_id, category_id),
                    FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_item_tags (
                    knowledge_item_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    PRIMARY KEY (knowledge_item_id, tag_id),
                    FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    heading TEXT NOT NULL DEFAULT '',
                    start_position INTEGER NOT NULL,
                    end_position INTEGER NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (item_id) REFERENCES knowledge_items (id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_item_id
                ON knowledge_chunks (item_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_item_chunk
                ON knowledge_chunks (item_id, chunk_index)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def save_knowledge_item(self, item: KnowledgeItem) -> None:
        """保存知识条目到存储。"""
        with self._use_connection() as conn:
            try:
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

                conn.execute("DELETE FROM knowledge_item_categories WHERE knowledge_item_id = ?", (item.id,))
                conn.execute("DELETE FROM knowledge_item_tags WHERE knowledge_item_id = ?", (item.id,))

                for category in item.categories:
                    self._save_category_if_not_exists(conn, category)
                    conn.execute("""
                        INSERT OR IGNORE INTO knowledge_item_categories
                        (knowledge_item_id, category_id) VALUES (?, ?)
                    """, (item.id, category.id))

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
        """保存分类（如果不存在）。"""
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
        """保存标签（如果不存在）。"""
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
        """根据 ID 检索知识条目。"""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT * FROM knowledge_items WHERE id = ?
            """, (item_id,))

            row = cursor.fetchone()
            if not row:
                return None

            categories = self._get_categories_for_item(conn, item_id)
            tags = self._get_tags_for_item(conn, item_id)

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
        """获取知识条目的所有分类。"""
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
        """获取知识条目的所有标签。"""
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

            cursor = conn.execute("SELECT * FROM knowledge_items")
            rows = cursor.fetchall()

            if not rows:
                return []

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

            item_ids = [row["id"] for row in rows]
            placeholders = ",".join(["?"] * len(item_ids))

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

    def update_knowledge_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新知识条目的部分字段。

        支持部分字段更新，自动更新 updated_at 时间戳。
        对于 categories 和 tags 字段，采用先删后插的策略替换关联关系。

        Args:
            item_id: 知识条目 ID
            updates: 可更新字段字典，支持 title、content、categories、tags

        Returns:
            更新成功返回 True，条目不存在返回 False
        """
        with self._use_connection() as conn:
            try:
                cursor = conn.execute(
                    "SELECT id FROM knowledge_items WHERE id = ?", (item_id,)
                )
                if cursor.fetchone() is None:
                    logger.debug(f"知识条目不存在，跳过更新: {item_id}")
                    return False

                now = datetime.now()

                set_clauses = []
                params = []

                if "title" in updates:
                    set_clauses.append("title = ?")
                    params.append(updates["title"])

                if "content" in updates:
                    set_clauses.append("content = ?")
                    params.append(updates["content"])

                set_clauses.append("updated_at = ?")
                params.append(now.isoformat())

                params.append(item_id)
                conn.execute(
                    f"UPDATE knowledge_items SET {', '.join(set_clauses)} WHERE id = ?",
                    params
                )

                if "categories" in updates:
                    conn.execute(
                        "DELETE FROM knowledge_item_categories WHERE knowledge_item_id = ?",
                        (item_id,)
                    )
                    for category in updates["categories"]:
                        self._save_category_if_not_exists(conn, category)
                        conn.execute(
                            "INSERT OR IGNORE INTO knowledge_item_categories "
                            "(knowledge_item_id, category_id) VALUES (?, ?)",
                            (item_id, category.id)
                        )

                if "tags" in updates:
                    conn.execute(
                        "DELETE FROM knowledge_item_tags WHERE knowledge_item_id = ?",
                        (item_id,)
                    )
                    for tag in updates["tags"]:
                        self._save_tag_if_not_exists(conn, tag)
                        conn.execute(
                            "INSERT OR IGNORE INTO knowledge_item_tags "
                            "(knowledge_item_id, tag_id) VALUES (?, ?)",
                            (item_id, tag.id)
                        )

                conn.commit()
                logger.debug(f"已更新知识条目: {item_id}, 更新字段: {list(updates.keys())}")
                return True

            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"更新知识条目失败 {item_id}: {e}")
                raise

    def delete_knowledge_item(self, item_id: str) -> bool:
        """从存储中删除知识条目。"""
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
        """保存分类到存储。"""
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
        """检索所有分类。"""
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
        """保存标签到存储。"""
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
        """检索所有标签。"""
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
        """保存关系到存储。"""
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
        """获取指定知识条目的所有关系。"""
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
        """以指定格式导出所有数据。"""
        if format != "json":
            raise ValueError(f"Unsupported export format: {format}")

        data = {
            "knowledge_items": [item.to_dict() for item in self.get_all_knowledge_items()],
            "categories": [cat.to_dict() for cat in self.get_all_categories()],
            "tags": [tag.to_dict() for tag in self.get_all_tags()],
            "relationships": []
        }

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
        """从字典导入数据。"""
        try:
            for cat_data in data.get("categories", []):
                category = Category.from_dict(cat_data)
                self.save_category(category)

            for tag_data in data.get("tags", []):
                tag = Tag.from_dict(tag_data)
                self.save_tag(tag)

            for item_data in data.get("knowledge_items", []):
                item = KnowledgeItem.from_dict(item_data)
                self.save_knowledge_item(item)

            for rel_data in data.get("relationships", []):
                relationship = Relationship.from_dict(rel_data)
                self.save_relationship(relationship)

            logger.info("Data import completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False

    def get_database_stats(self) -> Dict[str, int]:
        """获取数据库统计信息。"""
        with self._use_connection() as conn:
            stats = {}

            cursor = conn.execute("SELECT COUNT(*) FROM knowledge_items")
            stats["knowledge_items"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM categories")
            stats["categories"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM tags")
            stats["tags"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM relationships")
            stats["relationships"] = cursor.fetchone()[0]

            return stats

    def check_data_integrity(self) -> Dict[str, Any]:
        """检查数据完整性并返回发现的问题。"""
        issues = []

        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row

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

    def save_chunks(self, item_id: str, chunks: List[KnowledgeChunk]) -> None:
        """批量保存分块，先删除该 item_id 的旧分块再插入新分块。"""
        with self._use_connection() as conn:
            try:
                conn.execute(
                    "DELETE FROM knowledge_chunks WHERE item_id = ?", (item_id,)
                )
                conn.executemany(
                    """
                    INSERT INTO knowledge_chunks
                    (id, item_id, chunk_index, content, heading,
                     start_position, end_position, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            chunk.id,
                            item_id,
                            chunk.chunk_index,
                            chunk.content,
                            chunk.heading,
                            chunk.start_position,
                            chunk.end_position,
                            json.dumps(chunk.metadata) if chunk.metadata else None,
                        )
                        for chunk in chunks
                    ],
                )
                conn.commit()
                logger.debug(f"已保存 {len(chunks)} 个分块，item_id: {item_id}")
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"保存分块失败 item_id={item_id}: {e}")
                raise

    def get_chunks_for_item(self, item_id: str) -> List[KnowledgeChunk]:
        """按 chunk_index 排序返回指定条目的所有分块。"""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM knowledge_chunks WHERE item_id = ? ORDER BY chunk_index",
                (item_id,),
            )
            return [
                KnowledgeChunk(
                    id=row["id"],
                    item_id=row["item_id"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    heading=row["heading"],
                    start_position=row["start_position"],
                    end_position=row["end_position"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in cursor.fetchall()
            ]

    def get_chunk_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """根据 chunk_id 查询单个分块。"""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM knowledge_chunks WHERE id = ?", (chunk_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return KnowledgeChunk(
                id=row["id"],
                item_id=row["item_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                heading=row["heading"],
                start_position=row["start_position"],
                end_position=row["end_position"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

    def get_adjacent_chunks(
        self, item_id: str, chunk_index: int
    ) -> List[KnowledgeChunk]:
        """查询指定分块的前后相邻分块（chunk_index - 1 和 chunk_index + 1）。"""
        with self._use_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM knowledge_chunks "
                "WHERE item_id = ? AND chunk_index IN (?, ?) "
                "ORDER BY chunk_index",
                (item_id, chunk_index - 1, chunk_index + 1),
            )
            return [
                KnowledgeChunk(
                    id=row["id"],
                    item_id=row["item_id"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    heading=row["heading"],
                    start_position=row["start_position"],
                    end_position=row["end_position"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in cursor.fetchall()
            ]

    def close(self) -> None:
        """关闭数据库连接（用于持久连接）。"""
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None
            logger.info("Closed persistent database connection")
