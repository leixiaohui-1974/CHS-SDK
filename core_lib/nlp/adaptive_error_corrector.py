#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应错误修正机制
自动识别和修复常见配置错误，提升配置生成的准确性和可靠性
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from dataclasses import dataclass
from enum import Enum
import difflib
from collections import defaultdict, Counter
import math

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """错误类型"""
    SPELLING = "spelling"  # 拼写错误
    UNIT = "unit"  # 单位错误
    VALUE_RANGE = "value_range"  # 数值范围错误
    TYPE_MISMATCH = "type_mismatch"  # 类型不匹配
    MISSING_PARAMETER = "missing_parameter"  # 缺失参数
    INVALID_CONNECTION = "invalid_connection"  # 无效连接
    INCONSISTENT_DATA = "inconsistent_data"  # 数据不一致
    NAMING_CONVENTION = "naming_convention"  # 命名规范
    DUPLICATE = "duplicate"  # 重复项
    DEPENDENCY = "dependency"  # 依赖关系错误

class CorrectionConfidence(Enum):
    """修正置信度"""
    HIGH = "high"  # 高置信度
    MEDIUM = "medium"  # 中等置信度
    LOW = "low"  # 低置信度
    UNCERTAIN = "uncertain"  # 不确定

@dataclass
class ErrorPattern:
    """错误模式"""
    pattern: str
    error_type: ErrorType
    description: str
    correction_rule: str
    confidence: CorrectionConfidence
    examples: List[str]

@dataclass
class CorrectionSuggestion:
    """修正建议"""
    error_type: ErrorType
    location: str
    original_value: Any
    suggested_value: Any
    confidence: CorrectionConfidence
    reason: str
    auto_applicable: bool = False
    alternatives: List[Any] = None

@dataclass
class CorrectionResult:
    """修正结果"""
    corrected_config: Dict[str, Any]
    applied_corrections: List[CorrectionSuggestion]
    pending_suggestions: List[CorrectionSuggestion]
    correction_log: List[str]
    confidence_score: float

class AdaptiveErrorCorrector:
    """自适应错误修正器"""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.correction_rules = self._initialize_correction_rules()
        self.domain_knowledge = self._initialize_domain_knowledge()
        self.learning_data = self._initialize_learning_data()
        
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """初始化错误模式"""
        patterns = [
            # 拼写错误模式
            ErrorPattern(
                pattern=r"水库|水庫|shuiku|reservoir",
                error_type=ErrorType.SPELLING,
                description="水库拼写变体",
                correction_rule="统一为'Reservoir'",
                confidence=CorrectionConfidence.HIGH,
                examples=["水庫", "shuiku", "reservoir"]
            ),
            ErrorPattern(
                pattern=r"闸门|閘門|zhamen|gate",
                error_type=ErrorType.SPELLING,
                description="闸门拼写变体",
                correction_rule="统一为'Gate'",
                confidence=CorrectionConfidence.HIGH,
                examples=["閘門", "zhamen", "gate"]
            ),
            ErrorPattern(
                pattern=r"泵站|泵房|pumpstation|pump_station",
                error_type=ErrorType.SPELLING,
                description="泵站拼写变体",
                correction_rule="统一为'PumpStation'",
                confidence=CorrectionConfidence.HIGH,
                examples=["泵房", "pumpstation", "pump_station"]
            ),
            ErrorPattern(
                pattern=r"管道|管線|pipeline|pipe",
                error_type=ErrorType.SPELLING,
                description="管道拼写变体",
                correction_rule="统一为'Pipe'",
                confidence=CorrectionConfidence.HIGH,
                examples=["管線", "pipeline", "pipe"]
            ),
            ErrorPattern(
                pattern=r"渠道|水渠|canal|channel",
                error_type=ErrorType.SPELLING,
                description="渠道拼写变体",
                correction_rule="统一为'Canal'",
                confidence=CorrectionConfidence.HIGH,
                examples=["水渠", "canal", "channel"]
            ),
            
            # 单位错误模式
            ErrorPattern(
                pattern=r"\d+\s*(立方米|m³|cubic\s*meter|cbm)",
                error_type=ErrorType.UNIT,
                description="体积单位变体",
                correction_rule="统一为'm3'",
                confidence=CorrectionConfidence.HIGH,
                examples=["1000立方米", "1000m³", "1000 cubic meter"]
            ),
            ErrorPattern(
                pattern=r"\d+\s*(升/秒|l/s|liter/s|liters/second)",
                error_type=ErrorType.UNIT,
                description="流量单位变体",
                correction_rule="统一为'L/s'",
                confidence=CorrectionConfidence.HIGH,
                examples=["100升/秒", "100l/s", "100 liter/s"]
            ),
            ErrorPattern(
                pattern=r"\d+\s*(米|meter|metres?)",
                error_type=ErrorType.UNIT,
                description="长度单位变体",
                correction_rule="统一为'm'",
                confidence=CorrectionConfidence.HIGH,
                examples=["10米", "10 meter", "10 metres"]
            ),
            ErrorPattern(
                pattern=r"\d+\s*(千瓦|kw|kilowatt)",
                error_type=ErrorType.UNIT,
                description="功率单位变体",
                correction_rule="统一为'kW'",
                confidence=CorrectionConfidence.HIGH,
                examples=["100千瓦", "100kw", "100 kilowatt"]
            ),
            
            # 数值范围错误模式
            ErrorPattern(
                pattern=r"capacity.*[0-9]+\s*[a-zA-Z]*",
                error_type=ErrorType.VALUE_RANGE,
                description="容量数值检查",
                correction_rule="检查容量是否在合理范围内",
                confidence=CorrectionConfidence.MEDIUM,
                examples=["capacity: 0", "capacity: 1e20"]
            ),
            ErrorPattern(
                pattern=r"efficiency.*[0-9]+",
                error_type=ErrorType.VALUE_RANGE,
                description="效率数值检查",
                correction_rule="效率应在0-100%之间",
                confidence=CorrectionConfidence.HIGH,
                examples=["efficiency: 150", "efficiency: -10"]
            ),
            
            # 类型不匹配模式
            ErrorPattern(
                pattern=r"\"\d+\"",
                error_type=ErrorType.TYPE_MISMATCH,
                description="数值被错误地设为字符串",
                correction_rule="转换为数值类型",
                confidence=CorrectionConfidence.HIGH,
                examples=["\"100\"", "\"3.14\""]
            ),
            
            # 命名规范模式
            ErrorPattern(
                pattern=r"[a-zA-Z]+\d+",
                error_type=ErrorType.NAMING_CONVENTION,
                description="组件命名规范",
                correction_rule="使用下划线分隔",
                confidence=CorrectionConfidence.MEDIUM,
                examples=["reservoir1", "gate2", "pump3"]
            )
        ]
        return patterns
    
    def _initialize_correction_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化修正规则"""
        rules = {
            "component_type_mapping": {
                # 中文到英文映射
                "水库": "Reservoir", "水庫": "Reservoir", "蓄水池": "Reservoir",
                "闸门": "Gate", "閘門": "Gate", "水闸": "Gate", "闸": "Gate",
                "泵": "Pump", "水泵": "Pump", "抽水机": "Pump",
                "泵站": "PumpStation", "泵房": "PumpStation", "抽水站": "PumpStation",
                "阀门": "Valve", "阀": "Valve", "调节阀": "Valve",
                "管道": "Pipe", "管子": "Pipe", "水管": "Pipe", "管線": "Pipe",
                "渠道": "Canal", "水渠": "Canal", "明渠": "Canal",
                "传感器": "Sensor", "探测器": "Sensor", "监测器": "Sensor",
                "水轮机": "WaterTurbine", "涡轮机": "WaterTurbine", "发电机": "WaterTurbine",
                
                # 英文变体映射
                "reservoir": "Reservoir", "tank": "Reservoir", "basin": "Reservoir",
                "gate": "Gate", "sluice": "Gate", "weir": "Gate",
                "pump": "Pump", "pumping": "Pump",
                "pumpstation": "PumpStation", "pump_station": "PumpStation",
                "valve": "Valve", "control_valve": "Valve",
                "pipe": "Pipe", "pipeline": "Pipe", "conduit": "Pipe",
                "canal": "Canal", "channel": "Canal", "waterway": "Canal",
                "sensor": "Sensor", "monitor": "Sensor", "detector": "Sensor",
                "turbine": "WaterTurbine", "generator": "WaterTurbine"
            },
            
            "unit_standardization": {
                # 体积单位
                "立方米": "m3", "m³": "m3", "cubic meter": "m3", "cbm": "m3",
                "升": "L", "liter": "L", "litre": "L",
                "毫升": "mL", "milliliter": "mL", "ml": "mL",
                
                # 流量单位
                "立方米每秒": "m3/s", "m³/s": "m3/s", "cms": "m3/s",
                "升每秒": "L/s", "l/s": "L/s", "liter/s": "L/s",
                "立方米每小时": "m3/h", "m³/h": "m3/h",
                "升每分钟": "L/min", "l/min": "L/min", "lpm": "L/min",
                
                # 长度单位
                "米": "m", "meter": "m", "metre": "m",
                "厘米": "cm", "centimeter": "cm", "centimetre": "cm",
                "毫米": "mm", "millimeter": "mm", "millimetre": "mm",
                "千米": "km", "kilometer": "km", "kilometre": "km",
                "英尺": "ft", "foot": "ft", "feet": "ft",
                "英寸": "in", "inch": "in", "inches": "in",
                
                # 压力单位
                "帕斯卡": "Pa", "pascal": "Pa",
                "千帕": "kPa", "kilopascal": "kPa",
                "兆帕": "MPa", "megapascal": "MPa",
                "巴": "bar", "大气压": "atm", "atmosphere": "atm",
                "磅每平方英寸": "psi", "pounds per square inch": "psi",
                
                # 功率单位
                "瓦特": "W", "watt": "W", "w": "W",
                "千瓦": "kW", "kilowatt": "kW", "kw": "kW",
                "兆瓦": "MW", "megawatt": "MW", "mw": "MW",
                "马力": "hp", "horsepower": "hp",
                
                # 时间单位
                "秒": "s", "second": "s", "seconds": "s", "sec": "s",
                "分钟": "min", "minute": "min", "minutes": "min", "mins": "min",
                "小时": "h", "hour": "h", "hours": "h", "hr": "h", "hrs": "h",
                "天": "day", "days": "day", "日": "day",
                "年": "year", "years": "year", "yr": "year", "yrs": "year",
                
                # 百分比单位
                "百分比": "%", "percent": "%", "percentage": "%", "pct": "%"
            },
            
            "parameter_ranges": {
                "capacity": {"min": 0.1, "max": 1e12, "unit": "m3"},
                "flow_rate": {"min": 0.001, "max": 10000, "unit": "m3/s"},
                "level": {"min": 0, "max": 1000, "unit": "m"},
                "diameter": {"min": 0.01, "max": 10, "unit": "m"},
                "length": {"min": 0.1, "max": 100000, "unit": "m"},
                "width": {"min": 0.1, "max": 1000, "unit": "m"},
                "depth": {"min": 0.1, "max": 100, "unit": "m"},
                "head": {"min": 0.1, "max": 2000, "unit": "m"},
                "efficiency": {"min": 0, "max": 100, "unit": "%"},
                "power": {"min": 1, "max": 1e12, "unit": "W"},
                "pressure": {"min": 0, "max": 1e9, "unit": "Pa"},
                "opening": {"min": 0, "max": 100, "unit": "%"},
                "speed": {"min": 0, "max": 10000, "unit": "rpm"},
                "temperature": {"min": -50, "max": 200, "unit": "°C"},
                "roughness": {"min": 0, "max": 0.1, "unit": "m"},
                "slope": {"min": 0, "max": 0.5, "unit": "m/m"}
            },
            
            "naming_conventions": {
                "component_prefix": {
                    "Reservoir": "res",
                    "Gate": "gate",
                    "Pump": "pump",
                    "PumpStation": "ps",
                    "Valve": "valve",
                    "Pipe": "pipe",
                    "Canal": "canal",
                    "Sensor": "sensor",
                    "WaterTurbine": "turbine"
                },
                "separator": "_",
                "case_style": "snake_case"  # snake_case, camelCase, PascalCase
            }
        }
        return rules
    
    def _initialize_domain_knowledge(self) -> Dict[str, Any]:
        """初始化领域知识"""
        knowledge = {
            "typical_values": {
                "Reservoir": {
                    "capacity": {"small": "1000 m3", "medium": "100000 m3", "large": "10000000 m3"},
                    "initial_level": {"low": "2 m", "medium": "10 m", "high": "50 m"},
                    "max_level": {"low": "5 m", "medium": "20 m", "high": "100 m"}
                },
                "Gate": {
                    "max_flow_rate": {"small": "1 m3/s", "medium": "10 m3/s", "large": "100 m3/s"},
                    "opening": {"closed": "0%", "half": "50%", "full": "100%"}
                },
                "Pump": {
                    "max_flow_rate": {"small": "0.1 m3/s", "medium": "1 m3/s", "large": "10 m3/s"},
                    "max_head": {"low": "10 m", "medium": "50 m", "high": "200 m"},
                    "efficiency": {"poor": "60%", "good": "80%", "excellent": "90%"}
                },
                "Pipe": {
                    "diameter": {"small": "0.1 m", "medium": "0.5 m", "large": "2 m"},
                    "length": {"short": "10 m", "medium": "100 m", "long": "1000 m"}
                }
            },
            
            "engineering_constraints": {
                "flow_velocity": {
                    "pipe": {"min": 0.5, "max": 3.0, "unit": "m/s"},
                    "canal": {"min": 0.3, "max": 2.0, "unit": "m/s"}
                },
                "pressure_drop": {
                    "valve": {"max_ratio": 0.3},  # 最大压降比例
                    "pipe": {"max_gradient": 100}  # 最大压力梯度 Pa/m
                },
                "efficiency_ranges": {
                    "pump": {"min": 60, "max": 95, "unit": "%"},
                    "turbine": {"min": 70, "max": 95, "unit": "%"},
                    "valve": {"min": 90, "max": 99, "unit": "%"}
                }
            },
            
            "common_errors": {
                "unit_confusion": [
                    {"wrong": "m³", "correct": "m3", "reason": "避免特殊字符"},
                    {"wrong": "l/s", "correct": "L/s", "reason": "升的标准符号是大写L"},
                    {"wrong": "kw", "correct": "kW", "reason": "千瓦的标准符号"},
                    {"wrong": "Mpa", "correct": "MPa", "reason": "兆帕的标准符号"}
                ],
                "value_errors": [
                    {"parameter": "efficiency", "wrong_range": ">100", "reason": "效率不能超过100%"},
                    {"parameter": "capacity", "wrong_range": "<=0", "reason": "容量必须为正值"},
                    {"parameter": "diameter", "wrong_range": "<=0", "reason": "直径必须为正值"},
                    {"parameter": "flow_rate", "wrong_range": "<0", "reason": "流量不能为负值"}
                ],
                "naming_errors": [
                    {"pattern": "reservoir1", "suggestion": "res_1", "reason": "使用下划线分隔"},
                    {"pattern": "Gate2", "suggestion": "gate_2", "reason": "使用小写和下划线"},
                    {"pattern": "pumpStation", "suggestion": "pump_station", "reason": "使用下划线分隔"}
                ]
            }
        }
        return knowledge
    
    def _initialize_learning_data(self) -> Dict[str, Any]:
        """初始化学习数据"""
        return {
            "correction_history": [],
            "user_preferences": {},
            "success_patterns": {},
            "failure_patterns": {},
            "confidence_adjustments": {}
        }
    
    def correct_config(self, config: Dict[str, Any], 
                      auto_apply: bool = True,
                      confidence_threshold: float = 0.8) -> CorrectionResult:
        """修正配置文件"""
        corrected_config = self._deep_copy_config(config)
        applied_corrections = []
        pending_suggestions = []
        correction_log = []
        
        # 1. 检测和修正拼写错误
        spelling_corrections = self._correct_spelling_errors(corrected_config)
        applied_corrections.extend(spelling_corrections)
        
        # 2. 标准化单位
        unit_corrections = self._standardize_units(corrected_config)
        applied_corrections.extend(unit_corrections)
        
        # 3. 修正数值范围错误
        range_corrections = self._correct_value_ranges(corrected_config)
        applied_corrections.extend(range_corrections)
        
        # 4. 修正类型不匹配
        type_corrections = self._correct_type_mismatches(corrected_config)
        applied_corrections.extend(type_corrections)
        
        # 5. 补充缺失参数
        missing_corrections = self._add_missing_parameters(corrected_config)
        applied_corrections.extend(missing_corrections)
        
        # 6. 修正无效连接
        connection_corrections = self._correct_invalid_connections(corrected_config)
        applied_corrections.extend(connection_corrections)
        
        # 7. 解决数据不一致
        consistency_corrections = self._resolve_data_inconsistencies(corrected_config)
        applied_corrections.extend(consistency_corrections)
        
        # 8. 标准化命名
        naming_corrections = self._standardize_naming(corrected_config)
        applied_corrections.extend(naming_corrections)
        
        # 9. 去除重复项
        duplicate_corrections = self._remove_duplicates(corrected_config)
        applied_corrections.extend(duplicate_corrections)
        
        # 10. 修正依赖关系
        dependency_corrections = self._correct_dependencies(corrected_config)
        applied_corrections.extend(dependency_corrections)
        
        # 过滤低置信度的修正
        if auto_apply:
            final_corrections = [c for c in applied_corrections 
                               if self._get_confidence_score(c.confidence) >= confidence_threshold]
            pending_suggestions = [c for c in applied_corrections 
                                 if self._get_confidence_score(c.confidence) < confidence_threshold]
        else:
            final_corrections = []
            pending_suggestions = applied_corrections
        
        # 应用修正
        for correction in final_corrections:
            self._apply_correction(corrected_config, correction)
            correction_log.append(f"应用修正: {correction.reason}")
        
        # 计算置信度分数
        confidence_score = self._calculate_overall_confidence(final_corrections, pending_suggestions)
        
        # 记录学习数据
        self._update_learning_data(applied_corrections, final_corrections)
        
        return CorrectionResult(
            corrected_config=corrected_config,
            applied_corrections=final_corrections,
            pending_suggestions=pending_suggestions,
            correction_log=correction_log,
            confidence_score=confidence_score
        )
    
    def _correct_spelling_errors(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """修正拼写错误"""
        corrections = []
        
        # 修正组件类型拼写
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                if 'type' in comp_data:
                    original_type = comp_data['type']
                    corrected_type = self._correct_component_type(original_type)
                    
                    if corrected_type != original_type:
                        corrections.append(CorrectionSuggestion(
                            error_type=ErrorType.SPELLING,
                            location=f"components.{comp_id}.type",
                            original_value=original_type,
                            suggested_value=corrected_type,
                            confidence=CorrectionConfidence.HIGH,
                            reason=f"修正组件类型拼写: {original_type} -> {corrected_type}",
                            auto_applicable=True
                        ))
        
        return corrections
    
    def _correct_component_type(self, component_type: str) -> str:
        """修正组件类型"""
        type_mapping = self.correction_rules['component_type_mapping']
        
        # 直接映射
        if component_type in type_mapping:
            return type_mapping[component_type]
        
        # 模糊匹配
        best_match = self._find_best_match(component_type, list(type_mapping.values()))
        if best_match and self._calculate_similarity(component_type, best_match) > 0.8:
            return best_match
        
        return component_type
    
    def _standardize_units(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """标准化单位"""
        corrections = []
        unit_mapping = self.correction_rules['unit_standardization']
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                for param_name, param_value in comp_data.items():
                    if isinstance(param_value, str) and self._has_unit(param_value):
                        standardized_value = self._standardize_unit_value(param_value, unit_mapping)
                        
                        if standardized_value != param_value:
                            corrections.append(CorrectionSuggestion(
                                error_type=ErrorType.UNIT,
                                location=f"components.{comp_id}.{param_name}",
                                original_value=param_value,
                                suggested_value=standardized_value,
                                confidence=CorrectionConfidence.HIGH,
                                reason=f"标准化单位: {param_value} -> {standardized_value}",
                                auto_applicable=True
                            ))
        
        return corrections
    
    def _correct_value_ranges(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """修正数值范围错误"""
        corrections = []
        ranges = self.correction_rules['parameter_ranges']
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                for param_name, param_value in comp_data.items():
                    if param_name in ranges:
                        range_info = ranges[param_name]
                        numeric_value = self._extract_numeric_value(param_value)
                        
                        if numeric_value is not None:
                            suggested_value = None
                            reason = ""
                            
                            if numeric_value < range_info['min']:
                                suggested_value = f"{range_info['min']} {range_info['unit']}"
                                reason = f"数值过小，建议最小值: {range_info['min']}"
                            elif numeric_value > range_info['max']:
                                suggested_value = f"{range_info['max']} {range_info['unit']}"
                                reason = f"数值过大，建议最大值: {range_info['max']}"
                            
                            if suggested_value:
                                corrections.append(CorrectionSuggestion(
                                    error_type=ErrorType.VALUE_RANGE,
                                    location=f"components.{comp_id}.{param_name}",
                                    original_value=param_value,
                                    suggested_value=suggested_value,
                                    confidence=CorrectionConfidence.MEDIUM,
                                    reason=reason,
                                    auto_applicable=False
                                ))
        
        return corrections
    
    def _correct_type_mismatches(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """修正类型不匹配"""
        corrections = []
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                for param_name, param_value in comp_data.items():
                    # 检查数值参数是否被错误地设为字符串
                    if isinstance(param_value, str) and self._should_be_numeric(param_name):
                        try:
                            numeric_value = float(param_value)
                            corrections.append(CorrectionSuggestion(
                                error_type=ErrorType.TYPE_MISMATCH,
                                location=f"components.{comp_id}.{param_name}",
                                original_value=param_value,
                                suggested_value=numeric_value,
                                confidence=CorrectionConfidence.HIGH,
                                reason=f"转换字符串数值为数值类型: '{param_value}' -> {numeric_value}",
                                auto_applicable=True
                            ))
                        except ValueError:
                            pass
        
        return corrections
    
    def _add_missing_parameters(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """补充缺失参数"""
        corrections = []
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                comp_type = comp_data.get('type')
                if comp_type in self.domain_knowledge['typical_values']:
                    typical_values = self.domain_knowledge['typical_values'][comp_type]
                    
                    for param_name, value_options in typical_values.items():
                        if param_name not in comp_data:
                            # 选择中等值作为默认值
                            default_value = value_options.get('medium', list(value_options.values())[0])
                            
                            corrections.append(CorrectionSuggestion(
                                error_type=ErrorType.MISSING_PARAMETER,
                                location=f"components.{comp_id}.{param_name}",
                                original_value=None,
                                suggested_value=default_value,
                                confidence=CorrectionConfidence.MEDIUM,
                                reason=f"添加缺失的参数 {param_name}",
                                auto_applicable=False
                            ))
        
        return corrections
    
    def _correct_invalid_connections(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """修正无效连接"""
        corrections = []
        
        if 'connections' in config:
            components = config.get('components', {})
            
            for i, connection in enumerate(config['connections']):
                # 检查连接的组件是否存在
                source = connection.get('source')
                target = connection.get('target')
                
                if source and source not in components:
                    # 尝试找到相似的组件名
                    similar_comp = self._find_similar_component(source, components.keys())
                    if similar_comp:
                        corrections.append(CorrectionSuggestion(
                            error_type=ErrorType.INVALID_CONNECTION,
                            location=f"connections[{i}].source",
                            original_value=source,
                            suggested_value=similar_comp,
                            confidence=CorrectionConfidence.MEDIUM,
                            reason=f"修正不存在的源组件: {source} -> {similar_comp}",
                            auto_applicable=False
                        ))
                
                if target and target not in components:
                    similar_comp = self._find_similar_component(target, components.keys())
                    if similar_comp:
                        corrections.append(CorrectionSuggestion(
                            error_type=ErrorType.INVALID_CONNECTION,
                            location=f"connections[{i}].target",
                            original_value=target,
                            suggested_value=similar_comp,
                            confidence=CorrectionConfidence.MEDIUM,
                            reason=f"修正不存在的目标组件: {target} -> {similar_comp}",
                            auto_applicable=False
                        ))
        
        return corrections
    
    def _resolve_data_inconsistencies(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """解决数据不一致"""
        corrections = []
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                # 检查水库水位关系
                if comp_data.get('type') == 'Reservoir':
                    inconsistencies = self._check_reservoir_level_consistency(comp_id, comp_data)
                    corrections.extend(inconsistencies)
                
                # 检查泵的效率和功率关系
                elif comp_data.get('type') in ['Pump', 'PumpStation']:
                    inconsistencies = self._check_pump_consistency(comp_id, comp_data)
                    corrections.extend(inconsistencies)
        
        return corrections
    
    def _standardize_naming(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """标准化命名"""
        corrections = []
        naming_rules = self.correction_rules['naming_conventions']
        
        if 'components' in config:
            for comp_id, comp_data in config['components'].items():
                comp_type = comp_data.get('type')
                if comp_type in naming_rules['component_prefix']:
                    suggested_name = self._generate_standard_name(comp_type, comp_id, naming_rules)
                    
                    if suggested_name != comp_id and self._is_naming_improvement(comp_id, suggested_name):
                        corrections.append(CorrectionSuggestion(
                            error_type=ErrorType.NAMING_CONVENTION,
                            location=f"components.{comp_id}",
                            original_value=comp_id,
                            suggested_value=suggested_name,
                            confidence=CorrectionConfidence.LOW,
                            reason=f"标准化组件命名: {comp_id} -> {suggested_name}",
                            auto_applicable=False
                        ))
        
        return corrections
    
    def _remove_duplicates(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """去除重复项"""
        corrections = []
        
        # 检查重复连接
        if 'connections' in config:
            seen_connections = set()
            duplicates = []
            
            for i, connection in enumerate(config['connections']):
                conn_key = (connection.get('source'), connection.get('target'), connection.get('type'))
                if conn_key in seen_connections:
                    duplicates.append(i)
                else:
                    seen_connections.add(conn_key)
            
            for dup_index in duplicates:
                corrections.append(CorrectionSuggestion(
                    error_type=ErrorType.DUPLICATE,
                    location=f"connections[{dup_index}]",
                    original_value=config['connections'][dup_index],
                    suggested_value=None,  # 表示删除
                    confidence=CorrectionConfidence.HIGH,
                    reason=f"移除重复连接",
                    auto_applicable=True
                ))
        
        return corrections
    
    def _correct_dependencies(self, config: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """修正依赖关系"""
        corrections = []
        
        # 检查泵是否有电源连接
        if 'components' in config and 'connections' in config:
            pumps = [comp_id for comp_id, comp_data in config['components'].items() 
                    if comp_data.get('type') in ['Pump', 'PumpStation']]
            
            power_connections = [conn for conn in config['connections'] 
                               if conn.get('type') == 'power']
            
            for pump_id in pumps:
                has_power = any(conn.get('target') == pump_id for conn in power_connections)
                if not has_power:
                    corrections.append(CorrectionSuggestion(
                        error_type=ErrorType.DEPENDENCY,
                        location=f"components.{pump_id}",
                        original_value=None,
                        suggested_value={
                            "source": "power_supply",
                            "target": pump_id,
                            "type": "power"
                        },
                        confidence=CorrectionConfidence.MEDIUM,
                        reason=f"泵 {pump_id} 需要电源连接",
                        auto_applicable=False
                    ))
        
        return corrections
    
    # 辅助方法
    def _deep_copy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝配置"""
        import copy
        return copy.deepcopy(config)
    
    def _has_unit(self, value: str) -> bool:
        """检查字符串是否包含单位"""
        return bool(re.search(r'\d+\s*[a-zA-Z/%]+', value))
    
    def _standardize_unit_value(self, value: str, unit_mapping: Dict[str, str]) -> str:
        """标准化单位值"""
        for old_unit, new_unit in unit_mapping.items():
            if old_unit in value:
                return value.replace(old_unit, new_unit)
        return value
    
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """提取数值"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            match = re.search(r'([\d.]+)', value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _should_be_numeric(self, param_name: str) -> bool:
        """判断参数是否应该是数值类型"""
        numeric_params = {
            'capacity', 'flow_rate', 'level', 'diameter', 'length', 'width', 'depth',
            'head', 'efficiency', 'power', 'pressure', 'opening', 'speed', 'temperature',
            'roughness', 'slope', 'count', 'rating', 'initial_level', 'max_level', 'min_level',
            'max_flow_rate', 'max_head', 'max_power', 'pump_count', 'backup_pumps'
        }
        return any(keyword in param_name.lower() for keyword in numeric_params)
    
    def _find_best_match(self, target: str, candidates: List[str]) -> Optional[str]:
        """找到最佳匹配"""
        if not candidates:
            return None
        
        matches = difflib.get_close_matches(target, candidates, n=1, cutoff=0.6)
        return matches[0] if matches else None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _find_similar_component(self, target: str, component_names: List[str]) -> Optional[str]:
        """找到相似的组件名"""
        return self._find_best_match(target, list(component_names))
    
    def _check_reservoir_level_consistency(self, comp_id: str, comp_data: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """检查水库水位一致性"""
        corrections = []
        
        levels = {}
        for level_type in ['initial_level', 'min_level', 'max_level']:
            if level_type in comp_data:
                levels[level_type] = self._extract_numeric_value(comp_data[level_type])
        
        if len(levels) >= 2:
            if 'min_level' in levels and 'max_level' in levels:
                if levels['min_level'] >= levels['max_level']:
                    corrections.append(CorrectionSuggestion(
                        error_type=ErrorType.INCONSISTENT_DATA,
                        location=f"components.{comp_id}.min_level",
                        original_value=comp_data['min_level'],
                        suggested_value=f"{levels['max_level'] * 0.1} m",
                        confidence=CorrectionConfidence.MEDIUM,
                        reason="最小水位应小于最大水位",
                        auto_applicable=False
                    ))
            
            if 'initial_level' in levels:
                min_val = levels.get('min_level', 0)
                max_val = levels.get('max_level', float('inf'))
                
                if levels['initial_level'] < min_val or levels['initial_level'] > max_val:
                    suggested_level = (min_val + max_val) / 2 if max_val != float('inf') else min_val + 5
                    corrections.append(CorrectionSuggestion(
                        error_type=ErrorType.INCONSISTENT_DATA,
                        location=f"components.{comp_id}.initial_level",
                        original_value=comp_data['initial_level'],
                        suggested_value=f"{suggested_level} m",
                        confidence=CorrectionConfidence.MEDIUM,
                        reason="初始水位应在最小和最大水位之间",
                        auto_applicable=False
                    ))
        
        return corrections
    
    def _check_pump_consistency(self, comp_id: str, comp_data: Dict[str, Any]) -> List[CorrectionSuggestion]:
        """检查泵的一致性"""
        corrections = []
        
        # 检查效率范围
        if 'efficiency' in comp_data:
            efficiency = self._extract_numeric_value(comp_data['efficiency'])
            if efficiency is not None and (efficiency <= 0 or efficiency > 100):
                corrections.append(CorrectionSuggestion(
                    error_type=ErrorType.INCONSISTENT_DATA,
                    location=f"components.{comp_id}.efficiency",
                    original_value=comp_data['efficiency'],
                    suggested_value="85%",
                    confidence=CorrectionConfidence.HIGH,
                    reason="泵效率应在0-100%之间",
                    auto_applicable=False
                ))
        
        return corrections
    
    def _generate_standard_name(self, comp_type: str, current_name: str, naming_rules: Dict[str, Any]) -> str:
        """生成标准名称"""
        prefix = naming_rules['component_prefix'].get(comp_type, comp_type.lower())
        separator = naming_rules['separator']
        
        # 提取数字后缀
        match = re.search(r'(\d+)$', current_name)
        suffix = match.group(1) if match else "1"
        
        return f"{prefix}{separator}{suffix}"
    
    def _is_naming_improvement(self, current_name: str, suggested_name: str) -> bool:
        """判断是否是命名改进"""
        # 如果当前名称已经符合规范，不建议修改
        if '_' in current_name and current_name.islower():
            return False
        
        # 如果建议名称更规范，则推荐
        return '_' in suggested_name and suggested_name.islower()
    
    def _get_confidence_score(self, confidence: CorrectionConfidence) -> float:
        """获取置信度分数"""
        scores = {
            CorrectionConfidence.HIGH: 0.9,
            CorrectionConfidence.MEDIUM: 0.7,
            CorrectionConfidence.LOW: 0.5,
            CorrectionConfidence.UNCERTAIN: 0.3
        }
        return scores.get(confidence, 0.5)
    
    def _apply_correction(self, config: Dict[str, Any], correction: CorrectionSuggestion) -> None:
        """应用修正"""
        location_parts = correction.location.split('.')
        
        # 导航到目标位置
        current = config
        for part in location_parts[:-1]:
            if '[' in part and ']' in part:
                # 处理数组索引
                key, index_str = part.split('[', 1)
                index = int(index_str.rstrip(']'))
                current = current[key][index]
            else:
                current = current[part]
        
        # 应用修正
        final_key = location_parts[-1]
        if correction.suggested_value is None:
            # 删除项
            if '[' in final_key and ']' in final_key:
                key, index_str = final_key.split('[', 1)
                index = int(index_str.rstrip(']'))
                del current[key][index]
            else:
                del current[final_key]
        else:
            # 修改值
            current[final_key] = correction.suggested_value
    
    def _calculate_overall_confidence(self, applied_corrections: List[CorrectionSuggestion],
                                    pending_suggestions: List[CorrectionSuggestion]) -> float:
        """计算整体置信度"""
        if not applied_corrections and not pending_suggestions:
            return 1.0  # 没有错误，完全置信
        
        total_corrections = len(applied_corrections) + len(pending_suggestions)
        applied_weight = sum(self._get_confidence_score(c.confidence) for c in applied_corrections)
        pending_weight = sum(self._get_confidence_score(c.confidence) * 0.5 for c in pending_suggestions)
        
        return (applied_weight + pending_weight) / total_corrections if total_corrections > 0 else 1.0
    
    def _update_learning_data(self, all_corrections: List[CorrectionSuggestion],
                            applied_corrections: List[CorrectionSuggestion]) -> None:
        """更新学习数据"""
        # 记录修正历史
        self.learning_data['correction_history'].extend([
            {
                'error_type': c.error_type.value,
                'confidence': c.confidence.value,
                'applied': c in applied_corrections,
                'location': c.location
            } for c in all_corrections
        ])
        
        # 更新成功模式
        for correction in applied_corrections:
            pattern_key = f"{correction.error_type.value}_{correction.confidence.value}"
            if pattern_key not in self.learning_data['success_patterns']:
                self.learning_data['success_patterns'][pattern_key] = 0
            self.learning_data['success_patterns'][pattern_key] += 1

# 使用示例
if __name__ == "__main__":
    corrector = AdaptiveErrorCorrector()
    
    # 示例配置（包含各种错误）
    test_config = {
        "components": {
            "reservoir1": {
                "type": "水库",  # 拼写错误
                "capacity": "1000立方米",  # 单位错误
                "initial_level": "15 m",  # 数值范围错误（超过max_level）
                "max_level": "10 m",
                "min_level": "0 m",
                "efficiency": "120"  # 类型错误和数值范围错误
            },
            "Gate2": {  # 命名规范错误
                "type": "gate",  # 拼写错误
                "max_flow_rate": "50 m3/s"
            }
        },
        "connections": [
            {
                "source": "reservoir1",
                "target": "gate1",  # 无效连接（gate1不存在）
                "type": "flow"
            },
            {
                "source": "reservoir1",
                "target": "Gate2",
                "type": "flow"
            },
            {
                "source": "reservoir1",  # 重复连接
                "target": "Gate2",
                "type": "flow"
            }
        ],
        "simulation": {
            "duration": "2 hours",
            "time_step": "1 minute"
        }
    }
    
    # 执行修正
    result = corrector.correct_config(test_config, auto_apply=True, confidence_threshold=0.7)
    
    print("=== 修正结果 ===")
    print(f"整体置信度: {result.confidence_score:.2f}")
    print(f"应用的修正数量: {len(result.applied_corrections)}")
    print(f"待处理建议数量: {len(result.pending_suggestions)}")
    
    print("\n=== 应用的修正 ===")
    for correction in result.applied_corrections:
        print(f"- {correction.reason} ({correction.location})")
    
    print("\n=== 待处理建议 ===")
    for suggestion in result.pending_suggestions:
        print(f"- {suggestion.reason} ({suggestion.location})")
        print(f"  原值: {suggestion.original_value} -> 建议值: {suggestion.suggested_value}")
    
    print("\n=== 修正后的配置 ===")
    print(json.dumps(result.corrected_config, indent=2, ensure_ascii=False))