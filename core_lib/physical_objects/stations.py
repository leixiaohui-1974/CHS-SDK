#!/usr/bin/env python3
"""
站类物理对象实现

该模块实现了各种站类设施的物理对象，包括闸站、水电站、阀门站等，
遵循统一的接口规范和设计模式。
"""

from typing import Dict, Any, List, Optional
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.pump import Pump
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.core.event_bus import SimpleEventBus

class GateStation(PhysicalObjectInterface):
    """
    闸站 - 包含多个闸门的复合设施
    
    闸站管理多个闸门的协调运行，提供统一的控制接口和状态聚合。
    """
    
    def __init__(self, name: str, initial_state: State, parameters: Parameters, 
                 gates: List[Gate], message_bus: Optional[SimpleEventBus] = None):
        super().__init__(name, initial_state, parameters)
        self.gates = gates
        self.message_bus = message_bus
        
        # 初始化站级状态
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('active_gates', 0)
        self._state.setdefault('average_opening', 0.0)
        self._state.setdefault('operation_mode', 'manual')  # manual, automatic, emergency
        
        print(f"GateStation '{self.name}' created with {len(self.gates)} gates.")
    
    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        步进仿真：更新所有闸门状态并聚合结果
        
        Args:
            action: 包含上下游水位和控制信号的动作字典
            time_step: 时间步长
            
        Returns:
            更新后的站级状态
        """
        total_outflow = 0.0
        active_gates = 0
        total_opening = 0.0
        
        # 更新每个闸门状态
        for gate in self.gates:
            gate_state = gate.step(action, time_step)
            total_outflow += gate_state.get('outflow', 0.0)
            opening = gate_state.get('opening', 0.0)
            total_opening += opening
            
            if opening > 0.01:  # 认为开度大于1%为活跃状态
                active_gates += 1
        
        # 更新站级状态
        self._state['total_outflow'] = total_outflow
        self._state['active_gates'] = active_gates
        self._state['average_opening'] = total_opening / len(self.gates) if self.gates else 0.0
        
        # 根据活跃闸门数量确定操作模式
        if active_gates == 0:
            self._state['operation_mode'] = 'closed'
        elif active_gates == len(self.gates):
            self._state['operation_mode'] = 'full_open'
        else:
            self._state['operation_mode'] = 'partial'
            
        return self._state
    
    def get_gate_states(self) -> Dict[str, State]:
        """获取所有闸门的详细状态"""
        return {gate.name: gate.get_state() for gate in self.gates}
    
    def set_operation_mode(self, mode: str):
        """设置操作模式"""
        valid_modes = ['manual', 'automatic', 'emergency', 'closed', 'full_open', 'partial']
        if mode in valid_modes:
            self._state['operation_mode'] = mode
        else:
            raise ValueError(f"Invalid operation mode: {mode}. Valid modes: {valid_modes}")
    
    @property
    def is_stateful(self) -> bool:
        return True


class HydropowerStation(PhysicalObjectInterface):
    """
    水电站 - 包含多个水轮机的发电设施
    
    水电站管理多个水轮机的协调运行，优化发电效率和输出功率。
    """
    
    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 turbines: List[WaterTurbine], message_bus: Optional[SimpleEventBus] = None):
        super().__init__(name, initial_state, parameters)
        self.turbines = turbines
        self.message_bus = message_bus
        
        # 初始化电站级状态
        self._state.setdefault('total_power_output', 0.0)
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('active_turbines', 0)
        self._state.setdefault('average_efficiency', 0.0)
        self._state.setdefault('power_factor', 1.0)
        self._state.setdefault('grid_frequency', 50.0)  # Hz
        
        print(f"HydropowerStation '{self.name}' created with {len(self.turbines)} turbines.")
    
    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        步进仿真：更新所有水轮机状态并聚合发电结果
        
        Args:
            action: 包含水位差、负荷需求等的动作字典
            time_step: 时间步长
            
        Returns:
            更新后的电站级状态
        """
        total_power = 0.0
        total_outflow = 0.0
        active_turbines = 0
        total_efficiency = 0.0
        
        # 更新每个水轮机状态
        for turbine in self.turbines:
            turbine_state = turbine.step(action, time_step)
            power_output = turbine_state.get('power', 0.0)
            outflow = turbine_state.get('outflow', 0.0)
            efficiency = turbine_state.get('efficiency', 0.0)
            
            total_power += power_output
            total_outflow += outflow
            total_efficiency += efficiency
            
            if power_output > 0.1:  # 认为功率超过0.1MW为活跃状态
                active_turbines += 1
        
        # 更新电站级状态
        self._state['total_power_output'] = total_power
        self._state['total_outflow'] = total_outflow
        self._state['active_turbines'] = active_turbines
        self._state['average_efficiency'] = (total_efficiency / len(self.turbines) 
                                           if self.turbines else 0.0)
        
        # 根据负荷需求调整功率因子
        target_power = action.get('target_power', total_power)
        if target_power > 0:
            self._state['power_factor'] = min(1.0, total_power / target_power)
        
        return self._state
    
    def get_turbine_states(self) -> Dict[str, State]:
        """获取所有水轮机的详细状态"""
        return {turbine.name: turbine.get_state() for turbine in self.turbines}
    
    def calculate_total_capacity(self) -> float:
        """计算电站总装机容量"""
        total_capacity = 0.0
        for turbine in self.turbines:
            # 假设每个水轮机都有rated_power参数
            rated_power = turbine._params.get('rated_power', 0.0)
            total_capacity += rated_power
        return total_capacity
    
    def get_load_factor(self) -> float:
        """获取负荷系数（当前出力/装机容量）"""
        total_capacity = self.calculate_total_capacity()
        if total_capacity > 0:
            return self._state['total_power_output'] / total_capacity
        return 0.0
    
    @property
    def is_stateful(self) -> bool:
        return True


class ValveStation(PhysicalObjectInterface):
    """
    阀门站 - 包含多个阀门的调节设施
    
    阀门站管理多个阀门的协调运行，提供精确的流量控制。
    """
    
    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 valves: List, message_bus: Optional[SimpleEventBus] = None):
        super().__init__(name, initial_state, parameters)
        self.valves = valves  # 暂时使用通用列表，待实现Valve类后替换
        self.message_bus = message_bus
        
        # 初始化阀门站级状态
        self._state.setdefault('total_outflow', 0.0)
        self._state.setdefault('active_valves', 0)
        self._state.setdefault('average_opening', 0.0)
        self._state.setdefault('pressure_drop', 0.0)
        self._state.setdefault('control_mode', 'manual')  # manual, automatic, cascade
        
        print(f"ValveStation '{self.name}' created with {len(self.valves)} valves.")
    
    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        步进仿真：更新所有阀门状态并聚合结果
        
        Args:
            action: 包含压力、流量控制信号的动作字典
            time_step: 时间步长
            
        Returns:
            更新后的阀门站级状态
        """
        total_outflow = 0.0
        active_valves = 0
        total_opening = 0.0
        
        # 简化实现（待Valve类完成后完善）
        for i, valve in enumerate(self.valves):
            # 暂时使用简单的计算
            opening = action.get(f'valve_{i}_opening', 0.5)
            max_flow = self._params.get('valve_max_flow', 10.0)
            outflow = opening * max_flow
            
            total_outflow += outflow
            total_opening += opening
            
            if opening > 0.01:
                active_valves += 1
        
        # 更新站级状态
        self._state['total_outflow'] = total_outflow
        self._state['active_valves'] = active_valves
        self._state['average_opening'] = total_opening / len(self.valves) if self.valves else 0.0
        
        # 计算压力降（简化计算）
        upstream_pressure = action.get('upstream_pressure', 1.0)
        downstream_pressure = action.get('downstream_pressure', 0.8)
        self._state['pressure_drop'] = upstream_pressure - downstream_pressure
        
        return self._state
    
    def set_control_mode(self, mode: str):
        """设置控制模式"""
        valid_modes = ['manual', 'automatic', 'cascade', 'emergency']
        if mode in valid_modes:
            self._state['control_mode'] = mode
        else:
            raise ValueError(f"Invalid control mode: {mode}. Valid modes: {valid_modes}")
    
    @property
    def is_stateful(self) -> bool:
        return True


# ================================
# 站类设施创建工厂函数
# ================================

def create_gate_station(name: str, gate_configs: List[Dict[str, Any]], 
                       station_params: Optional[Dict[str, Any]] = None,
                       message_bus: Optional[SimpleEventBus] = None) -> GateStation:
    """
    创建闸站的工厂函数
    
    Args:
        name: 闸站名称
        gate_configs: 闸门配置列表
        station_params: 站级参数
        message_bus: 消息总线
        
    Returns:
        GateStation实例
    """
    gates = []
    
    for i, config in enumerate(gate_configs):
        gate_name = config.get('name', f"{name}_gate_{i+1}")
        initial_state = config.get('initial_state', {'opening': 0.0, 'outflow': 0.0})
        parameters = config.get('parameters', {'max_flow_rate': 50.0})
        control_topic = config.get('control_topic')
        
        if control_topic and message_bus:
            gate = Gate(gate_name, initial_state, parameters, message_bus, control_topic)
        else:
            gate = Gate(gate_name, initial_state, parameters)
        
        gates.append(gate)
    
    station_initial_state = {}
    station_parameters = station_params or {}
    
    return GateStation(name, station_initial_state, station_parameters, gates, message_bus)


def create_hydropower_station(name: str, turbine_configs: List[Dict[str, Any]],
                            station_params: Optional[Dict[str, Any]] = None,
                            message_bus: Optional[SimpleEventBus] = None) -> HydropowerStation:
    """
    创建水电站的工厂函数
    
    Args:
        name: 水电站名称
        turbine_configs: 水轮机配置列表
        station_params: 站级参数
        message_bus: 消息总线
        
    Returns:
        HydropowerStation实例
    """
    turbines = []
    
    for i, config in enumerate(turbine_configs):
        turbine_name = config.get('name', f"{name}_turbine_{i+1}")
        initial_state = config.get('initial_state', {'power': 0.0, 'outflow': 0.0})
        parameters = config.get('parameters', {
            'efficiency': 0.9, 
            'max_flow_rate': 100.0,
            'rated_power': 50.0
        })
        
        turbine = WaterTurbine(turbine_name, initial_state, parameters)
        turbines.append(turbine)
    
    station_initial_state = {}
    station_parameters = station_params or {}
    
    return HydropowerStation(name, station_initial_state, station_parameters, turbines, message_bus)


def create_valve_station(name: str, valve_count: int = 3,
                        station_params: Optional[Dict[str, Any]] = None,
                        message_bus: Optional[SimpleEventBus] = None) -> ValveStation:
    """
    创建阀门站的工厂函数（简化实现）
    
    Args:
        name: 阀门站名称
        valve_count: 阀门数量
        station_params: 站级参数
        message_bus: 消息总线
        
    Returns:
        ValveStation实例
    """
    # 创建简化的阀门对象列表（待Valve类实现后改进）
    valves = [f"valve_{i+1}" for i in range(valve_count)]
    
    station_initial_state = {}
    station_parameters = station_params or {'valve_max_flow': 15.0}
    
    return ValveStation(name, station_initial_state, station_parameters, valves, message_bus)