"""
组件注册和依赖注入系统

提供组件注册、依赖注入和生命周期管理功能。
支持组件间的松耦合和可配置的依赖关系。
"""

import logging
from typing import Dict, Any, Optional, Type, Callable
from dataclasses import dataclass
from enum import Enum


class ComponentLifecycle(Enum):
    """组件生命周期状态"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ComponentMetadata:
    """组件元数据"""
    name: str
    component_type: Type
    instance: Optional[Any] = None
    lifecycle: ComponentLifecycle = ComponentLifecycle.NOT_INITIALIZED
    dependencies: list[str] = None
    factory: Optional[Callable] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ComponentRegistry:
    """
    组件注册表
    
    管理系统中所有组件的注册、初始化和依赖关系。
    提供依赖注入和生命周期管理功能。
    """
    
    def __init__(self):
        """初始化组件注册表"""
        self.logger = logging.getLogger("knowledge_agent.registry")
        self._components: Dict[str, ComponentMetadata] = {}
        self._initialization_order: list[str] = []
    
    def register(
        self,
        name: str,
        component_type: Type,
        factory: Optional[Callable] = None,
        dependencies: Optional[list[str]] = None
    ) -> None:
        """
        注册组件
        
        Args:
            name: 组件名称
            component_type: 组件类型
            factory: 组件工厂函数（可选）
            dependencies: 依赖的组件名称列表（可选）
        """
        if name in self._components:
            self.logger.warning(f"Component {name} already registered, overwriting")
        
        metadata = ComponentMetadata(
            name=name,
            component_type=component_type,
            factory=factory,
            dependencies=dependencies or []
        )
        
        self._components[name] = metadata
        self.logger.info(f"Registered component: {name} (type: {component_type.__name__})")
    
    def get(self, name: str) -> Optional[Any]:
        """
        获取组件实例
        
        Args:
            name: 组件名称
            
        Returns:
            组件实例，如果不存在则返回None
        """
        if name not in self._components:
            self.logger.warning(f"Component {name} not found in registry")
            return None
        
        metadata = self._components[name]
        
        if metadata.instance is None:
            self.logger.warning(f"Component {name} not initialized yet")
            return None
        
        return metadata.instance
    
    def set_instance(self, name: str, instance: Any) -> None:
        """
        设置组件实例
        
        Args:
            name: 组件名称
            instance: 组件实例
        """
        if name not in self._components:
            self.logger.error(f"Cannot set instance for unregistered component: {name}")
            raise ValueError(f"Component {name} not registered")
        
        self._components[name].instance = instance
        self._components[name].lifecycle = ComponentLifecycle.INITIALIZED
        self.logger.info(f"Set instance for component: {name}")
    
    def initialize_all(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化所有注册的组件
        
        按照依赖关系顺序初始化组件。
        
        Args:
            config: 配置字典（可选）
        """
        self.logger.info("=" * 60)
        self.logger.info("Initializing all components...")
        self.logger.info("=" * 60)
        
        # 计算初始化顺序
        self._compute_initialization_order()
        
        # 按顺序初始化组件
        for component_name in self._initialization_order:
            try:
                self._initialize_component(component_name, config or {})
            except Exception as e:
                self.logger.error(f"Failed to initialize component {component_name}: {e}")
                self._components[component_name].lifecycle = ComponentLifecycle.ERROR
                raise
        
        self.logger.info("=" * 60)
        self.logger.info("All components initialized successfully")
        self.logger.info("=" * 60)
    
    def _compute_initialization_order(self) -> None:
        """计算组件初始化顺序（拓扑排序）"""
        # 简单的拓扑排序实现
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            
            if name in visited:
                return
            
            temp_visited.add(name)
            
            # 访问依赖
            if name in self._components:
                for dep in self._components[name].dependencies:
                    if dep not in self._components:
                        raise ValueError(f"Component {name} depends on unregistered component {dep}")
                    visit(dep)
            
            temp_visited.remove(name)
            visited.add(name)
            order.append(name)
        
        # 访问所有组件
        for component_name in self._components:
            if component_name not in visited:
                visit(component_name)
        
        self._initialization_order = order
        self.logger.info(f"Computed initialization order: {' -> '.join(order)}")
    
    def _initialize_component(self, name: str, config: Dict[str, Any]) -> None:
        """
        初始化单个组件
        
        Args:
            name: 组件名称
            config: 配置字典
        """
        metadata = self._components[name]
        
        if metadata.lifecycle != ComponentLifecycle.NOT_INITIALIZED:
            self.logger.info(f"Component {name} already initialized, skipping")
            return
        
        self.logger.info(f"Initializing component: {name}")
        metadata.lifecycle = ComponentLifecycle.INITIALIZING
        
        try:
            # 收集依赖实例
            dependencies = {}
            for dep_name in metadata.dependencies:
                dep_instance = self.get(dep_name)
                if dep_instance is None:
                    raise ValueError(f"Dependency {dep_name} not initialized")
                dependencies[dep_name] = dep_instance
            
            # 创建组件实例
            if metadata.factory:
                # 使用工厂函数
                instance = metadata.factory(config, dependencies)
            else:
                # 使用默认构造函数
                component_config = config.get(name, {})
                instance = metadata.component_type(component_config)
            
            metadata.instance = instance
            metadata.lifecycle = ComponentLifecycle.INITIALIZED
            
            self.logger.info(f"✓ Component {name} initialized successfully")
            
        except Exception as e:
            metadata.lifecycle = ComponentLifecycle.ERROR
            self.logger.error(f"✗ Failed to initialize component {name}: {e}")
            raise
    
    def shutdown_all(self) -> None:
        """关闭所有组件"""
        self.logger.info("=" * 60)
        self.logger.info("Shutting down all components...")
        self.logger.info("=" * 60)
        
        # 按照初始化顺序的逆序关闭组件
        shutdown_order = list(reversed(self._initialization_order))
        
        errors = []
        
        for component_name in shutdown_order:
            try:
                self._shutdown_component(component_name)
            except Exception as e:
                error_msg = f"Failed to shutdown component {component_name}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            self.logger.warning(f"Shutdown completed with {len(errors)} errors")
        else:
            self.logger.info("All components shut down successfully")
        
        self.logger.info("=" * 60)
    
    def _shutdown_component(self, name: str) -> None:
        """
        关闭单个组件
        
        Args:
            name: 组件名称
        """
        if name not in self._components:
            return
        
        metadata = self._components[name]
        
        if metadata.lifecycle in [ComponentLifecycle.NOT_INITIALIZED, ComponentLifecycle.STOPPED]:
            return
        
        self.logger.info(f"Shutting down component: {name}")
        metadata.lifecycle = ComponentLifecycle.STOPPING
        
        try:
            if metadata.instance and hasattr(metadata.instance, 'shutdown'):
                metadata.instance.shutdown()
            elif metadata.instance and hasattr(metadata.instance, 'close'):
                metadata.instance.close()
            elif metadata.instance and hasattr(metadata.instance, 'cleanup'):
                metadata.instance.cleanup()
            
            metadata.lifecycle = ComponentLifecycle.STOPPED
            self.logger.info(f"✓ Component {name} shut down successfully")
            
        except Exception as e:
            metadata.lifecycle = ComponentLifecycle.ERROR
            self.logger.error(f"✗ Failed to shutdown component {name}: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取所有组件的状态
        
        Returns:
            组件状态字典
        """
        status = {}
        
        for name, metadata in self._components.items():
            status[name] = {
                "type": metadata.component_type.__name__,
                "lifecycle": metadata.lifecycle.value,
                "dependencies": metadata.dependencies,
                "initialized": metadata.instance is not None
            }
        
        return status
    
    def log_status(self) -> None:
        """记录所有组件的状态到日志"""
        self.logger.info("=" * 60)
        self.logger.info("Component Registry Status")
        self.logger.info("=" * 60)
        
        status = self.get_status()
        
        for name, info in status.items():
            self.logger.info(f"\nComponent: {name}")
            self.logger.info(f"  Type: {info['type']}")
            self.logger.info(f"  Lifecycle: {info['lifecycle']}")
            self.logger.info(f"  Initialized: {info['initialized']}")
            if info['dependencies']:
                self.logger.info(f"  Dependencies: {', '.join(info['dependencies'])}")
        
        self.logger.info("=" * 60)


# 全局组件注册表实例
_component_registry: Optional[ComponentRegistry] = None


def get_component_registry() -> ComponentRegistry:
    """获取全局组件注册表实例"""
    global _component_registry
    if _component_registry is None:
        _component_registry = ComponentRegistry()
    return _component_registry


def reset_component_registry() -> None:
    """重置全局组件注册表（主要用于测试）"""
    global _component_registry
    _component_registry = None
