# -*- coding: utf-8 -*-
import numpy as np
from collections import deque
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any, Optional

class UnifiedCanal(PhysicalObjectInterface):
    """
    A unified model for a canal reach that can represent several different
    simplified models based on a `model_type` parameter.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus=None, inflow_topic: Optional[str] = None, **kwargs):
        super().__init__(name, initial_state, parameters)
        self._initial_state = initial_state.copy()

        # 重力加速度常量
        self.g = 9.81  # Saint-Venant方程中需要使用的重力加速度

        # 要求必需参数
        if 'model_type' not in self._params:
            raise ValueError(f"Canal '{name}': 'model_type' parameter is required")
        self.model_type = self._params['model_type']

        # 验证初始状态（关键参数应由用户提供） - 移除默认值警告
        if self.model_type in ['st_venant'] and 'water_level' not in initial_state:
            raise ValueError(f"Canal '{self.name}': 'water_level' in initial_state is required for st_venant model")
            
        # 要求必需的初始状态
        if 'water_level' not in initial_state:
            raise ValueError(f"Canal '{name}': 'water_level' in initial_state is required")
        if 'inflow' not in initial_state:
            raise ValueError(f"Canal '{name}': 'inflow' in initial_state is required")
        if 'outflow' not in initial_state:
            raise ValueError(f"Canal '{name}': 'outflow' in initial_state is required")
            
        self._state['water_level'] = initial_state['water_level']
        self._state['inflow'] = initial_state['inflow']
        self._state['outflow'] = initial_state['outflow']

        # 消息总线和主题订阅功能（简化版本）
        self.bus = message_bus
        self.inflow_topic = inflow_topic or self._params.get('inflow_topic')
        self.data_inflow = 0.0
        
        # 简化主题订阅功能
        self.topic_inflows = {}
        self.topic_outflows = {}

        # 初始化入流属性 - 要求必须提供
        if 'inflow' in kwargs:
            self._inflow = kwargs['inflow']
        elif 'inflow' in self._params:
            self._inflow = self._params['inflow']
        else:
            raise ValueError(f"Canal '{name}': 'inflow' parameter is required in kwargs or parameters")
        
        if self._inflow is None:
            raise ValueError(f"Canal '{name}': 'inflow' value cannot be None")

        # Model-specific parameter handling - 要求所有参数都必须提供
        if self.model_type == 'integral':
            if 'surface_area' not in self._params:
                raise ValueError(f"Canal '{name}': 'surface_area' parameter is required for integral model")
            if 'outlet_coefficient' not in self._params:
                raise ValueError(f"Canal '{name}': 'outlet_coefficient' parameter is required for integral model")
            self.surface_area = self._params['surface_area']
            self.outlet_coefficient = self._params['outlet_coefficient']
            
        elif self.model_type == 'integral_delay':
            if 'gain' not in self._params:
                raise ValueError(f"Canal '{name}': 'gain' parameter is required for integral_delay model")
            if 'delay' not in self._params:
                raise ValueError(f"Canal '{name}': 'delay' parameter is required for integral_delay model")
            self.gain = self._params['gain']
            self.delay = self._params['delay']
            
        elif self.model_type == 'integral_delay_zero':
            if 'gain' not in self._params:
                raise ValueError(f"Canal '{name}': 'gain' parameter is required for integral_delay_zero model")
            if 'delay' not in self._params:
                raise ValueError(f"Canal '{name}': 'delay' parameter is required for integral_delay_zero model")
            if 'zero_time_constant' not in self._params:
                raise ValueError(f"Canal '{name}': 'zero_time_constant' parameter is required for integral_delay_zero model")
            self.gain = self._params['gain']
            self.delay = self._params['delay']
            self.zero_time_constant = self._params['zero_time_constant']
            
        elif self.model_type == 'linear_reservoir':
            if 'storage_constant' not in self._params:
                raise ValueError(f"Canal '{name}': 'storage_constant' parameter is required for linear_reservoir model")
            if 'level_storage_ratio' not in self._params:
                raise ValueError(f"Canal '{name}': 'level_storage_ratio' parameter is required for linear_reservoir model")
            self.storage_constant = self._params['storage_constant']
            self.level_storage_ratio = self._params['level_storage_ratio']
            # level_storage_ratio 表示 水位/储水量 的比率
            self.storage = self._state['water_level'] / self.level_storage_ratio
            
        elif self.model_type == 'st_venant':
            # 要求所有Saint-Venant模型参数 - 不允许默认值
            required_st_venant_params = ['length', 'num_points', 'bottom_width', 'side_slope_z', 'manning_n', 'slope']
            missing_params = [p for p in required_st_venant_params if p not in self._params]
            if missing_params:
                raise ValueError(f"Canal '{name}': Missing required parameters for st_venant model: {missing_params}")
                
            self.length = self._params['length']
            self.num_points = self._params['num_points']
            # 修正：明确空间离散化，假设nom_points是网格点数
            # 那么有num_points-1个网格单元，每个单元长度为dx
            if self.num_points < 2:
                raise ValueError(f"Canal '{name}': num_points must be at least 2 for st_venant model")
            self.dx = self.length / (self.num_points - 1)

            self.bottom_width = self._params['bottom_width']
            self.side_slope_z = self._params['side_slope_z']
            self.manning_n = self._params['manning_n']
            self.slope = self._params['slope']

            # 要求初始H和Q - 不允许默认值
            if 'initial_H' not in self._params:
                raise ValueError(f"Canal '{name}': 'initial_H' parameter is required for st_venant model")
            if 'initial_Q' not in self._params:
                raise ValueError(f"Canal '{name}': 'initial_Q' parameter is required for st_venant model")
            
            initial_H = self._params['initial_H']
            initial_Q = self._params['initial_Q']

            self.H = np.array(initial_H, dtype=float)
            self.Q = np.array(initial_Q, dtype=float)
            
            # 重要注意：在这里 H 表示水深（depth）而非水位（elevation）
            # 这是为了与几何计算函数（_area, _wetted_perimeter等）保持一致
            # Q 表示流量（discharge）

            if len(self.H) != self.num_points or len(self.Q) != self.num_points:
                raise ValueError("Length of initial_H and initial_Q must match num_points.")

            print(f"UnifiedCanal '{self.name}' (st_venant model) created with {self.num_points} points (dx = {self.dx:.2f}m).")
        else:
            raise ValueError(f"Canal '{name}': Unknown model_type '{self.model_type}'. Supported types: integral, integral_delay, integral_delay_zero, linear_reservoir, st_venant")

        # History buffer for delay models
        self.inflow_history = None
        self.history_size = 0

        print(f"统一渠道 '{self.name}' 已创建 (模型类型: {self.model_type})，初始状态为 {self._state}.")

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """模拟渠道在单个时间步内的状态变化。"""
        if time_step <= 0:
            return self.get_state()

        # 确保_inflow属性存在 - 要求必须设置
        if not hasattr(self, '_inflow'):
            raise ValueError("_inflow attribute is required but not set")

        # 处理入流：简化版本，只使用物理入流
        physical_inflow = self._inflow
        legacy_data_inflow = getattr(self, 'data_inflow', 0.0)
        topic_based_inflow = sum(getattr(self, 'topic_inflows', {}).values())
        total_inflow = physical_inflow + legacy_data_inflow + topic_based_inflow

        # 处理出流：来自action的出流
        action_outflow = action.get('outflow', 0) if isinstance(action, dict) else 0
        topic_based_outflow = sum(getattr(self, 'topic_outflows', {}).values())
        total_external_outflow = action_outflow + topic_based_outflow

        # 更新入流状态供模型计算使用
        self._inflow = total_inflow
        self._state['inflow'] = total_inflow

        # 根据模型类型执行步进计算
        if self.model_type == 'integral':
            self._step_integral(time_step)
        elif self.model_type == 'integral_delay':
            self._step_integral_delay(time_step)
        elif self.model_type == 'integral_delay_zero':
            self._step_integral_delay_zero(time_step)
        elif self.model_type == 'linear_reservoir':
            self._step_linear_reservoir(time_step)
        elif self.model_type == 'st_venant':
            raise NotImplementedError("The 'st_venant' model cannot be run with step(). It must be used with the NetworkSolver.")
        else:
            raise ValueError(f"Unknown canal model type: {self.model_type}")

        # 将外部出流加到模型计算的出流上
        if total_external_outflow > 0:
            if 'outflow' not in self._state:
                raise ValueError("outflow state is required but not set")
            self._state['outflow'] = self._state['outflow'] + total_external_outflow

        # 为下一个时间步重置数据驱动的流量（简化版本）
        if hasattr(self, 'data_inflow'):
            self.data_inflow = 0.0
        if hasattr(self, 'topic_inflows'):
            for topic in self.topic_inflows:
                self.topic_inflows[topic] = 0.0
        if hasattr(self, 'topic_outflows'):
            for topic in self.topic_outflows:
                self.topic_outflows[topic] = 0.0

        return self.get_state()

    def _initialize_history(self, time_step):
        """初始化历史缓冲区，确保不为None"""
        if self.inflow_history is None:
            if not hasattr(self, 'delay'):
                raise ValueError("delay parameter is required but not set")
            self.history_size = int(self.delay / time_step) + 2 if self.delay else 2
            if 'inflow' not in self._state:
                raise ValueError("inflow state is required but not set")
            initial_inflow = self._state['inflow']
            self.inflow_history = deque([initial_inflow] * self.history_size, maxlen=self.history_size)

    def _step_integral(self, time_step: float):
        inflow = self._inflow
        # inflow已经在step函数中设置了self._state['inflow']

        # 简化的出流公式：Q = C * √h
        # 注意：这是一个经验性的简化公式，不一定遵循严格的物理定律
        # outlet_coefficient 已经包含了所有必要的系数和单位转换
        calculated_outflow = self.outlet_coefficient * np.sqrt(max(0, self._state['water_level']))
        self._state['outflow'] = calculated_outflow

        # 水位变化基于水量平衡
        water_balance = inflow - calculated_outflow
        self._state['water_level'] += water_balance / self.surface_area * time_step
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_integral_delay(self, time_step: float):
        """积分延迟模型步进计算"""
        self._initialize_history(time_step)
        inflow = self._inflow
        # inflow已经在step函数中设置了self._state['inflow']
        
        # 确保历史缓冲区已初始化（二次检查）
        if self.inflow_history is None:
            self._initialize_history(time_step)
        
        # 现在inflow_history绝对不为None
        assert self.inflow_history is not None
        
        self.inflow_history.append(inflow)
        delayed_inflow = self.inflow_history[0]
        self._state['outflow'] = delayed_inflow
        
        # 水位变化考虑延迟效应
        # 注意：gain的单位应为 [m/(m³/s·s)] = [s/m²]，表示水位对流量差值的响应系数
        level_change = self.gain * (inflow - delayed_inflow) * time_step
        self._state['water_level'] += level_change
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_integral_delay_zero(self, time_step: float):
        """积分延迟零点模型步进计算"""
        self._initialize_history(time_step)
        inflow = self._inflow
        # inflow已经在step函数中设置了self._state['inflow']
        
        # 确保历史缓冲区已初始化（二次检查）
        if self.inflow_history is None:
            self._initialize_history(time_step)
        
        # 现在inflow_history绝对不为None
        assert self.inflow_history is not None
        
        self.inflow_history.append(inflow)
        # 延迟零点模型需要两个连续的延迟值来计算导数
        # q_in_delayed: 当前时刻的延迟入流（较新的延迟值）
        # q_in_delayed_previous: 前一时刻的延迟入流（较旧的延迟值）
        q_in_delayed = self.inflow_history[1] if len(self.inflow_history) > 1 else self.inflow_history[0]
        q_in_delayed_previous = self.inflow_history[0]
        
        # 计算导数项和出流
        derivative_term = (q_in_delayed - q_in_delayed_previous) / time_step
        calculated_outflow = q_in_delayed + self.zero_time_constant * derivative_term
        self._state['outflow'] = calculated_outflow
        
        # 水位变化包含延迟和零点效应
        # 注意：gain的单位应为 [m/(m³/s·s)] = [s/m²]，表示水位对流量差值的响应系数
        level_change = self.gain * (inflow - calculated_outflow) * time_step
        self._state['water_level'] += level_change
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_linear_reservoir(self, time_step: float):
        inflow = self._inflow
        # inflow已经在step函数中设置了self._state['inflow']
        
        # 线性水库模型：一阶系统响应
        if 'outflow' not in self._state:
            raise ValueError("outflow state is required but not set")
        outflow_old = self._state['outflow']
        outflow_new = (self.storage_constant * outflow_old + time_step * inflow) / (self.storage_constant + time_step)
        self._state['outflow'] = outflow_new
        
        # 更新蓄水量和水位
        storage_change = (inflow - outflow_new) * time_step
        self.storage += storage_change
        # level_storage_ratio 表示 水位/储水量 的比率，所以 水位 = 储水量 × level_storage_ratio
        self._state['water_level'] = self.storage * self.level_storage_ratio
        self._state['water_level'] = max(0, self._state['water_level'])

    def set_inflow(self, inflow: float):
        """设置渠道的入流量。
        
        Args:
            inflow: 新的入流量 (m³/s)
        """
        self._inflow = inflow

    @property
    def is_stateful(self) -> bool:
        return True

    # --- St. Venant Model Methods ---

    def _area(self, h):
        # 梯形断面面积公式：A = (b + z*h) * h
        # 其中b为底宽，z为边坡系数（水平:1，垂直:z），h为水深
        return (self.bottom_width + self.side_slope_z * h) * h

    def _top_width(self, h):
        return self.bottom_width + 2 * self.side_slope_z * h

    def _wetted_perimeter(self, h):
        return self.bottom_width + 2 * h * np.sqrt(1 + self.side_slope_z**2)

    def _friction_slope(self, Q, A, R):
        if A < 1e-6 or R < 1e-6:
            return 0
        # 修正：使用Q的绝对值的平方乘以Q的符号，确保摩擦坡度方向正确
        return (self.manning_n**2 * Q * abs(Q)) / (A**2 * R**(4/3))

    def get_equations(self, time_step: float, theta: float):
        """
        Generates the linearized Saint-Venant equations for each segment of the reach.
        This method is only applicable when model_type is 'st_venant'.
        Note: theta parameter is now required, no default value.
        """
        if self.model_type != 'st_venant':
            raise RuntimeError("get_equations() is only valid for the 'st_venant' model type.")

        equations = []
        for i in range(self.num_points - 1):
            H_i, Q_i = self.H[i], self.Q[i]
            H_i1, Q_i1 = self.H[i+1], self.Q[i+1]
            H_avg = (H_i + H_i1) / 2
            Q_avg = (Q_i + Q_i1) / 2
            A_avg = self._area(H_avg)
            B_avg = self._top_width(H_avg)
            P_avg = self._wetted_perimeter(H_avg)
            R_avg = A_avg / P_avg if P_avg > 1e-6 else 0
            Sf_avg = self._friction_slope(Q_avg, A_avg, R_avg)

            # Simplified but stable Preissmann scheme formulation
            # Eq1: Continuity
            L1 = -theta
            L2 = B_avg * self.dx / (2 * time_step)
            L3 = theta
            L4 = B_avg * self.dx / (2 * time_step)
            RHS_cont = Q_i - Q_i1

            # Eq2: Momentum
            M1 = -self.g * A_avg * theta
            M2 = self.dx / (2 * time_step)
            M3 = self.g * A_avg * theta
            M4 = self.dx / (2 * time_step)

            if R_avg > 1e-6 and A_avg > 1e-6:
                # 摩擦坡度对流量的偏导数：dSf/dQ = (2 * n² * Q) / (A² * R^(4/3))
                # 注意：这里直接使用Q而不是|Q|，因为d(Q*|Q|)/dQ = 2*Q
                if abs(Q_avg) > 1e-6:
                    dSf_dQ = 2 * self.manning_n**2 * Q_avg / (A_avg**2 * R_avg**(4/3))
                else:
                    dSf_dQ = 0
                M2 += self.g * A_avg * self.dx * dSf_dQ * theta
                M4 += self.g * A_avg * self.dx * dSf_dQ * theta

            RHS_mom = self.dx/time_step * ( (Q_i+Q_i1)/2 - (self.Q[i]+self.Q[i+1])/2) - \
                      self.g*A_avg*self.dx * ( (H_i1-H_i)/self.dx - self.slope + Sf_avg)

            Ai = np.array([[L3, L4], [M3, M4]])
            Bi = np.array([[L1, L2], [M1, M2]])
            Ci = np.array([RHS_cont, RHS_mom])

            equations.append((Ai, Bi, Ci))

        return equations

    def update_state(self, dH: np.ndarray, dQ: np.ndarray):
        """
        Updates the state variables H and Q with the deltas calculated by the solver.
        This method is only applicable when model_type is 'st_venant'.
        """
        if self.model_type != 'st_venant':
            raise RuntimeError("update_state() is only valid for the 'st_venant' model type.")

        self.H += dH
        self.Q += dQ