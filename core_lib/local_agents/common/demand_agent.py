"""
通用需求代理 - 用于模拟各种需求模式

这个组件应该在 core_lib 中，而不是在教学案例中重复定义
"""

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from typing import Dict, Any, Callable, Optional
import numpy as np

class DemandAgent(Agent):
    """通用需求代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 demand_function: Optional[Callable[[float], float]] = None,
                 demand_schedule: Optional[Dict[float, float]] = None):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_function = demand_function
        self.demand_schedule = demand_schedule or {}
        
    def run(self, current_time: float):
        """根据配置生成需求"""
        if self.demand_function:
            demand = self.demand_function(current_time)
        elif int(current_time) in self.demand_schedule:
            demand = self.demand_schedule[int(current_time)]
        else:
            demand = 0.0
            
        if demand > 0:
            self.bus.publish(self.demand_topic, {'value': demand})

class StepDemandAgent(DemandAgent):
    """阶跃需求代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 steps: Dict[float, float]):
        super().__init__(agent_id, message_bus, demand_topic, demand_schedule=steps)

class SinusoidalDemandAgent(DemandAgent):
    """正弦需求代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str,
                 amplitude: float = 10.0, period: float = 200.0, offset: float = 10.0):
        def sin_function(t):
            return offset + amplitude * np.sin(2 * np.pi * t / period)
        super().__init__(agent_id, message_bus, demand_topic, demand_function=sin_function)
