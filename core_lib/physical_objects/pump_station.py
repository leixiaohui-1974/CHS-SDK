"""
Simulation model for a Pump.

物理模型特点：
1. 只关注物理特性（流量、扬程、功率、效率）
2. 不包含控制逻辑
3. 通过状态更新响应外部控制信号
4. 提供完整的物理特性计算
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any, Optional


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

    def step(self, action: Dict[str, Any], dt: float) -> State:
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
            pump_state = pump.step(action, dt)
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
