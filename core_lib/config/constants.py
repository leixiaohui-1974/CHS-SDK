#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物理常量和系统常量定义

这个模块定义了CHS-SDK中使用的所有物理常量、数学常量和系统常量，
避免在代码中硬编码魔数，提高代码的可维护性和可读性。

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import math
from typing import Dict, Any

# =============================================================================
# 物理常量 (Physical Constants)
# =============================================================================

class PhysicalConstants:
    """物理常量类 - 包含所有不可变的自然常数"""
    
    # 重力加速度 (m/s²)
    GRAVITY_ACCELERATION = 9.81
    
    # 水密度 (kg/m³)
    WATER_DENSITY = 1000.0
    
    # 空气密度 (kg/m³) - 用于某些计算
    AIR_DENSITY = 1.225
    
    # 水的动力粘度 (Pa·s)
    WATER_DYNAMIC_VISCOSITY = 1.002e-3
    
    # 水的运动粘度 (m²/s)
    WATER_KINEMATIC_VISCOSITY = 1.004e-6
    
    # 大气压力 (Pa)
    ATMOSPHERIC_PRESSURE = 101325.0
    
    # 水的比热容 (J/(kg·K))
    WATER_SPECIFIC_HEAT = 4186.0
    
    # 水的汽化潜热 (J/kg)
    WATER_LATENT_HEAT_VAPORIZATION = 2.26e6


# =============================================================================
# 数学常量 (Mathematical Constants)
# =============================================================================

class MathematicalConstants:
    """数学常量类 - 包含所有数学常数"""
    
    # 圆周率
    PI = math.pi
    
    # 自然对数的底
    E = math.e
    
    # 黄金比例
    GOLDEN_RATIO = (1 + math.sqrt(5)) / 2
    
    # 常用分数
    ONE_HALF = 0.5
    ONE_THIRD = 1.0 / 3.0
    TWO_THIRDS = 2.0 / 3.0
    ONE_QUARTER = 0.25
    THREE_QUARTERS = 0.75


# =============================================================================
# 单位转换常量 (Unit Conversion Constants)
# =============================================================================

class UnitConversionConstants:
    """单位转换常量类 - 包含所有单位转换系数"""
    
    # 功率转换
    W_TO_KW = 1000.0
    KW_TO_W = 1.0 / 1000.0
    MW_TO_W = 1e6
    W_TO_MW = 1e-6
    
    # 长度转换
    M_TO_MM = 1000.0
    MM_TO_M = 0.001
    M_TO_CM = 100.0
    CM_TO_M = 0.01
    KM_TO_M = 1000.0
    M_TO_KM = 0.001
    
    # 面积转换
    M2_TO_CM2 = 10000.0
    CM2_TO_M2 = 0.0001
    M2_TO_MM2 = 1000000.0
    MM2_TO_M2 = 1e-6
    
    # 体积转换
    M3_TO_L = 1000.0
    L_TO_M3 = 0.001
    M3_TO_ML = 1e6
    ML_TO_M3 = 1e-6
    
    # 时间转换
    S_TO_MS = 1000.0
    MS_TO_S = 0.001
    S_TO_MIN = 1.0 / 60.0
    MIN_TO_S = 60.0
    S_TO_H = 1.0 / 3600.0
    H_TO_S = 3600.0
    
    # 百分比转换
    PERCENT_TO_DECIMAL = 0.01
    DECIMAL_TO_PERCENT = 100.0
    
    # 角度转换
    DEG_TO_RAD = math.pi / 180.0
    RAD_TO_DEG = 180.0 / math.pi


# =============================================================================
# 水力工程常量 (Hydraulic Engineering Constants)
# =============================================================================

class HydraulicConstants:
    """水力工程常量类 - 包含水力工程相关的常数"""
    
    # 堰流公式指数
    WEIR_FLOW_EXPONENT = 0.5
    
    # 孔口流量公式指数
    ORIFICE_FLOW_EXPONENT = 0.5
    
    # Manning公式指数
    MANNING_EXPONENT_2_3 = 2.0 / 3.0
    MANNING_EXPONENT_1_2 = 0.5
    
    # Darcy-Weisbach公式指数
    DARCY_WEISBACH_EXPONENT = 2.0
    
    # 几何系数
    DIAMETER_FACTOR = 2.0  # 直径到半径的转换
    CIRCULAR_AREA_FACTOR = math.pi / 4.0  # 圆形面积系数
    HYDRAULIC_RADIUS_FACTOR = 4.0  # 满管圆形管道水力半径系数
    SQRT_FACTOR = 2.0  # 孔口流动公式中的平方根因子
    POWER_EXPONENT = 0.5  # 功率指数
    
    # 流量系数范围
    MIN_DISCHARGE_COEFFICIENT = 0.1
    MAX_DISCHARGE_COEFFICIENT = 1.0
    DEFAULT_DISCHARGE_COEFFICIENT = 0.6
    
    # 开度范围
    MIN_OPENING = 0.0
    MAX_OPENING = 1.0
    FULL_OPENING_PERCENT = 100.0


# =============================================================================
# 默认配置参数 (Default Configuration Parameters)
# =============================================================================

class DefaultConfigParameters:
    """默认配置参数类 - 包含所有可配置参数的默认值"""
    
    # 仿真参数
    DEFAULT_TIME_STEP = 0.1  # 秒
    DEFAULT_PRINT_INTERVAL = 10  # 步数
    DEFAULT_SIMULATION_DURATION = 3600.0  # 秒
    DEFAULT_CONVERGENCE_TOLERANCE = 1e-6
    
    # 物理对象默认参数
    DEFAULT_DIAMETER = 0.5  # 米
    DEFAULT_SURFACE_AREA = 10000.0  # 平方米
    DEFAULT_WATER_LEVEL = 0.0  # 米
    DEFAULT_INFLOW = 0.0  # 立方米/秒
    DEFAULT_OUTFLOW = 0.0  # 立方米/秒
    
    # 渠道模型默认参数
    DEFAULT_OUTLET_COEFFICIENT = 5.0
    DEFAULT_GAIN = 0.001
    DEFAULT_DELAY = 300.0  # 秒
    DEFAULT_ZERO_TIME_CONSTANT = 50.0  # 秒
    DEFAULT_STORAGE_CONSTANT = 1200.0  # 秒
    DEFAULT_LEVEL_STORAGE_RATIO = 0.005
    DEFAULT_INITIAL_DEPTH = 5.0  # 米
    DEFAULT_INITIAL_FLOW = 10.0  # 立方米/秒
    
    # 泵站默认参数
    DEFAULT_PUMP_EFFICIENCY = 0.8
    DEFAULT_PUMP_POWER = 50.0  # kW
    DEFAULT_MIN_FLOW_RATIO = 0.1
    DEFAULT_OPTIMAL_FLOW_RATIO = 0.7
    DEFAULT_MIN_EFFICIENCY = 0.3
    DEFAULT_MAX_EFFICIENCY_LOSS = 0.3
    
    # 传感器默认参数
    DEFAULT_NOISE_LEVEL = 0.01
    DEFAULT_SENSOR_ACCURACY = 0.001
    
    # 控制默认参数
    DEFAULT_PID_KP = 1.0
    DEFAULT_PID_KI = 0.1
    DEFAULT_PID_KD = 0.01
    DEFAULT_CONTROL_DEADBAND = 0.01
    
    # 扰动默认参数
    DEFAULT_DISTURBANCE_INTENSITY = 0.1
    DEFAULT_DISTURBANCE_DURATION = 60.0  # 秒


# =============================================================================
# 系统限制常量 (System Limit Constants)
# =============================================================================

class SystemLimits:
    """系统限制常量类 - 包含系统运行的各种限制"""
    
    # 数值精度限制
    MIN_POSITIVE_VALUE = 1e-12
    MAX_ITERATIONS = 1000
    CONVERGENCE_TOLERANCE = 1e-6
    
    # 物理限制
    MIN_WATER_LEVEL = 0.0
    MAX_WATER_LEVEL = 1000.0  # 米
    MIN_FLOW_RATE = 0.0
    MAX_FLOW_RATE = 10000.0  # 立方米/秒
    
    # 时间限制
    MIN_TIME_STEP = 0.001  # 秒
    MAX_TIME_STEP = 3600.0  # 秒
    MAX_SIMULATION_TIME = 86400.0 * 365  # 一年
    
    # 内存限制
    MAX_HISTORY_SIZE = 10000
    MAX_CACHE_SIZE = 1000


# =============================================================================
# 状态枚举常量 (Status Enumeration Constants)
# =============================================================================

class StatusConstants:
    """状态枚举常量类 - 包含各种状态定义"""
    
    # 设备状态
    STATUS_OFF = 0
    STATUS_ON = 1
    STATUS_FAULT = -1
    STATUS_MAINTENANCE = -2
    
    # 控制模式
    CONTROL_MODE_AUTOMATIC = "automatic"
    CONTROL_MODE_MANUAL = "manual"
    CONTROL_MODE_MAINTENANCE = "maintenance"
    
    # 阀门状态
    VALVE_STATUS_NORMAL = "normal"
    VALVE_STATUS_FAULT = "fault"
    VALVE_STATUS_MAINTENANCE = "maintenance"
    
    # 泵状态
    PUMP_STATUS_NORMAL = "normal"
    PUMP_STATUS_STARTING = "starting"
    PUMP_STATUS_STOPPING = "stopping"
    PUMP_STATUS_FAULT = "fault"


# =============================================================================
# 配置验证常量 (Configuration Validation Constants)
# =============================================================================

class ValidationConstants:
    """配置验证常量类 - 包含参数验证的边界值"""
    
    # 参数范围验证
    VALID_DIAMETER_RANGE = (0.001, 100.0)  # 米
    VALID_SURFACE_AREA_RANGE = (1.0, 1e8)  # 平方米
    VALID_WATER_LEVEL_RANGE = (0.0, 1000.0)  # 米
    VALID_FLOW_RATE_RANGE = (0.0, 10000.0)  # 立方米/秒
    VALID_EFFICIENCY_RANGE = (0.0, 1.0)
    VALID_OPENING_RANGE = (0.0, 1.0)
    VALID_TIME_STEP_RANGE = (0.001, 3600.0)  # 秒
    
    # 必需参数列表
    REQUIRED_PUMP_PARAMS = ['max_flow_rate', 'max_head']
    REQUIRED_VALVE_PARAMS = ['discharge_coefficient', 'diameter']
    REQUIRED_CANAL_PARAMS = ['model_type']
    REQUIRED_ST_VENANT_PARAMS = ['length', 'num_points', 'bottom_width', 
                                 'side_slope_z', 'manning_n', 'slope']


# =============================================================================
# 便利函数 (Convenience Functions)
# =============================================================================

def get_all_constants() -> Dict[str, Any]:
    """获取所有常量字典"""
    return {
        'physical': PhysicalConstants.__dict__,
        'mathematical': MathematicalConstants.__dict__,
        'unit_conversion': UnitConversionConstants.__dict__,
        'hydraulic': HydraulicConstants.__dict__,
        'default_config': DefaultConfigParameters.__dict__,
        'system_limits': SystemLimits.__dict__,
        'status': StatusConstants.__dict__,
        'validation': ValidationConstants.__dict__,
    }


def validate_parameter_range(value: float, param_name: str, 
                           min_val: float, max_val: float) -> bool:
    """验证参数是否在有效范围内"""
    if not (min_val <= value <= max_val):
        raise ValueError(f"参数 '{param_name}' 的值 {value} 超出有效范围 [{min_val}, {max_val}]")
    return True


def get_parameter_with_default(config: Dict[str, Any], param_name: str, 
                              default_value: Any) -> Any:
    """从配置中获取参数值，如果不存在则返回默认值"""
    return config.get(param_name, default_value)


def validate_required_parameters(config: Dict[str, Any], 
                                required_params: list) -> None:
    """验证必需参数是否存在"""
    missing_params = [p for p in required_params if p not in config]
    if missing_params:
        raise ValueError(f"缺少必需参数: {missing_params}")


# =============================================================================
# 模块初始化
# =============================================================================

# 导出主要常量类
__all__ = [
    'PhysicalConstants',
    'MathematicalConstants', 
    'UnitConversionConstants',
    'HydraulicConstants',
    'DefaultConfigParameters',
    'SystemLimits',
    'StatusConstants',
    'ValidationConstants',
    'get_all_constants',
    'validate_parameter_range',
    'get_parameter_with_default',
    'validate_required_parameters'
]
