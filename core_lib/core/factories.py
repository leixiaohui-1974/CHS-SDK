"""
基础工厂实现

提供Agent、控制器、数据源的创建工厂
"""
from typing import Dict, Any, List, Type, Optional
from core_lib.core.new_interfaces import (
    BaseAgent, AgentFactory, ControllerFactory, DataSourceFactory,
    ControlStrategy, DataSourceType, Config
)
import importlib
import inspect

class SimpleAgentFactory(AgentFactory):
    """简单Agent工厂实现"""
    
    def __init__(self):
        self._agent_registry: Dict[str, Type[BaseAgent]] = {}
        self._register_builtin_agents()
    
    def _register_builtin_agents(self):
        """注册内置Agent类型"""
        # 这里将在后续阶段注册具体的Agent实现
        pass
    
    def register_agent_type(self, agent_type: str, agent_class: Type[BaseAgent]):
        """注册Agent类型"""
        self._agent_registry[agent_type] = agent_class
        print(f"[AgentFactory] Registered agent type: {agent_type}")
    
    def create_agent(self, agent_type: str, agent_id: str, config: Config) -> BaseAgent:
        """创建Agent"""
        if agent_type not in self._agent_registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self._agent_registry[agent_type]
        
        # 检查构造函数参数
        sig = inspect.signature(agent_class.__init__)
        params = list(sig.parameters.keys())[1:]  # 排除self
        
        # 准备构造参数
        constructor_args = {'agent_id': agent_id}
        
        # 从配置中提取构造参数
        for param in params:
            if param in config:
                constructor_args[param] = config[param]
            elif param == 'config':
                constructor_args[param] = config
        
        try:
            agent = agent_class(**constructor_args)
            print(f"[AgentFactory] Created agent: {agent_type}({agent_id})")
            return agent
        except Exception as e:
            raise RuntimeError(f"Failed to create agent {agent_type}({agent_id}): {e}")
    
    def get_supported_types(self) -> List[str]:
        """获取支持的Agent类型"""
        return list(self._agent_registry.keys())

class SimpleControllerFactory(ControllerFactory):
    """简单控制器工厂实现"""
    
    def __init__(self):
        self._controller_registry: Dict[ControlStrategy, Type] = {}
        self._register_builtin_controllers()
    
    def _register_builtin_controllers(self):
        """注册内置控制器类型"""
        # PID控制器
        try:
            from core_lib.core_engine.solver.pid_controller import PIDController
            self._controller_registry[ControlStrategy.PID] = PIDController
        except ImportError:
            print("[ControllerFactory] PIDController not available")
        
        # MPC控制器
        try:
            from core_lib.central_agents.control.mpc_agent import MPCController
            self._controller_registry[ControlStrategy.MPC] = MPCController
        except ImportError:
            print("[ControllerFactory] MPCController not available")
    
    def register_controller_type(self, strategy: ControlStrategy, controller_class: Type):
        """注册控制器类型"""
        self._controller_registry[strategy] = controller_class
        print(f"[ControllerFactory] Registered controller: {strategy}")
    
    def create_controller(self, strategy: ControlStrategy, config: Config) -> Any:
        """创建控制器"""
        if strategy not in self._controller_registry:
            raise ValueError(f"Unknown control strategy: {strategy}")
        
        controller_class = self._controller_registry[strategy]
        
        try:
            # 检查构造函数参数
            sig = inspect.signature(controller_class.__init__)
            params = list(sig.parameters.keys())[1:]  # 排除self
            
            # 准备构造参数
            constructor_args = {}
            for param in params:
                if param in config:
                    constructor_args[param] = config[param]
            
            controller = controller_class(**constructor_args)
            print(f"[ControllerFactory] Created controller: {strategy}")
            return controller
        except Exception as e:
            raise RuntimeError(f"Failed to create controller {strategy}: {e}")
    
    def get_supported_strategies(self) -> List[ControlStrategy]:
        """获取支持的控制策略"""
        return list(self._controller_registry.keys())

class SimpleDataSourceFactory(DataSourceFactory):
    """简单数据源工厂实现"""
    
    def __init__(self):
        self._datasource_registry: Dict[DataSourceType, Type] = {}
        self._register_builtin_datasources()
    
    def _register_builtin_datasources(self):
        """注册内置数据源类型"""
        # 将在阶段3中实现具体的数据源
        pass
    
    def register_datasource_type(self, source_type: DataSourceType, datasource_class: Type):
        """注册数据源类型"""
        self._datasource_registry[source_type] = datasource_class
        print(f"[DataSourceFactory] Registered data source: {source_type}")
    
    def create_data_source(self, source_type: DataSourceType, config: Config):
        """创建数据源"""
        if source_type not in self._datasource_registry:
            raise ValueError(f"Unknown data source type: {source_type}")
        
        datasource_class = self._datasource_registry[source_type]
        
        try:
            # 检查构造函数参数
            sig = inspect.signature(datasource_class.__init__)
            params = list(sig.parameters.keys())[1:]  # 排除self
            
            # 准备构造参数
            constructor_args = {'source_type': source_type}
            for param in params:
                if param in config:
                    constructor_args[param] = config[param]
                elif param == 'config':
                    constructor_args[param] = config
            
            datasource = datasource_class(**constructor_args)
            print(f"[DataSourceFactory] Created data source: {source_type}")
            return datasource
        except Exception as e:
            raise RuntimeError(f"Failed to create data source {source_type}: {e}")
    
    def get_supported_types(self) -> List[DataSourceType]:
        """获取支持的数据源类型"""
        return list(self._datasource_registry.keys())

# 全局工厂实例
_global_agent_factory = None
_global_controller_factory = None
_global_datasource_factory = None

def get_global_agent_factory() -> SimpleAgentFactory:
    """获取全局Agent工厂实例"""
    global _global_agent_factory
    if _global_agent_factory is None:
        _global_agent_factory = SimpleAgentFactory()
    return _global_agent_factory

def get_global_controller_factory() -> SimpleControllerFactory:
    """获取全局控制器工厂实例"""
    global _global_controller_factory
    if _global_controller_factory is None:
        _global_controller_factory = SimpleControllerFactory()
    return _global_controller_factory

def get_global_datasource_factory() -> SimpleDataSourceFactory:
    """获取全局数据源工厂实例"""
    global _global_datasource_factory
    if _global_datasource_factory is None:
        _global_datasource_factory = SimpleDataSourceFactory()
    return _global_datasource_factory
