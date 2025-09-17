# -*- coding: utf-8 -*-

"""
This package contains the physical models of the water system components.

新增功能:
- 基于 Gymnasium 的统一 Action 接口
- 标准化的强化学习环境
- 向后兼容的适配器
"""

from .reservoir import Reservoir
from .pipe import Pipe
from .gate import Gate
from .pump import Pump
from .valve import Valve
# from .river_channel import RiverChannel  # 文件不存在，暂时注释
from .hydropower_station import HydropowerStation
# from .lake import Lake  # 文件不存在，暂时注释
from .water_turbine import WaterTurbine
from .rainfall_runoff import RainfallRunoff
# from .integral_delay_canal import IntegralDelayCanal
# from .integral_delay_zero_canal import IntegralDelayZeroCanal
from .unified_canal import UnifiedCanal
from .junction import Junction

# 新的 Gymnasium 接口
from .base_gym import (
    BaseAction, ActionType, PhysicalObjectEnv,
    ControlSignalAction, FlowControlAction, LevelControlAction,
    StatusControlAction, MixedControlAction,
    create_gym_env, dict_to_base_action
)
from .gym_adapter import (
    GymnasiumCompatiblePhysicalObject, TypedPhysicalObjectEnv,
    make_gym_compatible, create_typed_env, auto_create_env,
    detect_object_type
)

# 兼容性别名 - 支持从hydro_nodes迁移的代码
ValveNode = Valve
GateNode = Gate
PumpNode = Pump
TurbineNode = WaterTurbine
JunctionNode = Junction

__all__ = [
    # 原有物理对象
    'Reservoir',
    'Pipe',
    'Gate',
    'Pump',
    'Valve',
    'HydropowerStation',
    # 'Lake',  # 文件不存在
    'WaterTurbine',
    'RainfallRunoff',
    # 'RiverChannel',  # 文件不存在
    'UnifiedCanal',
    'Junction',
    # 兼容性别名
    'ValveNode',
    'GateNode', 
    'PumpNode',
    'TurbineNode',
    'JunctionNode',
    
    # 新的 Gymnasium 接口
    'BaseAction',
    'ActionType', 
    'PhysicalObjectEnv',
    'ControlSignalAction',
    'FlowControlAction', 
    'LevelControlAction',
    'StatusControlAction',
    'MixedControlAction',
    'create_gym_env',
    'dict_to_base_action',
    
    # Gymnasium 适配器
    'GymnasiumCompatiblePhysicalObject',
    'TypedPhysicalObjectEnv',
    'make_gym_compatible',
    'create_typed_env',
    'auto_create_env',
    'detect_object_type'
]
