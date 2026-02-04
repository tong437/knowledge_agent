"""
配置管理器测试
"""

import json
import yaml
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from knowledge_agent.core.config_manager import (
    ConfigManager,
    ClassificationRule,
    SearchParameters,
    OrganizationConfig,
    ProcessingConfig,
    StorageConfig,
    KnowledgeAgentConfig,
    get_config_manager,
    reset_config_manager
)
from knowledge_agent.core.exceptions import ConfigurationError


class TestConfigManager:
    """配置管理器测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            config = manager.get_config()
            
            assert config.storage.type == "sqlite"
            assert config.search.min_relevance == 0.1
            assert config.organization.auto_classify is True
        finally:
            Path(config_path).unlink()
    
    def test_load_yaml_config(self):
        """测试加载YAML配置"""
        config_data = {
            'server': {'version': '1.0.0'},
            'storage': {
                'type': 'sqlite',
                'path': 'test.db',
                'backup_enabled': False
            },
            'search': {
                'min_relevance': 0.2,
                'max_results': 100
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            assert manager.get_config().version == '1.0.0'
            assert manager.get_storage_config().path == 'test.db'
            assert manager.get_storage_config().backup_enabled is False
            assert manager.get_search_parameters().min_relevance == 0.2
            assert manager.get_search_parameters().max_results == 100
        finally:
            Path(config_path).unlink()
    
    def test_load_json_config(self):
        """测试加载JSON配置"""
        config_data = {
            'server': {'version': '2.0.0'},
            'search': {
                'min_relevance': 0.3,
                'max_results': 200
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            assert manager.get_config().version == '2.0.0'
            assert manager.get_search_parameters().min_relevance == 0.3
        finally:
            Path(config_path).unlink()
    
    def test_save_yaml_config(self):
        """测试保存YAML配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            manager.update_search_parameters(min_relevance=0.5, max_results=75)
            manager.save()
            
            # 重新加载验证
            manager2 = ConfigManager(config_path)
            assert manager2.get_search_parameters().min_relevance == 0.5
            assert manager2.get_search_parameters().max_results == 75
        finally:
            Path(config_path).unlink()
    
    def test_save_json_config(self):
        """测试保存JSON配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)  # Write empty JSON object instead of empty file
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            manager.update_search_parameters(min_relevance=0.6)
            manager.save()
            
            # 重新加载验证
            manager2 = ConfigManager(config_path)
            assert manager2.get_search_parameters().min_relevance == 0.6
        finally:
            Path(config_path).unlink()
    
    def test_custom_classification_rules(self):
        """测试自定义分类规则"""
        config_data = {
            'organization': {
                'custom_classification_rules': [
                    {
                        'name': 'Python Code',
                        'keywords': ['python', 'def', 'class'],
                        'category': 'Programming',
                        'priority': 10,
                        'enabled': True
                    },
                    {
                        'name': 'Machine Learning',
                        'keywords': ['ml', 'neural', 'model'],
                        'category': 'AI',
                        'priority': 5,
                        'enabled': False
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            rules = manager.get_classification_rules(enabled_only=False)
            
            assert len(rules) == 2
            assert rules[0].name == 'Python Code'
            assert rules[0].priority == 10
            assert rules[1].name == 'Machine Learning'
            
            # 测试只获取启用的规则
            enabled_rules = manager.get_classification_rules(enabled_only=True)
            assert len(enabled_rules) == 1
            assert enabled_rules[0].name == 'Python Code'
        finally:
            Path(config_path).unlink()
    
    def test_add_classification_rule(self):
        """测试添加分类规则"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            rule = ClassificationRule(
                name='Test Rule',
                keywords=['test', 'example'],
                category='Testing',
                priority=1
            )
            
            manager.add_classification_rule(rule)
            rules = manager.get_classification_rules()
            
            assert len(rules) == 1
            assert rules[0].name == 'Test Rule'
            assert rules[0].category == 'Testing'
        finally:
            Path(config_path).unlink()
    
    def test_remove_classification_rule(self):
        """测试删除分类规则"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            rule1 = ClassificationRule(name='Rule1', keywords=['a'], category='Cat1')
            rule2 = ClassificationRule(name='Rule2', keywords=['b'], category='Cat2')
            
            manager.add_classification_rule(rule1)
            manager.add_classification_rule(rule2)
            
            assert len(manager.get_classification_rules()) == 2
            
            # 删除一个规则
            result = manager.remove_classification_rule('Rule1')
            assert result is True
            assert len(manager.get_classification_rules()) == 1
            assert manager.get_classification_rules()[0].name == 'Rule2'
            
            # 尝试删除不存在的规则
            result = manager.remove_classification_rule('NonExistent')
            assert result is False
        finally:
            Path(config_path).unlink()
    
    def test_update_search_parameters(self):
        """测试更新搜索参数"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            manager.update_search_parameters(
                min_relevance=0.25,
                max_results=150,
                enable_semantic=False
            )
            
            params = manager.get_search_parameters()
            assert params.min_relevance == 0.25
            assert params.max_results == 150
            assert params.enable_semantic is False
        finally:
            Path(config_path).unlink()
    
    def test_validate_config(self):
        """测试配置验证"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            # 有效配置
            errors = manager.validate()
            assert len(errors) == 0
            
            # 无效的搜索参数
            manager.update_search_parameters(min_relevance=1.5)
            errors = manager.validate()
            assert len(errors) > 0
            assert any('min_relevance' in error for error in errors)
            
            # 修复配置
            manager.update_search_parameters(min_relevance=0.5)
            errors = manager.validate()
            assert len(errors) == 0
        finally:
            Path(config_path).unlink()
    
    def test_reload_if_changed(self):
        """测试配置热重载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({'search': {'min_relevance': 0.1}}, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            assert manager.get_search_parameters().min_relevance == 0.1
            
            # 修改配置文件
            import time
            time.sleep(0.1)  # 确保文件修改时间不同
            
            with open(config_path, 'w') as f:
                yaml.safe_dump({'search': {'min_relevance': 0.9}}, f)
            
            # 重新加载
            reloaded = manager.reload_if_changed()
            assert reloaded is True
            assert manager.get_search_parameters().min_relevance == 0.9
            
            # 再次调用，文件未改变
            reloaded = manager.reload_if_changed()
            assert reloaded is False
        finally:
            Path(config_path).unlink()
    
    def test_config_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(ConfigurationError, match="not found"):
            manager = ConfigManager("nonexistent.yaml")
            manager.load()
    
    def test_invalid_config_format(self):
        """测试无效的配置格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid content")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Unsupported config format"):
                manager = ConfigManager(config_path)
                manager.load()
        finally:
            Path(config_path).unlink()
    
    def test_global_config_manager(self):
        """测试全局配置管理器"""
        reset_config_manager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump({'search': {'min_relevance': 0.7}}, f)
            config_path = f.name
        
        try:
            manager1 = get_config_manager(config_path)
            manager2 = get_config_manager()
            
            # 应该返回同一个实例
            assert manager1 is manager2
            assert manager1.get_search_parameters().min_relevance == 0.7
        finally:
            Path(config_path).unlink()
            reset_config_manager()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
