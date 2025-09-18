"""
闸门的仿真模型。
"""
import math
from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message

class Gate(PhysicalObjectInterface):
    """
    代表水务系统中的一个可控闸门。
    其出流量根据上游和下游的水位计算得出。
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None,
                 action_key: str = 'opening',
                 default_width: float = 2.0,
                 default_max_opening: float = 1.0,
                 default_discharge_coefficient: float = 0.6,
                 default_max_rate_of_change: float = 0.05,
                 default_gate_bottom_elevation: float = 0.0,
                 discharge_coeff_min_range: float = 0.4,
                 discharge_coeff_max_range: float = 0.8,
                 free_flow_ratio: float = 0.67,
                 optimization_timeout: int = 3600,
                 identification_bounds_min: float = 0.4,
                 identification_bounds_max: float = 0.8):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        
        # 参数映射：将配置文件中的参数名映射为内部使用的标准参数名
        if 'zb' in parameters and 'gate_bottom_elevation' not in parameters:
            self._params['gate_bottom_elevation'] = parameters['zb']
            print(f"闸门 '{self.name}' 映射参数: zb={parameters['zb']} -> gate_bottom_elevation")
        
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_key = action_key
        self.target_opening = self._state.get('opening', 0)
        self.last_head_diff = 1.0 # 存储上一次的水头差，用于反向计算 (m)
        
        # 初始化入流
        self._inflow = 0.0
        
        # 将默认参数值设置为实例属性
        self.default_width = default_width
        self.default_max_opening = default_max_opening
        self.default_discharge_coefficient = default_discharge_coefficient
        self.default_max_rate_of_change = default_max_rate_of_change
        self.default_gate_bottom_elevation = default_gate_bottom_elevation
        self.discharge_coeff_min_range = discharge_coeff_min_range
        self.discharge_coeff_max_range = discharge_coeff_max_range
        self.free_flow_ratio = free_flow_ratio
        self.optimization_timeout = optimization_timeout
        self.identification_bounds_min = identification_bounds_min
        self.identification_bounds_max = identification_bounds_max
        
        # 验证必要的物理参数
        self._validate_physical_parameters()

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"闸门 '{self.name}' 已订阅动作主题 '{self.action_topic}'.")

        print(f"闸门 '{self.name}' 已创建，初始状态为 {self._state}.")

    def set_inflow(self, inflow: float):
        """设置闸门的入流量。
        
        Args:
            inflow: 新的入流量 (m³/s)
        """
        self._inflow = inflow
        print(f"闸门 '{self.name}' 入流已设置为 {inflow} m³/s")

    def _validate_physical_parameters(self):
        """验证物理参数的合理性。"""
        width = self._params.get('width', self.default_width)
        if width <= 0:
            raise ValueError(f"闸门宽度必须大于0，当前值: {width}")
        
        max_opening = self._params.get('max_opening', self.default_max_opening)
        if max_opening <= 0:
            raise ValueError(f"最大开度必须大于0，当前值: {max_opening}")
        
        discharge_coeff = self._params.get('discharge_coefficient', self.default_discharge_coefficient)
        if not self.discharge_coeff_min_range <= discharge_coeff <= self.discharge_coeff_max_range:
            print(f"警告: 流量系数 {discharge_coeff} 超出典型范围 [{self.discharge_coeff_min_range}, {self.discharge_coeff_max_range}]")
        
        max_roc = self._params.get('max_rate_of_change', self.default_max_rate_of_change)
        if max_roc <= 0:
            raise ValueError(f"最大变化速率必须大于0，当前值: {max_roc}")

    def _calculate_outflow(self, upstream_level: float, opening: float, downstream_level: float = 0, C: Optional[float] = None) -> float:
        """
        使用改进的闸门出流公式计算通过闸门的流量。
        考虑自由出流和淹没出流两种情况：
        - 自由出流: Q = Cc * Cv * b * a * sqrt(2 * g * H)
        - 淹没出流: Q = Cc * Cv * b * a * sqrt(2 * g * (H1 - H2))
        
        其中：
        Cc: 收缩系数 (通常为0.61)
        Cv: 流速系数 (通常为0.98)
        b: 闸门宽度 (m)
        a: 闸门开度 (m)
        H: 上游水头 (m)
        H1, H2: 上下游水位 (m)
        """
        if C is None:
            # 综合流量系数 = 收缩系数 × 流速系数
            C = self._params.get('discharge_coefficient', self.default_discharge_coefficient)
        
        width = self._params.get('width', self.default_width)  # 闸门宽度 (m)
        g = 9.81  # 重力加速度 (m/s²)
        
        # 物理边界检查
        max_opening = self._params.get('max_opening', self.default_max_opening)
        opening = max(0.0, min(opening, max_opening))
        
        area = opening * width  # 过流面积 (m²)
        head_diff = upstream_level - downstream_level  # 水头差 (m)
        self.last_head_diff = head_diff
        
        if head_diff <= 0:
            return 0
        
        # 判断自由出流还是淹没出流
        # 当下游水位低于闸底+自由出流比例×开度时为自由出流，否则为淹没出流
        gate_bottom = self._params.get('gate_bottom_elevation', self.default_gate_bottom_elevation)
        critical_downstream_level = gate_bottom + self.free_flow_ratio * opening
        
        # 调试信息：计算过程
        is_gate1_debug = hasattr(self, 'name') and self.name == 'Gate_1'
        if is_gate1_debug:
            print(f"  计算过程: area={area:.3f}m2, head_diff={head_diff:.3f}m")
            print(f"  gate_bottom={gate_bottom:.3f}m, critical_downstream_level={critical_downstream_level:.3f}m")
            print(f"  流态判断: downstream_level({downstream_level:.3f}) <= critical({critical_downstream_level:.3f}) ? {downstream_level <= critical_downstream_level}")
        
        if downstream_level <= critical_downstream_level:
            # 自由出流：只考虑上游水头
            effective_head = upstream_level - gate_bottom
            if effective_head <= 0:
                if is_gate1_debug:
                    print(f"  自由出流: effective_head={effective_head:.3f}m <= 0, 返回 0")
                return 0
            result = C * area * math.sqrt(2 * g * effective_head)
            if is_gate1_debug:
                print(f"  自由出流: effective_head={effective_head:.3f}m, 计算结果={result:.3f}m3/s")
            return result
        else:
            # 淹没出流：考虑上下游水位差
            result = C * area * math.sqrt(2 * g * head_diff)
            if is_gate1_debug:
                print(f"  淹没出流: head_diff={head_diff:.3f}m, 计算结果={result:.3f}m3/s")
            return result

    def calculate_outflow(self, upstream_level: float, opening: float, downstream_level: float = 0, C: Optional[float] = None) -> float:
        """
        公共方法：计算通过闸门的流量。
        这是对私有方法_calculate_outflow的包装，供外部代码调用。
        """
        return self._calculate_outflow(upstream_level, opening, downstream_level, C)

    def _calculate_opening_for_flow(self, target_flow: float) -> float:
        """孔口公式的反向计算，用于根据目标流量计算所需的闸门开度。"""
        C = self._params.get('discharge_coefficient', self.default_discharge_coefficient)
        width = self._params.get('width', self.default_width)
        g = 9.81
        if self.last_head_diff <= 0:
            return 0 # 没有水头差则无法实现流动
        denominator = C * width * math.sqrt(2 * g * self.last_head_diff)
        if denominator == 0:
            return self._params.get('max_opening', self.default_max_opening) # 无法计算，如果需要流量则全开
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
        max_roc = self._params.get('max_rate_of_change', self.default_max_rate_of_change) # 最大变化速率
        current_opening = self._state.get('opening', 0)
        if self.target_opening > current_opening:
            new_opening = min(current_opening + max_roc * time_step, self.target_opening)
        else:
            new_opening = max(current_opening - max_roc * time_step, self.target_opening)
        max_opening = self._params.get('max_opening', self.default_max_opening)
        self._state['opening'] = max(0.0, min(new_opening, max_opening))
        
        if 'upstream_head' not in action:
            raise KeyError(f"Gate '{self.name}': 'upstream_head' is required in action but not provided")
        if 'downstream_head' not in action:
            raise KeyError(f"Gate '{self.name}': 'downstream_head' is required in action but not provided")
            
        upstream_level = action['upstream_head']
        downstream_level = action['downstream_head']
        
        # 调试信息：输出闸门的关键参数
        gate_bottom = self._params.get('gate_bottom_elevation', self.default_gate_bottom_elevation)
        if self.name == 'Gate_1':  # 只为特定闸门输出调试信息
            print(f"\n=== Gate_1 调试信息 ===")
            print(f"upstream_level: {upstream_level:.3f}m")
            print(f"downstream_level: {downstream_level:.3f}m")
            print(f"gate_bottom_elevation: {gate_bottom:.3f}m")
            print(f"opening: {self._state['opening']:.3f}")
            print(f"width: {self._params.get('width', self.default_width):.3f}m")
            print(f"discharge_coefficient: {self._params.get('discharge_coefficient', self.default_discharge_coefficient):.6f}")
        
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

        initial_guess = np.array([self._params.get('discharge_coefficient', self.default_discharge_coefficient)])
        result = minimize(
            _simulation_error,
            initial_guess,
            method='Nelder-Mead', # 适用于简单的单变量优化
            bounds=[(self.identification_bounds_min, self.identification_bounds_max)] # 更合理的C值物理边界：收缩系数0.61×流速系数0.98≈0.6
        )

        if result.success:
            new_c = result.x[0]
            print(f"为 '{self.name}' 进行的参数辨识成功。 新 C = {new_c:.4f}")
            return {'discharge_coefficient': new_c}
        else:
            print(f"警告: 为 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {}
