#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参数管理器 - 统一管理CHS-SDK中的所有配置参数

这个模块提供了一个统一的参数管理接口，用于：
1. 从配置文件加载参数
2. 提供参数默认值
3. 验证参数有效性
4. 支持参数热更新
5. 避免硬编码魔数

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
import logging

from .constants import (
    PhysicalConstants, MathematicalConstants, UnitConversionConstants,
    HydraulicConstants, DefaultConfigParameters, SystemLimits,
    StatusConstants, ValidationConstants,
    validate_parameter_range, get_parameter_with_default, validate_required_parameters
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParameterCategory:
    """参数分类"""
    name: str
    description: str
    parameters: Dict[str, Any]
    validation_rules: Optional[Dict[str, Tuple[float, float]]] = None


class ParameterManager:
    """
    参数管理器 - 统一管理所有配置参数
    
    主要功能：
    1. 从配置文件加载参数
    2. 提供参数默认值
    3. 验证参数有效性
    4. 支持参数热更新
    5. 避免硬编码魔数
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化参数管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config_file = config_file
        self.config = {}
        self.parameter_categories = {}
        
        # 初始化参数分类
        self._initialize_parameter_categories()
        
        # 加载配置
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        else:
            self._load_default_config()
    
    def _initialize_parameter_categories(self):
        """初始化参数分类"""
        self.parameter_categories = {
            'physical': ParameterCategory(
                name='物理常量',
                description='不可变的物理常数',
                parameters=PhysicalConstants.__dict__,
                validation_rules=None  # 物理常量不需要验证
            ),
            'mathematical': ParameterCategory(
                name='数学常量',
                description='数学常数',
                parameters=MathematicalConstants.__dict__,
                validation_rules=None
            ),
            'unit_conversion': ParameterCategory(
                name='单位转换',
                description='单位转换系数',
                parameters=UnitConversionConstants.__dict__,
                validation_rules=None
            ),
            'hydraulic': ParameterCategory(
                name='水力工程',
                description='水力工程相关常量',
                parameters=HydraulicConstants.__dict__,
                validation_rules=None
            ),
            'simulation': ParameterCategory(
                name='仿真参数',
                description='仿真相关参数',
                parameters={
                    'time_step': DefaultConfigParameters.DEFAULT_TIME_STEP,
                    'print_interval': DefaultConfigParameters.DEFAULT_PRINT_INTERVAL,
                    'simulation_duration': DefaultConfigParameters.DEFAULT_SIMULATION_DURATION,
                    'convergence_tolerance': DefaultConfigParameters.DEFAULT_CONVERGENCE_TOLERANCE,
                },
                validation_rules={
                    'time_step': ValidationConstants.VALID_TIME_STEP_RANGE,
                    'simulation_duration': (1.0, SystemLimits.MAX_SIMULATION_TIME),
                }
            ),
            'physical_objects': ParameterCategory(
                name='物理对象',
                description='物理对象默认参数',
                parameters={
                    'default_diameter': DefaultConfigParameters.DEFAULT_DIAMETER,
                    'default_surface_area': DefaultConfigParameters.DEFAULT_SURFACE_AREA,
                    'default_water_level': DefaultConfigParameters.DEFAULT_WATER_LEVEL,
                    'default_inflow': DefaultConfigParameters.DEFAULT_INFLOW,
                    'default_outflow': DefaultConfigParameters.DEFAULT_OUTFLOW,
                },
                validation_rules={
                    'default_diameter': ValidationConstants.VALID_DIAMETER_RANGE,
                    'default_surface_area': ValidationConstants.VALID_SURFACE_AREA_RANGE,
                    'default_water_level': ValidationConstants.VALID_WATER_LEVEL_RANGE,
                }
            ),
            'pump_parameters': ParameterCategory(
                name='泵参数',
                description='泵相关参数',
                parameters={
                    'default_efficiency': DefaultConfigParameters.DEFAULT_PUMP_EFFICIENCY,
                    'default_power': DefaultConfigParameters.DEFAULT_PUMP_POWER,
                    'min_flow_ratio': DefaultConfigParameters.DEFAULT_MIN_FLOW_RATIO,
                    'optimal_flow_ratio': DefaultConfigParameters.DEFAULT_OPTIMAL_FLOW_RATIO,
                    'min_efficiency': DefaultConfigParameters.DEFAULT_MIN_EFFICIENCY,
                    'max_efficiency_loss': DefaultConfigParameters.DEFAULT_MAX_EFFICIENCY_LOSS,
                },
                validation_rules={
                    'default_efficiency': ValidationConstants.VALID_EFFICIENCY_RANGE,
                    'min_flow_ratio': (0.0, 1.0),
                    'optimal_flow_ratio': (0.0, 1.0),
                    'min_efficiency': ValidationConstants.VALID_EFFICIENCY_RANGE,
                }
            ),
            'valve_parameters': ParameterCategory(
                name='阀门参数',
                description='阀门相关参数',
                parameters={
                    'default_discharge_coefficient': HydraulicConstants.DEFAULT_DISCHARGE_COEFFICIENT,
                    'min_opening': HydraulicConstants.MIN_OPENING,
                    'max_opening': HydraulicConstants.MAX_OPENING,
                    'full_opening_percent': HydraulicConstants.FULL_OPENING_PERCENT,
                },
                validation_rules={
                    'default_discharge_coefficient': (HydraulicConstants.MIN_DISCHARGE_COEFFICIENT, 
                                                     HydraulicConstants.MAX_DISCHARGE_COEFFICIENT),
                    'min_opening': (0.0, 1.0),
                    'max_opening': (0.0, 1.0),
                }
            ),
            'canal_parameters': ParameterCategory(
                name='渠道参数',
                description='渠道模型参数',
                parameters={
                    'default_outlet_coefficient': DefaultConfigParameters.DEFAULT_OUTLET_COEFFICIENT,
                    'default_gain': DefaultConfigParameters.DEFAULT_GAIN,
                    'default_delay': DefaultConfigParameters.DEFAULT_DELAY,
                    'default_zero_time_constant': DefaultConfigParameters.DEFAULT_ZERO_TIME_CONSTANT,
                    'default_storage_constant': DefaultConfigParameters.DEFAULT_STORAGE_CONSTANT,
                    'default_level_storage_ratio': DefaultConfigParameters.DEFAULT_LEVEL_STORAGE_RATIO,
                    'default_initial_depth': DefaultConfigParameters.DEFAULT_INITIAL_DEPTH,
                    'default_initial_flow': DefaultConfigParameters.DEFAULT_INITIAL_FLOW,
                },
                validation_rules={
                    'default_delay': (0.0, 3600.0),
                    'default_storage_constant': (1.0, 10000.0),
                    'default_level_storage_ratio': (0.001, 1.0),
                }
            ),
            'sensor_parameters': ParameterCategory(
                name='传感器参数',
                description='传感器相关参数',
                parameters={
                    'default_noise_level': DefaultConfigParameters.DEFAULT_NOISE_LEVEL,
                    'default_accuracy': DefaultConfigParameters.DEFAULT_SENSOR_ACCURACY,
                },
                validation_rules={
                    'default_noise_level': (0.0, 1.0),
                    'default_accuracy': (0.0, 1.0),
                }
            ),
            'control_parameters': ParameterCategory(
                name='控制参数',
                description='控制算法参数',
                parameters={
                    'default_pid_kp': DefaultConfigParameters.DEFAULT_PID_KP,
                    'default_pid_ki': DefaultConfigParameters.DEFAULT_PID_KI,
                    'default_pid_kd': DefaultConfigParameters.DEFAULT_PID_KD,
                    'default_control_deadband': DefaultConfigParameters.DEFAULT_CONTROL_DEADBAND,
                },
                validation_rules={
                    'default_pid_kp': (0.0, 100.0),
                    'default_pid_ki': (0.0, 10.0),
                    'default_pid_kd': (0.0, 1.0),
                }
            ),
            'disturbance_parameters': ParameterCategory(
                name='扰动参数',
                description='扰动相关参数',
                parameters={
                    'default_intensity': DefaultConfigParameters.DEFAULT_DISTURBANCE_INTENSITY,
                    'default_duration': DefaultConfigParameters.DEFAULT_DISTURBANCE_DURATION,
                },
                validation_rules={
                    'default_intensity': (0.0, 1.0),
                    'default_duration': (1.0, 3600.0),
                }
            )
        }
    
    def _load_default_config(self):
        """加载默认配置"""
        self.config = {}
        for category_name, category in self.parameter_categories.items():
            self.config[category_name] = category.parameters.copy()
        
        logger.info("已加载默认配置")
    
    def load_config(self, config_file: str):
        """
        从配置文件加载参数
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    config_data = yaml.safe_load(f)
                elif config_file.endswith('.json'):
                    config_data = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_file}")
            
            # 合并配置
            self._merge_config(config_data)
            logger.info(f"已从 {config_file} 加载配置")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._load_default_config()
    
    def _merge_config(self, config_data: Dict[str, Any]):
        """合并配置数据"""
        for category_name, category_data in config_data.items():
            if category_name in self.parameter_categories:
                # 验证参数
                if self.parameter_categories[category_name].validation_rules:
                    for param_name, value in category_data.items():
                        if param_name in self.parameter_categories[category_name].validation_rules:
                            min_val, max_val = self.parameter_categories[category_name].validation_rules[param_name]
                            validate_parameter_range(value, param_name, min_val, max_val)
                
                # 合并参数
                self.config[category_name] = self.config.get(category_name, {})
                self.config[category_name].update(category_data)
            else:
                logger.warning(f"未知的配置分类: {category_name}")
    
    def get_parameter(self, category: str, parameter: str, 
                     default_value: Optional[Any] = None) -> Any:
        """
        获取参数值
        
        Args:
            category: 参数分类
            parameter: 参数名
            default_value: 默认值，如果为None则使用系统默认值
            
        Returns:
            参数值
        """
        if category not in self.config:
            logger.warning(f"未知的参数分类: {category}")
            return default_value
        
        if parameter not in self.config[category]:
            if default_value is not None:
                return default_value
            elif category in self.parameter_categories:
                return self.parameter_categories[category].parameters.get(parameter, default_value)
            else:
                return default_value
        
        return self.config[category][parameter]
    
    def set_parameter(self, category: str, parameter: str, value: Any) -> bool:
        """
        设置参数值
        
        Args:
            category: 参数分类
            parameter: 参数名
            value: 参数值
            
        Returns:
            是否设置成功
        """
        try:
            # 验证参数
            if (category in self.parameter_categories and 
                self.parameter_categories[category].validation_rules and
                parameter in self.parameter_categories[category].validation_rules):
                min_val, max_val = self.parameter_categories[category].validation_rules[parameter]
                validate_parameter_range(value, parameter, min_val, max_val)
            
            # 设置参数
            if category not in self.config:
                self.config[category] = {}
            self.config[category][parameter] = value
            
            logger.info(f"已设置参数 {category}.{parameter} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return False
    
    def get_category_parameters(self, category: str) -> Dict[str, Any]:
        """
        获取分类的所有参数
        
        Args:
            category: 参数分类
            
        Returns:
            参数字典
        """
        return self.config.get(category, {})
    
    def validate_configuration(self, required_categories: Optional[List[str]] = None) -> bool:
        """
        验证配置完整性
        
        Args:
            required_categories: 必需的分类列表
            
        Returns:
            配置是否有效
        """
        try:
            if required_categories:
                for category in required_categories:
                    if category not in self.config:
                        logger.error(f"缺少必需的配置分类: {category}")
                        return False
            
            # 验证每个分类的参数
            for category_name, category in self.parameter_categories.items():
                if category_name in self.config and category.validation_rules:
                    for param_name, (min_val, max_val) in category.validation_rules.items():
                        if param_name in self.config[category_name]:
                            validate_parameter_range(
                                self.config[category_name][param_name], 
                                param_name, min_val, max_val
                            )
            
            # 特别验证时间步长
            self._validate_time_step()
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def _validate_time_step(self):
        """验证时间步长参数"""
        if 'simulation' in self.config:
            time_step = self.config['simulation'].get('time_step')
            if time_step is not None:
                min_step = SystemLimits.MIN_TIME_STEP
                max_step = SystemLimits.MAX_TIME_STEP
                
                if not isinstance(time_step, (int, float)):
                    raise ValueError(f"时间步长必须是数值类型，当前类型: {type(time_step)}")
                
                if time_step <= 0:
                    raise ValueError(f"时间步长必须大于0，当前值: {time_step}")
                
                if time_step < min_step:
                    logger.warning(f"时间步长 {time_step} 小于推荐最小值 {min_step}")
                
                if time_step > max_step:
                    raise ValueError(f"时间步长 {time_step} 超过最大值 {max_step}")
                
                # 检查时间步长精度
                if time_step < 0.001:
                    logger.warning(f"时间步长 {time_step} 过小，可能影响计算精度")
                
                logger.info(f"时间步长验证通过: {time_step} 秒")
    
    def save_config(self, output_file: str):
        """
        保存配置到文件
        
        Args:
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.endswith('.yaml') or output_file.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                elif output_file.endswith('.json'):
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的输出文件格式: {output_file}")
            
            logger.info(f"配置已保存到 {output_file}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_physical_constant(self, constant_name: str) -> Any:
        """获取物理常量"""
        return PhysicalConstants.__dict__.get(constant_name)
    
    def get_mathematical_constant(self, constant_name: str) -> Any:
        """获取数学常量"""
        return MathematicalConstants.__dict__.get(constant_name)
    
    def get_unit_conversion(self, conversion_name: str) -> Any:
        """获取单位转换系数"""
        return UnitConversionConstants.__dict__.get(conversion_name)
    
    def get_hydraulic_constant(self, constant_name: str) -> Any:
        """获取水力工程常量"""
        return HydraulicConstants.__dict__.get(constant_name)
    
    def get_default_parameter(self, category: str, parameter: str) -> Any:
        """获取默认参数值"""
        if category in self.parameter_categories:
            return self.parameter_categories[category].parameters.get(parameter)
        return None
    
    def list_categories(self) -> List[str]:
        """列出所有参数分类"""
        return list(self.parameter_categories.keys())
    
    def list_parameters(self, category: str) -> List[str]:
        """列出指定分类的所有参数"""
        if category in self.parameter_categories:
            return list(self.parameter_categories[category].parameters.keys())
        return []


# =============================================================================
# 全局参数管理器实例
# =============================================================================

# 创建全局参数管理器实例
_global_parameter_manager = None

def get_parameter_manager(config_file: Optional[str] = None) -> ParameterManager:
    """
    获取全局参数管理器实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        参数管理器实例
    """
    global _global_parameter_manager
    
    if _global_parameter_manager is None:
        _global_parameter_manager = ParameterManager(config_file)
    
    return _global_parameter_manager


def initialize_parameter_manager(config_file: Optional[str] = None) -> ParameterManager:
    """
    初始化全局参数管理器
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        参数管理器实例
    """
    global _global_parameter_manager
    _global_parameter_manager = ParameterManager(config_file)
    return _global_parameter_manager


# =============================================================================
# 便利函数
# =============================================================================

def get_param(category: str, parameter: str, default_value: Optional[Any] = None) -> Any:
    """获取参数的便利函数"""
    return get_parameter_manager().get_parameter(category, parameter, default_value)

def set_param(category: str, parameter: str, value: Any) -> bool:
    """设置参数的便利函数"""
    return get_parameter_manager().set_parameter(category, parameter, value)

def get_physical_constant(constant_name: str) -> Any:
    """获取物理常量的便利函数"""
    return get_parameter_manager().get_physical_constant(constant_name)

def get_default_parameter(category: str, parameter: str) -> Any:
    """获取默认参数的便利函数"""
    return get_parameter_manager().get_default_parameter(category, parameter)


# =============================================================================
# 模块初始化
# =============================================================================

# 导出主要类和函数
__all__ = [
    'ParameterManager',
    'ParameterCategory',
    'get_parameter_manager',
    'initialize_parameter_manager',
    'get_param',
    'set_param',
    'get_physical_constant',
    'get_default_parameter'
]
