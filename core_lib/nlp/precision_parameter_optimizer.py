#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高精度参数优化器
实现智能单位转换、数值范围验证、参数依赖关系检查
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)

class ParameterType(Enum):
    """参数类型枚举"""
    CAPACITY = "capacity"  # 容量
    FLOW_RATE = "flow_rate"  # 流量
    WATER_LEVEL = "water_level"  # 水位
    POWER = "power"  # 功率
    EFFICIENCY = "efficiency"  # 效率
    DIMENSION = "dimension"  # 尺寸
    TIME = "time"  # 时间
    PRESSURE = "pressure"  # 压力
    VELOCITY = "velocity"  # 速度
    TEMPERATURE = "temperature"  # 温度
    ROUGHNESS = "roughness"  # 粗糙度
    SLOPE = "slope"  # 坡度
    OPENING = "opening"  # 开度
    HEAD = "head"  # 扬程

@dataclass
class UnitConversion:
    """单位转换规则"""
    from_unit: str
    to_unit: str
    factor: float
    offset: float = 0.0

@dataclass
class ParameterConstraint:
    """参数约束"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    valid_units: List[str] = None
    dependencies: List[str] = None  # 依赖的其他参数
    validation_rules: List[str] = None  # 验证规则

class PrecisionParameterOptimizer:
    """高精度参数优化器"""
    
    def __init__(self):
        self.unit_conversions = self._initialize_unit_conversions()
        self.parameter_constraints = self._initialize_parameter_constraints()
        self.parameter_patterns = self._initialize_parameter_patterns()
        self.synonym_mappings = self._initialize_synonym_mappings()
        
    def _initialize_unit_conversions(self) -> Dict[str, List[UnitConversion]]:
        """初始化单位转换规则"""
        conversions = {
            # 容量单位转换 (统一转换为立方米)
            "capacity": [
                UnitConversion("立方米", "m³", 1.0),
                UnitConversion("立方米", "m3", 1.0),
                UnitConversion("万立方米", "m³", 10000.0),
                UnitConversion("万m³", "m³", 10000.0),
                UnitConversion("万m3", "m³", 10000.0),
                UnitConversion("亿立方米", "m³", 100000000.0),
                UnitConversion("亿m³", "m³", 100000000.0),
                UnitConversion("升", "m³", 0.001),
                UnitConversion("L", "m³", 0.001),
                UnitConversion("毫升", "m³", 0.000001),
                UnitConversion("mL", "m³", 0.000001),
            ],
            # 流量单位转换 (统一转换为立方米每秒)
            "flow_rate": [
                UnitConversion("立方米每秒", "m³/s", 1.0),
                UnitConversion("m³/s", "m³/s", 1.0),
                UnitConversion("m3/s", "m³/s", 1.0),
                UnitConversion("立方米/秒", "m³/s", 1.0),
                UnitConversion("立方米/s", "m³/s", 1.0),
                UnitConversion("升每秒", "m³/s", 0.001),
                UnitConversion("L/s", "m³/s", 0.001),
                UnitConversion("升/秒", "m³/s", 0.001),
                UnitConversion("升/s", "m³/s", 0.001),
                UnitConversion("立方米每小时", "m³/s", 1/3600),
                UnitConversion("m³/h", "m³/s", 1/3600),
                UnitConversion("m3/h", "m³/s", 1/3600),
            ],
            # 水位/高度单位转换 (统一转换为米)
            "water_level": [
                UnitConversion("米", "m", 1.0),
                UnitConversion("m", "m", 1.0),
                UnitConversion("厘米", "m", 0.01),
                UnitConversion("cm", "m", 0.01),
                UnitConversion("毫米", "m", 0.001),
                UnitConversion("mm", "m", 0.001),
                UnitConversion("千米", "m", 1000.0),
                UnitConversion("km", "m", 1000.0),
                UnitConversion("公里", "m", 1000.0),
            ],
            # 功率单位转换 (统一转换为瓦特)
            "power": [
                UnitConversion("瓦特", "W", 1.0),
                UnitConversion("W", "W", 1.0),
                UnitConversion("千瓦", "W", 1000.0),
                UnitConversion("kW", "W", 1000.0),
                UnitConversion("兆瓦", "W", 1000000.0),
                UnitConversion("MW", "W", 1000000.0),
                UnitConversion("马力", "W", 745.7),
                UnitConversion("HP", "W", 745.7),
                UnitConversion("hp", "W", 745.7),
            ],
            # 时间单位转换 (统一转换为秒)
            "time": [
                UnitConversion("秒", "s", 1.0),
                UnitConversion("s", "s", 1.0),
                UnitConversion("分钟", "s", 60.0),
                UnitConversion("分", "s", 60.0),
                UnitConversion("min", "s", 60.0),
                UnitConversion("小时", "s", 3600.0),
                UnitConversion("时", "s", 3600.0),
                UnitConversion("h", "s", 3600.0),
                UnitConversion("天", "s", 86400.0),
                UnitConversion("日", "s", 86400.0),
                UnitConversion("d", "s", 86400.0),
                UnitConversion("年", "s", 31536000.0),
                UnitConversion("y", "s", 31536000.0),
            ],
            # 压力单位转换 (统一转换为帕斯卡)
            "pressure": [
                UnitConversion("帕斯卡", "Pa", 1.0),
                UnitConversion("Pa", "Pa", 1.0),
                UnitConversion("千帕", "Pa", 1000.0),
                UnitConversion("kPa", "Pa", 1000.0),
                UnitConversion("兆帕", "Pa", 1000000.0),
                UnitConversion("MPa", "Pa", 1000000.0),
                UnitConversion("巴", "Pa", 100000.0),
                UnitConversion("bar", "Pa", 100000.0),
                UnitConversion("大气压", "Pa", 101325.0),
                UnitConversion("atm", "Pa", 101325.0),
            ]
        }
        return conversions
    
    def _initialize_parameter_constraints(self) -> Dict[str, ParameterConstraint]:
        """初始化参数约束"""
        constraints = {
            # 水库参数约束
            "reservoir_capacity": ParameterConstraint(
                min_value=0.0,
                max_value=1e12,  # 1万亿立方米
                valid_units=["m³", "万m³", "亿m³"],
                validation_rules=["positive_value"]
            ),
            "reservoir_initial_level": ParameterConstraint(
                min_value=0.0,
                max_value=1000.0,  # 1000米
                valid_units=["m"],
                dependencies=["reservoir_capacity"],
                validation_rules=["positive_value", "level_capacity_consistency"]
            ),
            "reservoir_max_level": ParameterConstraint(
                min_value=0.0,
                max_value=1000.0,
                valid_units=["m"],
                dependencies=["reservoir_initial_level"],
                validation_rules=["positive_value", "max_greater_than_initial"]
            ),
            # 流量参数约束
            "flow_rate": ParameterConstraint(
                min_value=0.0,
                max_value=100000.0,  # 10万立方米每秒
                valid_units=["m³/s", "L/s", "m³/h"],
                validation_rules=["positive_value"]
            ),
            "inflow_rate": ParameterConstraint(
                min_value=0.0,
                max_value=100000.0,
                valid_units=["m³/s", "L/s", "m³/h"],
                validation_rules=["positive_value"]
            ),
            "outflow_rate": ParameterConstraint(
                min_value=0.0,
                max_value=100000.0,
                valid_units=["m³/s", "L/s", "m³/h"],
                validation_rules=["positive_value"]
            ),
            # 功率参数约束
            "power": ParameterConstraint(
                min_value=0.0,
                max_value=1e10,  # 100亿瓦特
                valid_units=["W", "kW", "MW"],
                validation_rules=["positive_value"]
            ),
            "rated_power": ParameterConstraint(
                min_value=0.0,
                max_value=1e10,
                valid_units=["W", "kW", "MW"],
                validation_rules=["positive_value"]
            ),
            # 效率参数约束
            "efficiency": ParameterConstraint(
                min_value=0.0,
                max_value=1.0,
                valid_units=["%", "无量纲"],
                validation_rules=["efficiency_range"]
            ),
            # 开度参数约束
            "opening": ParameterConstraint(
                min_value=0.0,
                max_value=1.0,
                valid_units=["%", "无量纲"],
                validation_rules=["opening_range"]
            ),
            # 时间参数约束
            "duration": ParameterConstraint(
                min_value=0.0,
                max_value=3.15e8,  # 10年
                valid_units=["s", "min", "h", "d", "y"],
                validation_rules=["positive_value"]
            ),
            "time_step": ParameterConstraint(
                min_value=0.001,  # 1毫秒
                max_value=86400.0,  # 1天
                valid_units=["s", "min", "h"],
                validation_rules=["positive_value", "reasonable_time_step"]
            )
        }
        return constraints
    
    def _initialize_parameter_patterns(self) -> Dict[str, List[str]]:
        """初始化参数提取模式"""
        patterns = {
            "capacity": [
                r'容量[：:为是]?\s*([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)',
                r'库容[：:为是]?\s*([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)',
                r'总库容[：:为是]?\s*([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)',
                r'蓄水量[：:为是]?\s*([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)',
                r'储水量[：:为是]?\s*([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)',
                r'([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)[的]?容量',
                r'([\d.,]+)\s*([万亿]?[立方米m³m3升L毫升mL]+)[的]?库容',
            ],
            "flow_rate": [
                r'流量[：:为是]?\s*([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)',
                r'流速[：:为是]?\s*([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)',
                r'入流[：:为是]?\s*([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)',
                r'出流[：:为是]?\s*([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)',
                r'泄流[：:为是]?\s*([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)',
                r'([\d.,]+)\s*([立方米m³m3升L毫升mL]+[/每]?[秒分时小时天日年sminhdy]+)[的]?流量',
            ],
            "water_level": [
                r'水位[：:为是]?\s*([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)',
                r'液位[：:为是]?\s*([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)',
                r'高度[：:为是]?\s*([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)',
                r'高程[：:为是]?\s*([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)',
                r'([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)[的]?水位',
                r'([\d.,]+)\s*([千公]?[米厘毫]?[米m]|[kcm]+m)[的]?高度',
            ],
            "power": [
                r'功率[：:为是]?\s*([\d.,]+)\s*([千兆]?[瓦特W]|[km]?[Ww]|[马力HP])',
                r'额定功率[：:为是]?\s*([\d.,]+)\s*([千兆]?[瓦特W]|[km]?[Ww]|[马力HP])',
                r'装机容量[：:为是]?\s*([\d.,]+)\s*([千兆]?[瓦特W]|[km]?[Ww]|[马力HP])',
                r'([\d.,]+)\s*([千兆]?[瓦特W]|[km]?[Ww]|[马力HP])[的]?功率',
            ],
            "efficiency": [
                r'效率[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'转换效率[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'发电效率[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'([\d.,]+)\s*[%％][的]?效率',
            ],
            "opening": [
                r'开度[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'开启度[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'阀门开度[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'闸门开度[：:为是]?\s*([\d.,]+)\s*[%％]?',
                r'([\d.,]+)\s*[%％][的]?开度',
            ],
            "time": [
                r'时间[：:为是]?\s*([\d.,]+)\s*([秒分时小时天日年sminhdy]+)',
                r'持续时间[：:为是]?\s*([\d.,]+)\s*([秒分时小时天日年sminhdy]+)',
                r'运行时间[：:为是]?\s*([\d.,]+)\s*([秒分时小时天日年sminhdy]+)',
                r'时长[：:为是]?\s*([\d.,]+)\s*([秒分时小时天日年sminhdy]+)',
                r'([\d.,]+)\s*([秒分时小时天日年sminhdy]+)[的]?时间',
            ]
        }
        return patterns
    
    def _initialize_synonym_mappings(self) -> Dict[str, List[str]]:
        """初始化同义词映射"""
        mappings = {
            "capacity": ["容量", "库容", "总库容", "蓄水量", "储水量", "容积", "体积"],
            "flow_rate": ["流量", "流速", "入流", "出流", "泄流", "流出量", "流入量"],
            "water_level": ["水位", "液位", "高度", "高程", "水面高程", "蓄水位"],
            "power": ["功率", "额定功率", "装机容量", "发电功率", "输出功率"],
            "efficiency": ["效率", "转换效率", "发电效率", "传输效率", "利用效率"],
            "opening": ["开度", "开启度", "阀门开度", "闸门开度", "开启程度"],
            "time": ["时间", "持续时间", "运行时间", "时长", "周期", "间隔"]
        }
        return mappings
    
    def optimize_parameters(self, parameters: Dict[str, Any], component_type: str = None) -> Dict[str, Any]:
        """优化参数"""
        try:
            optimized_params = {}
            
            for param_name, param_value in parameters.items():
                # 1. 参数类型识别和标准化
                param_type = self._identify_parameter_type(param_name, param_value)
                
                # 2. 单位转换和数值提取
                standardized_value, unit = self._extract_and_convert_value(param_value, param_type)
                
                # 3. 数值范围验证
                validated_value = self._validate_parameter_range(param_name, standardized_value, param_type)
                
                # 4. 参数依赖关系检查
                if self._check_parameter_dependencies(param_name, validated_value, optimized_params):
                    optimized_params[param_name] = {
                        'value': validated_value,
                        'unit': unit,
                        'type': param_type,
                        'confidence': self._calculate_confidence(param_name, param_value, validated_value)
                    }
                else:
                    logger.warning(f"参数 {param_name} 依赖关系检查失败")
                    # 尝试修正
                    corrected_value = self._correct_parameter_dependency(param_name, validated_value, optimized_params)
                    if corrected_value is not None:
                        optimized_params[param_name] = {
                            'value': corrected_value,
                            'unit': unit,
                            'type': param_type,
                            'confidence': 0.7  # 修正后的置信度较低
                        }
            
            # 5. 全局一致性检查
            optimized_params = self._ensure_global_consistency(optimized_params, component_type)
            
            return optimized_params
            
        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            return parameters
    
    def _identify_parameter_type(self, param_name: str, param_value: Any) -> str:
        """识别参数类型"""
        param_name_lower = param_name.lower()
        param_str = str(param_value).lower()
        
        # 基于参数名称的类型识别
        type_keywords = {
            ParameterType.CAPACITY: ['capacity', 'volume', '容量', '库容', '体积', '蓄水量'],
            ParameterType.FLOW_RATE: ['flow', 'rate', '流量', '流速', '入流', '出流'],
            ParameterType.WATER_LEVEL: ['level', 'height', '水位', '液位', '高度', '高程'],
            ParameterType.POWER: ['power', '功率', '装机', '额定'],
            ParameterType.EFFICIENCY: ['efficiency', '效率'],
            ParameterType.OPENING: ['opening', '开度', '开启'],
            ParameterType.TIME: ['time', 'duration', '时间', '持续', '周期'],
            ParameterType.PRESSURE: ['pressure', '压力', '压强'],
            ParameterType.VELOCITY: ['velocity', 'speed', '速度', '流速'],
            ParameterType.DIMENSION: ['length', 'width', 'diameter', '长度', '宽度', '直径']
        }
        
        for param_type, keywords in type_keywords.items():
            if any(keyword in param_name_lower for keyword in keywords):
                return param_type.value
        
        # 基于参数值的单位识别
        unit_patterns = {
            ParameterType.CAPACITY: [r'[万亿]?[立方米m³m3升L]', r'[万亿]?m[³3]'],
            ParameterType.FLOW_RATE: [r'm[³3]/[sh]', r'[升L]/[sh]', r'立方米/[秒时]'],
            ParameterType.WATER_LEVEL: [r'[千公]?[米m]', r'[kcm]m'],
            ParameterType.POWER: [r'[千兆]?[瓦特W]', r'[km]?W', r'[马力HP]'],
            ParameterType.TIME: [r'[秒分时小时天日年sminhdy]']
        }
        
        for param_type, patterns in unit_patterns.items():
            if any(re.search(pattern, param_str) for pattern in patterns):
                return param_type.value
        
        return "unknown"
    
    def _extract_and_convert_value(self, param_value: Any, param_type: str) -> Tuple[float, str]:
        """提取并转换数值"""
        param_str = str(param_value)
        
        # 提取数值和单位
        number_pattern = r'([\d.,]+)\s*([^\d\s]*?)\s*$'
        match = re.search(number_pattern, param_str)
        
        if not match:
            # 尝试只提取数值
            number_only_pattern = r'([\d.,]+)'
            number_match = re.search(number_only_pattern, param_str)
            if number_match:
                value = float(number_match.group(1).replace(',', ''))
                return value, "无量纲"
            else:
                raise ValueError(f"无法从 '{param_str}' 中提取数值")
        
        value_str = match.group(1).replace(',', '')
        unit_str = match.group(2).strip()
        
        try:
            value = float(value_str)
        except ValueError:
            raise ValueError(f"无法将 '{value_str}' 转换为数值")
        
        # 单位转换
        if param_type in self.unit_conversions and unit_str:
            for conversion in self.unit_conversions[param_type]:
                if conversion.from_unit == unit_str:
                    converted_value = value * conversion.factor + conversion.offset
                    return converted_value, conversion.to_unit
        
        return value, unit_str if unit_str else "无量纲"
    
    def _validate_parameter_range(self, param_name: str, value: float, param_type: str) -> float:
        """验证参数范围"""
        # 查找对应的约束
        constraint = None
        if param_name in self.parameter_constraints:
            constraint = self.parameter_constraints[param_name]
        elif param_type in self.parameter_constraints:
            constraint = self.parameter_constraints[param_type]
        
        if constraint:
            # 检查最小值
            if constraint.min_value is not None and value < constraint.min_value:
                logger.warning(f"参数 {param_name} 值 {value} 小于最小值 {constraint.min_value}")
                return constraint.min_value
            
            # 检查最大值
            if constraint.max_value is not None and value > constraint.max_value:
                logger.warning(f"参数 {param_name} 值 {value} 大于最大值 {constraint.max_value}")
                return constraint.max_value
        
        return value
    
    def _check_parameter_dependencies(self, param_name: str, value: float, existing_params: Dict[str, Any]) -> bool:
        """检查参数依赖关系"""
        constraint = self.parameter_constraints.get(param_name)
        if not constraint or not constraint.dependencies:
            return True
        
        for dep_param in constraint.dependencies:
            if dep_param not in existing_params:
                continue
            
            dep_value = existing_params[dep_param]['value']
            
            # 特定的依赖关系检查
            if param_name == "reservoir_max_level" and dep_param == "reservoir_initial_level":
                if value <= dep_value:
                    logger.warning(f"最大水位 {value} 应大于初始水位 {dep_value}")
                    return False
            
            elif param_name == "reservoir_initial_level" and dep_param == "reservoir_capacity":
                # 检查水位与容量的合理性（简化检查）
                if value > 1000:  # 水位超过1000米可能不合理
                    logger.warning(f"初始水位 {value} 可能过高")
                    return False
        
        return True
    
    def _correct_parameter_dependency(self, param_name: str, value: float, existing_params: Dict[str, Any]) -> Optional[float]:
        """修正参数依赖关系"""
        constraint = self.parameter_constraints.get(param_name)
        if not constraint or not constraint.dependencies:
            return value
        
        for dep_param in constraint.dependencies:
            if dep_param not in existing_params:
                continue
            
            dep_value = existing_params[dep_param]['value']
            
            # 特定的修正逻辑
            if param_name == "reservoir_max_level" and dep_param == "reservoir_initial_level":
                if value <= dep_value:
                    # 将最大水位设置为初始水位的1.2倍
                    corrected_value = dep_value * 1.2
                    logger.info(f"修正最大水位从 {value} 到 {corrected_value}")
                    return corrected_value
        
        return value
    
    def _ensure_global_consistency(self, parameters: Dict[str, Any], component_type: str = None) -> Dict[str, Any]:
        """确保全局一致性"""
        # 检查时间参数的一致性
        if 'duration' in parameters and 'time_step' in parameters:
            duration = parameters['duration']['value']
            time_step = parameters['time_step']['value']
            
            if time_step > duration:
                logger.warning(f"时间步长 {time_step} 大于仿真时长 {duration}")
                # 修正时间步长为仿真时长的1/100
                corrected_time_step = duration / 100
                parameters['time_step']['value'] = corrected_time_step
                parameters['time_step']['confidence'] = 0.6
                logger.info(f"修正时间步长为 {corrected_time_step}")
        
        # 检查效率参数
        for param_name, param_data in parameters.items():
            if param_data.get('type') == 'efficiency':
                value = param_data['value']
                if value > 1.0:
                    # 可能是百分比形式，转换为小数
                    if value <= 100:
                        corrected_value = value / 100
                        parameters[param_name]['value'] = corrected_value
                        parameters[param_name]['unit'] = '无量纲'
                        logger.info(f"将效率参数 {param_name} 从 {value}% 转换为 {corrected_value}")
        
        return parameters
    
    def _calculate_confidence(self, param_name: str, original_value: Any, final_value: float) -> float:
        """计算置信度"""
        base_confidence = 0.8
        
        # 如果原始值包含单位，提高置信度
        if re.search(r'[a-zA-Z\u4e00-\u9fff]+', str(original_value)):
            base_confidence += 0.1
        
        # 如果参数名称明确，提高置信度
        if param_name in self.parameter_constraints:
            base_confidence += 0.05
        
        # 如果数值在合理范围内，提高置信度
        constraint = self.parameter_constraints.get(param_name)
        if constraint:
            if (constraint.min_value is None or final_value >= constraint.min_value) and \
               (constraint.max_value is None or final_value <= constraint.max_value):
                base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def extract_parameters_with_precision(self, text: str, component_type: str = None) -> Dict[str, Any]:
        """高精度参数提取"""
        extracted_params = {}
        
        # 遍历所有参数模式
        for param_type, patterns in self.parameter_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1)
                        unit_str = match.group(2) if len(match.groups()) > 1 else ""
                        
                        # 构造参数值字符串
                        param_value = f"{value_str} {unit_str}".strip()
                        
                        # 生成参数名称
                        param_name = self._generate_parameter_name(param_type, component_type)
                        
                        if param_name not in extracted_params:
                            extracted_params[param_name] = param_value
                    
                    except Exception as e:
                        logger.warning(f"提取参数时出错: {e}")
                        continue
        
        # 优化提取的参数
        return self.optimize_parameters(extracted_params, component_type)
    
    def _generate_parameter_name(self, param_type: str, component_type: str = None) -> str:
        """生成参数名称"""
        if component_type:
            return f"{component_type}_{param_type}"
        else:
            return param_type