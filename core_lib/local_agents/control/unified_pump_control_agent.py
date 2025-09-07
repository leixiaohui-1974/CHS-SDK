"""
统一泵控制代理 - 基于统一架构

特点：
1. 继承 UnifiedLocalControlAgent
2. 使用 DISCRETE 控制策略
3. 集成泵站协调功能
4. 保持架构一致性
"""
from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.pump import PumpStation
import math
from typing import Optional, Dict, Any

class UnifiedPumpControlAgent(UnifiedLocalControlAgent):
    """
    统一泵控制代理
    
    继承统一架构，添加泵站特定功能：
    - 泵站协调控制
    - 需求驱动控制
    - 离散开关逻辑
    - 流量需求管理
    """
    
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 pump_station: PumpStation,
                 demand_topic: str,
                 control_topic_prefix: str,
                 dt: float = 1.0,
                 **kwargs):
        """
        初始化统一泵控制代理
        
        Args:
            agent_id: 代理标识
            message_bus: 消息总线
            pump_station: 泵站对象
            demand_topic: 需求主题
            control_topic_prefix: 控制主题前缀
            dt: 时间步长
            **kwargs: 泵站特定配置
        """
        # 调用父类构造函数，使用离散控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            dt=dt,
            control_strategy=ControlStrategy.DISCRETE,
            observation_topic=demand_topic,  # 需求作为观测
            observation_key='value',  # 需求值
            action_topic=None,  # 多执行器模式，不需要单一动作主题
            **kwargs
        )
        
        # 泵站特定属性
        self.pump_station = pump_station
        self.control_topic_prefix = control_topic_prefix
        self.pumps = self.pump_station.pumps
        self.current_demand = 0.0
        
        # 假设所有泵具有相同的流量率（简化）
        self.pump_flow_rate = self.pumps[0].get_parameters().get('max_flow_rate', 1.0) if self.pumps else 0
        
        print(f"UnifiedPumpControlAgent '{self.agent_id}' initialized with {len(self.pumps)} pumps")
    
    def _initialize_device_specific(self, **kwargs):
        """泵站特定初始化"""
        # 泵站配置
        self.max_pumps = kwargs.get('max_pumps', len(self.pumps) if hasattr(self, 'pumps') else 0)
        self.min_pumps = kwargs.get('min_pumps', 0)
        self.pump_startup_delay = kwargs.get('pump_startup_delay', 0)
        
        # 控制策略配置
        self.control_strategy_type = kwargs.get('control_strategy', 'demand_based')  # demand_based, level_based, etc.
        
        print(f"Pump station configured: {self.max_pumps} max pumps, {self.min_pumps} min pumps")
    
    def preprocess_observation(self, message: Message) -> Message:
        """泵站特定观测预处理"""
        # 提取需求信息
        demand = message.get('value')
        if isinstance(demand, (int, float)):
            self.current_demand = demand
            print(f"[{self.agent_id}] Received flow demand: {self.current_demand:.2f} m³/s")
        
        return message
    
    def compute_discrete_control_action(self, message: Message) -> Optional[Dict[str, int]]:
        """计算离散控制动作（泵开关状态）"""
        if not self.pumps or self.pump_flow_rate <= 0:
            return None
        
        # 计算满足当前需求所需的泵数量
        num_pumps_needed = math.ceil(self.current_demand / self.pump_flow_rate)
        
        # 确保泵数量在合理范围内
        num_pumps_needed = max(self.min_pumps, min(num_pumps_needed, self.max_pumps))
        
        print(f"[{self.agent_id}] Demand: {self.current_demand:.2f} m³/s, Activating {num_pumps_needed}/{len(self.pumps)} pumps")
        
        # 生成泵控制信号字典
        pump_control_signals = {}
        for i, pump in enumerate(self.pumps):
            control_signal = 1 if i < num_pumps_needed else 0
            topic = f"{self.control_topic_prefix}.{pump.name}"
            pump_control_signals[topic] = control_signal
        
        return pump_control_signals
    
    def handle_command_message(self, message: Message):
        """处理泵站特定命令"""
        command_type = message.get('command_type')
        
        if command_type == 'set_demand':
            # 直接设置需求
            new_demand = message.get('demand', 0.0)
            self.current_demand = new_demand
            print(f"[{self.agent_id}] Manual demand set to: {new_demand:.2f} m³/s")
        
        elif command_type == 'emergency_stop':
            # 紧急停止所有泵
            pump_control_signals = {}
            for pump in self.pumps:
                topic = f"{self.control_topic_prefix}.{pump.name}"
                pump_control_signals[topic] = 0
            
            self.publish_action(pump_control_signals)
            print(f"[{self.agent_id}] Emergency stop activated")
        
        elif command_type == 'set_pump_count':
            # 直接设置泵数量
            pump_count = message.get('pump_count', 0)
            pump_count = max(0, min(pump_count, len(self.pumps)))
            
            pump_control_signals = {}
            for i, pump in enumerate(self.pumps):
                control_signal = 1 if i < pump_count else 0
                topic = f"{self.control_topic_prefix}.{pump.name}"
                pump_control_signals[topic] = control_signal
            
            self.publish_action(pump_control_signals)
            print(f"[{self.agent_id}] Pump count set to: {pump_count}")
    
    def get_pump_status(self) -> Dict[str, Any]:
        """获取泵站状态信息"""
        active_pumps = sum(1 for pump in self.pumps if hasattr(pump, 'is_running') and pump.is_running)
        
        return {
            'total_pumps': len(self.pumps),
            'active_pumps': active_pumps,
            'current_demand': self.current_demand,
            'total_capacity': len(self.pumps) * self.pump_flow_rate,
            'utilization': active_pumps / len(self.pumps) if self.pumps else 0
        }
