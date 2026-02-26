"""
Core knowledge agent implementation.
"""

from core.knowledge_agent_core import KnowledgeAgentCore
from core.exceptions import KnowledgeAgentError, ProcessingError, StorageError, SearchError
from core.config_manager import ConfigManager, get_config_manager
from core.component_registry import ComponentRegistry, get_component_registry
from core.monitoring import (
    monitor_performance,
    track_errors,
    performance_context,
    get_performance_monitor,
    get_error_tracker
)

__all__ = [
    "KnowledgeAgentCore",
    "KnowledgeAgentError",
    "ProcessingError",
    "StorageError",
    "SearchError",
    "ConfigManager",
    "get_config_manager",
    "ComponentRegistry",
    "get_component_registry",
    "monitor_performance",
    "track_errors",
    "performance_context",
    "get_performance_monitor",
    "get_error_tracker",
]
