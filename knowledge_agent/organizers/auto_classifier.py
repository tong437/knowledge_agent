"""
Auto classifier implementation using TF-IDF and keyword matching.
"""

import uuid
import re
from typing import List, Dict, Set
from collections import Counter
import math

from ..models import KnowledgeItem, Category
from ..interfaces import StorageManager


class AutoClassifier:
    """
    Automatic classifier for knowledge items using TF-IDF and keyword matching.
    
    This classifier analyzes the content of knowledge items and assigns
    appropriate categories based on content similarity and keyword matching.
    """
    
    def __init__(self, storage_manager: StorageManager, min_confidence: float = 0.3):
        """
        Initialize the auto classifier.
        
        Args:
            storage_manager: Storage manager for accessing existing data
            min_confidence: Minimum confidence threshold for category assignment
        """
        self.storage_manager = storage_manager
        self.min_confidence = min_confidence
        self._predefined_categories = self._initialize_predefined_categories()
        self._category_keywords = self._initialize_category_keywords()
    
    def _initialize_predefined_categories(self) -> List[Category]:
        """Initialize a set of predefined categories."""
        return [
            Category(
                id="cat_programming",
                name="Programming",
                description="Code, software development, and programming concepts",
                confidence=1.0
            ),
            Category(
                id="cat_documentation",
                name="Documentation",
                description="Technical documentation, guides, and manuals",
                confidence=1.0
            ),
            Category(
                id="cat_research",
                name="Research",
                description="Research papers, articles, and academic content",
                confidence=1.0
            ),
            Category(
                id="cat_notes",
                name="Notes",
                description="Personal notes and quick references",
                confidence=1.0
            ),
            Category(
                id="cat_reference",
                name="Reference",
                description="Reference materials and resources",
                confidence=1.0
            ),
            Category(
                id="cat_tutorial",
                name="Tutorial",
                description="Learning materials and tutorials",
                confidence=1.0
            ),
            Category(
                id="cat_general",
                name="General",
                description="General knowledge and miscellaneous content",
                confidence=1.0
            ),
        ]
    
    def _initialize_category_keywords(self) -> Dict[str, Set[str]]:
        """Initialize keyword sets for each category."""
        return {
            "cat_programming": {
                "code", "function", "class", "method", "variable", "algorithm",
                "programming", "software", "development", "debug", "compile",
                "python", "java", "javascript", "typescript", "c++", "rust",
                "api", "library", "framework", "module", "package"
            },
            "cat_documentation": {
                "documentation", "guide", "manual", "readme", "specification",
                "reference", "api", "usage", "installation", "configuration",
                "setup", "instructions", "how-to", "overview"
            },
            "cat_research": {
                "research", "paper", "study", "analysis", "experiment", "findings",
                "methodology", "results", "conclusion", "abstract", "hypothesis",
                "theory", "academic", "journal", "publication"
            },
            "cat_notes": {
                "note", "notes", "memo", "reminder", "todo", "idea", "thought",
                "quick", "draft", "scratch", "jot", "record"
            },
            "cat_reference": {
                "reference", "cheatsheet", "glossary", "dictionary", "index",
                "lookup", "table", "list", "catalog", "directory"
            },
            "cat_tutorial": {
                "tutorial", "lesson", "course", "learning", "teach", "example",
                "walkthrough", "step-by-step", "beginner", "introduction",
                "getting started", "basics", "fundamentals"
            },
            "cat_general": set()  # Catch-all category
        }
    
    def classify(self, item: KnowledgeItem) -> List[Category]:
        """
        Automatically classify a knowledge item.
        
        Args:
            item: The knowledge item to classify
            
        Returns:
            List[Category]: List of assigned categories with confidence scores
        """
        # Combine title and content for analysis
        text = f"{item.title} {item.content}".lower()
        
        # Tokenize the text
        tokens = self._tokenize(text)
        
        # Calculate category scores
        category_scores = {}
        
        for category in self._predefined_categories:
            if category.id == "cat_general":
                continue  # Skip general category for now
            
            score = self._calculate_category_score(tokens, category.id)
            if score >= self.min_confidence:
                category_scores[category.id] = score
        
        # If no categories match, assign to general
        if not category_scores:
            general_cat = next(c for c in self._predefined_categories if c.id == "cat_general")
            return [Category(
                id=general_cat.id,
                name=general_cat.name,
                description=general_cat.description,
                confidence=1.0
            )]
        
        # Sort by score and return top categories
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for cat_id, score in sorted_categories[:3]:  # Return top 3 categories
            category = next(c for c in self._predefined_categories if c.id == cat_id)
            result.append(Category(
                id=category.id,
                name=category.name,
                description=category.description,
                confidence=score
            ))
        
        return result
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        # Remove special characters and split into words
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.split()
        
        # Remove very short tokens and common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]
        
        return tokens
    
    def _calculate_category_score(self, tokens: List[str], category_id: str) -> float:
        """
        Calculate the relevance score for a category.
        
        Args:
            tokens: List of tokens from the content
            category_id: ID of the category to score
            
        Returns:
            float: Relevance score between 0.0 and 1.0
        """
        keywords = self._category_keywords.get(category_id, set())
        
        if not keywords or not tokens:
            return 0.0
        
        # Count keyword matches
        token_set = set(tokens)
        matches = len(token_set.intersection(keywords))
        
        # Calculate TF-IDF-like score
        token_counts = Counter(tokens)
        keyword_frequency = sum(token_counts[token] for token in keywords if token in token_counts)
        
        # Normalize by document length and keyword set size
        tf_score = keyword_frequency / len(tokens) if tokens else 0.0
        keyword_coverage = matches / len(keywords) if keywords else 0.0
        
        # Combine scores
        score = (tf_score * 0.7) + (keyword_coverage * 0.3)
        
        # Normalize to 0-1 range
        return min(1.0, score * 10)  # Scale up for better discrimination
    
    def add_custom_category(self, name: str, description: str, keywords: Set[str]) -> Category:
        """
        Add a custom category with associated keywords.
        
        Args:
            name: Category name
            description: Category description
            keywords: Set of keywords for this category
            
        Returns:
            Category: The created category
        """
        category_id = f"cat_{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        category = Category(
            id=category_id,
            name=name,
            description=description,
            confidence=1.0
        )
        
        self._predefined_categories.append(category)
        self._category_keywords[category_id] = keywords
        
        # Save to storage
        self.storage_manager.save_category(category)
        
        return category
    
    def learn_from_feedback(self, item: KnowledgeItem, user_categories: List[Category]) -> None:
        """
        Learn from user corrections to improve classification.
        
        Args:
            item: The knowledge item that was corrected
            user_categories: Categories assigned by the user
        """
        # Extract important terms from the item
        tokens = self._tokenize(f"{item.title} {item.content}".lower())
        
        # Get most frequent terms (excluding very common ones)
        token_counts = Counter(tokens)
        important_terms = [term for term, count in token_counts.most_common(10) if count > 1]
        
        # Add these terms to the category keywords
        for category in user_categories:
            if category.id in self._category_keywords:
                self._category_keywords[category.id].update(important_terms[:5])
