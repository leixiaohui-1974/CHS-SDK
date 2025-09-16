"""
统一Agent注册中心

提供Agent类型注册、发现和实例化功能
"""
from typing import Dict, Type, List, Optional, Any
from core_lib.core.new_interfaces import BaseAgent, DeviceType, ControlStrategy, DataSourceType
from core_lib.core.factories import (
    get_global_agent_factory, get_global_controller_factory, get_global_datasource_factory
)

def register_all_agents():
    """注册所有Agent类型到工厂"""
    
    agent_factory = get_global_agent_factory()
    controller_factory = get_global_controller_factory()
    datasource_factory = get_global_datasource_factory()
    
    # 注册数据源Agent
    try:
        from core_lib.core.new_agents.service_agents.data.unified_data_source import UnifiedDataSourceAgent
        agent_factory.register_agent_type('UnifiedDataSourceAgent', UnifiedDataSourceAgent)
        agent_factory.register_agent_type('DataSourceAgent', UnifiedDataSourceAgent)
        
        # 注册到数据源工厂
        datasource_factory.register_datasource_type(DataSourceType.CSV, UnifiedDataSourceAgent)
        datasource_factory.register_datasource_type(DataSourceType.DATABASE, UnifiedDataSourceAgent)
        datasource_factory.register_datasource_type(DataSourceType.API, UnifiedDataSourceAgent)
        datasource_factory.register_datasource_type(DataSourceType.REALTIME, UnifiedDataSourceAgent)
        datasource_factory.register_datasource_type(DataSourceType.MOCK, UnifiedDataSourceAgent)
        
        print("[Registry] Registered UnifiedDataSourceAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register UnifiedDataSourceAgent: {e}")
    
    # 注册本地控制Agent
    try:
        from core_lib.core.new_agents.local_agents.control.unified_local_control import UnifiedLocalControlAgent
        agent_factory.register_agent_type('UnifiedLocalControlAgent', UnifiedLocalControlAgent)
        agent_factory.register_agent_type('LocalControlAgent', UnifiedLocalControlAgent)
        
        print("[Registry] Registered UnifiedLocalControlAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register UnifiedLocalControlAgent: {e}")
    
    # 注册中央协调Agent
    try:
        from core_lib.core.new_agents.central_agents.coordination.central_coordinator import CentralCoordinatorAgentImpl
        agent_factory.register_agent_type('CentralCoordinatorAgent', CentralCoordinatorAgentImpl)
        agent_factory.register_agent_type('CentralCoordinator', CentralCoordinatorAgentImpl)
        
        print("[Registry] Registered CentralCoordinatorAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register CentralCoordinatorAgent: {e}")
    
    # 注册中央控制Agent
    try:
        from core_lib.core.new_agents.central_agents.control.central_control import CentralControlAgentImpl
        agent_factory.register_agent_type('CentralControlAgent', CentralControlAgentImpl)
        agent_factory.register_agent_type('CentralControl', CentralControlAgentImpl)
        
        print("[Registry] Registered CentralControlAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register CentralControlAgent: {e}")
    
    # 注册扰动Agent
    try:
        from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import UnifiedDisturbanceAgent
        agent_factory.register_agent_type('UnifiedDisturbanceAgent', UnifiedDisturbanceAgent)
        agent_factory.register_agent_type('DisturbanceAgent', UnifiedDisturbanceAgent)
        
        print("[Registry] Registered UnifiedDisturbanceAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register UnifiedDisturbanceAgent: {e}")
    
    # 注册识别Agent
    try:
        from core_lib.core.new_agents.service_agents.identification.unified_identification import UnifiedIdentificationAgent
        agent_factory.register_agent_type('UnifiedIdentificationAgent', UnifiedIdentificationAgent)
        agent_factory.register_agent_type('IdentificationAgent', UnifiedIdentificationAgent)
        
        print("[Registry] Registered UnifiedIdentificationAgent")
    except ImportError as e:
        print(f"[Registry] Failed to register UnifiedIdentificationAgent: {e}")
    
    # 注册适配器（向后兼容）
    _register_adapters(agent_factory)
    
    print(f"[Registry] Registration complete. Total agent types: {len(agent_factory.get_supported_types())}")

def _register_adapters(agent_factory):
    """注册适配器类型"""
    try:
        # 数据源适配器
        from core_lib.core.new_agents.service_agents.data.unified_data_source import (
            CsvReaderAgentAdapter, CsvInflowAgentAdapter
        )
        agent_factory.register_agent_type('CsvReaderAgent', CsvReaderAgentAdapter)
        agent_factory.register_agent_type('CsvInflowAgent', CsvInflowAgentAdapter)
        
        # 控制Agent适配器
        from core_lib.core.new_agents.local_agents.control.unified_local_control import (
            GateControlAgentAdapter, PumpControlAgentAdapter, ValveControlAgentAdapter
        )
        agent_factory.register_agent_type('GateControlAgent', GateControlAgentAdapter)
        agent_factory.register_agent_type('PumpControlAgent', PumpControlAgentAdapter)
        agent_factory.register_agent_type('ValveControlAgent', ValveControlAgentAdapter)
        
        # 扰动适配器
        from core_lib.core.new_agents.service_agents.disturbance.unified_disturbance import (
            RainfallAgentAdapter, WaterUseAgentAdapter, CsvReaderAgentDisturbanceAdapter
        )
        agent_factory.register_agent_type('RainfallAgent', RainfallAgentAdapter)
        agent_factory.register_agent_type('WaterUseAgent', WaterUseAgentAdapter)
        agent_factory.register_agent_type('CsvReaderAgentDisturbance', CsvReaderAgentDisturbanceAdapter)
        
        # 识别适配器
        from core_lib.core.new_agents.service_agents.identification.unified_identification import (
            IdentificationAgentAdapter, ModelUpdaterAgentAdapter
        )
        agent_factory.register_agent_type('IdentificationAgentOld', IdentificationAgentAdapter)
        agent_factory.register_agent_type('ModelUpdaterAgent', ModelUpdaterAgentAdapter)
        
        print("[Registry] Registered adapter types for backward compatibility")
        
    except ImportError as e:
        print(f"[Registry] Failed to register some adapters: {e}")

def create_agent_from_config(config: Dict[str, Any]) -> Optional[BaseAgent]:
    """从配置创建Agent"""
    try:
        agent_factory = get_global_agent_factory()
        
        agent_type = config.get('agent_type')
        agent_id = config.get('agent_id')
        
        if not agent_type or not agent_id:
            raise ValueError("agent_type and agent_id are required")
        
        agent = agent_factory.create_agent(agent_type, agent_id, config)
        
        # 配置Agent
        if agent.configure(config):
            return agent
        else:
            print(f"[Registry] Failed to configure agent: {agent_id}")
            return None
            
    except Exception as e:
        print(f"[Registry] Failed to create agent from config: {e}")
        return None

def get_registered_agent_types() -> List[str]:
    """获取已注册的Agent类型"""
    agent_factory = get_global_agent_factory()
    return agent_factory.get_supported_types()

def get_registered_controller_strategies() -> List[ControlStrategy]:
    """获取已注册的控制策略"""
    controller_factory = get_global_controller_factory()
    return controller_factory.get_supported_strategies()

def get_registered_datasource_types() -> List[DataSourceType]:
    """获取已注册的数据源类型"""
    datasource_factory = get_global_datasource_factory()
    return datasource_factory.get_supported_types()

# 自动注册
if __name__ == "__main__":
    register_all_agents()
    
    print("\nRegistered Agent Types:")
    for agent_type in get_registered_agent_types():
        print(f"  - {agent_type}")
    
    print("\nRegistered Controller Strategies:")
    for strategy in get_registered_controller_strategies():
        print(f"  - {strategy.value}")
    
    print("\nRegistered Data Source Types:")
    for ds_type in get_registered_datasource_types():
        print(f"  - {ds_type.value}")
