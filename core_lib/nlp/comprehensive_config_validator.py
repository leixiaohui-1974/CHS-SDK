#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面配置验证系统
确保生成的配置文件在结构、语义和工程约束方面都是正确的
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """验证级别"""
    BASIC = "basic"  # 基础验证
    STANDARD = "standard"  # 标准验证
    STRICT = "strict"  # 严格验证
    ENGINEERING = "engineering"  # 工程验证

class ValidationSeverity(Enum):
    """验证严重性"""
    ERROR = "error"  # 错误
    WARNING = "warning"  # 警告
    INFO = "info"  # 信息
    SUGGESTION = "suggestion"  # 建议

@dataclass
class ValidationIssue:
    """验证问题"""
    severity: ValidationSeverity
    category: str
    message: str
    location: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fix_data: Optional[Dict[str, Any]] = None

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float  # 0-100分
    issues: List[ValidationIssue]
    summary: Dict[str, int]  # 按严重性统计
    recommendations: List[str]

class ComprehensiveConfigValidator:
    """全面配置验证器"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.component_schemas = self._initialize_component_schemas()
        self.parameter_constraints = self._initialize_parameter_constraints()
        self.connection_rules = self._initialize_connection_rules()
        self.engineering_constraints = self._initialize_engineering_constraints()
        self.unit_conversions = self._initialize_unit_conversions()
        
    def _initialize_component_schemas(self) -> Dict[str, Dict[str, Any]]:
        """初始化组件模式"""
        schemas = {
            "Reservoir": {
                "required_params": ["capacity", "initial_level"],
                "optional_params": ["max_level", "min_level", "area", "evaporation_rate"],
                "param_types": {
                    "capacity": "volume",
                    "initial_level": "length",
                    "max_level": "length",
                    "min_level": "length",
                    "area": "area",
                    "evaporation_rate": "rate"
                },
                "constraints": {
                    "capacity": {"min": 0, "max": 1e12},
                    "initial_level": {"min": 0, "max": 1000},
                    "max_level": {"min": 0, "max": 1000},
                    "min_level": {"min": 0, "max": 1000}
                },
                "relationships": {
                    "initial_level": "should be between min_level and max_level",
                    "min_level": "should be less than max_level"
                }
            },
            "Gate": {
                "required_params": ["max_flow_rate"],
                "optional_params": ["opening", "control_type", "response_time"],
                "param_types": {
                    "max_flow_rate": "flow_rate",
                    "opening": "percentage",
                    "response_time": "time"
                },
                "constraints": {
                    "max_flow_rate": {"min": 0, "max": 10000},
                    "opening": {"min": 0, "max": 100},
                    "response_time": {"min": 0, "max": 3600}
                }
            },
            "Pump": {
                "required_params": ["max_flow_rate", "max_head"],
                "optional_params": ["efficiency", "power", "speed", "control_type"],
                "param_types": {
                    "max_flow_rate": "flow_rate",
                    "max_head": "length",
                    "efficiency": "percentage",
                    "power": "power",
                    "speed": "frequency"
                },
                "constraints": {
                    "max_flow_rate": {"min": 0, "max": 10000},
                    "max_head": {"min": 0, "max": 1000},
                    "efficiency": {"min": 0, "max": 100},
                    "power": {"min": 0, "max": 1e9}
                }
            },
            "PumpStation": {
                "required_params": ["pump_count"],
                "optional_params": ["total_capacity", "backup_pumps", "control_strategy"],
                "param_types": {
                    "pump_count": "integer",
                    "total_capacity": "flow_rate",
                    "backup_pumps": "integer"
                },
                "constraints": {
                    "pump_count": {"min": 1, "max": 20},
                    "backup_pumps": {"min": 0, "max": 10}
                }
            },
            "Valve": {
                "required_params": ["diameter"],
                "optional_params": ["opening", "pressure_rating", "control_type"],
                "param_types": {
                    "diameter": "length",
                    "opening": "percentage",
                    "pressure_rating": "pressure"
                },
                "constraints": {
                    "diameter": {"min": 0.01, "max": 10},
                    "opening": {"min": 0, "max": 100},
                    "pressure_rating": {"min": 0, "max": 100}
                }
            },
            "Pipe": {
                "required_params": ["diameter", "length"],
                "optional_params": ["roughness", "material", "pressure_rating"],
                "param_types": {
                    "diameter": "length",
                    "length": "length",
                    "roughness": "length",
                    "pressure_rating": "pressure"
                },
                "constraints": {
                    "diameter": {"min": 0.01, "max": 10},
                    "length": {"min": 0.1, "max": 100000},
                    "roughness": {"min": 0, "max": 0.1}
                }
            },
            "Canal": {
                "required_params": ["width", "depth", "length"],
                "optional_params": ["slope", "roughness", "lining_type"],
                "param_types": {
                    "width": "length",
                    "depth": "length",
                    "length": "length",
                    "slope": "dimensionless",
                    "roughness": "dimensionless"
                },
                "constraints": {
                    "width": {"min": 0.1, "max": 1000},
                    "depth": {"min": 0.1, "max": 100},
                    "length": {"min": 1, "max": 1000000},
                    "slope": {"min": 0, "max": 0.1}
                }
            },
            "Sensor": {
                "required_params": ["sensor_type"],
                "optional_params": ["accuracy", "range", "response_time"],
                "param_types": {
                    "accuracy": "percentage",
                    "response_time": "time"
                },
                "constraints": {
                    "accuracy": {"min": 0, "max": 100},
                    "response_time": {"min": 0, "max": 3600}
                }
            },
            "WaterTurbine": {
                "required_params": ["rated_power", "rated_head", "rated_flow"],
                "optional_params": ["efficiency", "turbine_type", "speed"],
                "param_types": {
                    "rated_power": "power",
                    "rated_head": "length",
                    "rated_flow": "flow_rate",
                    "efficiency": "percentage",
                    "speed": "frequency"
                },
                "constraints": {
                    "rated_power": {"min": 1000, "max": 1e9},
                    "rated_head": {"min": 1, "max": 2000},
                    "rated_flow": {"min": 0.1, "max": 10000},
                    "efficiency": {"min": 70, "max": 95}
                }
            }
        }
        return schemas
    
    def _initialize_parameter_constraints(self) -> Dict[str, Dict[str, Any]]:
        """初始化参数约束"""
        constraints = {
            "volume": {
                "units": ["m3", "L", "ML", "GL", "ft3", "gal"],
                "base_unit": "m3",
                "min_value": 0,
                "max_value": 1e12
            },
            "flow_rate": {
                "units": ["m3/s", "L/s", "m3/h", "L/min", "ft3/s", "gpm"],
                "base_unit": "m3/s",
                "min_value": 0,
                "max_value": 10000
            },
            "length": {
                "units": ["m", "cm", "mm", "km", "ft", "in"],
                "base_unit": "m",
                "min_value": 0,
                "max_value": 100000
            },
            "area": {
                "units": ["m2", "km2", "ha", "ft2", "acre"],
                "base_unit": "m2",
                "min_value": 0,
                "max_value": 1e12
            },
            "pressure": {
                "units": ["Pa", "kPa", "MPa", "bar", "psi", "atm"],
                "base_unit": "Pa",
                "min_value": 0,
                "max_value": 1e9
            },
            "power": {
                "units": ["W", "kW", "MW", "GW", "hp"],
                "base_unit": "W",
                "min_value": 0,
                "max_value": 1e12
            },
            "time": {
                "units": ["s", "min", "h", "day", "year"],
                "base_unit": "s",
                "min_value": 0,
                "max_value": 1e10
            },
            "percentage": {
                "units": ["%", "fraction"],
                "base_unit": "%",
                "min_value": 0,
                "max_value": 100
            },
            "frequency": {
                "units": ["Hz", "rpm", "rad/s"],
                "base_unit": "Hz",
                "min_value": 0,
                "max_value": 10000
            }
        }
        return constraints
    
    def _initialize_connection_rules(self) -> Dict[str, List[str]]:
        """初始化连接规则"""
        rules = {
            "valid_flow_connections": [
                "Reservoir->Gate", "Reservoir->Pump", "Reservoir->Canal", "Reservoir->Pipe",
                "Gate->Canal", "Gate->Pipe", "Gate->RiverChannel",
                "Pump->Pipe", "Pump->Canal", "Pump->Reservoir",
                "Valve->Pipe", "Pipe->Valve", "Pipe->Junction",
                "Canal->Junction", "Canal->RiverChannel",
                "PumpStation->Pipe", "PumpStation->Canal",
                "WaterTurbine->RiverChannel", "Reservoir->WaterTurbine"
            ],
            "valid_control_connections": [
                "Controller->Gate", "Controller->Pump", "Controller->Valve",
                "PLC->Gate", "PLC->Pump", "PLC->Valve",
                "SCADA->Gate", "SCADA->Pump", "SCADA->Valve"
            ],
            "valid_signal_connections": [
                "Sensor->Controller", "Sensor->PLC", "Sensor->SCADA",
                "Reservoir->Sensor", "Gate->Sensor", "Pump->Sensor",
                "Valve->Sensor", "Canal->Sensor", "Pipe->Sensor"
            ],
            "invalid_connections": [
                "Sensor->Reservoir", "Sensor->Gate", "Sensor->Pump",  # 传感器不能控制
                "Reservoir->Reservoir", "Gate->Gate", "Pump->Pump",  # 自连接
                "Canal->Reservoir",  # 渠道不能直接流入水库
            ]
        }
        return rules
    
    def _initialize_engineering_constraints(self) -> Dict[str, List[str]]:
        """初始化工程约束"""
        constraints = {
            "hydraulic_constraints": [
                "水只能从高水位流向低水位（除非有泵）",
                "管道流速应在0.5-3.0 m/s之间",
                "渠道流速应在0.3-2.0 m/s之间",
                "泵的扬程应匹配系统需求",
                "阀门压降不应超过系统压力的30%"
            ],
            "structural_constraints": [
                "泵必须有电源连接",
                "闸门必须有操作机构",
                "传感器必须有信号传输路径",
                "管道必须有支撑结构",
                "水库必须有溢洪道"
            ],
            "operational_constraints": [
                "备用设备数量应合理",
                "控制系统应有冗余",
                "关键设备应有监测",
                "应急停机系统必须可靠",
                "维护通道应畅通"
            ],
            "safety_constraints": [
                "压力容器应有安全阀",
                "电气设备应有接地保护",
                "有毒气体区域应有检测",
                "高压区域应有警示标识",
                "应急出口应畅通"
            ]
        }
        return constraints
    
    def _initialize_unit_conversions(self) -> Dict[str, Dict[str, float]]:
        """初始化单位转换"""
        conversions = {
            "volume": {
                "m3": 1.0,
                "L": 0.001,
                "ML": 1000.0,
                "GL": 1000000.0,
                "ft3": 0.0283168,
                "gal": 0.00378541
            },
            "flow_rate": {
                "m3/s": 1.0,
                "L/s": 0.001,
                "m3/h": 1/3600,
                "L/min": 0.001/60,
                "ft3/s": 0.0283168,
                "gpm": 0.00006309
            },
            "length": {
                "m": 1.0,
                "cm": 0.01,
                "mm": 0.001,
                "km": 1000.0,
                "ft": 0.3048,
                "in": 0.0254
            },
            "pressure": {
                "Pa": 1.0,
                "kPa": 1000.0,
                "MPa": 1000000.0,
                "bar": 100000.0,
                "psi": 6894.76,
                "atm": 101325.0
            },
            "power": {
                "W": 1.0,
                "kW": 1000.0,
                "MW": 1000000.0,
                "GW": 1000000000.0,
                "hp": 745.7
            }
        }
        return conversions
    
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证配置文件"""
        issues = []
        
        # 1. 结构验证
        structure_issues = self._validate_structure(config)
        issues.extend(structure_issues)
        
        # 2. 组件验证
        component_issues = self._validate_components(config.get('components', {}))
        issues.extend(component_issues)
        
        # 3. 连接验证
        connection_issues = self._validate_connections(config.get('connections', []))
        issues.extend(connection_issues)
        
        # 4. 参数验证
        parameter_issues = self._validate_parameters(config)
        issues.extend(parameter_issues)
        
        # 5. 仿真设置验证
        simulation_issues = self._validate_simulation_settings(config.get('simulation', {}))
        issues.extend(simulation_issues)
        
        # 6. 工程约束验证
        if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.ENGINEERING]:
            engineering_issues = self._validate_engineering_constraints(config)
            issues.extend(engineering_issues)
        
        # 7. 一致性验证
        consistency_issues = self._validate_consistency(config)
        issues.extend(consistency_issues)
        
        # 计算验证结果
        result = self._calculate_validation_result(issues)
        
        return result
    
    def _validate_structure(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """验证配置结构"""
        issues = []
        
        # 检查必需的顶级字段
        required_fields = ['components', 'connections', 'simulation']
        for field in required_fields:
            if field not in config:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="structure",
                    message=f"缺少必需字段: {field}",
                    location="root",
                    suggestion=f"添加 {field} 字段",
                    auto_fixable=True,
                    fix_data={"field": field, "default_value": {} if field != 'connections' else []}
                ))
        
        # 检查字段类型
        if 'components' in config and not isinstance(config['components'], dict):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="components字段必须是字典类型",
                location="components",
                suggestion="将components改为字典格式"
            ))
        
        if 'connections' in config and not isinstance(config['connections'], list):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="connections字段必须是列表类型",
                location="connections",
                suggestion="将connections改为列表格式"
            ))
        
        if 'simulation' in config and not isinstance(config['simulation'], dict):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="structure",
                message="simulation字段必须是字典类型",
                location="simulation",
                suggestion="将simulation改为字典格式"
            ))
        
        return issues
    
    def _validate_components(self, components: Dict[str, Any]) -> List[ValidationIssue]:
        """验证组件"""
        issues = []
        
        if not components:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="components",
                message="配置中没有定义任何组件",
                location="components",
                suggestion="添加至少一个组件定义"
            ))
            return issues
        
        for comp_id, comp_data in components.items():
            comp_issues = self._validate_single_component(comp_id, comp_data)
            issues.extend(comp_issues)
        
        return issues
    
    def _validate_single_component(self, comp_id: str, comp_data: Dict[str, Any]) -> List[ValidationIssue]:
        """验证单个组件"""
        issues = []
        location = f"components.{comp_id}"
        
        # 检查组件类型
        if 'type' not in comp_data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="components",
                message=f"组件 {comp_id} 缺少type字段",
                location=location,
                suggestion="添加type字段指定组件类型",
                auto_fixable=True,
                fix_data={"field": "type", "component_id": comp_id}
            ))
            return issues
        
        comp_type = comp_data['type']
        
        # 检查组件类型是否支持
        if comp_type not in self.component_schemas:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="components",
                message=f"未知的组件类型: {comp_type}",
                location=location,
                suggestion=f"支持的组件类型: {', '.join(self.component_schemas.keys())}"
            ))
            return issues
        
        schema = self.component_schemas[comp_type]
        
        # 检查必需参数
        for required_param in schema['required_params']:
            if required_param not in comp_data:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="components",
                    message=f"组件 {comp_id} 缺少必需参数: {required_param}",
                    location=f"{location}.{required_param}",
                    suggestion=f"添加 {required_param} 参数",
                    auto_fixable=True,
                    fix_data={
                        "component_id": comp_id,
                        "parameter": required_param,
                        "param_type": schema['param_types'].get(required_param, "unknown")
                    }
                ))
        
        # 验证参数值
        for param_name, param_value in comp_data.items():
            if param_name in ['type', 'id']:  # 跳过特殊字段
                continue
            
            param_issues = self._validate_parameter_value(
                comp_id, param_name, param_value, schema
            )
            issues.extend(param_issues)
        
        # 验证参数关系
        relationship_issues = self._validate_parameter_relationships(
            comp_id, comp_data, schema
        )
        issues.extend(relationship_issues)
        
        return issues
    
    def _validate_parameter_value(self, comp_id: str, param_name: str, 
                                param_value: Any, schema: Dict[str, Any]) -> List[ValidationIssue]:
        """验证参数值"""
        issues = []
        location = f"components.{comp_id}.{param_name}"
        
        # 检查参数类型
        if param_name in schema['param_types']:
            param_type = schema['param_types'][param_name]
            type_issues = self._validate_parameter_type(param_name, param_value, param_type, location)
            issues.extend(type_issues)
        
        # 检查参数约束
        if param_name in schema.get('constraints', {}):
            constraint = schema['constraints'][param_name]
            constraint_issues = self._validate_parameter_constraints(
                param_name, param_value, constraint, location
            )
            issues.extend(constraint_issues)
        
        return issues
    
    def _validate_parameter_type(self, param_name: str, param_value: Any, 
                               param_type: str, location: str) -> List[ValidationIssue]:
        """验证参数类型"""
        issues = []
        
        # 数值类型验证
        if param_type in ['volume', 'flow_rate', 'length', 'area', 'pressure', 'power', 'time']:
            if not isinstance(param_value, (int, float, str)):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="parameters",
                    message=f"参数 {param_name} 应为数值类型",
                    location=location,
                    suggestion="提供数值或带单位的字符串"
                ))
            elif isinstance(param_value, str):
                # 验证单位
                unit_issues = self._validate_unit(param_value, param_type, location)
                issues.extend(unit_issues)
        
        # 百分比验证
        elif param_type == 'percentage':
            if isinstance(param_value, str) and param_value.endswith('%'):
                try:
                    value = float(param_value[:-1])
                    if not (0 <= value <= 100):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="parameters",
                            message=f"百分比参数 {param_name} 应在0-100%之间",
                            location=location
                        ))
                except ValueError:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="parameters",
                        message=f"无效的百分比格式: {param_value}",
                        location=location
                    ))
            elif isinstance(param_value, (int, float)):
                if not (0 <= param_value <= 100):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="parameters",
                        message=f"百分比参数 {param_name} 应在0-100之间",
                        location=location
                    ))
        
        # 整数验证
        elif param_type == 'integer':
            if not isinstance(param_value, int):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="parameters",
                    message=f"参数 {param_name} 应为整数类型",
                    location=location,
                    suggestion="提供整数值"
                ))
        
        return issues
    
    def _validate_unit(self, value_str: str, param_type: str, location: str) -> List[ValidationIssue]:
        """验证单位"""
        issues = []
        
        if param_type not in self.parameter_constraints:
            return issues
        
        valid_units = self.parameter_constraints[param_type]['units']
        
        # 提取数值和单位
        import re
        match = re.match(r'^([\d.]+)\s*([a-zA-Z/%]+)$', value_str.strip())
        
        if not match:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="parameters",
                message=f"无效的参数格式: {value_str}",
                location=location,
                suggestion=f"使用格式: 数值 单位，如 '10 {valid_units[0]}'"
            ))
            return issues
        
        value, unit = match.groups()
        
        if unit not in valid_units:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="parameters",
                message=f"未识别的单位: {unit}",
                location=location,
                suggestion=f"支持的单位: {', '.join(valid_units)}",
                auto_fixable=True,
                fix_data={
                    "original_unit": unit,
                    "valid_units": valid_units,
                    "param_type": param_type
                }
            ))
        
        return issues
    
    def _validate_parameter_constraints(self, param_name: str, param_value: Any, 
                                      constraint: Dict[str, Any], location: str) -> List[ValidationIssue]:
        """验证参数约束"""
        issues = []
        
        # 提取数值
        if isinstance(param_value, str):
            try:
                # 尝试提取数值部分
                import re
                match = re.match(r'^([\d.]+)', param_value.strip())
                if match:
                    numeric_value = float(match.group(1))
                else:
                    return issues  # 无法提取数值，跳过约束检查
            except ValueError:
                return issues
        else:
            numeric_value = float(param_value)
        
        # 检查最小值
        if 'min' in constraint and numeric_value < constraint['min']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="parameters",
                message=f"参数 {param_name} 值 {numeric_value} 小于最小值 {constraint['min']}",
                location=location,
                suggestion=f"设置值不小于 {constraint['min']}"
            ))
        
        # 检查最大值
        if 'max' in constraint and numeric_value > constraint['max']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="parameters",
                message=f"参数 {param_name} 值 {numeric_value} 大于最大值 {constraint['max']}",
                location=location,
                suggestion=f"设置值不大于 {constraint['max']}"
            ))
        
        return issues
    
    def _validate_parameter_relationships(self, comp_id: str, comp_data: Dict[str, Any], 
                                        schema: Dict[str, Any]) -> List[ValidationIssue]:
        """验证参数关系"""
        issues = []
        
        if 'relationships' not in schema:
            return issues
        
        for param, relationship in schema['relationships'].items():
            if param not in comp_data:
                continue
            
            # 水库水位关系检查
            if param == 'initial_level' and 'min_level' in comp_data and 'max_level' in comp_data:
                try:
                    initial = self._extract_numeric_value(comp_data['initial_level'])
                    min_level = self._extract_numeric_value(comp_data['min_level'])
                    max_level = self._extract_numeric_value(comp_data['max_level'])
                    
                    if initial < min_level or initial > max_level:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="parameters",
                            message=f"组件 {comp_id} 的初始水位应在最小和最大水位之间",
                            location=f"components.{comp_id}.initial_level",
                            suggestion=f"设置初始水位在 {min_level} 到 {max_level} 之间"
                        ))
                except (ValueError, TypeError):
                    pass  # 无法提取数值，跳过检查
            
            elif param == 'min_level' and 'max_level' in comp_data:
                try:
                    min_level = self._extract_numeric_value(comp_data['min_level'])
                    max_level = self._extract_numeric_value(comp_data['max_level'])
                    
                    if min_level >= max_level:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category="parameters",
                            message=f"组件 {comp_id} 的最小水位应小于最大水位",
                            location=f"components.{comp_id}.min_level",
                            suggestion="确保最小水位小于最大水位"
                        ))
                except (ValueError, TypeError):
                    pass
        
        return issues
    
    def _validate_connections(self, connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """验证连接"""
        issues = []
        
        if not connections:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="connections",
                message="配置中没有定义任何连接",
                location="connections",
                suggestion="添加组件之间的连接关系"
            ))
            return issues
        
        for i, connection in enumerate(connections):
            conn_issues = self._validate_single_connection(i, connection)
            issues.extend(conn_issues)
        
        # 检查连接的一致性
        consistency_issues = self._validate_connection_consistency(connections)
        issues.extend(consistency_issues)
        
        return issues
    
    def _validate_single_connection(self, index: int, connection: Dict[str, Any]) -> List[ValidationIssue]:
        """验证单个连接"""
        issues = []
        location = f"connections[{index}]"
        
        # 检查必需字段
        required_fields = ['source', 'target', 'type']
        for field in required_fields:
            if field not in connection:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="connections",
                    message=f"连接 {index} 缺少必需字段: {field}",
                    location=location,
                    suggestion=f"添加 {field} 字段"
                ))
        
        if len([f for f in required_fields if f in connection]) < len(required_fields):
            return issues  # 缺少必需字段，跳过后续验证
        
        # 检查连接类型
        conn_type = connection['type']
        valid_types = ['flow', 'control', 'signal', 'data', 'power', 'structural']
        if conn_type not in valid_types:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="connections",
                message=f"未知的连接类型: {conn_type}",
                location=f"{location}.type",
                suggestion=f"支持的连接类型: {', '.join(valid_types)}"
            ))
        
        # 检查自连接
        if connection['source'] == connection['target']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="connections",
                message=f"检测到自连接: {connection['source']}",
                location=location,
                suggestion="移除自连接或修正连接的源和目标"
            ))
        
        return issues
    
    def _validate_connection_consistency(self, connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """验证连接一致性"""
        issues = []
        
        # 检查重复连接
        seen_connections = set()
        for i, connection in enumerate(connections):
            if all(field in connection for field in ['source', 'target', 'type']):
                conn_key = (connection['source'], connection['target'], connection['type'])
                if conn_key in seen_connections:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="connections",
                        message=f"重复的连接: {connection['source']} -> {connection['target']} ({connection['type']})",
                        location=f"connections[{i}]",
                        suggestion="移除重复的连接"
                    ))
                else:
                    seen_connections.add(conn_key)
        
        return issues
    
    def _validate_parameters(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """验证参数"""
        issues = []
        
        # 全局参数一致性检查
        components = config.get('components', {})
        
        # 检查流量平衡
        flow_balance_issues = self._check_flow_balance(components, config.get('connections', []))
        issues.extend(flow_balance_issues)
        
        # 检查压力兼容性
        pressure_issues = self._check_pressure_compatibility(components, config.get('connections', []))
        issues.extend(pressure_issues)
        
        return issues
    
    def _check_flow_balance(self, components: Dict[str, Any], 
                          connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查流量平衡"""
        issues = []
        
        # 构建流量图
        flow_graph = defaultdict(list)
        for conn in connections:
            if conn.get('type') == 'flow' and all(field in conn for field in ['source', 'target']):
                flow_graph[conn['source']].append(conn['target'])
        
        # 检查每个节点的流量平衡
        for comp_id, comp_data in components.items():
            if comp_data.get('type') in ['Junction', 'Reservoir']:
                # 这些组件需要流量平衡
                inflow_sources = [src for src, targets in flow_graph.items() if comp_id in targets]
                outflow_targets = flow_graph.get(comp_id, [])
                
                if len(inflow_sources) == 0 and len(outflow_targets) > 0:
                    if comp_data.get('type') != 'Reservoir':  # 水库可以作为源
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="flow_balance",
                            message=f"组件 {comp_id} 有出流但无入流",
                            location=f"components.{comp_id}",
                            suggestion="检查流量来源或添加入流连接"
                        ))
                
                elif len(inflow_sources) > 0 and len(outflow_targets) == 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="flow_balance",
                        message=f"组件 {comp_id} 有入流但无出流",
                        location=f"components.{comp_id}",
                        suggestion="检查流量去向或添加出流连接"
                    ))
        
        return issues
    
    def _check_pressure_compatibility(self, components: Dict[str, Any], 
                                    connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查压力兼容性"""
        issues = []
        
        # 检查管道和阀门的压力等级
        for conn in connections:
            if conn.get('type') == 'flow' and all(field in conn for field in ['source', 'target']):
                source_comp = components.get(conn['source'], {})
                target_comp = components.get(conn['target'], {})
                
                # 检查压力等级匹配
                if 'pressure_rating' in source_comp and 'pressure_rating' in target_comp:
                    try:
                        source_pressure = self._extract_numeric_value(source_comp['pressure_rating'])
                        target_pressure = self._extract_numeric_value(target_comp['pressure_rating'])
                        
                        if abs(source_pressure - target_pressure) / max(source_pressure, target_pressure) > 0.5:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="pressure_compatibility",
                                message=f"组件 {conn['source']} 和 {conn['target']} 的压力等级差异较大",
                                location=f"connection: {conn['source']}->{conn['target']}",
                                suggestion="检查压力等级匹配性"
                            ))
                    except (ValueError, TypeError):
                        pass
        
        return issues
    
    def _validate_simulation_settings(self, simulation: Dict[str, Any]) -> List[ValidationIssue]:
        """验证仿真设置"""
        issues = []
        
        if not simulation:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="simulation",
                message="缺少仿真设置",
                location="simulation",
                suggestion="添加仿真参数如duration、time_step等",
                auto_fixable=True,
                fix_data={"default_simulation": {
                    "duration": "1 hour",
                    "time_step": "1 minute",
                    "solver": "euler"
                }}
            ))
            return issues
        
        # 检查必需的仿真参数
        required_sim_params = ['duration', 'time_step']
        for param in required_sim_params:
            if param not in simulation:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="simulation",
                    message=f"缺少仿真参数: {param}",
                    location=f"simulation.{param}",
                    suggestion=f"添加 {param} 参数",
                    auto_fixable=True,
                    fix_data={"parameter": param}
                ))
        
        # 验证时间参数
        if 'duration' in simulation and 'time_step' in simulation:
            try:
                duration = self._parse_time_value(simulation['duration'])
                time_step = self._parse_time_value(simulation['time_step'])
                
                if time_step >= duration:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="simulation",
                        message="时间步长不应大于或等于仿真持续时间",
                        location="simulation.time_step",
                        suggestion="减小时间步长或增加仿真持续时间"
                    ))
                
                if duration / time_step > 100000:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="simulation",
                        message="仿真步数过多，可能导致计算时间过长",
                        location="simulation",
                        suggestion="增大时间步长或减少仿真持续时间"
                    ))
            
            except ValueError as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="simulation",
                    message=f"时间参数格式错误: {str(e)}",
                    location="simulation",
                    suggestion="使用正确的时间格式，如 '1 hour', '30 minutes'"
                ))
        
        return issues
    
    def _validate_engineering_constraints(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """验证工程约束"""
        issues = []
        
        components = config.get('components', {})
        connections = config.get('connections', [])
        
        # 检查水力约束
        hydraulic_issues = self._check_hydraulic_constraints(components, connections)
        issues.extend(hydraulic_issues)
        
        # 检查结构约束
        structural_issues = self._check_structural_constraints(components, connections)
        issues.extend(structural_issues)
        
        # 检查操作约束
        operational_issues = self._check_operational_constraints(components, connections)
        issues.extend(operational_issues)
        
        # 检查安全约束
        safety_issues = self._check_safety_constraints(components, connections)
        issues.extend(safety_issues)
        
        return issues
    
    def _check_hydraulic_constraints(self, components: Dict[str, Any], 
                                   connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查水力约束"""
        issues = []
        
        # 检查管道流速
        for comp_id, comp_data in components.items():
            if comp_data.get('type') == 'Pipe':
                if 'diameter' in comp_data and 'flow_rate' in comp_data:
                    try:
                        diameter = self._extract_numeric_value(comp_data['diameter'])
                        flow_rate = self._extract_numeric_value(comp_data['flow_rate'])
                        
                        area = math.pi * (diameter / 2) ** 2
                        velocity = flow_rate / area
                        
                        if velocity < 0.5:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="hydraulic",
                                message=f"管道 {comp_id} 流速过低 ({velocity:.2f} m/s)",
                                location=f"components.{comp_id}",
                                suggestion="增加流量或减小管径"
                            ))
                        elif velocity > 3.0:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="hydraulic",
                                message=f"管道 {comp_id} 流速过高 ({velocity:.2f} m/s)",
                                location=f"components.{comp_id}",
                                suggestion="减少流量或增大管径"
                            ))
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass
        
        return issues
    
    def _check_structural_constraints(self, components: Dict[str, Any], 
                                    connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查结构约束"""
        issues = []
        
        # 检查泵是否有电源
        pumps = [comp_id for comp_id, comp_data in components.items() 
                if comp_data.get('type') in ['Pump', 'PumpStation']]
        
        power_connections = [conn for conn in connections 
                           if conn.get('type') == 'power']
        
        for pump_id in pumps:
            has_power = any(conn.get('target') == pump_id for conn in power_connections)
            if not has_power:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="structural",
                    message=f"泵 {pump_id} 缺少电源连接",
                    location=f"components.{pump_id}",
                    suggestion="添加电源连接"
                ))
        
        return issues
    
    def _check_operational_constraints(self, components: Dict[str, Any], 
                                     connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查操作约束"""
        issues = []
        
        # 检查关键设备是否有监测
        critical_components = [comp_id for comp_id, comp_data in components.items() 
                             if comp_data.get('type') in ['Reservoir', 'Gate', 'Pump', 'PumpStation']]
        
        signal_connections = [conn for conn in connections 
                            if conn.get('type') == 'signal']
        
        for comp_id in critical_components:
            has_monitoring = any(conn.get('source') == comp_id for conn in signal_connections)
            if not has_monitoring:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="operational",
                    message=f"关键设备 {comp_id} 缺少监测",
                    location=f"components.{comp_id}",
                    suggestion="添加传感器监测"
                ))
        
        return issues
    
    def _check_safety_constraints(self, components: Dict[str, Any], 
                                connections: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """检查安全约束"""
        issues = []
        
        # 检查高压组件是否有安全措施
        for comp_id, comp_data in components.items():
            if 'pressure_rating' in comp_data:
                try:
                    pressure = self._extract_numeric_value(comp_data['pressure_rating'])
                    if pressure > 1000000:  # 1 MPa
                        # 检查是否有安全阀
                        has_safety_valve = any(
                            conn.get('source') == comp_id and 
                            components.get(conn.get('target'), {}).get('type') == 'SafetyValve'
                            for conn in connections
                        )
                        if not has_safety_valve:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.WARNING,
                                category="safety",
                                message=f"高压组件 {comp_id} 缺少安全阀",
                                location=f"components.{comp_id}",
                                suggestion="添加安全阀保护"
                            ))
                except (ValueError, TypeError):
                    pass
        
        return issues
    
    def _validate_consistency(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """验证一致性"""
        issues = []
        
        components = config.get('components', {})
        connections = config.get('connections', [])
        
        # 检查连接引用的组件是否存在
        for i, conn in enumerate(connections):
            if 'source' in conn and conn['source'] not in components:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    message=f"连接 {i} 引用了不存在的源组件: {conn['source']}",
                    location=f"connections[{i}].source",
                    suggestion="检查组件名称或添加缺失的组件"
                ))
            
            if 'target' in conn and conn['target'] not in components:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    message=f"连接 {i} 引用了不存在的目标组件: {conn['target']}",
                    location=f"connections[{i}].target",
                    suggestion="检查组件名称或添加缺失的组件"
                ))
        
        # 检查孤立组件
        connected_components = set()
        for conn in connections:
            if 'source' in conn:
                connected_components.add(conn['source'])
            if 'target' in conn:
                connected_components.add(conn['target'])
        
        isolated_components = set(components.keys()) - connected_components
        for comp_id in isolated_components:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="consistency",
                message=f"组件 {comp_id} 没有任何连接",
                location=f"components.{comp_id}",
                suggestion="添加与其他组件的连接或确认这是预期的"
            ))
        
        return issues
    
    def _calculate_validation_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """计算验证结果"""
        # 统计问题
        summary = {
            "error": len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
            "warning": len([i for i in issues if i.severity == ValidationSeverity.WARNING]),
            "info": len([i for i in issues if i.severity == ValidationSeverity.INFO]),
            "suggestion": len([i for i in issues if i.severity == ValidationSeverity.SUGGESTION])
        }
        
        # 计算分数
        total_issues = len(issues)
        error_weight = 10
        warning_weight = 5
        info_weight = 2
        suggestion_weight = 1
        
        penalty = (summary["error"] * error_weight + 
                  summary["warning"] * warning_weight + 
                  summary["info"] * info_weight + 
                  summary["suggestion"] * suggestion_weight)
        
        # 基础分数100，根据问题扣分
        score = max(0, 100 - penalty)
        
        # 判断是否有效
        is_valid = summary["error"] == 0
        
        # 生成建议
        recommendations = self._generate_recommendations(issues)
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            summary=summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 按类别统计问题
        category_counts = defaultdict(int)
        for issue in issues:
            if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.WARNING]:
                category_counts[issue.category] += 1
        
        # 生成针对性建议
        if category_counts["structure"] > 0:
            recommendations.append("修复配置文件结构问题，确保包含必需的字段")
        
        if category_counts["components"] > 0:
            recommendations.append("完善组件定义，添加缺失的必需参数")
        
        if category_counts["connections"] > 0:
            recommendations.append("检查连接定义，确保连接关系正确")
        
        if category_counts["parameters"] > 0:
            recommendations.append("验证参数值和单位，确保在合理范围内")
        
        if category_counts["simulation"] > 0:
            recommendations.append("完善仿真设置，添加必要的仿真参数")
        
        if category_counts["hydraulic"] > 0:
            recommendations.append("检查水力设计，确保流速和压力在合理范围内")
        
        if category_counts["safety"] > 0:
            recommendations.append("添加必要的安全措施和保护设备")
        
        return recommendations
    
    # 辅助方法
    def _extract_numeric_value(self, value: Any) -> float:
        """提取数值"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # 尝试提取数值部分
            import re
            match = re.match(r'^([\d.]+)', value.strip())
            if match:
                return float(match.group(1))
            else:
                raise ValueError(f"无法从字符串中提取数值: {value}")
        else:
            raise ValueError(f"不支持的数值类型: {type(value)}")
    
    def _parse_time_value(self, time_str: str) -> float:
        """解析时间值，返回秒数"""
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        time_str = time_str.strip().lower()
        
        # 时间单位转换
        time_units = {
            's': 1, 'sec': 1, 'second': 1, 'seconds': 1,
            'min': 60, 'minute': 60, 'minutes': 60,
            'h': 3600, 'hour': 3600, 'hours': 3600,
            'day': 86400, 'days': 86400,
            'week': 604800, 'weeks': 604800,
            'month': 2592000, 'months': 2592000,
            'year': 31536000, 'years': 31536000
        }
        
        import re
        match = re.match(r'^([\d.]+)\s*([a-zA-Z]+)$', time_str)
        if match:
            value, unit = match.groups()
            if unit in time_units:
                return float(value) * time_units[unit]
            else:
                raise ValueError(f"未知的时间单位: {unit}")
        else:
            # 尝试直接解析为数值（假设为秒）
            try:
                return float(time_str)
            except ValueError:
                raise ValueError(f"无效的时间格式: {time_str}")
    
    def auto_fix_issues(self, config: Dict[str, Any], 
                       issues: List[ValidationIssue]) -> Tuple[Dict[str, Any], List[str]]:
        """自动修复问题"""
        fixed_config = config.copy()
        fix_log = []
        
        for issue in issues:
            if issue.auto_fixable and issue.fix_data:
                try:
                    if issue.category == "structure":
                        fixed_config, log = self._fix_structure_issue(fixed_config, issue)
                        fix_log.extend(log)
                    elif issue.category == "components":
                        fixed_config, log = self._fix_component_issue(fixed_config, issue)
                        fix_log.extend(log)
                    elif issue.category == "simulation":
                        fixed_config, log = self._fix_simulation_issue(fixed_config, issue)
                        fix_log.extend(log)
                    elif issue.category == "parameters":
                        fixed_config, log = self._fix_parameter_issue(fixed_config, issue)
                        fix_log.extend(log)
                except Exception as e:
                    logger.warning(f"修复问题失败: {issue.message}, 错误: {str(e)}")
        
        return fixed_config, fix_log
    
    def _fix_structure_issue(self, config: Dict[str, Any], 
                           issue: ValidationIssue) -> Tuple[Dict[str, Any], List[str]]:
        """修复结构问题"""
        fix_log = []
        
        if "field" in issue.fix_data:
            field = issue.fix_data["field"]
            default_value = issue.fix_data.get("default_value", {})
            
            if field not in config:
                config[field] = default_value
                fix_log.append(f"添加缺失字段: {field}")
        
        return config, fix_log
    
    def _fix_component_issue(self, config: Dict[str, Any], 
                           issue: ValidationIssue) -> Tuple[Dict[str, Any], List[str]]:
        """修复组件问题"""
        fix_log = []
        
        if "component_id" in issue.fix_data and "parameter" in issue.fix_data:
            comp_id = issue.fix_data["component_id"]
            param = issue.fix_data["parameter"]
            param_type = issue.fix_data.get("param_type", "unknown")
            
            if comp_id in config.get("components", {}):
                # 添加默认参数值
                default_values = {
                    "capacity": "1000 m3",
                    "initial_level": "5 m",
                    "max_level": "10 m",
                    "min_level": "0 m",
                    "max_flow_rate": "10 m3/s",
                    "diameter": "0.5 m",
                    "length": "100 m",
                    "width": "5 m",
                    "depth": "2 m",
                    "max_head": "50 m",
                    "efficiency": "85%",
                    "power": "100 kW",
                    "pump_count": 2,
                    "opening": "50%",
                    "sensor_type": "level"
                }
                
                if param in default_values:
                    config["components"][comp_id][param] = default_values[param]
                    fix_log.append(f"为组件 {comp_id} 添加参数 {param}: {default_values[param]}")
        
        return config, fix_log
    
    def _fix_simulation_issue(self, config: Dict[str, Any], 
                            issue: ValidationIssue) -> Tuple[Dict[str, Any], List[str]]:
        """修复仿真问题"""
        fix_log = []
        
        if "default_simulation" in issue.fix_data:
            if "simulation" not in config:
                config["simulation"] = {}
            
            default_sim = issue.fix_data["default_simulation"]
            for key, value in default_sim.items():
                if key not in config["simulation"]:
                    config["simulation"][key] = value
                    fix_log.append(f"添加仿真参数 {key}: {value}")
        
        elif "parameter" in issue.fix_data:
            param = issue.fix_data["parameter"]
            default_values = {
                "duration": "1 hour",
                "time_step": "1 minute",
                "solver": "euler",
                "output_interval": "5 minutes"
            }
            
            if "simulation" not in config:
                config["simulation"] = {}
            
            if param in default_values:
                config["simulation"][param] = default_values[param]
                fix_log.append(f"添加仿真参数 {param}: {default_values[param]}")
        
        return config, fix_log
    
    def _fix_parameter_issue(self, config: Dict[str, Any], 
                           issue: ValidationIssue) -> Tuple[Dict[str, Any], List[str]]:
        """修复参数问题"""
        fix_log = []
        
        if "original_unit" in issue.fix_data and "valid_units" in issue.fix_data:
            # 单位转换修复
            original_unit = issue.fix_data["original_unit"]
            valid_units = issue.fix_data["valid_units"]
            param_type = issue.fix_data.get("param_type", "unknown")
            
            # 尝试找到最相似的单位
            similar_unit = self._find_similar_unit(original_unit, valid_units)
            if similar_unit:
                fix_log.append(f"建议将单位 '{original_unit}' 改为 '{similar_unit}'")
        
        return config, fix_log
    
    def _find_similar_unit(self, original_unit: str, valid_units: List[str]) -> Optional[str]:
        """查找相似单位"""
        original_lower = original_unit.lower()
        
        # 直接匹配
        for unit in valid_units:
            if unit.lower() == original_lower:
                return unit
        
        # 部分匹配
        for unit in valid_units:
            if original_lower in unit.lower() or unit.lower() in original_lower:
                return unit
        
        # 常见单位映射
        unit_mappings = {
            "meter": "m", "meters": "m", "metre": "m", "metres": "m",
            "liter": "L", "liters": "L", "litre": "L", "litres": "L",
            "second": "s", "seconds": "s", "sec": "s",
            "minute": "min", "minutes": "min", "mins": "min",
            "hour": "h", "hours": "h", "hr": "h", "hrs": "h",
            "watt": "W", "watts": "W", "kilowatt": "kW", "kilowatts": "kW",
            "pascal": "Pa", "pascals": "Pa", "kilopascal": "kPa", "kilopascals": "kPa",
            "percent": "%", "percentage": "%", "pct": "%"
        }
        
        mapped_unit = unit_mappings.get(original_lower)
        if mapped_unit and mapped_unit in valid_units:
            return mapped_unit
        
        return None

# 使用示例
if __name__ == "__main__":
    # 创建验证器
    validator = ComprehensiveConfigValidator(ValidationLevel.STANDARD)
    
    # 示例配置
    test_config = {
        "components": {
            "reservoir1": {
                "type": "Reservoir",
                "capacity": "1000 m3",
                "initial_level": "5 m",
                "max_level": "10 m",
                "min_level": "0 m"
            },
            "gate1": {
                "type": "Gate",
                "max_flow_rate": "50 m3/s"
            }
        },
        "connections": [
            {
                "source": "reservoir1",
                "target": "gate1",
                "type": "flow"
            }
        ],
        "simulation": {
            "duration": "2 hours",
            "time_step": "1 minute"
        }
    }
    
    # 验证配置
    result = validator.validate_config(test_config)
    
    print(f"验证结果: {'通过' if result.is_valid else '失败'}")
    print(f"得分: {result.score:.1f}/100")
    print(f"问题统计: {result.summary}")
    
    if result.issues:
        print("\n发现的问题:")
        for issue in result.issues:
            print(f"- [{issue.severity.value.upper()}] {issue.message} ({issue.location})")
    
    if result.recommendations:
        print("\n建议:")
        for rec in result.recommendations:
            print(f"- {rec}")
    
    # 自动修复
    if not result.is_valid:
        fixed_config, fix_log = validator.auto_fix_issues(test_config, result.issues)
        print("\n自动修复日志:")
        for log in fix_log:
            print(f"- {log}")