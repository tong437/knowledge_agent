"""
配置管理系统

提供YAML/JSON配置文件支持，支持用户自定义分类规则和搜索参数。
实现配置验证、热重载和默认值管理。
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

from knowledge_agent.core.exceptions import ConfigurationError


@dataclass
class ClassificationRule:
    """自定义分类规则"""
    name: str
    keywords: List[str]
    category: str
    priority: int = 0
    enabled: bool = True


@dataclass
class SearchParameters:
    """搜索参数配置"""
    min_relevance: float = 0.1
    max_results: int = 50
    enable_semantic: bool = True
    enable_keyword: bool = True
    result_grouping: bool = True
    highlight_matches: bool = True


@dataclass
class OrganizationConfig:
    """知识整理配置"""
    auto_classify: bool = True
    auto_tag: bool = True
    auto_relationships: bool = True
    classification_confidence_threshold: float = 0.7
    relationship_strength_threshold: float = 0.5
    custom_rules: List[ClassificationRule] = field(default_factory=list)


@dataclass
class ProcessingConfig:
    """数据处理配置"""
    max_file_size: int = 10485760  # 10MB
    supported_encodings: List[str] = field(default_factory=lambda: ["utf-8", "utf-16", "latin-1"])
    web_timeout: int = 30
    web_max_retries: int = 3


@dataclass
class StorageConfig:
    """存储配置"""
    type: str = "sqlite"
    path: str = "knowledge_base.db"
    backup_enabled: bool = True
    backup_interval: int = 3600


@dataclass
class KnowledgeAgentConfig:
    """知识管理智能体完整配置"""
    storage: StorageConfig = field(default_factory=StorageConfig)
    search: SearchParameters = field(default_factory=SearchParameters)
    organization: OrganizationConfig = field(default_factory=OrganizationConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    version: str = "0.1.0"
    last_modified: Optional[datetime] = None


class ConfigManager:
    """配置管理器
    
    支持YAML和JSON格式的配置文件加载、保存、验证和热重载。
    提供用户自定义分类规则和搜索参数的管理功能。
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，支持.yaml, .yml, .json格式
        """
        self.config_path = Path(config_path) if config_path else Path("knowledge_agent/config.yaml")
        self._config: KnowledgeAgentConfig = KnowledgeAgentConfig()
        self._file_mtime: Optional[float] = None
        
        if self.config_path.exists():
            self.load()
    
    def load(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用初始化时的路径
            
        Raises:
            ConfigurationError: 配置文件格式错误或不存在
        """
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif self.config_path.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config format: {self.config_path.suffix}")
            
            self._parse_config(data)
            self._file_mtime = self.config_path.stat().st_mtime
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用当前路径
            
        Raises:
            ConfigurationError: 保存失败
        """
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            data = self._serialize_config()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
                elif self.config_path.suffix == '.json':
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    raise ConfigurationError(f"Unsupported config format: {self.config_path.suffix}")
            
            self._file_mtime = self.config_path.stat().st_mtime
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def reload_if_changed(self) -> bool:
        """如果配置文件已修改则重新加载
        
        Returns:
            bool: 如果重新加载了配置返回True，否则返回False
        """
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        if self._file_mtime is None or current_mtime > self._file_mtime:
            self.load()
            return True
        
        return False
    
    def _parse_config(self, data: Dict[str, Any]) -> None:
        """解析配置数据"""
        # 处理空配置文件
        if data is None:
            data = {}
        
        # 解析存储配置
        if 'storage' in data:
            storage_data = data['storage']
            self._config.storage = StorageConfig(
                type=storage_data.get('type', 'sqlite'),
                path=storage_data.get('path', 'knowledge_base.db'),
                backup_enabled=storage_data.get('backup_enabled', True),
                backup_interval=storage_data.get('backup_interval', 3600)
            )
        
        # 解析搜索配置
        if 'search' in data:
            search_data = data['search']
            self._config.search = SearchParameters(
                min_relevance=search_data.get('min_relevance', 0.1),
                max_results=search_data.get('max_results', 50),
                enable_semantic=search_data.get('enable_semantic', True),
                enable_keyword=search_data.get('enable_keyword', True),
                result_grouping=search_data.get('result_grouping', True),
                highlight_matches=search_data.get('highlight_matches', True)
            )
        
        # 解析组织配置
        if 'organization' in data:
            org_data = data['organization']
            custom_rules = []
            
            if 'custom_classification_rules' in org_data:
                for rule_data in org_data['custom_classification_rules']:
                    rule = ClassificationRule(
                        name=rule_data['name'],
                        keywords=rule_data['keywords'],
                        category=rule_data['category'],
                        priority=rule_data.get('priority', 0),
                        enabled=rule_data.get('enabled', True)
                    )
                    custom_rules.append(rule)
            
            self._config.organization = OrganizationConfig(
                auto_classify=org_data.get('auto_classify', True),
                auto_tag=org_data.get('auto_tag', True),
                auto_relationships=org_data.get('auto_relationships', True),
                classification_confidence_threshold=org_data.get('classification_confidence_threshold', 0.7),
                relationship_strength_threshold=org_data.get('relationship_strength_threshold', 0.5),
                custom_rules=custom_rules
            )
        
        # 解析处理配置
        if 'processing' in data:
            proc_data = data['processing']
            self._config.processing = ProcessingConfig(
                max_file_size=proc_data.get('max_file_size', 10485760),
                supported_encodings=proc_data.get('supported_encodings', ["utf-8", "utf-16", "latin-1"]),
                web_timeout=proc_data.get('web_scraping', {}).get('timeout', 30),
                web_max_retries=proc_data.get('web_scraping', {}).get('max_retries', 3)
            )
        
        # 解析版本信息
        if 'server' in data and 'version' in data['server']:
            self._config.version = data['server']['version']
        
        self._config.last_modified = datetime.now()
    
    def _serialize_config(self) -> Dict[str, Any]:
        """序列化配置为字典"""
        data = {
            'server': {
                'version': self._config.version
            },
            'storage': {
                'type': self._config.storage.type,
                'path': self._config.storage.path,
                'backup_enabled': self._config.storage.backup_enabled,
                'backup_interval': self._config.storage.backup_interval
            },
            'search': {
                'min_relevance': self._config.search.min_relevance,
                'max_results': self._config.search.max_results,
                'enable_semantic': self._config.search.enable_semantic,
                'enable_keyword': self._config.search.enable_keyword,
                'result_grouping': self._config.search.result_grouping,
                'highlight_matches': self._config.search.highlight_matches
            },
            'organization': {
                'auto_classify': self._config.organization.auto_classify,
                'auto_tag': self._config.organization.auto_tag,
                'auto_relationships': self._config.organization.auto_relationships,
                'classification_confidence_threshold': self._config.organization.classification_confidence_threshold,
                'relationship_strength_threshold': self._config.organization.relationship_strength_threshold,
                'custom_classification_rules': [
                    {
                        'name': rule.name,
                        'keywords': rule.keywords,
                        'category': rule.category,
                        'priority': rule.priority,
                        'enabled': rule.enabled
                    }
                    for rule in self._config.organization.custom_rules
                ]
            },
            'processing': {
                'max_file_size': self._config.processing.max_file_size,
                'supported_encodings': self._config.processing.supported_encodings,
                'web_scraping': {
                    'timeout': self._config.processing.web_timeout,
                    'max_retries': self._config.processing.web_max_retries
                }
            }
        }
        
        return data
    
    # Getter methods for easy access
    
    def get_storage_config(self) -> StorageConfig:
        """获取存储配置"""
        return self._config.storage
    
    def get_search_parameters(self) -> SearchParameters:
        """获取搜索参数"""
        return self._config.search
    
    def get_organization_config(self) -> OrganizationConfig:
        """获取组织配置"""
        return self._config.organization
    
    def get_processing_config(self) -> ProcessingConfig:
        """获取处理配置"""
        return self._config.processing
    
    def get_config(self) -> KnowledgeAgentConfig:
        """获取完整配置"""
        return self._config
    
    # Configuration update methods
    
    def update_search_parameters(self, **kwargs) -> None:
        """更新搜索参数
        
        Args:
            **kwargs: 搜索参数键值对
        """
        for key, value in kwargs.items():
            if hasattr(self._config.search, key):
                setattr(self._config.search, key, value)
        
        self._config.last_modified = datetime.now()
    
    def add_classification_rule(self, rule: ClassificationRule) -> None:
        """添加自定义分类规则
        
        Args:
            rule: 分类规则对象
        """
        self._config.organization.custom_rules.append(rule)
        self._config.last_modified = datetime.now()
    
    def remove_classification_rule(self, rule_name: str) -> bool:
        """删除自定义分类规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 如果删除成功返回True，否则返回False
        """
        original_length = len(self._config.organization.custom_rules)
        self._config.organization.custom_rules = [
            rule for rule in self._config.organization.custom_rules
            if rule.name != rule_name
        ]
        
        if len(self._config.organization.custom_rules) < original_length:
            self._config.last_modified = datetime.now()
            return True
        
        return False
    
    def get_classification_rules(self, enabled_only: bool = True) -> List[ClassificationRule]:
        """获取分类规则列表
        
        Args:
            enabled_only: 是否只返回启用的规则
            
        Returns:
            List[ClassificationRule]: 分类规则列表
        """
        rules = self._config.organization.custom_rules
        
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        
        # 按优先级排序
        return sorted(rules, key=lambda r: r.priority, reverse=True)
    
    def validate(self) -> List[str]:
        """验证配置有效性
        
        Returns:
            List[str]: 验证错误列表，如果为空则配置有效
        """
        errors = []
        
        # 验证搜索参数
        if self._config.search.min_relevance < 0 or self._config.search.min_relevance > 1:
            errors.append("search.min_relevance must be between 0 and 1")
        
        if self._config.search.max_results <= 0:
            errors.append("search.max_results must be positive")
        
        # 验证组织配置
        if self._config.organization.classification_confidence_threshold < 0 or \
           self._config.organization.classification_confidence_threshold > 1:
            errors.append("organization.classification_confidence_threshold must be between 0 and 1")
        
        if self._config.organization.relationship_strength_threshold < 0 or \
           self._config.organization.relationship_strength_threshold > 1:
            errors.append("organization.relationship_strength_threshold must be between 0 and 1")
        
        # 验证处理配置
        if self._config.processing.max_file_size <= 0:
            errors.append("processing.max_file_size must be positive")
        
        if self._config.processing.web_timeout <= 0:
            errors.append("processing.web_timeout must be positive")
        
        # 验证自定义规则
        rule_names = set()
        for rule in self._config.organization.custom_rules:
            if not rule.name:
                errors.append("Classification rule must have a name")
            elif rule.name in rule_names:
                errors.append(f"Duplicate classification rule name: {rule.name}")
            else:
                rule_names.add(rule.name)
            
            if not rule.keywords:
                errors.append(f"Classification rule '{rule.name}' must have keywords")
            
            if not rule.category:
                errors.append(f"Classification rule '{rule.name}' must have a category")
        
        return errors


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[Union[str, Path]] = None) -> ConfigManager:
    """获取全局配置管理器实例
    
    Args:
        config_path: 配置文件路径，仅在首次调用时有效
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    
    return _config_manager


def reset_config_manager() -> None:
    """重置全局配置管理器（主要用于测试）"""
    global _config_manager
    _config_manager = None
