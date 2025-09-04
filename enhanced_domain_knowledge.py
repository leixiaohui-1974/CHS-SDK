#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强水利工程领域知识库
包含专业术语、标准参数范围、典型配置模式等
"""

import re
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

class ComponentType(Enum):
    """组件类型"""
    RESERVOIR = "reservoir"          # 水库
    CHANNEL = "channel"              # 渠道
    PIPE = "pipe"                    # 管道
    GATE = "gate"                    # 闸门
    PUMP = "pump"                    # 泵站
    VALVE = "valve"                  # 阀门
    TANK = "tank"                    # 水箱
    FILTER = "filter"                # 过滤器
    METER = "meter"                  # 流量计
    SENSOR = "sensor"                # 传感器

class ParameterType(Enum):
    """参数类型"""
    CAPACITY = "capacity"            # 容量
    FLOW_RATE = "flow_rate"          # 流量
    PRESSURE = "pressure"            # 压力
    LEVEL = "level"                  # 水位
    DIAMETER = "diameter"            # 直径
    LENGTH = "length"                # 长度
    HEIGHT = "height"                # 高度
    TEMPERATURE = "temperature"      # 温度
    VELOCITY = "velocity"            # 流速
    EFFICIENCY = "efficiency"        # 效率

class UnitType(Enum):
    """单位类型"""
    VOLUME = "volume"                # 体积
    FLOW = "flow"                    # 流量
    PRESSURE_UNIT = "pressure"       # 压力
    LENGTH_UNIT = "length"           # 长度
    TEMPERATURE_UNIT = "temperature" # 温度
    PERCENTAGE = "percentage"        # 百分比

@dataclass
class ParameterRange:
    """参数范围"""
    min_value: float
    max_value: float
    typical_value: float
    unit: str
    description: str = ""

@dataclass
class ComponentSpec:
    """组件规格"""
    name: str
    type: ComponentType
    parameters: Dict[str, ParameterRange] = field(default_factory=dict)
    synonyms: List[str] = field(default_factory=list)
    description: str = ""
    typical_applications: List[str] = field(default_factory=list)

@dataclass
class ConfigurationPattern:
    """配置模式"""
    name: str
    components: List[str]
    connections: List[Dict[str, str]]
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    use_cases: List[str] = field(default_factory=list)

class EnhancedDomainKnowledge:
    """增强水利工程领域知识库"""
    
    def __init__(self):
        """初始化知识库"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化各种知识库
        self._init_terminology_db()
        self._init_component_specs()
        self._init_parameter_ranges()
        self._init_unit_conversions()
        self._init_configuration_patterns()
        self._init_validation_rules()
        self._init_error_patterns()
        
        # 统计信息
        self.usage_stats = {
            "terminology_queries": 0,
            "parameter_validations": 0,
            "pattern_matches": 0,
            "error_corrections": 0
        }
    
    def _init_terminology_db(self):
        """初始化术语数据库"""
        self.terminology_db = {
            # 组件术语
            "components": {
                "水库": {
                    "standard_term": "水库",
                    "synonyms": ["reservoir", "蓄水池", "水库", "蓄水库", "调节池"],
                    "type": ComponentType.RESERVOIR,
                    "category": "storage"
                },
                "渠道": {
                    "standard_term": "渠道",
                    "synonyms": ["channel", "渠道", "明渠", "水渠", "输水渠", "灌溉渠"],
                    "type": ComponentType.CHANNEL,
                    "category": "conveyance"
                },
                "管道": {
                    "standard_term": "管道",
                    "synonyms": ["pipe", "管道", "管线", "输水管", "压力管", "给水管"],
                    "type": ComponentType.PIPE,
                    "category": "conveyance"
                },
                "闸门": {
                    "standard_term": "闸门",
                    "synonyms": ["gate", "闸门", "水闸", "控制闸", "调节闸", "节制闸"],
                    "type": ComponentType.GATE,
                    "category": "control"
                },
                "泵站": {
                    "standard_term": "泵站",
                    "synonyms": ["pump", "泵站", "水泵", "提升泵", "排水泵", "供水泵"],
                    "type": ComponentType.PUMP,
                    "category": "machinery"
                },
                "阀门": {
                    "standard_term": "阀门",
                    "synonyms": ["valve", "阀门", "调节阀", "截止阀", "球阀", "蝶阀"],
                    "type": ComponentType.VALVE,
                    "category": "control"
                },
                "水箱": {
                    "standard_term": "水箱",
                    "synonyms": ["tank", "水箱", "储水箱", "高位水箱", "调节水箱"],
                    "type": ComponentType.TANK,
                    "category": "storage"
                },
                "过滤器": {
                    "standard_term": "过滤器",
                    "synonyms": ["filter", "过滤器", "滤网", "沉淀池", "澄清池"],
                    "type": ComponentType.FILTER,
                    "category": "treatment"
                },
                "流量计": {
                    "standard_term": "流量计",
                    "synonyms": ["meter", "流量计", "水表", "计量表", "测流设备"],
                    "type": ComponentType.METER,
                    "category": "measurement"
                },
                "传感器": {
                    "standard_term": "传感器",
                    "synonyms": ["sensor", "传感器", "监测器", "探头", "检测器"],
                    "type": ComponentType.SENSOR,
                    "category": "measurement"
                }
            },
            
            # 参数术语
            "parameters": {
                "容量": {
                    "standard_term": "容量",
                    "synonyms": ["capacity", "容量", "库容", "蓄水量", "储水量", "容积"],
                    "type": ParameterType.CAPACITY,
                    "unit_type": UnitType.VOLUME
                },
                "流量": {
                    "standard_term": "流量",
                    "synonyms": ["flow", "流量", "流速", "discharge", "通过量", "输水量"],
                    "type": ParameterType.FLOW_RATE,
                    "unit_type": UnitType.FLOW
                },
                "水位": {
                    "standard_term": "水位",
                    "synonyms": ["level", "水位", "液位", "高程", "标高", "水深"],
                    "type": ParameterType.LEVEL,
                    "unit_type": UnitType.LENGTH_UNIT
                },
                "压力": {
                    "standard_term": "压力",
                    "synonyms": ["pressure", "压力", "水压", "压强", "水头"],
                    "type": ParameterType.PRESSURE,
                    "unit_type": UnitType.PRESSURE_UNIT
                },
                "直径": {
                    "standard_term": "直径",
                    "synonyms": ["diameter", "直径", "管径", "口径", "孔径"],
                    "type": ParameterType.DIAMETER,
                    "unit_type": UnitType.LENGTH_UNIT
                },
                "长度": {
                    "standard_term": "长度",
                    "synonyms": ["length", "长度", "距离", "长", "总长"],
                    "type": ParameterType.LENGTH,
                    "unit_type": UnitType.LENGTH_UNIT
                },
                "高度": {
                    "standard_term": "高度",
                    "synonyms": ["height", "高度", "高", "标高", "海拔"],
                    "type": ParameterType.HEIGHT,
                    "unit_type": UnitType.LENGTH_UNIT
                },
                "温度": {
                    "standard_term": "温度",
                    "synonyms": ["temperature", "温度", "水温", "气温"],
                    "type": ParameterType.TEMPERATURE,
                    "unit_type": UnitType.TEMPERATURE_UNIT
                },
                "效率": {
                    "standard_term": "效率",
                    "synonyms": ["efficiency", "效率", "效能", "利用率"],
                    "type": ParameterType.EFFICIENCY,
                    "unit_type": UnitType.PERCENTAGE
                }
            },
            
            # 单位术语
            "units": {
                "体积": {
                    "standard_units": ["立方米", "m³", "m3"],
                    "conversions": {
                        "万立方米": 10000,
                        "千立方米": 1000,
                        "升": 0.001,
                        "毫升": 0.000001
                    }
                },
                "流量": {
                    "standard_units": ["立方米每秒", "m³/s", "m3/s"],
                    "conversions": {
                        "升每秒": 0.001,
                        "立方米每小时": 1/3600,
                        "立方米每分钟": 1/60
                    }
                },
                "长度": {
                    "standard_units": ["米", "m"],
                    "conversions": {
                        "公里": 1000,
                        "千米": 1000,
                        "厘米": 0.01,
                        "毫米": 0.001,
                        "英尺": 0.3048,
                        "英寸": 0.0254
                    }
                },
                "压力": {
                    "standard_units": ["MPa"],
                    "conversions": {
                        "kPa": 0.001,
                        "Pa": 0.000001,
                        "bar": 0.1,
                        "atm": 0.101325
                    }
                },
                "温度": {
                    "standard_units": ["℃"],
                    "conversions": {
                        "K": lambda c: c + 273.15,
                        "°F": lambda c: c * 9/5 + 32
                    }
                }
            }
        }
    
    def _init_component_specs(self):
        """初始化组件规格"""
        self.component_specs = {
            ComponentType.RESERVOIR: ComponentSpec(
                name="水库",
                type=ComponentType.RESERVOIR,
                parameters={
                    "容量": ParameterRange(1000, 1000000000, 10000000, "立方米", "水库蓄水容量"),
                    "最高水位": ParameterRange(10, 300, 100, "米", "设计最高水位"),
                    "最低水位": ParameterRange(5, 250, 80, "米", "设计最低水位"),
                    "坝高": ParameterRange(10, 300, 50, "米", "大坝高度")
                },
                synonyms=["水库", "蓄水池", "调节池"],
                description="用于蓄水调节的水利工程设施",
                typical_applications=["供水", "灌溉", "防洪", "发电"]
            ),
            
            ComponentType.CHANNEL: ComponentSpec(
                name="渠道",
                type=ComponentType.CHANNEL,
                parameters={
                    "长度": ParameterRange(100, 100000, 5000, "米", "渠道总长度"),
                    "宽度": ParameterRange(1, 50, 5, "米", "渠道底宽"),
                    "深度": ParameterRange(0.5, 10, 2, "米", "渠道深度"),
                    "流量": ParameterRange(0.1, 1000, 10, "立方米每秒", "设计流量"),
                    "坡度": ParameterRange(0.0001, 0.01, 0.001, "", "渠道纵坡")
                },
                synonyms=["渠道", "明渠", "水渠"],
                description="用于输水的明渠工程",
                typical_applications=["灌溉", "排水", "输水"]
            ),
            
            ComponentType.PIPE: ComponentSpec(
                name="管道",
                type=ComponentType.PIPE,
                parameters={
                    "直径": ParameterRange(0.05, 5, 0.5, "米", "管道内径"),
                    "长度": ParameterRange(10, 50000, 1000, "米", "管道长度"),
                    "压力": ParameterRange(0.1, 10, 1, "MPa", "工作压力"),
                    "流量": ParameterRange(0.01, 100, 5, "立方米每秒", "设计流量")
                },
                synonyms=["管道", "管线", "输水管"],
                description="用于输送水的压力管道",
                typical_applications=["供水", "输水", "排水"]
            ),
            
            ComponentType.PUMP: ComponentSpec(
                name="泵站",
                type=ComponentType.PUMP,
                parameters={
                    "流量": ParameterRange(0.1, 100, 10, "立方米每秒", "额定流量"),
                    "扬程": ParameterRange(5, 500, 50, "米", "额定扬程"),
                    "功率": ParameterRange(1, 10000, 100, "kW", "电机功率"),
                    "效率": ParameterRange(60, 95, 80, "%", "泵效率")
                },
                synonyms=["泵站", "水泵", "提升泵"],
                description="用于提升和输送水的机械设备",
                typical_applications=["供水", "排水", "灌溉"]
            ),
            
            ComponentType.GATE: ComponentSpec(
                name="闸门",
                type=ComponentType.GATE,
                parameters={
                    "宽度": ParameterRange(1, 20, 5, "米", "闸门宽度"),
                    "高度": ParameterRange(1, 15, 3, "米", "闸门高度"),
                    "启闭力": ParameterRange(10, 10000, 500, "kN", "启闭所需力"),
                    "水头": ParameterRange(1, 50, 10, "米", "设计水头")
                },
                synonyms=["闸门", "水闸", "控制闸"],
                description="用于控制水流的启闭设备",
                typical_applications=["流量控制", "水位调节", "防洪"]
            )
        }
    
    def _init_parameter_ranges(self):
        """初始化参数范围"""
        self.parameter_ranges = {
            # 通用参数范围
            "容量": {
                "小型": ParameterRange(1000, 100000, 50000, "立方米", "小型水库容量"),
                "中型": ParameterRange(100000, 10000000, 1000000, "立方米", "中型水库容量"),
                "大型": ParameterRange(10000000, 1000000000, 100000000, "立方米", "大型水库容量")
            },
            "流量": {
                "小流量": ParameterRange(0.01, 1, 0.1, "立方米每秒", "小流量范围"),
                "中流量": ParameterRange(1, 100, 10, "立方米每秒", "中流量范围"),
                "大流量": ParameterRange(100, 10000, 1000, "立方米每秒", "大流量范围")
            },
            "压力": {
                "低压": ParameterRange(0.1, 0.6, 0.3, "MPa", "低压系统"),
                "中压": ParameterRange(0.6, 1.6, 1.0, "MPa", "中压系统"),
                "高压": ParameterRange(1.6, 10, 4, "MPa", "高压系统")
            }
        }
    
    def _init_unit_conversions(self):
        """初始化单位转换"""
        self.unit_conversions = {
            # 体积单位转换（转换为立方米）
            "volume": {
                "立方米": 1.0,
                "m³": 1.0,
                "m3": 1.0,
                "万立方米": 10000.0,
                "千立方米": 1000.0,
                "升": 0.001,
                "毫升": 0.000001,
                "加仑": 0.003785,
                "英制加仑": 0.004546
            },
            
            # 流量单位转换（转换为立方米每秒）
            "flow": {
                "立方米每秒": 1.0,
                "m³/s": 1.0,
                "m3/s": 1.0,
                "升每秒": 0.001,
                "立方米每小时": 1/3600,
                "立方米每分钟": 1/60,
                "升每分钟": 1/60000,
                "加仑每分钟": 0.00006309
            },
            
            # 长度单位转换（转换为米）
            "length": {
                "米": 1.0,
                "m": 1.0,
                "公里": 1000.0,
                "千米": 1000.0,
                "km": 1000.0,
                "厘米": 0.01,
                "cm": 0.01,
                "毫米": 0.001,
                "mm": 0.001,
                "英尺": 0.3048,
                "ft": 0.3048,
                "英寸": 0.0254,
                "in": 0.0254
            },
            
            # 压力单位转换（转换为MPa）
            "pressure": {
                "MPa": 1.0,
                "kPa": 0.001,
                "Pa": 0.000001,
                "bar": 0.1,
                "atm": 0.101325,
                "psi": 0.006895,
                "mmHg": 0.000133322,
                "mH2O": 0.009807
            }
        }
    
    def _init_configuration_patterns(self):
        """初始化配置模式"""
        self.configuration_patterns = {
            "gravity_flow_system": ConfigurationPattern(
                name="重力流系统",
                components=["水库", "渠道", "闸门"],
                connections=[
                    {"from": "水库", "to": "渠道", "type": "重力流"},
                    {"from": "闸门", "to": "渠道", "type": "控制"}
                ],
                parameters={
                    "水库容量": "大于下游需水量",
                    "渠道坡度": "0.0005-0.002",
                    "闸门类型": "平板闸门或弧形闸门"
                },
                description="利用重力势能输水的系统",
                use_cases=["灌溉系统", "城市供水", "工业用水"]
            ),
            
            "pumped_system": ConfigurationPattern(
                name="泵送系统",
                components=["水源", "泵站", "管道", "水箱"],
                connections=[
                    {"from": "水源", "to": "泵站", "type": "吸水"},
                    {"from": "泵站", "to": "管道", "type": "压力输送"},
                    {"from": "管道", "to": "水箱", "type": "储存"}
                ],
                parameters={
                    "泵站扬程": "根据地形高差确定",
                    "管道压力": "1.0-1.6MPa",
                    "水箱容量": "满足调节需求"
                },
                description="使用水泵提升输送的系统",
                use_cases=["高地供水", "长距离输水", "增压供水"]
            ),
            
            "treatment_system": ConfigurationPattern(
                name="水处理系统",
                components=["原水", "过滤器", "沉淀池", "清水池"],
                connections=[
                    {"from": "原水", "to": "沉淀池", "type": "预处理"},
                    {"from": "沉淀池", "to": "过滤器", "type": "过滤"},
                    {"from": "过滤器", "to": "清水池", "type": "储存"}
                ],
                parameters={
                    "沉淀时间": "2-4小时",
                    "过滤速度": "5-10m/h",
                    "清水池容量": "日用水量的20-25%"
                },
                description="水质净化处理系统",
                use_cases=["饮用水处理", "工业用水处理", "污水处理"]
            )
        }
    
    def _init_validation_rules(self):
        """初始化验证规则"""
        self.validation_rules = {
            "physical_constraints": {
                "flow_continuity": "进入系统的流量应等于流出系统的流量",
                "energy_conservation": "系统总能量守恒",
                "pressure_limits": "压力不能超过管道或设备的承压能力",
                "capacity_limits": "流量不能超过管道或设备的通流能力"
            },
            
            "engineering_standards": {
                "safety_factor": "设计参数应包含适当的安全系数",
                "material_compatibility": "材料选择应与介质和环境兼容",
                "maintenance_access": "设备布置应便于维护和检修",
                "redundancy": "关键设备应有备用或冗余设计"
            },
            
            "operational_requirements": {
                "control_capability": "系统应具备必要的控制和调节能力",
                "monitoring_system": "重要参数应有监测和报警系统",
                "emergency_shutdown": "应有紧急停机和安全保护措施",
                "operational_flexibility": "系统应适应不同工况的运行需求"
            }
        }
    
    def _init_error_patterns(self):
        """初始化错误模式"""
        self.error_patterns = {
            "unit_errors": {
                "missing_units": {
                    "pattern": r"\d+(?!\s*[a-zA-Z\u4e00-\u9fff])",
                    "description": "数值缺少单位",
                    "correction": "根据参数类型添加合适单位"
                },
                "wrong_units": {
                    "pattern": r"(\d+)\s*(kg|ton)\s*(?=容量|体积)",
                    "description": "体积参数使用重量单位",
                    "correction": "将重量单位转换为体积单位"
                }
            },
            
            "value_errors": {
                "unrealistic_values": {
                    "pattern": r"容量\s*[：:=]?\s*(\d+)\s*立方米",
                    "validation": lambda x: 1000 <= float(x) <= 1e12,
                    "description": "容量值不在合理范围内",
                    "correction": "检查数值是否缺少量级单位"
                },
                "negative_values": {
                    "pattern": r"-\d+",
                    "description": "物理量出现负值",
                    "correction": "将负值修正为正值或零"
                }
            },
            
            "terminology_errors": {
                "mixed_languages": {
                    "pattern": r"[a-zA-Z]+\s*[\u4e00-\u9fff]+|[\u4e00-\u9fff]+\s*[a-zA-Z]+",
                    "description": "中英文术语混用",
                    "correction": "统一使用中文术语"
                },
                "abbreviation_errors": {
                    "pattern": r"\b(res|chan|pip)\b",
                    "description": "使用了非标准缩写",
                    "correction": "使用完整的标准术语"
                }
            }
        }
    
    def standardize_terminology(self, text: str) -> str:
        """标准化术语"""
        self.usage_stats["terminology_queries"] += 1
        
        standardized_text = text
        
        # 标准化组件术语
        for standard_term, term_data in self.terminology_db["components"].items():
            for synonym in term_data["synonyms"]:
                if synonym != standard_term:
                    pattern = rf'\b{re.escape(synonym)}\b'
                    standardized_text = re.sub(pattern, standard_term, standardized_text, flags=re.IGNORECASE)
        
        # 标准化参数术语
        for standard_term, term_data in self.terminology_db["parameters"].items():
            for synonym in term_data["synonyms"]:
                if synonym != standard_term:
                    pattern = rf'\b{re.escape(synonym)}\b'
                    standardized_text = re.sub(pattern, standard_term, standardized_text, flags=re.IGNORECASE)
        
        return standardized_text
    
    def validate_parameter(self, component_type: str, parameter_name: str, value: str) -> Dict[str, Any]:
        """验证参数"""
        self.usage_stats["parameter_validations"] += 1
        
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "corrected_value": value
        }
        
        try:
            # 查找组件类型
            comp_type = None
            for comp_name, comp_data in self.terminology_db["components"].items():
                if component_type.lower() in [s.lower() for s in comp_data["synonyms"]]:
                    comp_type = comp_data["type"]
                    break
            
            if not comp_type:
                validation_result["warnings"].append(f"未识别的组件类型: {component_type}")
                return validation_result
            
            # 获取组件规格
            component_spec = self.component_specs.get(comp_type)
            if not component_spec:
                validation_result["warnings"].append(f"缺少组件规格定义: {comp_type}")
                return validation_result
            
            # 查找参数规格
            param_spec = None
            for param_name_spec, param_range in component_spec.parameters.items():
                if parameter_name.lower() in param_name_spec.lower():
                    param_spec = param_range
                    break
            
            if not param_spec:
                validation_result["warnings"].append(f"未找到参数规格: {parameter_name}")
                return validation_result
            
            # 提取数值和单位
            value_match = re.search(r'([\d.]+)\s*([^\d\s]*)', value)
            if not value_match:
                validation_result["errors"].append(f"无法解析参数值: {value}")
                validation_result["is_valid"] = False
                return validation_result
            
            numeric_value = float(value_match.group(1))
            unit = value_match.group(2).strip()
            
            # 单位转换
            converted_value = self._convert_to_standard_unit(numeric_value, unit, param_spec.unit)
            
            # 范围验证
            if converted_value < param_spec.min_value:
                validation_result["warnings"].append(
                    f"参数值 {converted_value}{param_spec.unit} 低于最小值 {param_spec.min_value}{param_spec.unit}"
                )
            elif converted_value > param_spec.max_value:
                validation_result["warnings"].append(
                    f"参数值 {converted_value}{param_spec.unit} 超过最大值 {param_spec.max_value}{param_spec.unit}"
                )
            
            # 提供典型值建议
            if abs(converted_value - param_spec.typical_value) / param_spec.typical_value > 2:
                validation_result["suggestions"].append(
                    f"典型值为 {param_spec.typical_value}{param_spec.unit}，请确认当前值是否合理"
                )
            
            # 更新修正值
            validation_result["corrected_value"] = f"{converted_value}{param_spec.unit}"
            
        except Exception as e:
            validation_result["errors"].append(f"验证过程中发生错误: {str(e)}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    def _convert_to_standard_unit(self, value: float, from_unit: str, to_unit: str) -> float:
        """单位转换"""
        if not from_unit or from_unit == to_unit:
            return value
        
        # 确定单位类型
        unit_type = None
        for utype, conversions in self.unit_conversions.items():
            if from_unit in conversions and to_unit in conversions:
                unit_type = utype
                break
        
        if not unit_type:
            return value  # 无法转换，返回原值
        
        # 执行转换
        from_factor = self.unit_conversions[unit_type][from_unit]
        to_factor = self.unit_conversions[unit_type][to_unit]
        
        # 先转换为标准单位，再转换为目标单位
        standard_value = value * from_factor
        converted_value = standard_value / to_factor
        
        return converted_value
    
    def find_configuration_pattern(self, components: List[str], connections: List[Dict[str, str]]) -> Optional[str]:
        """查找配置模式"""
        self.usage_stats["pattern_matches"] += 1
        
        for pattern_name, pattern in self.configuration_patterns.items():
            # 检查组件匹配
            pattern_components = set(pattern.components)
            input_components = set(components)
            
            # 计算匹配度
            common_components = pattern_components.intersection(input_components)
            match_ratio = len(common_components) / len(pattern_components)
            
            if match_ratio >= 0.7:  # 70%以上匹配认为是同一模式
                return pattern_name
        
        return None
    
    def detect_and_correct_errors(self, text: str) -> Dict[str, Any]:
        """检测和修正错误"""
        self.usage_stats["error_corrections"] += 1
        
        correction_result = {
            "original_text": text,
            "corrected_text": text,
            "errors_found": [],
            "corrections_made": []
        }
        
        corrected_text = text
        
        # 检测各类错误
        for error_category, error_types in self.error_patterns.items():
            for error_type, error_config in error_types.items():
                if "pattern" in error_config:
                    matches = re.finditer(error_config["pattern"], corrected_text)
                    for match in matches:
                        error_info = {
                            "type": error_type,
                            "category": error_category,
                            "position": match.span(),
                            "matched_text": match.group(),
                            "description": error_config["description"]
                        }
                        correction_result["errors_found"].append(error_info)
                        
                        # 应用修正
                        if error_type == "missing_units":
                            corrected_text = self._add_missing_units(corrected_text, match)
                        elif error_type == "negative_values":
                            corrected_text = self._fix_negative_values(corrected_text, match)
                        elif error_type == "mixed_languages":
                            corrected_text = self._fix_mixed_languages(corrected_text, match)
        
        correction_result["corrected_text"] = corrected_text
        
        return correction_result
    
    def _add_missing_units(self, text: str, match) -> str:
        """添加缺失的单位"""
        # 简化实现：根据上下文推断单位
        matched_text = match.group()
        
        # 检查上下文关键词
        context_start = max(0, match.start() - 20)
        context_end = min(len(text), match.end() + 20)
        context = text[context_start:context_end].lower()
        
        if any(keyword in context for keyword in ['容量', '库容', '蓄水']):
            return text.replace(matched_text, f"{matched_text}立方米", 1)
        elif any(keyword in context for keyword in ['流量', '流速']):
            return text.replace(matched_text, f"{matched_text}立方米每秒", 1)
        elif any(keyword in context for keyword in ['长度', '距离', '高度']):
            return text.replace(matched_text, f"{matched_text}米", 1)
        elif any(keyword in context for keyword in ['压力', '水压']):
            return text.replace(matched_text, f"{matched_text}MPa", 1)
        
        return text
    
    def _fix_negative_values(self, text: str, match) -> str:
        """修正负值"""
        matched_text = match.group()
        positive_value = matched_text.replace('-', '')
        return text.replace(matched_text, positive_value, 1)
    
    def _fix_mixed_languages(self, text: str, match) -> str:
        """修正中英文混用"""
        matched_text = match.group()
        
        # 简化实现：将常见英文术语替换为中文
        replacements = {
            'reservoir': '水库',
            'channel': '渠道',
            'pipe': '管道',
            'pump': '泵站',
            'gate': '闸门',
            'capacity': '容量',
            'flow': '流量',
            'pressure': '压力'
        }
        
        corrected = matched_text
        for en_term, cn_term in replacements.items():
            corrected = re.sub(rf'\b{en_term}\b', cn_term, corrected, flags=re.IGNORECASE)
        
        return text.replace(matched_text, corrected, 1)
    
    def get_component_info(self, component_name: str) -> Optional[Dict[str, Any]]:
        """获取组件信息"""
        # 标准化组件名称
        standardized_name = self.standardize_terminology(component_name)
        
        # 查找组件类型
        for comp_name, comp_data in self.terminology_db["components"].items():
            if standardized_name.lower() in [s.lower() for s in comp_data["synonyms"]]:
                comp_type = comp_data["type"]
                comp_spec = self.component_specs.get(comp_type)
                
                if comp_spec:
                    return {
                        "name": comp_spec.name,
                        "type": comp_spec.type.value,
                        "parameters": {k: v.__dict__ for k, v in comp_spec.parameters.items()},
                        "synonyms": comp_spec.synonyms,
                        "description": comp_spec.description,
                        "applications": comp_spec.typical_applications
                    }
        
        return None
    
    def suggest_parameters(self, component_type: str) -> List[Dict[str, Any]]:
        """建议参数"""
        suggestions = []
        
        # 查找组件类型
        comp_type = None
        for comp_name, comp_data in self.terminology_db["components"].items():
            if component_type.lower() in [s.lower() for s in comp_data["synonyms"]]:
                comp_type = comp_data["type"]
                break
        
        if comp_type and comp_type in self.component_specs:
            comp_spec = self.component_specs[comp_type]
            for param_name, param_range in comp_spec.parameters.items():
                suggestions.append({
                    "parameter": param_name,
                    "typical_value": f"{param_range.typical_value}{param_range.unit}",
                    "range": f"{param_range.min_value}-{param_range.max_value}{param_range.unit}",
                    "description": param_range.description
                })
        
        return suggestions
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return self.usage_stats.copy()
    
    def export_knowledge_base(self, format_type: str = "json") -> str:
        """导出知识库"""
        knowledge_data = {
            "terminology_db": self.terminology_db,
            "component_specs": {k.value: v.__dict__ for k, v in self.component_specs.items()},
            "parameter_ranges": {k: {kk: vv.__dict__ for kk, vv in v.items()} for k, v in self.parameter_ranges.items()},
            "unit_conversions": self.unit_conversions,
            "configuration_patterns": {k: v.__dict__ for k, v in self.configuration_patterns.items()},
            "validation_rules": self.validation_rules,
            "error_patterns": self.error_patterns,
            "usage_stats": self.usage_stats
        }
        
        if format_type.lower() == "json":
            return json.dumps(knowledge_data, ensure_ascii=False, indent=2, default=str)
        else:
            return str(knowledge_data)