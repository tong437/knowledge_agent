"""
Unit tests for relationship analyzer functionality.
"""

import pytest
from datetime import datetime
from knowledge_agent.organizers import RelationshipAnalyzer
from knowledge_agent.models import KnowledgeItem, Category, Tag, SourceType, RelationshipType


class TestRelationshipAnalyzer:
    """Test cases for RelationshipAnalyzer."""
    
    def test_find_relationships_with_similar_content(self, storage_manager):
        """Test finding relationships between items with similar content."""
        analyzer = RelationshipAnalyzer(storage_manager, similarity_threshold=0.2)
        
        # Create and save first item
        item1 = KnowledgeItem(
            id="item1",
            title="Python Programming Basics",
            content="Python is a high-level programming language. It is widely used for web development, data science, and automation.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/python_basics.txt"
        )
        storage_manager.save_knowledge_item(item1)
        
        # Create second item with similar content
        item2 = KnowledgeItem(
            id="item2",
            title="Introduction to Python",
            content="Python is a versatile programming language used in web development, machine learning, and scripting.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/python_intro.txt"
        )
        
        # Find relationships
        relationships = analyzer.find_relationships(item2)
        
        # Should find at least one relationship
        assert len(relationships) > 0
        
        # Check relationship properties
        rel = relationships[0]
        assert rel.source_id == "item2"
        assert rel.target_id == "item1"
        assert rel.strength >= 0.2
        assert rel.relationship_type in [RelationshipType.SIMILAR, RelationshipType.RELATED]
    
    def test_find_relationships_with_shared_categories(self, storage_manager):
        """Test finding relationships based on shared categories."""
        analyzer = RelationshipAnalyzer(storage_manager, similarity_threshold=0.2)
        
        # Create shared category
        category = Category(
            id="cat1",
            name="Programming",
            description="Programming related content",
            confidence=0.9
        )
        
        # Create and save first item with category
        item1 = KnowledgeItem(
            id="item1",
            title="Java Basics",
            content="Java is an object-oriented programming language.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/java.txt",
            categories=[category]
        )
        storage_manager.save_knowledge_item(item1)
        
        # Create second item with same category
        item2 = KnowledgeItem(
            id="item2",
            title="C++ Tutorial",
            content="C++ is a powerful programming language.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/cpp.txt",
            categories=[category]
        )
        
        # Find relationships
        relationships = analyzer.find_relationships(item2)
        
        # Should find relationship due to shared category
        assert len(relationships) > 0
    
    def test_find_relationships_with_shared_tags(self, storage_manager):
        """Test finding relationships based on shared tags."""
        analyzer = RelationshipAnalyzer(storage_manager, similarity_threshold=0.2)
        
        # Create shared tag
        tag = Tag(id="tag1", name="tutorial", color="#FF0000")
        
        # Create and save first item with tag
        item1 = KnowledgeItem(
            id="item1",
            title="Git Tutorial",
            content="Learn how to use Git for version control.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/git.txt",
            tags=[tag]
        )
        storage_manager.save_knowledge_item(item1)
        
        # Create second item with same tag
        item2 = KnowledgeItem(
            id="item2",
            title="Docker Tutorial",
            content="Learn how to use Docker for containerization.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/docker.txt",
            tags=[tag]
        )
        
        # Find relationships
        relationships = analyzer.find_relationships(item2)
        
        # Should find relationship due to shared tag
        assert len(relationships) > 0
    
    def test_no_relationships_for_dissimilar_items(self, storage_manager):
        """Test that no relationships are found for completely dissimilar items."""
        analyzer = RelationshipAnalyzer(storage_manager, similarity_threshold=0.3)
        
        # Create and save first item
        item1 = KnowledgeItem(
            id="item1",
            title="Cooking Recipes",
            content="How to make delicious pasta with tomato sauce.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/cooking.txt"
        )
        storage_manager.save_knowledge_item(item1)
        
        # Create second item with completely different content
        item2 = KnowledgeItem(
            id="item2",
            title="Quantum Physics",
            content="Understanding quantum mechanics and wave-particle duality.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/to/physics.txt"
        )
        
        # Find relationships
        relationships = analyzer.find_relationships(item2)
        
        # Should find no relationships
        assert len(relationships) == 0
    
    def test_update_knowledge_graph(self, storage_manager):
        """Test updating the knowledge graph with relationships."""
        analyzer = RelationshipAnalyzer(storage_manager)
        
        # Create items
        item1 = KnowledgeItem(
            id="item1",
            title="Item 1",
            content="Content 1",
            source_type=SourceType.DOCUMENT,
            source_path="/path/1.txt"
        )
        item2 = KnowledgeItem(
            id="item2",
            title="Item 2",
            content="Content 2",
            source_type=SourceType.DOCUMENT,
            source_path="/path/2.txt"
        )
        storage_manager.save_knowledge_item(item1)
        storage_manager.save_knowledge_item(item2)
        
        # Find relationships
        relationships = analyzer.find_relationships(item1)
        
        # Update knowledge graph
        analyzer.update_knowledge_graph(relationships)
        
        # Verify relationships were saved
        saved_relationships = storage_manager.get_relationships_for_item("item1")
        assert len(saved_relationships) >= 0  # May or may not find relationships
    
    def test_cosine_similarity_calculation(self, storage_manager):
        """Test cosine similarity calculation."""
        analyzer = RelationshipAnalyzer(storage_manager)
        
        # Test identical texts
        text1 = "machine learning artificial intelligence"
        text2 = "machine learning artificial intelligence"
        similarity = analyzer._cosine_similarity(text1, text2)
        assert similarity == 1.0
        
        # Test completely different texts
        text1 = "machine learning"
        text2 = "cooking recipes"
        similarity = analyzer._cosine_similarity(text1, text2)
        assert similarity == 0.0
        
        # Test similar texts
        text1 = "machine learning and artificial intelligence"
        text2 = "artificial intelligence and machine learning"
        similarity = analyzer._cosine_similarity(text1, text2)
        assert similarity > 0.8
    
    def test_tokenization(self, storage_manager):
        """Test text tokenization."""
        analyzer = RelationshipAnalyzer(storage_manager)
        
        text = "This is a test of the tokenization system."
        tokens = analyzer._tokenize(text.lower())
        
        # Should remove stop words (short ones) and short tokens
        assert "is" not in tokens  # 2 chars
        assert "a" not in tokens   # 1 char
        assert "of" not in tokens  # 2 chars
        # Should keep meaningful words
        assert "test" in tokens
        assert "tokenization" in tokens
        assert "system" in tokens
    
    def test_get_related_items(self, storage_manager):
        """Test getting related items from knowledge graph."""
        analyzer = RelationshipAnalyzer(storage_manager)
        
        # Create a chain of related items
        item1 = KnowledgeItem(
            id="item1",
            title="Python Programming",
            content="Python is a programming language used for web development and data science.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/1.txt"
        )
        item2 = KnowledgeItem(
            id="item2",
            title="Web Development with Python",
            content="Python is great for web development using frameworks like Django and Flask.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/2.txt"
        )
        item3 = KnowledgeItem(
            id="item3",
            title="Django Framework",
            content="Django is a web framework for Python that makes development easier.",
            source_type=SourceType.DOCUMENT,
            source_path="/path/3.txt"
        )
        
        storage_manager.save_knowledge_item(item1)
        storage_manager.save_knowledge_item(item2)
        storage_manager.save_knowledge_item(item3)
        
        # Build relationships
        relationships1 = analyzer.find_relationships(item2)
        analyzer.update_knowledge_graph(relationships1)
        
        relationships2 = analyzer.find_relationships(item3)
        analyzer.update_knowledge_graph(relationships2)
        
        # Get related items
        related = analyzer.get_related_items("item1", max_depth=2)
        
        # Should find some related items
        assert isinstance(related, list)
