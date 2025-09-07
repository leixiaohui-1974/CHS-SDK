"""
改进的水泵物理模型 - 分离物理特性和控制逻辑

物理模型应该只关注物理特性，不包含控制逻辑
"""

from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional

class ImprovedPump(PhysicalObjectInterface):
    """
    改进的水泵物理模型
    
    特点：
    1. 只关注物理特性（流量、扬程、功率、效率）
    2. 不包含控制逻辑
    3. 通过状态更新响应外部控制信号
    4. 提供完整的物理特性计算
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        
        # 物理状态
        self._state.setdefault('outflow', 0.0)
        self._state.setdefault('power_draw_kw', 0.0)
        self._state.setdefault('efficiency', 0.0)
        self._state.setdefault('status', 0)  # 0=停止, 1=运行
        
        # 控制接口
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_status = self._state.get('status', 0)

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Pump '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Pump '{self.name}' created with initial state {self._state}.")

    def handle_action_message(self, message: Message):
        """处理控制消息 - 只更新目标状态，不包含控制逻辑"""
        new_target = message.get('control_signal')
        if new_target in [0, 1]:
            self.target_status = new_target
            print(f"Pump '{self.name}' received control signal: {new_target}")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """计算水泵流量 - 纯物理计算"""
        if self._state.get('status', 0) == 0:
            return 0.0

        max_flow_rate = self._params.get('max_flow_rate', 10.0)
        max_head = self._params.get('max_head', 20.0)
        
        # 计算实际扬程（泵从上游抽水到下游）
        actual_head = downstream_level - upstream_level
        
        # 检查扬程限制（负扬程表示抽水，正扬程表示排水）
        if abs(actual_head) > max_head:
            return 0.0
        
        # 对于抽水工况，流量基本不受扬程影响
        # 直接返回最大流量
        return max_flow_rate

    def _calculate_power(self, flow: float, head: float) -> float:
        """计算功率消耗 - 纯物理计算"""
        if flow <= 0:
            return 0.0
            
        # 基本功率计算
        basic_power = (flow * head * 9.81 * 1000) / 1000  # kW
        
        # 考虑效率
        efficiency = self._calculate_efficiency(flow, head)
        if efficiency > 0:
            return basic_power / efficiency
        else:
            return 0.0

    def _calculate_efficiency(self, flow: float, head: float) -> float:
        """计算效率 - 纯物理计算"""
        if flow <= 0:
            return 0.0
            
        max_flow_rate = self._params.get('max_flow_rate', 10.0)
        flow_ratio = flow / max_flow_rate
        
        # 效率特性曲线（基于实际水泵特性）
        if flow_ratio < 0.1:
            return 0.0
        elif flow_ratio <= 0.7:
            return 0.3 + 0.7 * (flow_ratio / 0.7)
        else:
            return 1.0 - 0.3 * ((flow_ratio - 0.7) / 0.3)

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        物理步进 - 只处理物理状态更新
        """
        # 更新运行状态
        if self.target_status != self._state.get('status', 0):
            self._state['status'] = self.target_status
            print(f"Pump '{self.name}' status changed to: {self.target_status}")

        # 计算物理量（需要上下游水位信息）
        upstream_level = action.get('upstream_level', 25.0)  # 默认上游水位
        downstream_level = action.get('downstream_level', 8.0)  # 默认下游水位
        
        # 计算流量
        flow = self._calculate_flow(upstream_level, downstream_level)
        self._state['outflow'] = flow
        
        # 计算功率 - 使用简化的功率计算
        if self._state.get('status', 0) == 1 and flow > 0:
            # 使用参数中的额定功率作为基础
            rated_power = self._params.get('power_consumption_kw', 50.0)
            # 功率与流量成正比，但考虑效率
            efficiency = self._params.get('efficiency', 0.8)
            power = rated_power * efficiency
        else:
            power = 0.0
            
        self._state['power_draw_kw'] = power
        
        # 计算效率
        efficiency = self._calculate_efficiency(flow, downstream_level - upstream_level)
        self._state['efficiency'] = efficiency

        return self._state.copy()

    def get_parameters(self) -> Parameters:
        """获取参数"""
        return self._params.copy()

    def get_state(self) -> State:
        """获取状态"""
        return self._state.copy()
