"""
管道的仿真模型。
"""
import math
from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters

class Pipe(PhysicalObjectInterface):
    """
    代表一个在两点之间输送水的管道。
    该模型可以根据 'calculation_method' 参数使用 Darcy-Weisbach 或 Manning 公式来计算流量。
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._state.setdefault('head_loss', 0)

        self.method = self._params.get('calculation_method', 'darcy_weisbach')
        if self.method not in ['darcy_weisbach', 'manning']:
            raise ValueError(f"未知的计算方法: {self.method}")

        print(f"管道 '{self.name}' 已创建，使用 '{self.method}' 方法。")

    def _calculate_flow_darcy_weisbach(self, head_difference: float, f: Optional[float] = None) -> float:
        """使用 Darcy-Weisbach 公式计算流量。"""
        if head_difference <= 0:
            return 0

        g = 9.81
        friction_factor = f if f is not None else self._params['friction_factor']
        length = self._params['length']
        diameter = self._params['diameter']
        area = (math.pi / 4) * (diameter ** 2)

        # Q = A * sqrt(2 * g * h_L * D / (f * L))
        if friction_factor * length == 0: return 0
        flow = area * math.sqrt(2 * g * head_difference * diameter / (friction_factor * length))
        return flow

    def _calculate_flow_manning(self, head_difference: float, n: Optional[float] = None) -> float:
        """使用 Manning 公式（适用于满管圆形管道）计算流量。"""
        if head_difference <= 0:
            return 0

        manning_n = n if n is not None else self._params['manning_n']
        if manning_n == 0: return float('inf')

        length = self._params['length']
        if length == 0: return float('inf')

        diameter = self._params['diameter']

        area = (math.pi / 4) * (diameter ** 2)
        hydraulic_radius = diameter / 4 # 满管圆形管道的水力半径
        slope = head_difference / length

        # Q = (1.0/n) * A * R_h^(2/3) * S^(1/2) --- 国际单位制
        flow = (1.0 / manning_n) * area * (hydraulic_radius ** (2/3)) * math.sqrt(slope)
        return flow

    def _calculate_head_loss_darcy_weisbach(self, flow: float) -> float:
        """Calculates head loss for a given flow rate using the Darcy-Weisbach equation."""
        if flow <= 0:
            return 0

        g = 9.81
        friction_factor = self._params['friction_factor']
        length = self._params['length']
        diameter = self._params['diameter']
        area = (math.pi / 4) * (diameter ** 2)

        if diameter == 0 or area == 0:
            return float('inf')

        # h_L = f * (L/D) * (v^2 / (2*g)) = f * (L/D) * (Q^2 / (A^2 * 2*g))
        head_loss = friction_factor * (length / diameter) * (flow**2) / (2 * g * area**2)
        return head_loss

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Calculates the pipe's state. It can operate in two modes:
        1. If upstream and downstream heads are provided, it calculates the resulting flow.
        2. If an outflow is provided (e.g., from a downstream component), it calculates the required head loss.
        """
        if 'outflow' in action:
            # Mode 2: Calculate head loss from a given flow
            outflow = action['outflow']
            if self.method == 'darcy_weisbach':
                head_loss = self._calculate_head_loss_darcy_weisbach(outflow)
            else:
                # Note: Manning's equation is typically used to calculate flow, not head loss directly.
                # This is a simplified inversion for the example. A proper implementation might need a solver.
                # For now, we'll use a simplified approach assuming we can rearrange the formula.
                # Q = (1/n) * A * R_h^(2/3) * (h_L/L)^(1/2) => h_L = L * (Q*n / (A*R_h^(2/3)))^2
                manning_n = self._params.get('manning_n', 0.013)
                diameter = self._params['diameter']
                area = (math.pi / 4) * (diameter ** 2)
                hydraulic_radius = diameter / 4
                length = self._params['length']
                if area > 0 and hydraulic_radius > 0:
                    head_loss = length * (outflow * manning_n / (area * hydraulic_radius**(2/3)))**2
                else:
                    head_loss = 0
            self._state['head_loss'] = head_loss
            self._state['outflow'] = outflow
        else:
            # Mode 1: Calculate flow from heads
            upstream_head = action.get('upstream_head', 0)
            downstream_head = action.get('downstream_head', 0)
            head_difference = upstream_head - downstream_head

            if self.method == 'darcy_weisbach':
                outflow = self._calculate_flow_darcy_weisbach(head_difference)
            else: # manning
                outflow = self._calculate_flow_manning(head_difference)

            self._state['head_loss'] = head_difference if head_difference > 0 else 0
            self._state['outflow'] = outflow

        return self.get_state()

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """辨识管道的水力参数（摩擦系数 f 或曼宁 n）。"""
        required_keys = ['upstream_levels', 'downstream_levels', 'observed_flows']
        if not all(k in data for k in required_keys):
            raise ValueError(f"辨识数据必须包含 {required_keys}。")

        up_levels = data['upstream_levels']
        down_levels = data['downstream_levels']
        obs_flows = data['observed_flows']
        head_diffs = up_levels - down_levels

        if self.method == 'manning':
            param_key = 'manning_n'
            calc_func = self._calculate_flow_manning
            initial_guess = self._params.get(param_key, 0.013)
            bounds = [(0.001, 0.1)] # 曼宁 n 的物理边界
        else: # darcy_weisbach
            param_key = 'friction_factor'
            calc_func = self._calculate_flow_darcy_weisbach
            initial_guess = self._params.get(param_key, 0.02)
            bounds = [(0.001, 0.5)] # f 的物理边界

        def _simulation_error(param_to_id: np.ndarray) -> float:
            """优化器的目标函数。"""
            param = param_to_id[0]
            simulated_flows = np.array([calc_func(h, param) for h in head_diffs])
            rmse = np.sqrt(np.mean((simulated_flows - obs_flows)**2))
            return rmse

        result = minimize(
            _simulation_error,
            np.array([initial_guess]),
            method='L-BFGS-B', # 该方法支持边界
            bounds=bounds
        )

        if result.success:
            new_param_val = result.x[0]
            print(f"为 '{self.name}' 进行的参数辨识成功。 新 {param_key} = {new_param_val:.6f}")
            return {param_key: new_param_val}
        else:
            print(f"警告: 为 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {}
