"""
控制代理工厂类 - 统一架构

特点：
1. 统一创建所有类型的控制代理
2. 基于配置自动选择控制策略
3. 简化控制代理的实例化过程
4. 提供向后兼容性
"""
from typing import Dict, Any, Optional
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core.interfaces import Controller
from core_lib.physical_objects.pump import PumpStation

from .unified_local_control_agent import ControlStrategy
from .gate_control_agent import GateControlAgent
from .pump_control_agent import PumpControlAgent
from .valve_control_agent import ValveControlAgent
from .water_turbine_control_agent import WaterTurbineControlAgent

class ControlAgentFactory:
    """
    控制代理工厂类
    
    提供统一的接口来创建各种类型的控制代理，
    自动处理控制策略选择和参数配置。
    """
    
    # 控制代理类型映射
    AGENT_TYPES = {
        'gate': GateControlAgent,
        'pump': PumpControlAgent,
        'valve': ValveControlAgent,
        'water_turbine': WaterTurbineControlAgent,
        'turbine': WaterTurbineControlAgent,  # 别名
        'hydropower': WaterTurbineControlAgent,  # 别名
    }
    
    # 默认控制策略映射
    DEFAULT_STRATEGIES = {
        'gate': ControlStrategy.MULTI_ACTUATOR,
        'pump': ControlStrategy.DISCRETE,
        'valve': ControlStrategy.CONTINUOUS,
        'water_turbine': ControlStrategy.CONTINUOUS,
        'turbine': ControlStrategy.CONTINUOUS,
        'hydropower': ControlStrategy.CONTINUOUS,
    }
    
    @classmethod
    def create_control_agent(cls,
                           agent_type: str,
                           agent_id: str,
                           message_bus: MessageBus,
                           time_step: float,
                           controller: Optional[Controller] = None,
                           **kwargs) -> 'UnifiedLocalControlAgent':
        """
        创建控制代理实例
        
        Args:
            agent_type: 代理类型 ('gate', 'pump', 'valve', 'water_turbine')
            agent_id: 代理唯一标识
            message_bus: 消息总线
            time_step: 时间步长
            controller: 控制器实例（泵控制代理不需要）
            **kwargs: 设备特定配置参数
            
        Returns:
            控制代理实例
            
        Raises:
            ValueError: 不支持的代理类型
        """
        agent_type_lower = agent_type.lower()
        
        if agent_type_lower not in cls.AGENT_TYPES:
            supported_types = list(cls.AGENT_TYPES.keys())
            raise ValueError(f"不支持的控制代理类型: {agent_type}. 支持的类型: {supported_types}")
        
        agent_class = cls.AGENT_TYPES[agent_type_lower]
        
        # 根据代理类型准备特定参数
        if agent_type_lower == 'pump':
            return cls._create_pump_agent(agent_class, agent_id, message_bus, time_step, **kwargs)
        else:
            return cls._create_standard_agent(agent_class, agent_id, message_bus, time_step, controller, **kwargs)
    
    @classmethod
    def _create_pump_agent(cls, agent_class, agent_id: str, message_bus: MessageBus, 
                          time_step: float, **kwargs):
        """创建泵控制代理"""
        # 泵控制代理需要特定参数
        required_params = ['pump_station', 'demand_topic', 'control_topic_prefix']
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"泵控制代理缺少必需参数: {param}")
        
        return agent_class(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
            **kwargs
        )
    
    @classmethod
    def _create_standard_agent(cls, agent_class, agent_id: str, message_bus: MessageBus,
                             time_step: float, controller: Controller, **kwargs):
        """创建标准控制代理（闸门、阀门、水轮机）"""
        # 标准控制代理需要控制器
        if controller is None:
            raise ValueError(f"标准控制代理需要控制器参数")
        
        # 提取标准参数
        observation_topic = kwargs.pop('observation_topic', None)
        observation_key = kwargs.pop('observation_key', 'value')
        action_topic = kwargs.pop('action_topic', None)
        command_topic = kwargs.pop('command_topic', None)
        feedback_topic = kwargs.pop('feedback_topic', None)
        
        if observation_topic is None:
            raise ValueError("标准控制代理需要 observation_topic 参数")
        
        if action_topic is None:
            action_topic = f'control.{agent_id}.action'
        
        return agent_class(
            agent_id=agent_id,
            controller=controller,
            message_bus=message_bus,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            time_step=time_step,
            command_topic=command_topic,
            feedback_topic=feedback_topic,
            **kwargs
        )
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any], message_bus: MessageBus, 
                          time_step: float, controller: Optional[Controller] = None):
        """
        从配置字典创建控制代理
        
        Args:
            config: 配置字典，必须包含 'type' 和 'agent_id' 键
            message_bus: 消息总线
            time_step: 时间步长
            controller: 控制器实例
            
        Returns:
            控制代理实例
        """
        if 'type' not in config:
            raise ValueError("配置字典必须包含 'type' 键")
        if 'agent_id' not in config:
            raise ValueError("配置字典必须包含 'agent_id' 键")
        
        agent_type = config.pop('type')
        agent_id = config.pop('agent_id')
        
        return cls.create_control_agent(
            agent_type=agent_type,
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
            controller=controller,
            **config
        )
    
    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的控制代理类型列表"""
        return list(cls.AGENT_TYPES.keys())
    
    @classmethod
    def get_default_strategy(cls, agent_type: str) -> ControlStrategy:
        """获取指定代理类型的默认控制策略"""
        agent_type_lower = agent_type.lower()
        return cls.DEFAULT_STRATEGIES.get(agent_type_lower, ControlStrategy.CONTINUOUS)


# 向后兼容的便捷函数
def create_gate_control_agent(agent_id: str, controller: Controller, message_bus: MessageBus,
                            observation_topic: str, observation_key: str, action_topic: str,
                            time_step: float, **kwargs) -> GateControlAgent:
    """创建闸门控制代理的便捷函数"""
    return ControlAgentFactory.create_control_agent(
        agent_type='gate',
        agent_id=agent_id,
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic=observation_topic,
        observation_key=observation_key,
        action_topic=action_topic,
        **kwargs
    )

def create_pump_control_agent(agent_id: str, message_bus: MessageBus, pump_station: PumpStation,
                            demand_topic: str, control_topic_prefix: str,
                            time_step: float = 1.0, **kwargs) -> PumpControlAgent:
    """创建泵控制代理的便捷函数"""
    return ControlAgentFactory.create_control_agent(
        agent_type='pump',
        agent_id=agent_id,
        message_bus=message_bus,
        time_step=time_step,
        pump_station=pump_station,
        demand_topic=demand_topic,
        control_topic_prefix=control_topic_prefix,
        **kwargs
    )

def create_valve_control_agent(agent_id: str, controller: Controller, message_bus: MessageBus,
                             observation_topic: str, observation_key: str, action_topic: str,
                             time_step: float, **kwargs) -> ValveControlAgent:
    """创建阀门控制代理的便捷函数"""
    return ControlAgentFactory.create_control_agent(
        agent_type='valve',
        agent_id=agent_id,
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic=observation_topic,
        observation_key=observation_key,
        action_topic=action_topic,
        **kwargs
    )

def create_water_turbine_control_agent(agent_id: str, controller: Controller, message_bus: MessageBus,
                                     observation_topic: str, observation_key: str, action_topic: str,
                                     time_step: float, **kwargs) -> WaterTurbineControlAgent:
    """创建水轮机控制代理的便捷函数"""
    return ControlAgentFactory.create_control_agent(
        agent_type='water_turbine',
        agent_id=agent_id,
        message_bus=message_bus,
        time_step=time_step,
        controller=controller,
        observation_topic=observation_topic,
        observation_key=observation_key,
        action_topic=action_topic,
        **kwargs
    )
