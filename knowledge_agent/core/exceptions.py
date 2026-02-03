"""
Custom exceptions for the knowledge agent.
"""


class KnowledgeAgentError(Exception):
    """Base exception for knowledge agent errors."""
    pass


class ProcessingError(KnowledgeAgentError):
    """Exception raised during data source processing."""
    pass


class StorageError(KnowledgeAgentError):
    """Exception raised during storage operations."""
    pass


class SearchError(KnowledgeAgentError):
    """Exception raised during search operations."""
    pass


class ValidationError(KnowledgeAgentError):
    """Exception raised during data validation."""
    pass


class ConfigurationError(KnowledgeAgentError):
    """Exception raised for configuration issues."""
    pass