"""
倒虹吸的仿真模型。
倒虹吸是一种特殊的管道结构，用于跨越河流或低洼地带的水力输送。
主要特点：管道呈倒U形结构，通过大气压作用实现跨越。
注意：根据当前参数配置（出口高程>进口高程），这实际上是一个箱涵或管涵结构。
"""
import math
from typing import Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize
import sys
import os

# 添加 core_lib 目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
core_lib_dir = os.path.dirname(current_dir)
if core_lib_dir not in sys.path:
    sys.path.insert(0, core_lib_dir)

from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters


class InvertedSiphon(PhysicalObjectInterface):
    """
    代表水务系统中的倒虹吸结构。
    
    注意：根据提供的参数（出口高程55.764m > 进口高程55.674m），
    这实际上是一个箱涵或管涵结构，不是传统意义上的倒虹吸。
    
    主要特点：
    1. 多孔口结构：具有多个并行的孔口以增加过流能力
    2. 管道流计算：基于Darcy-Weisbach公式计算沿程损失
    3. 孔口出流：在某些工况下可按孔口出流计算
    4. 局部损失：考虑进出口、弯道等局部损失
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 default_gravity: float = 9.81,
                 default_pi: float = math.pi,
                 default_quarter: float = 0.25,
                 default_darcy_exponent: int = 2,
                 default_hydraulic_radius_factor: int = 4,
                 default_friction_base: float = 0.02,
                 default_friction_empirical: float = 50.0,
                 default_friction_exponent: float = 1/3,
                 default_friction_min: float = 0.012,
                 default_friction_max: float = 0.08,
                 default_flow_coefficient_max: float = 0.8,
                 default_froude_high_threshold: float = 0.5,
                 default_froude_low_threshold: float = 0.2,
                 default_loss_ratio_high_threshold: float = 2.0,
                 default_loss_ratio_low_threshold: float = 0.5,
                 default_conservative_factor: float = 0.7,
                 default_additional_loss_coefficient: float = 0.1):
        super().__init__(name, initial_state, parameters)
        
        # 初始化状态变量
        self._state.setdefault('outflow', 0)
        self._state.setdefault('head_loss', 0)
        self._state.setdefault('velocity', 0)
        self._state.setdefault('flow_per_orifice', 0)

        # 将默认参数值设置为实例属性
        self.GRAVITY_ACCELERATION = default_gravity      # 重力加速度 (m/s²)
        self.PI = default_pi                     # 圆周率
        self.QUARTER = default_quarter                   # 1/4
        self.DARCY_EXPONENT = default_darcy_exponent               # Darcy-Weisbach公式指数
        self.HYDRAULIC_RADIUS_FACTOR = default_hydraulic_radius_factor      # 矩形管道水力半径系数
        self.default_friction_base = default_friction_base
        self.default_friction_empirical = default_friction_empirical
        self.default_friction_exponent = default_friction_exponent
        self.default_friction_min = default_friction_min
        self.default_friction_max = default_friction_max
        self.default_flow_coefficient_max = default_flow_coefficient_max
        self.default_froude_high_threshold = default_froude_high_threshold
        self.default_froude_low_threshold = default_froude_low_threshold
        self.default_loss_ratio_high_threshold = default_loss_ratio_high_threshold
        self.default_loss_ratio_low_threshold = default_loss_ratio_low_threshold
        self.default_conservative_factor = default_conservative_factor
        self.default_additional_loss_coefficient = default_additional_loss_coefficient
        
        # 警告：物理配置检查
        if self._params['outlet_zb'] > self._params['inlet_zb']:
            print(f"⚠️  警告：出口高程({self._params['outlet_zb']:.3f}m) > 进口高程({self._params['inlet_zb']:.3f}m)")
            print(f"   这是上坡管道配置，不是传统的倒虹吸结构！")

        # 参数验证
        self._validate_parameters()
        
        print(f"倒虹吸 '{self.name}' 已创建。")
        print(f"  长度: {self._params['length']:.1f} m")
        print(f"  孔数: {self._params['n_orifice']:.0f}")
        print(f"  单孔尺寸: {self._params['b_orifice']:.1f} × {self._params['h_orifice']:.1f} m")
        print(f"  进口底高程: {self._params['inlet_zb']:.3f} m")
        print(f"  出口底高程: {self._params['outlet_zb']:.3f} m")

    def _validate_parameters(self):
        """验证倒虹吸参数的合理性。"""
        required_params = [
            'length', 'l_orifice', 'manning_n', 'inlet_zb', 'inlet_b', 'inlet_m',
            'outlet_zb', 'outlet_b', 'outlet_m', 'n_orifice', 'b_orifice', 
            'h_orifice', 'loss_coeff'
        ]
        
        for param in required_params:
            if param not in self._params:
                raise ValueError(f"倒虹吸缺少必需参数: {param}")
        
        # 物理约束检查
        if self._params['length'] <= 0:
            raise ValueError("倒虹吸长度必须大于0")
        if self._params['n_orifice'] <= 0:
            raise ValueError("孔数必须大于0")
        if self._params['b_orifice'] <= 0 or self._params['h_orifice'] <= 0:
            raise ValueError("孔口尺寸必须大于0")
        if self._params['manning_n'] <= 0:
            raise ValueError("曼宁系数必须大于0")
        if self._params['loss_coeff'] < 0:
            raise ValueError("损失系数不能为负")

    def _calculate_orifice_area(self) -> float:
        """计算单个孔口的过流面积。"""
        return self._params['b_orifice'] * self._params['h_orifice']

    def _calculate_total_area(self) -> float:
        """计算总过流面积。"""
        return self._params['n_orifice'] * self._calculate_orifice_area()

    def _calculate_hydraulic_radius(self) -> float:
        """计算单个孔口的水力半径（矩形管道，四面有壁）。"""
        b = self._params['b_orifice']
        h = self._params['h_orifice']
        area = b * h
        wetted_perimeter = 2 * (h + b)  # 矩形管道四面有壁
        return area / wetted_perimeter if wetted_perimeter > 0 else 0

    def _calculate_darcy_weisbach_flow(self, head_difference: float) -> float:
        """
        使用Darcy-Weisbach公式计算管道流量。
        这是管道流的标准方法，比Manning公式更适合。
        Q = A * sqrt(2*g*H / (f*L/D + K))
        其中 f 是摩擦系数，K 是局部损失系数
        """
        if head_difference <= 0:
            return 0

        # 计算等效摩擦系数（基于Manning系数的正确转换）
        manning_n = self._params['manning_n']
        hydraulic_radius = self._calculate_hydraulic_radius()
        
        # 正确的Manning转Darcy-Weisbach转换：
        # 对于矩形管道：f = 6.78 * (n/R^(1/6))^2
        # 这里使用简化的工程公式
        if hydraulic_radius > 0:
            # 使用更准确的经验公式：f = 0.02 * (1 + 50*n^2/R^(1/3))
            friction_factor = 0.02 * (1 + 50 * (manning_n ** 2) / (hydraulic_radius ** (1/3)))
            # 限制在合理范围内
            friction_factor = max(0.012, min(friction_factor, 0.08))
        else:
            friction_factor = 0.02  # 默认值
        
        length = self._params['l_orifice']
        # 等效直径（矩形管道）
        equiv_diameter = 4 * hydraulic_radius
        
        # 沿程损失系数
        friction_loss_coeff = friction_factor * length / equiv_diameter if equiv_diameter > 0 else 0
        
        # 注意：这里只使用沿程损失系数，局部损失将在反推时单独计算
        # 避免重复计算同一个loss_coeff
        if friction_loss_coeff <= 0:
            return 0
        
        # 单孔流量（仅考虑沿程损失）
        single_area = self._calculate_orifice_area()
        single_flow = single_area * math.sqrt(2 * self.GRAVITY_ACCELERATION * head_difference / friction_loss_coeff)
        
        # 总流量
        total_flow = self._params['n_orifice'] * single_flow
        
        return total_flow

    def _calculate_orifice_flow(self, head_difference: float) -> float:
        """
        使用孔口出流公式计算流量。
        Q = μ * A * sqrt(2 * g * H)
        其中 μ 是流量系数（一般0.6-0.8），A 是总过流面积，H 是水头差
        """
        if head_difference <= 0:
            return 0

        # 流量系数的正确计算（基于损失系数）
        # 对于矩形孔口，流量系数一般在0.6-0.8之间
        loss_coeff = self._params['loss_coeff']
        # 使用经验公式：μ = 1/sqrt(1 + K)，但不超过0.8
        flow_coefficient = min(0.8, 1.0 / math.sqrt(1.0 + loss_coeff))
        
        total_area = self._calculate_total_area()
        
        # 孔口出流公式
        flow = flow_coefficient * total_area * math.sqrt(2 * self.GRAVITY_ACCELERATION * head_difference)
        
        return flow

    def _calculate_head_loss_darcy_weisbach(self, flow: float) -> float:
        """使用Darcy-Weisbach公式反推水头损失。"""
        if flow <= 0:
            return 0

        # 单孔流量
        single_flow = flow / self._params['n_orifice']
        single_area = self._calculate_orifice_area()
        
        if single_area <= 0:
            return float('inf')
        
        # 单孔流速
        velocity = single_flow / single_area
        velocity_head = velocity**2 / (2 * self.GRAVITY_ACCELERATION)
        
        # 计算摩擦系数（使用修正后的公式）
        manning_n = self._params['manning_n']
        hydraulic_radius = self._calculate_hydraulic_radius()
        
        if hydraulic_radius > 0:
            friction_factor = 0.02 * (1 + 50 * (manning_n ** 2) / (hydraulic_radius ** (1/3)))
            friction_factor = max(0.012, min(friction_factor, 0.08))
        else:
            friction_factor = 0.02
        
        # 等效直径
        equiv_diameter = 4 * hydraulic_radius
        length = self._params['l_orifice']
        
        # 沿程损失
        if equiv_diameter > 0:
            friction_loss = friction_factor * (length / equiv_diameter) * velocity_head
        else:
            friction_loss = 0
        
        # 局部损失
        local_loss = self._params['loss_coeff'] * velocity_head
        
        # 总损失
        total_loss = friction_loss + local_loss
        
        return total_loss

    def _calculate_total_head_loss(self, flow: float) -> float:
        """
        计算总水头损失，确保各类损失只被计算一次。
        包括：
        1. 沿程损失（摩擦损失）
        2. 主要局部损失（孔口收缩、突然扩大等）
        3. 其他附加损失（进出口渐变、弯道等）
        """
        if flow <= 0:
            return 0

        # 计算沿程损失（使用Darcy-Weisbach公式但不包括主要局部损失）
        friction_loss = self._calculate_friction_loss_only(flow)
        
        # 计算主要局部损失（孔口收缩、突然扩大等）
        major_local_loss = self._calculate_major_local_loss(flow)
        
        # 计算其他附加损失（进出口渐变、弯道等）
        additional_loss = self._calculate_additional_losses(flow)
        
        # 总损失 = 沿程损失 + 主要局部损失 + 其他附加损失
        total_loss = friction_loss + major_local_loss + additional_loss
        
        return total_loss
    
    def _calculate_friction_loss_only(self, flow: float) -> float:
        """仅计算沿程摩擦损失，不包括局部损失。"""
        if flow <= 0:
            return 0

        # 单孔流量
        single_flow = flow / self._params['n_orifice']
        single_area = self._calculate_orifice_area()
        
        if single_area <= 0:
            return 0
        
        # 单孔流速
        velocity = single_flow / single_area
        velocity_head = velocity**2 / (2 * self.GRAVITY_ACCELERATION)
        
        # 计算摩擦系数
        manning_n = self._params['manning_n']
        hydraulic_radius = self._calculate_hydraulic_radius()
        
        if hydraulic_radius > 0:
            friction_factor = 0.02 * (1 + 50 * (manning_n ** 2) / (hydraulic_radius ** (1/3)))
            friction_factor = max(0.012, min(friction_factor, 0.08))
        else:
            friction_factor = 0.02
        
        # 等效直径
        equiv_diameter = 4 * hydraulic_radius
        length = self._params['l_orifice']
        
        # 仅沿程摩擦损失
        if equiv_diameter > 0:
            friction_loss = friction_factor * (length / equiv_diameter) * velocity_head
        else:
            friction_loss = 0
        
        return friction_loss
    
    def _calculate_major_local_loss(self, flow: float) -> float:
        """计算主要局部损失（孔口收缩、突然扩大等）。"""
        if flow <= 0:
            return 0

        total_area = self._calculate_total_area()
        if total_area == 0:
            return 0

        # 计算平均流速
        velocity = flow / total_area
        velocity_head = velocity**2 / (2 * self.GRAVITY_ACCELERATION)
        
        # 主要局部损失系数（孔口收缩、突然扩大等）
        major_local_loss_coeff = self._params['loss_coeff']
        
        # 主要局部损失 = 损失系数 × 速度水头
        major_local_loss = major_local_loss_coeff * velocity_head
        
        return major_local_loss

    def _calculate_additional_losses(self, flow: float) -> float:
        """
        计算其他附加损失（如进出口渐变、弯道等）。
        注意：这里不包括主要的孔口损失，那个已在Darcy-Weisbach中计算。
        这里主要计算：
        1. 进口渐变损失
        2. 出口扩散损失  
        3. 弯道损失等
        """
        if flow <= 0:
            return 0

        total_area = self._calculate_total_area()
        if total_area == 0:
            return 0

        # 计算平均流速
        velocity = flow / total_area
        velocity_head = velocity**2 / (2 * self.GRAVITY_ACCELERATION)
        
        # 其他附加损失系数（进出口渐变、弯道等）
        # 这些通常比主要孔口损失小得多
        additional_loss_coeff = 0.1  # 经验值，可根据具体结构调整
        
        # 附加损失 = 附加损失系数 × 速度水头
        additional_loss = additional_loss_coeff * velocity_head
        
        return additional_loss

    def _determine_flow_regime(self, head_difference: float, flow_darcy: float, flow_orifice: float) -> float:
        """
        根据水力条件确定适合的流动计算方法。
        
        物理判断依据：
        1. 对于上坡管道（非倒虹吸），主要为有压管道流
        2. 高水头、高流速时，沿程损失占主导，用Darcy-Weisbach
        3. 低水头、低流速时，局部损失占主导，接近孔口出流
        """
        # 计算当量数（无量纲参数）
        total_area = self._calculate_total_area()
        if total_area > 0 and flow_darcy > 0:
            velocity = flow_darcy / total_area
            hydraulic_radius = self._calculate_hydraulic_radius()
            
            if hydraulic_radius > 0:
                # 弗劳德数 Fr = v/sqrt(g*R)
                froude_number = velocity / math.sqrt(self.GRAVITY_ACCELERATION * hydraulic_radius)
                
                # 损失比值 = 沿程损失 / 局部损失
                friction_factor = 0.02 * (1 + 50 * (self._params['manning_n'] ** 2) / (hydraulic_radius ** (1/3)))
                equiv_diameter = 4 * hydraulic_radius
                length = self._params['l_orifice']
                
                if equiv_diameter > 0:
                    friction_loss_ratio = (friction_factor * length / equiv_diameter)
                    local_loss_ratio = self._params['loss_coeff']
                    loss_ratio = friction_loss_ratio / max(local_loss_ratio, 0.1)
                    
                    # 物理判断逻辑：
                    if froude_number > 0.5 and loss_ratio > 2.0:
                        # 高速流动，沿程损失占主导
                        return flow_darcy
                    elif froude_number < 0.2 and loss_ratio < 0.5:
                        # 低速流动，局部损失占主导
                        return flow_orifice
                    else:
                        # 过渡区间，采用保守值
                        return min(flow_darcy, flow_orifice)
        
        # 默认情况：对于箱涵类结构，优先使用Darcy-Weisbach
        return flow_darcy

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """
        计算倒虹吸的水力状态。支持两种计算模式：
        1. 根据上下游水头计算流量
        2. 根据给定流量计算水头损失
        """
        if 'outflow' in action:
            # 模式2：根据给定流量计算水头损失
            outflow = action['outflow']
            
            # 使用修正后的总损失计算方法（避免重复计算）
            total_head_loss = self._calculate_total_head_loss(outflow)
            
            self._state['head_loss'] = total_head_loss
            self._state['outflow'] = outflow
            
            # 计算其他状态量
            if outflow > 0:
                total_area = self._calculate_total_area()
                self._state['velocity'] = outflow / total_area if total_area > 0 else 0
                self._state['flow_per_orifice'] = outflow / self._params['n_orifice']
            else:
                self._state['velocity'] = 0
                self._state['flow_per_orifice'] = 0
                
        else:
            # 模式1：根据水头差计算流量
            if 'upstream_head' not in action:
                raise KeyError(f"InvertedSiphon '{self.name}': 'upstream_head' is required in action but not provided")
            if 'downstream_head' not in action:
                raise KeyError(f"InvertedSiphon '{self.name}': 'downstream_head' is required in action but not provided")
                
            upstream_head = action['upstream_head']
            downstream_head = action['downstream_head']
            
            # 计算有效水头差（考虑进出口高程）
            inlet_level = upstream_head  # 假设上游水头对应进口水位
            outlet_level = downstream_head  # 假设下游水头对应出口水位
            
            # 有效水头 = 进口水位 - 出口水位
            effective_head = inlet_level - outlet_level
            
            if effective_head <= 0:
                self._state['outflow'] = 0
                self._state['head_loss'] = 0
                self._state['velocity'] = 0
                self._state['flow_per_orifice'] = 0
            else:
                # 使用改进的流动制判断方法
                darcy_flow = self._calculate_darcy_weisbach_flow(effective_head)
                orifice_flow = self._calculate_orifice_flow(effective_head)
                
                # 根据物理条件选择适合的计算方法
                outflow = self._determine_flow_regime(effective_head, darcy_flow, orifice_flow)
                
                # 计算实际水头损失（与有效水头不同，避免重复计算）
                actual_head_loss = self._calculate_total_head_loss(outflow)
                
                self._state['outflow'] = outflow
                self._state['head_loss'] = actual_head_loss  # 使用实际水头损失，不是有效水头
                
                # 计算其他状态量
                if outflow > 0:
                    total_area = self._calculate_total_area()
                    self._state['velocity'] = outflow / total_area if total_area > 0 else 0
                    self._state['flow_per_orifice'] = outflow / self._params['n_orifice']
                else:
                    self._state['velocity'] = 0
                    self._state['flow_per_orifice'] = 0

        return self.get_state()

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """
        辨识倒虹吸的水力参数，主要是曼宁系数和损失系数。
        """
        required_keys = ['upstream_levels', 'downstream_levels', 'observed_flows']
        if not all(k in data for k in required_keys):
            raise ValueError(f"辨识数据必须包含 {required_keys}。")

        up_levels = data['upstream_levels']
        down_levels = data['downstream_levels']
        obs_flows = data['observed_flows']
        head_diffs = up_levels - down_levels

        def _simulation_error(params: np.ndarray) -> float:
            """优化器的目标函数。"""
            manning_n, loss_coeff = params
            
            # 临时更新参数进行计算
            original_manning_n = self._params['manning_n']
            original_loss_coeff = self._params['loss_coeff']
            
            self._params['manning_n'] = manning_n
            self._params['loss_coeff'] = loss_coeff
            
            try:
                simulated_flows = []
                for head_diff in head_diffs:
                    if head_diff > 0:
                        darcy_flow = self._calculate_darcy_weisbach_flow(head_diff)
                        orifice_flow = self._calculate_orifice_flow(head_diff)
                        flow = self._determine_flow_regime(head_diff, darcy_flow, orifice_flow)
                    else:
                        flow = 0
                    simulated_flows.append(flow)
                
                simulated_flows = np.array(simulated_flows)
                rmse = np.sqrt(np.mean((simulated_flows - obs_flows)**2))
                
            finally:
                # 恢复原始参数
                self._params['manning_n'] = original_manning_n
                self._params['loss_coeff'] = original_loss_coeff
            
            return rmse

        # 初始猜测值
        initial_manning_n = self._params.get('manning_n', 0.015)
        initial_loss_coeff = self._params.get('loss_coeff', 1.0)
        initial_guess = np.array([initial_manning_n, initial_loss_coeff])
        
        # 参数边界
        bounds = [
            (0.008, 0.050),  # 曼宁系数的合理范围
            (0.1, 5.0)       # 损失系数的合理范围
        ]

        result = minimize(
            _simulation_error,
            initial_guess,
            method='L-BFGS-B',
            bounds=bounds
        )

        if result.success:
            new_manning_n, new_loss_coeff = result.x
            print(f"为倒虹吸 '{self.name}' 进行的参数辨识成功：")
            print(f"  新曼宁系数: {new_manning_n:.6f}")
            print(f"  新损失系数: {new_loss_coeff:.4f}")
            return {
                'manning_n': new_manning_n,
                'loss_coeff': new_loss_coeff
            }
        else:
            print(f"警告: 为倒虹吸 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {}

    def get_design_parameters(self) -> Dict[str, Any]:
        """获取倒虹吸的设计参数摘要。
        
        注意：参数中的 'length' 和 'l_orifice' 含义不明确，
        建议明确区分：
        - total_length: 总管道长度
        - effective_length: 有效流动段长度  
        - orifice_length: 孔口段长度
        """
        single_orifice_area = self._calculate_orifice_area()
        total_area = self._calculate_total_area()
        hydraulic_radius = self._calculate_hydraulic_radius()
        
        return {
            'geometry': {
                'length': self._params['length'],
                'orifice_length': self._params['l_orifice'],
                'n_orifice': self._params['n_orifice'],
                'single_orifice_dimensions': {
                    'width': self._params['b_orifice'],
                    'height': self._params['h_orifice'],
                    'area': single_orifice_area
                },
                'total_area': total_area,
                'hydraulic_radius': hydraulic_radius
            },
            'elevations': {
                'inlet_bottom': self._params['inlet_zb'],
                'outlet_bottom': self._params['outlet_zb'],
                'elevation_difference': self._params['outlet_zb'] - self._params['inlet_zb']
            },
            'hydraulic_parameters': {
                'manning_n': self._params['manning_n'],
                'loss_coefficient': self._params['loss_coeff']
            },
            'inlet_section': {
                'bottom_width': self._params['inlet_b'],
                'side_slope': self._params['inlet_m']
            },
            'outlet_section': {
                'bottom_width': self._params['outlet_b'],
                'side_slope': self._params['outlet_m']
            }
        }