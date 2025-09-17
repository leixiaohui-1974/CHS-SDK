"""
泵控制代理 - 基于统一架构

特点：
1. 继承 UnifiedLocalControlAgent
2. 使用 DISCRETE 控制策略
3. 集成泵站特定功能
4. 保持架构一致性
"""
from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.pump import PumpStation
from typing import Optional, Dict, Any, Union
import math

class PumpControlAgent(UnifiedLocalControlAgent):
    """
    泵控制代理
    
    继承统一架构，添加泵站特定功能：
    - 离散控制（开关控制）
    - 泵站需求管理
    - 多泵协调
    - 流量优化
    """
    
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 pump_station: PumpStation,
                 demand_topic: str,
                 control_topic_prefix: str,
                 time_step: float = 1.0,
                 **kwargs):
        """
        初始化泵控制代理
        
        Args:
            agent_id: 代理标识
            message_bus: 消息总线
            pump_station: 泵站对象
            demand_topic: 需求主题
            control_topic_prefix: 控制主题前缀
            time_step: 时间步长
            **kwargs: 泵站特定配置
        """
        # 调用父类构造函数，使用离散控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
            control_strategy=ControlStrategy.DISCRETE,
            observation_topic=demand_topic,
            observation_key='value',
            action_topic=None,  # 多泵控制不使用单一主题
            pump_station=pump_station,
            control_topic_prefix=control_topic_prefix,
            **kwargs
        )
    
    def _initialize_device_specific(self, **kwargs):
        """泵站特定初始化"""
        self.pump_station = kwargs.get('pump_station')
        self.control_topic_prefix = kwargs.get('control_topic_prefix', 'pump_control')
        self.current_demand = 0.0
        
        if self.pump_station:
            self.pumps = self.pump_station.pumps
            # 假设所有泵具有相同的流量
            self.pump_flow_rate = self.pumps[0].get_parameters().get('max_flow_rate', 1.0) if self.pumps else 0
            print(f"[{self.agent_id}] Initialized with {len(self.pumps)} pumps, flow rate: {self.pump_flow_rate:.2f} m³/s each")
        else:
            self.pumps = []
            self.pump_flow_rate = 0
            print(f"[{self.agent_id}] Warning: No pump station provided")
    
    def compute_discrete_control_action(self, message: Message) -> Optional[Dict[str, Any]]:
        """计算离散控制动作"""
        # 更新需求
        demand = message.get(self.observation_key, 0.0)
        if isinstance(demand, (int, float)):
            self.current_demand = demand
            print(f"[{self.agent_id}] Received new flow demand: {self.current_demand:.2f} m³/s")
        
        # 计算需要开启的泵数量
        if self.pump_flow_rate > 0:
            required_pumps = math.ceil(self.current_demand / self.pump_flow_rate)
            required_pumps = max(0, min(required_pumps, len(self.pumps)))
        else:
            required_pumps = 0
        
        # 生成控制信号
        control_signals = {}
        for i, pump in enumerate(self.pumps):
            pump_topic = f"{self.control_topic_prefix}.pump_{i+1}"
            control_signals[pump_topic] = 1 if i < required_pumps else 0
        
        print(f"[{self.agent_id}] Control decision: {required_pumps}/{len(self.pumps)} pumps ON")
        return control_signals
    
    def publish_action(self, control_signals: Dict[str, Any]):
        """发布控制动作到多个泵"""
        if not isinstance(control_signals, dict):
            print(f"[{self.agent_id}] Error: Expected dict for pump control signals")
            return
        
        active_pumps = 0
        for topic, signal in control_signals.items():
            action_message = {
                'control_signal': signal,
                'agent_id': self.agent_id,
                'timestamp': self.bus.get_current_time() if hasattr(self.bus, 'get_current_time') else 0
            }
            self.bus.publish(topic, action_message)
            if signal > 0:
                active_pumps += 1
        
        total_flow = active_pumps * self.pump_flow_rate
        print(f"[{self.agent_id}] Published pump controls: {active_pumps} pumps ON, total flow: {total_flow:.2f} m³/s")
    
    def execute_control_logic(self):
        """执行控制逻辑（向后兼容方法）"""
        if self.current_observation:
            control_signals = self.compute_discrete_control_action(self.current_observation)
            if control_signals:
                self.publish_action(control_signals)