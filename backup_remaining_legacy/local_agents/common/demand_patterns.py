"""
需求模式模块 - 提供各种需求生成模式

遵循单一职责原则，每个类只负责一种需求模式
"""

from abc import abstractmethod
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Dict, Any, Callable, Optional
import numpy as np

class DemandPattern(Agent):
    """需求模式基类 - 单一职责：生成需求值"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        
    @abstractmethod
    def generate_demand(self, current_time: float) -> float:
        """生成需求值"""
        pass
        
    def run(self, current_time: float):
        """运行需求生成"""
        demand = self.generate_demand(current_time)
        self.bus.publish(self.demand_topic, {'value': demand})

class ConstantDemandPattern(DemandPattern):
    """恒定需求模式"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str, 
                 constant_value: float = 10.0):
        super().__init__(agent_id, message_bus, demand_topic)
        self.constant_value = constant_value
        
    def generate_demand(self, current_time: float) -> float:
        return self.constant_value

class StepDemandPattern(DemandPattern):
    """阶跃需求模式"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 steps: Dict[float, float]):
        super().__init__(agent_id, message_bus, demand_topic)
        self.steps = steps
        
    def generate_demand(self, current_time: float) -> float:
        # 找到当前时间对应的需求值
        for time_point in sorted(self.steps.keys(), reverse=True):
            if current_time >= time_point:
                return self.steps[time_point]
        return 0.0

class SinusoidalDemandPattern(DemandPattern):
    """正弦需求模式"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 amplitude: float = 10.0, period: float = 200.0, offset: float = 10.0):
        super().__init__(agent_id, message_bus, demand_topic)
        self.amplitude = amplitude
        self.period = period
        self.offset = offset
        
    def generate_demand(self, current_time: float) -> float:
        return self.offset + self.amplitude * np.sin(2 * np.pi * current_time / self.period)

class VariableDemandPattern(DemandPattern):
    """变化需求模式"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 base_value: float = 10.0, variation_amplitude: float = 5.0, 
                 variation_period: float = 150.0, noise_level: float = 2.0):
        super().__init__(agent_id, message_bus, demand_topic)
        self.base_value = base_value
        self.variation_amplitude = variation_amplitude
        self.variation_period = variation_period
        self.noise_level = noise_level
        
    def generate_demand(self, current_time: float) -> float:
        variation = self.variation_amplitude * np.sin(2 * np.pi * current_time / self.variation_period)
        noise = self.noise_level * np.random.normal(0, 1)
        return max(0, self.base_value + variation + noise)
