"""
闸门的仿真模型。
"""
import math
from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.communication.message_bus import MessageBus, Message
from core_lib.config.parameter_manager import get_parameter_manager
from core_lib.config.constants import PhysicalConstants, HydraulicConstants

class Gate(PhysicalObjectInterface):
    """
    代表水务系统中的一个可控闸门。
    其出流量根据上游和下游的水位计算得出。
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None,
                 action_key: str = 'opening'):
        super().__init__(name, initial_state, parameters)
        
        # 获取参数管理器
        self.param_manager = get_parameter_manager()
        
        # 物理常量定义（从常量类获取）
        self.GRAVITY_ACCELERATION = PhysicalConstants.GRAVITY_ACCELERATION
        self.SQRT_FACTOR = HydraulicConstants.SQRT_FACTOR
        
        # 默认参数定义（从参数管理器获取）
        self.DEFAULT_DISCHARGE_COEFFICIENT = self.param_manager.get_parameter('valve_parameters', 'default_discharge_coefficient', 0.6)
        self.DEFAULT_WIDTH = 2.0              # 默认闸门宽度 (m)
        self.DEFAULT_MAX_OPENING = 1.0        # 默认最大开度 (m)
        
        # 状态常量定义（从参数管理器获取）
        self.DEFAULT_OPENING = HydraulicConstants.MIN_OPENING
        self.DEFAULT_OUTFLOW = self.param_manager.get_parameter('physical_objects', 'default_outflow', 0.0)
        self.DEFAULT_HEAD_DIFF = 1            # 默认水头差
        
        self._state.setdefault('outflow', self.DEFAULT_OUTFLOW)
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_key = action_key
        self.target_opening = self._state.get('opening', self.DEFAULT_OPENING)
        self.last_head_diff = self.DEFAULT_HEAD_DIFF  # 存储上一次的水头差，用于反向计算

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"闸门 '{self.name}' 已订阅动作主题 '{self.action_topic}'.")

        print(f"闸门 '{self.name}' 已创建，初始状态为 {self._state}.")

    def _calculate_outflow(self, upstream_level: float, opening: float, downstream_level: float = 0, C: Optional[float] = None) -> float:
        """
        使用孔口出流公式计算通过闸门的流量。
        Q = C * A * sqrt(2 * g * h)
        """
        if C is None:
            C = self._params.get('discharge_coefficient', self.DEFAULT_DISCHARGE_COEFFICIENT)
        width = self._params.get('width', self.DEFAULT_WIDTH)
        area = opening * width
        head = upstream_level - downstream_level
        self.last_head_diff = head
        if head <= 0:
            return self.DEFAULT_OUTFLOW
        return C * area * math.sqrt(self.SQRT_FACTOR * self.GRAVITY_ACCELERATION * head)

    def calculate_outflow(self, upstream_level: float, opening: float, downstream_level: float = 0, C: Optional[float] = None) -> float:
        """
        公共方法：计算通过闸门的流量。
        这是对私有方法_calculate_outflow的包装，供外部代码调用。
        """
        return self._calculate_outflow(upstream_level, opening, downstream_level, C)

    def _calculate_opening_for_flow(self, target_flow: float) -> float:
        """孔口公式的反向计算，用于根据目标流量计算所需的闸门开度。"""
        C = self._params.get('discharge_coefficient', self.DEFAULT_DISCHARGE_COEFFICIENT)
        width = self._params.get('width', self.DEFAULT_WIDTH)
        if self.last_head_diff <= 0:
            return self.DEFAULT_OPENING  # 没有水头差则无法实现流动
        denominator = C * width * math.sqrt(self.SQRT_FACTOR * self.GRAVITY_ACCELERATION * self.last_head_diff)
        if denominator == 0:
            return self._params.get('max_opening', self.DEFAULT_MAX_OPENING)  # 无法计算，如果需要流量则全开
        return target_flow / denominator

    def handle_action_message(self, message: Message):
        """处理总线传入的动作消息的回调函数。"""
        # 处理控制信号
        if 'control_signal' in message:
            new_target = message.get('control_signal')
            if new_target is not None:
                self.target_opening = float(new_target)
                print(f"闸门 '{self.name}' 收到控制信号: {new_target:.4f}")
        # 处理直接的开度指令
        elif self.action_key in message:
            new_target = message.get(self.action_key)
            if new_target is not None:
                self.target_opening = float(new_target)
                print(f"闸门 '{self.name}' 收到开度指令: {new_target:.4f}")
        # 处理目标出流量指令
        elif 'gate_target_outflow' in message:
            target_flow = message.get('gate_target_outflow')
            if target_flow is not None:
                self.target_opening = self._calculate_opening_for_flow(float(target_flow))
                print(f"闸门 '{self.name}' 收到流量指令: {target_flow:.4f}, 计算开度: {self.target_opening:.4f}")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """更新闸门在单个时间步内的状态。"""
        if not isinstance(action, dict):
            raise TypeError(f"Gate.step(action, time_step) 需要 dict，收到 {type(action).__name__}")
        if 'control_signal' in action and action['control_signal'] is not None:
            self.target_opening = action['control_signal']
        max_roc = self._params.get('max_rate_of_change', 0.05) # 最大变化速率
        current_opening = self._state.get('opening', 0)
        if self.target_opening > current_opening:
            new_opening = min(current_opening + max_roc * time_step, self.target_opening)
        else:
            new_opening = max(current_opening - max_roc * time_step, self.target_opening)
        max_opening = self._params.get('max_opening', 1.0)
        self._state['opening'] = max(0.0, min(new_opening, max_opening))
        upstream_level = action.get('upstream_head', 0)
        downstream_level = action.get('downstream_head', 0)
        self._state['outflow'] = self._calculate_outflow(upstream_level, self._state['opening'], downstream_level)
        return self.get_state()

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """
        辨识闸门的流量系数 (C)。
        """
        required_keys = ['upstream_levels', 'downstream_levels', 'openings', 'observed_flows']
        if not all(k in data for k in required_keys):
            raise ValueError(f"辨识数据必须包含 {required_keys}。")

        up_levels = data['upstream_levels']
        down_levels = data['downstream_levels']
        openings = data['openings']
        obs_flows = data['observed_flows']

        def _simulation_error(c_param: np.ndarray) -> float:
            """优化器的目标函数。"""
            C = c_param[0]
            simulated_flows = np.zeros_like(obs_flows)
            for i in range(len(obs_flows)):
                simulated_flows[i] = self._calculate_outflow(
                    upstream_level=up_levels[i],
                    downstream_level=down_levels[i],
                    opening=openings[i],
                    C=C
                )
            # 计算均方根误差 (RMSE)
            rmse = np.sqrt(np.mean((simulated_flows - obs_flows)**2))
            return rmse

        initial_guess = np.array([self._params.get('discharge_coefficient', 0.6)])
        result = minimize(
            _simulation_error,
            initial_guess,
            method='Nelder-Mead', # 适用于简单的单变量优化
            bounds=[(0.1, 1.0)] # C值的物理边界
        )

        if result.success:
            new_c = result.x[0]
            print(f"为 '{self.name}' 进行的参数辨识成功。 新 C = {new_c:.4f}")
            return {'discharge_coefficient': new_c}
        else:
            print(f"警告: 为 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {}
