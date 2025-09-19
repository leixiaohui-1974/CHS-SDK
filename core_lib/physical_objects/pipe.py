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

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 default_gravity: float = 9.81,
                 default_manning_n: float = 0.013,
                 default_pi_factor: float = 0.25,
                 default_hydraulic_radius_factor: float = 0.25,
                 default_exponent_two_thirds: float = 2/3,
                 identification_bounds_manning_min: float = 0.001,
                 identification_bounds_manning_max: float = 0.1,
                 identification_bounds_friction_min: float = 0.001,
                 identification_bounds_friction_max: float = 0.5):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0)
        self._state.setdefault('head_loss', 0)

        # 将默认参数值设置为实例属性
        self.default_gravity = default_gravity
        self.default_manning_n = default_manning_n
        self.default_pi_factor = default_pi_factor
        self.default_hydraulic_radius_factor = default_hydraulic_radius_factor
        self.default_exponent_two_thirds = default_exponent_two_thirds
        self.identification_bounds_manning_min = identification_bounds_manning_min
        self.identification_bounds_manning_max = identification_bounds_manning_max
        self.identification_bounds_friction_min = identification_bounds_friction_min
        self.identification_bounds_friction_max = identification_bounds_friction_max

        self.method = self._params.get('calculation_method', 'darcy_weisbach')
        if self.method not in ['darcy_weisbach', 'manning']:
            raise ValueError(f"未知的计算方法: {self.method}")

        print(f"管道 '{self.name}' 已创建，使用 '{self.method}' 方法。")

    def _calculate_flow_darcy_weisbach(self, head_difference: float, f: Optional[float] = None) -> float:
        """使用 Darcy-Weisbach 公式计算流量。"""
        if head_difference <= 0:
            return 0

        # 特殊处理：如果是倒虹吸（有孔口参数），使用孔口过流公式
        if 'n_orifice' in self._params and 'b_orifice' in self._params and 'h_orifice' in self._params:
            # 孔口过流公式：Q = Cd * A * sqrt(2 * g * h)
            n_orifice = self._params['n_orifice']
            b_orifice = self._params['b_orifice']
            h_orifice = self._params['h_orifice']
            orifice_area = n_orifice * b_orifice * h_orifice  # 总过流面积
            
            # 孔口流量系数，从损失系数计算得出
            loss_coeff = self._params.get('loss_coeff', 1.0)
            discharge_coeff = 1.0 / math.sqrt(1.0 + loss_coeff)  # Cd = 1/sqrt(1+k)
            
            g = self.default_gravity
            flow = discharge_coeff * orifice_area * math.sqrt(2 * g * head_difference)
            
            if hasattr(self, 'name') and self.name == 'Pipe_1':
                print(f"  倒虹吸孔口计算: {n_orifice}个孔，每孔{b_orifice}x{h_orifice}m")
                print(f"  过流面积: {orifice_area:.3f}m2, 流量系数: {discharge_coeff:.3f}")
            
            return flow
        
        # 原有的满管流Darcy-Weisbach公式
        g = self.default_gravity
        friction_factor = f if f is not None else self._params['friction_factor']
        length = self._params['length']
        diameter = self._params['diameter']
        area = math.pi * self.default_pi_factor * (diameter ** 2)

        # Q = A * sqrt(2 * g * h_L * D / (f * L))
        if friction_factor * length == 0: return 0
        flow = area * math.sqrt(2 * g * head_difference * diameter / (friction_factor * length))
        return flow

    def _calculate_flow_manning(self, head_difference: float, n: Optional[float] = None) -> float:
        """使用 Manning 公式（适用于满管圆形管道）计算流量。"""
        if head_difference <= 0:
            return 0

        manning_n = n if n is not None else self._params.get('manning_n', self.default_manning_n)
        if manning_n == 0: return float('inf')

        length = self._params['length']
        if length == 0: return float('inf')

        diameter = self._params['diameter']

        area = math.pi * self.default_pi_factor * (diameter ** 2)
        hydraulic_radius = diameter * self.default_hydraulic_radius_factor # 满管圆形管道的水力半径
        slope = head_difference / length

        # Q = (1.0/n) * A * R_h^(2/3) * S^(1/2) --- 国际单位制
        flow = (1.0 / manning_n) * area * (hydraulic_radius ** self.default_exponent_two_thirds) * math.sqrt(slope)
        return flow

    def _calculate_head_loss_darcy_weisbach(self, flow: float) -> float:
        """Calculates head loss for a given flow rate using the Darcy-Weisbach equation."""
        if flow <= 0:
            return 0

        g = self.default_gravity
        friction_factor = self._params['friction_factor']
        length = self._params['length']
        diameter = self._params['diameter']
        area = math.pi * self.default_pi_factor * (diameter ** 2)

        if diameter == 0 or area == 0:
            return float('inf')

        # h_L = f * (L/D) * (v^2 / (2*g)) = f * (L/D) * (Q^2 / (A^2 * 2*g))
        head_loss = friction_factor * (length / diameter) * (flow**2) / (2 * g * area**2)
        return head_loss

    def step(self, action: Dict[str, Any], time_step: float) -> State:
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
                manning_n = self._params.get('manning_n', self.default_manning_n)
                diameter = self._params['diameter']
                area = math.pi * self.default_pi_factor * (diameter ** 2)
                hydraulic_radius = diameter * self.default_hydraulic_radius_factor
                length = self._params['length']
                if area > 0 and hydraulic_radius > 0:
                    head_loss = length * (outflow * manning_n / (area * hydraulic_radius**self.default_exponent_two_thirds))**2
                else:
                    head_loss = 0
            self._state['head_loss'] = head_loss
            self._state['outflow'] = outflow
        else:
            # Mode 1: Calculate flow from heads
            if 'upstream_head' not in action:
                raise KeyError(f"Pipe '{self.name}': 'upstream_head' is required in action but not provided")
            if 'downstream_head' not in action:
                raise KeyError(f"Pipe '{self.name}': 'downstream_head' is required in action but not provided")
                
            upstream_head = action['upstream_head']
            downstream_head = action['downstream_head']
            head_difference = upstream_head - downstream_head
            
            # 调试信息：Pipe_1的水头差和流量计算
            if hasattr(self, 'name') and self.name == 'Pipe_1':
                print(f"\n=== Pipe_1 调试信息 ===")
                print(f"上游水头: {upstream_head:.3f}m")
                print(f"下游水头: {downstream_head:.3f}m")
                print(f"水头差: {head_difference:.3f}m")
                print(f"计算方法: {self.method}")
                print(f"管道参数: L={self._params['length']}m, D={self._params['diameter']}m")
                if self.method == 'darcy_weisbach':
                    print(f"摩擦系数 f: {self._params['friction_factor']}")
                else:
                    print(f"曼宁系数 n: {self._params.get('manning_n', 0.015)}")

            if self.method == 'darcy_weisbach':
                theoretical_flow = self._calculate_flow_darcy_weisbach(head_difference)
            else: # manning
                theoretical_flow = self._calculate_flow_manning(head_difference)
                
            # 关键修复：实际出流不能超过实际入流
            actual_inflow = getattr(self, '_inflow', 0.0)
            outflow = min(theoretical_flow, actual_inflow) if actual_inflow > 0 else theoretical_flow
                
            if hasattr(self, 'name') and self.name == 'Pipe_1':
                print(f"  理论通过能力: {theoretical_flow:.3f} m3/s")
                print(f"  实际入流: {actual_inflow:.3f} m3/s")
                print(f"  最终出流: {outflow:.3f} m3/s")

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

        # 验证输入数据的有效性
        valid_indices = (head_diffs > 0) & (obs_flows >= 0)
        if not np.any(valid_indices):
            print(f"警告: 管道 '{self.name}' 没有有效的辨识数据点（需要水头差>0且流量>=0）。")
            return {}

        # 使用有效数据点
        head_diffs = head_diffs[valid_indices]
        obs_flows = obs_flows[valid_indices]

        if len(head_diffs) < 5:
            print(f"警告: 管道 '{self.name}' 有效数据点太少 ({len(head_diffs)} < 5)，可能影响辨识精度。")

        if self.method == 'manning':
            param_key = 'manning_n'
            calc_func = self._calculate_flow_manning
            initial_guess = self._params.get(param_key, self.default_manning_n)
            bounds = [(self.identification_bounds_manning_min, self.identification_bounds_manning_max)] # 曼宁 n 的物理边界
        else: # darcy_weisbach
            param_key = 'friction_factor'
            calc_func = self._calculate_flow_darcy_weisbach
            initial_guess = self._params.get(param_key, 0.02)
            bounds = [(self.identification_bounds_friction_min, self.identification_bounds_friction_max)] # f 的物理边界

        def _simulation_error(param_to_id: np.ndarray) -> float:
            """优化器的目标函数。"""
            param = param_to_id[0]
            simulated_flows = np.array([calc_func(h, param) for h in head_diffs])
            rmse = np.sqrt(np.mean((simulated_flows - obs_flows)**2))
            return rmse

        result = minimize(
            _simulation_error,
            np.array([initial_guess]),
            method='L-BFGS-B',  # 该方法支持边界
            bounds=bounds,
            options={'maxiter': 1000, 'ftol': 1e-12}  # 增加最大迭代次数和精度
        )

        if result.success:
            new_param_val = result.x[0]
            print(f"为 '{self.name}' 进行的参数辨识成功。 新 {param_key} = {new_param_val:.6f}")
            return {param_key: new_param_val}
        else:
            print(f"警告: 为 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {}
