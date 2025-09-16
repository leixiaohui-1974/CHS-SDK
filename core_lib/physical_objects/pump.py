"""
Simulation model for a Pump.

物理模型特点：
1. 只关注物理特性（流量、扬程、功率、效率）
2. 不包含控制逻辑
3. 通过状态更新响应外部控制信号
4. 提供完整的物理特性计算
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.config.parameter_manager import get_parameter_manager
from core_lib.config.constants import PhysicalConstants, StatusConstants
from typing import Dict, Any, Optional

class Pump(PhysicalObjectInterface):
    """
    Represents a controllable pump in a water system.
    
    特点：
    1. 只关注物理特性（流量、扬程、功率、效率）
    2. 不包含控制逻辑
    3. 通过状态更新响应外部控制信号
    4. 提供完整的物理特性计算
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        
        # 获取参数管理器
        self.param_manager = get_parameter_manager()
        
        # 物理常量定义（从常量类获取）
        self.GRAVITY_ACCELERATION = PhysicalConstants.GRAVITY_ACCELERATION
        self.WATER_DENSITY = PhysicalConstants.WATER_DENSITY
        self.POWER_CONVERSION = self.param_manager.get_unit_conversion('W_TO_KW')
        
        # 状态枚举常量（从常量类获取）
        self.STATUS_OFF = StatusConstants.STATUS_OFF
        self.STATUS_ON = StatusConstants.STATUS_ON
        
        # 默认值常量（从参数管理器获取）
        self.DEFAULT_OUTFLOW = self.param_manager.get_parameter('physical_objects', 'default_outflow', 0.0)
        self.DEFAULT_POWER_DRAW = 0.0
        self.DEFAULT_EFFICIENCY = 0.0
        
        # 效率特性常量（从参数管理器获取）
        self.DEFAULT_MIN_FLOW_RATIO = self.param_manager.get_parameter('pump_parameters', 'min_flow_ratio', 0.1)
        self.DEFAULT_OPTIMAL_FLOW_RATIO = self.param_manager.get_parameter('pump_parameters', 'optimal_flow_ratio', 0.7)
        self.DEFAULT_MIN_EFFICIENCY = self.param_manager.get_parameter('pump_parameters', 'min_efficiency', 0.3)
        self.DEFAULT_MAX_EFFICIENCY_LOSS = self.param_manager.get_parameter('pump_parameters', 'max_efficiency_loss', 0.3)
        
        # 物理状态
        self._state.setdefault('outflow', self.DEFAULT_OUTFLOW)
        self._state.setdefault('power_draw_kw', self.DEFAULT_POWER_DRAW)
        self._state.setdefault('efficiency', self.DEFAULT_EFFICIENCY)
        self._state.setdefault('status', self.STATUS_OFF)
        
        # 控制接口
        self.bus = message_bus
        self.action_topic = action_topic
        self.target_status = self._state.get('status', self.STATUS_OFF)

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"Pump '{self.name}' subscribed to action topic '{self.action_topic}'.")

        print(f"Pump '{self.name}' created with initial state {self._state}.")

    def _calculate_flow(self, upstream_level: float, downstream_level: float) -> float:
        """计算水泵流量 - 纯物理计算"""
        if self._state.get('status', self.STATUS_OFF) == self.STATUS_OFF:
            return self.DEFAULT_OUTFLOW

        # 从参数获取泵的物理特性（必须由用户提供）
        max_flow_rate = self._params.get('max_flow_rate')
        max_head = self._params.get('max_head')
        
        if max_flow_rate is None:
            raise ValueError(f"泵 '{self.name}' 缺少必需参数 'max_flow_rate'")
        if max_head is None:
            raise ValueError(f"泵 '{self.name}' 缺少必需参数 'max_head'")
        
        # 计算实际扬程（泵从上游抽水到下游）
        actual_head = downstream_level - upstream_level
        
        # 检查扬程限制（负扬程表示抽水，正扬程表示排水）
        if abs(actual_head) > max_head:
            return self.DEFAULT_OUTFLOW
        
        # 对于抽水工况，流量基本不受扬程影响
        # 直接返回最大流量
        return max_flow_rate

    def _calculate_power(self, flow: float, head: float) -> float:
        """计算功率消耗 - 纯物理计算"""
        if flow <= 0:
            return self.DEFAULT_POWER_DRAW
            
        # 基本功率计算
        basic_power = (flow * head * self.GRAVITY_ACCELERATION * self.WATER_DENSITY) / self.POWER_CONVERSION  # kW
        
        # 考虑效率
        efficiency = self._calculate_efficiency(flow, head)
        if efficiency > 0:
            return basic_power / efficiency
        else:
            return self.DEFAULT_POWER_DRAW

    def _calculate_efficiency(self, flow: float, head: float) -> float:
        """计算效率 - 纯物理计算"""
        if flow <= 0:
            return self.DEFAULT_EFFICIENCY
            
        # 从参数获取效率特性（可配置，有默认值）
        max_flow_rate = self._params.get('max_flow_rate')
        min_flow_ratio = self._params.get('min_flow_ratio', self.DEFAULT_MIN_FLOW_RATIO)
        optimal_flow_ratio = self._params.get('optimal_flow_ratio', self.DEFAULT_OPTIMAL_FLOW_RATIO)
        min_efficiency = self._params.get('min_efficiency', self.DEFAULT_MIN_EFFICIENCY)
        max_efficiency_loss = self._params.get('max_efficiency_loss', self.DEFAULT_MAX_EFFICIENCY_LOSS)
        
        if max_flow_rate is None:
            raise ValueError(f"泵 '{self.name}' 缺少必需参数 'max_flow_rate'")
            
        flow_ratio = flow / max_flow_rate
        
        # 效率特性曲线（基于配置的泵特性）
        if flow_ratio < min_flow_ratio:
            return self.DEFAULT_EFFICIENCY
        elif flow_ratio <= optimal_flow_ratio:
            return min_efficiency + (1.0 - min_efficiency) * (flow_ratio / optimal_flow_ratio)
        else:
            return 1.0 - max_efficiency_loss * ((flow_ratio - optimal_flow_ratio) / (1.0 - optimal_flow_ratio))

    def handle_action_message(self, message: Message):
        """处理控制消息 - 只更新目标状态，不包含控制逻辑"""
        new_target = message.get('control_signal')
        if new_target in [0, 1]:
            self.target_status = new_target
            print(f"Pump '{self.name}' received control signal: {new_target}")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        物理步进 - 只处理物理状态更新
        """
        # 更新运行状态
        if self.target_status != self._state.get('status', 0):
            self._state['status'] = self.target_status
            print(f"Pump '{self.name}' status changed to: {self.target_status}")

        # 计算物理量（需要上下游水位信息）
        # 从参数管理器获取默认水位，如果action中没有提供
        default_upstream_level = self.param_manager.get_parameter('business_scenarios', 'pump_station.upstream_level', 25.0)
        default_downstream_level = self.param_manager.get_parameter('business_scenarios', 'pump_station.downstream_level', 8.0)
        
        upstream_level = action.get('upstream_level', default_upstream_level)
        downstream_level = action.get('downstream_level', default_downstream_level)
        
        # 计算流量
        flow = self._calculate_flow(upstream_level, downstream_level)
        self._state['outflow'] = flow
        
        # 计算功率 - 使用改进的功率计算
        if self._state.get('status', 0) == 1 and flow > 0:
            # 从参数管理器获取默认功率和效率
            default_rated_power = self.param_manager.get_parameter('business_scenarios', 'pump_station.rated_power', 50.0)
            default_efficiency = self.param_manager.get_parameter('business_scenarios', 'pump_station.efficiency', 0.8)
            
            # 使用参数中的额定功率作为基础
            rated_power = self._params.get('power_consumption_kw', default_rated_power)
            # 功率与流量成正比，但考虑效率
            efficiency = self._params.get('efficiency', default_efficiency)
            power = rated_power * efficiency
        else:
            power = 0.0
            
        self._state['power_draw_kw'] = power
        
        # 计算效率
        efficiency = self._calculate_efficiency(flow, downstream_level - upstream_level)
        self._state['efficiency'] = efficiency

        return self.get_state()

    def get_parameters(self) -> Parameters:
        """获取参数"""
        return self._params.copy()

    def get_state(self) -> State:
        """获取状态"""
        return self._state.copy()


class PumpStation(PhysicalObjectInterface):
    """
    Represents a pump station, which is a collection of individual pumps.
    It aggregates the flow and power consumption of all pumps within it.
    The control of individual pumps is handled by an external agent.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters, pumps: list[Pump]):
        super().__init__(name, initial_state, parameters)
        self.pumps = pumps
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('active_pumps', 0)
        self._state.setdefault('total_power_draw_kw', 0.0)
        print(f"PumpStation '{self.name}' created with {len(self.pumps)} pumps.")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        Steps each pump in the station and aggregates their states.
        The `action` dict (containing upstream/downstream heads) is passed to each pump.
        """
        total_outflow = 0.0
        active_pumps = 0
        total_power = 0.0

        for pump in self.pumps:
            # Individual pump control signals are received via their own message bus subscriptions,
            # so they are not included in the station-level action.
            pump_state = pump.step(action, time_step)
            total_outflow += pump_state.get('outflow', 0)
            total_power += pump_state.get('power_draw_kw', 0)
            if pump_state.get('status', 0) == 1:
                active_pumps += 1

        self._state['total_outflow'] = total_outflow
        self._state['active_pumps'] = active_pumps
        self._state['total_power_draw_kw'] = total_power

        return self._state

    @property
    def is_stateful(self) -> bool:
        return False
