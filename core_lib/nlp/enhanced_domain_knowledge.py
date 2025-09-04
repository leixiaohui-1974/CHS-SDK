#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的水利工程领域知识库
包含专业术语、标准参数范围、典型配置模式等领域知识
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from dataclasses import dataclass
from enum import Enum
import math

class ComponentCategory(Enum):
    """组件类别"""
    STORAGE = "storage"  # 蓄水设施
    CONTROL = "control"  # 控制设施
    CONVEYANCE = "conveyance"  # 输水设施
    POWER = "power"  # 动力设施
    MONITORING = "monitoring"  # 监测设施
    TREATMENT = "treatment"  # 处理设施
    PROTECTION = "protection"  # 防护设施

class ParameterType(Enum):
    """参数类型"""
    GEOMETRIC = "geometric"  # 几何参数
    HYDRAULIC = "hydraulic"  # 水力参数
    MECHANICAL = "mechanical"  # 机械参数
    ELECTRICAL = "electrical"  # 电气参数
    OPERATIONAL = "operational"  # 运行参数
    ENVIRONMENTAL = "environmental"  # 环境参数
    ECONOMIC = "economic"  # 经济参数

@dataclass
class ParameterSpec:
    """参数规格"""
    name: str
    type: ParameterType
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    typical_range: Optional[Tuple[float, float]] = None
    default_value: Optional[float] = None
    description: str = ""
    dependencies: List[str] = None
    calculation_formula: Optional[str] = None

@dataclass
class ComponentTemplate:
    """组件模板"""
    type: str
    category: ComponentCategory
    required_parameters: List[str]
    optional_parameters: List[str]
    parameter_specs: Dict[str, ParameterSpec]
    typical_configurations: List[Dict[str, Any]]
    engineering_constraints: List[str]
    common_connections: List[str]

class EnhancedDomainKnowledge:
    """增强的领域知识库"""
    
    def __init__(self):
        self.terminology = self._initialize_terminology()
        self.component_templates = self._initialize_component_templates()
        self.parameter_specifications = self._initialize_parameter_specifications()
        self.engineering_standards = self._initialize_engineering_standards()
        self.typical_configurations = self._initialize_typical_configurations()
        self.calculation_formulas = self._initialize_calculation_formulas()
        self.design_guidelines = self._initialize_design_guidelines()
        self.operational_patterns = self._initialize_operational_patterns()
    
    def _initialize_terminology(self) -> Dict[str, Dict[str, Any]]:
        """初始化专业术语库"""
        terminology = {
            # 水利工程基础术语
            "hydraulic_terms": {
                "流量": {"en": "flow_rate", "unit": "m3/s", "synonyms": ["流速", "水流量", "discharge"]},
                "水位": {"en": "water_level", "unit": "m", "synonyms": ["液位", "水深", "level"]},
                "水头": {"en": "head", "unit": "m", "synonyms": ["扬程", "压头", "hydraulic_head"]},
                "压力": {"en": "pressure", "unit": "Pa", "synonyms": ["水压", "压强", "hydraulic_pressure"]},
                "流速": {"en": "velocity", "unit": "m/s", "synonyms": ["速度", "水流速度", "flow_velocity"]},
                "流态": {"en": "flow_regime", "unit": "-", "synonyms": ["流动状态", "流型"]},
                "雷诺数": {"en": "reynolds_number", "unit": "-", "synonyms": ["Re", "reynolds"]},
                "弗劳德数": {"en": "froude_number", "unit": "-", "synonyms": ["Fr", "froude"]},
                "曼宁系数": {"en": "manning_coefficient", "unit": "-", "synonyms": ["糙率", "粗糙系数", "manning_n"]},
                "水力半径": {"en": "hydraulic_radius", "unit": "m", "synonyms": ["R", "hydraulic_R"]},
                "湿周": {"en": "wetted_perimeter", "unit": "m", "synonyms": ["润湿周长"]},
                "过流断面": {"en": "cross_section", "unit": "m2", "synonyms": ["断面面积", "流通面积"]},
                "比降": {"en": "slope", "unit": "m/m", "synonyms": ["坡度", "梯度", "gradient"]},
                "水力坡度": {"en": "hydraulic_slope", "unit": "m/m", "synonyms": ["能坡", "水面坡度"]},
                "临界流": {"en": "critical_flow", "unit": "-", "synonyms": ["临界状态"]},
                "超临界流": {"en": "supercritical_flow", "unit": "-", "synonyms": ["急流"]},
                "亚临界流": {"en": "subcritical_flow", "unit": "-", "synonyms": ["缓流"]}
            },
            
            # 水工建筑物术语
            "structure_terms": {
                "水库": {"en": "reservoir", "category": "storage", "synonyms": ["蓄水池", "水池", "库区"]},
                "大坝": {"en": "dam", "category": "control", "synonyms": ["坝体", "挡水坝"]},
                "闸门": {"en": "gate", "category": "control", "synonyms": ["水闸", "闸", "调节闸"]},
                "溢洪道": {"en": "spillway", "category": "control", "synonyms": ["泄洪道", "溢流道"]},
                "泵站": {"en": "pump_station", "category": "power", "synonyms": ["抽水站", "泵房"]},
                "水轮机": {"en": "turbine", "category": "power", "synonyms": ["涡轮机", "水轮发电机"]},
                "渠道": {"en": "canal", "category": "conveyance", "synonyms": ["水渠", "明渠", "输水渠"]},
                "管道": {"en": "pipe", "category": "conveyance", "synonyms": ["水管", "输水管", "压力管"]},
                "隧洞": {"en": "tunnel", "category": "conveyance", "synonyms": ["引水隧洞", "输水隧洞"]},
                "渡槽": {"en": "aqueduct", "category": "conveyance", "synonyms": ["水桥", "过水桥"]},
                "倒虹吸": {"en": "inverted_siphon", "category": "conveyance", "synonyms": ["虹吸管"]},
                "调压塔": {"en": "surge_tank", "category": "control", "synonyms": ["调压井", "平压塔"]},
                "前池": {"en": "forebay", "category": "storage", "synonyms": ["调节池", "蓄水池"]},
                "尾水渠": {"en": "tailrace", "category": "conveyance", "synonyms": ["尾水道", "排水渠"]},
                "鱼道": {"en": "fishway", "category": "protection", "synonyms": ["鱼梯", "过鱼设施"]}
            },
            
            # 机电设备术语
            "equipment_terms": {
                "水泵": {"en": "pump", "category": "power", "synonyms": ["泵", "离心泵", "轴流泵"]},
                "阀门": {"en": "valve", "category": "control", "synonyms": ["调节阀", "截止阀", "蝶阀"]},
                "变频器": {"en": "frequency_converter", "category": "electrical", "synonyms": ["变频调速器", "VFD"]},
                "电机": {"en": "motor", "category": "electrical", "synonyms": ["电动机", "马达"]},
                "传感器": {"en": "sensor", "category": "monitoring", "synonyms": ["探测器", "检测器"]},
                "流量计": {"en": "flowmeter", "category": "monitoring", "synonyms": ["流量传感器", "流量表"]},
                "压力表": {"en": "pressure_gauge", "category": "monitoring", "synonyms": ["压力计", "压力传感器"]},
                "液位计": {"en": "level_gauge", "category": "monitoring", "synonyms": ["水位计", "液位传感器"]},
                "控制柜": {"en": "control_cabinet", "category": "electrical", "synonyms": ["电控柜", "配电柜"]},
                "PLC": {"en": "plc", "category": "electrical", "synonyms": ["可编程控制器", "programmable_logic_controller"]},
                "SCADA": {"en": "scada", "category": "monitoring", "synonyms": ["数据采集与监视控制系统"]},
                "HMI": {"en": "hmi", "category": "monitoring", "synonyms": ["人机界面", "操作界面"]}
            },
            
            # 水文气象术语
            "hydro_terms": {
                "降雨量": {"en": "rainfall", "unit": "mm", "synonyms": ["降水量", "雨量"]},
                "蒸发量": {"en": "evaporation", "unit": "mm", "synonyms": ["蒸发"]},
                "径流": {"en": "runoff", "unit": "m3/s", "synonyms": ["地表径流", "河川径流"]},
                "入流": {"en": "inflow", "unit": "m3/s", "synonyms": ["来水", "入库流量"]},
                "出流": {"en": "outflow", "unit": "m3/s", "synonyms": ["出库流量", "下泄流量"]},
                "洪峰": {"en": "flood_peak", "unit": "m3/s", "synonyms": ["洪峰流量", "最大流量"]},
                "枯水期": {"en": "dry_season", "unit": "-", "synonyms": ["枯季", "低水期"]},
                "丰水期": {"en": "wet_season", "unit": "-", "synonyms": ["汛期", "高水期"]},
                "调蓄": {"en": "regulation", "unit": "m3", "synonyms": ["调节", "蓄水调节"]},
                "库容": {"en": "storage_capacity", "unit": "m3", "synonyms": ["蓄水量", "库容量"]},
                "死库容": {"en": "dead_storage", "unit": "m3", "synonyms": ["死水位以下库容"]},
                "有效库容": {"en": "active_storage", "unit": "m3", "synonyms": ["调节库容", "兴利库容"]},
                "防洪库容": {"en": "flood_control_storage", "unit": "m3", "synonyms": ["防洪调节库容"]}
            },
            
            # 工程管理术语
            "management_terms": {
                "调度": {"en": "operation", "synonyms": ["运行调度", "水库调度"]},
                "优化": {"en": "optimization", "synonyms": ["最优化", "寻优"]},
                "仿真": {"en": "simulation", "synonyms": ["模拟", "数值模拟"]},
                "预报": {"en": "forecast", "synonyms": ["预测", "水文预报"]},
                "预警": {"en": "warning", "synonyms": ["报警", "预警系统"]},
                "监控": {"en": "monitoring", "synonyms": ["监测", "实时监控"]},
                "自动化": {"en": "automation", "synonyms": ["自动控制", "智能化"]},
                "远程控制": {"en": "remote_control", "synonyms": ["遥控", "远程操作"]},
                "数据采集": {"en": "data_acquisition", "synonyms": ["数据收集", "信息采集"]},
                "故障诊断": {"en": "fault_diagnosis", "synonyms": ["故障检测", "异常诊断"]}
            }
        }
        return terminology
    
    def _initialize_component_templates(self) -> Dict[str, ComponentTemplate]:
        """初始化组件模板"""
        templates = {}
        
        # 水库模板
        templates["Reservoir"] = ComponentTemplate(
            type="Reservoir",
            category=ComponentCategory.STORAGE,
            required_parameters=["capacity", "initial_level", "max_level"],
            optional_parameters=["min_level", "dead_level", "flood_level", "area", "length", "width", "depth"],
            parameter_specs={
                "capacity": ParameterSpec(
                    name="库容", type=ParameterType.GEOMETRIC, unit="m3",
                    min_value=100, max_value=1e12, typical_range=(1000, 1e9),
                    description="水库总库容"
                ),
                "initial_level": ParameterSpec(
                    name="初始水位", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=0, max_value=1000, typical_range=(5, 100),
                    description="仿真开始时的水位"
                ),
                "max_level": ParameterSpec(
                    name="最高水位", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=1, max_value=1000, typical_range=(10, 200),
                    description="水库设计最高水位"
                ),
                "min_level": ParameterSpec(
                    name="最低水位", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=0, max_value=500, typical_range=(1, 50),
                    description="水库最低运行水位"
                ),
                "dead_level": ParameterSpec(
                    name="死水位", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=0, max_value=100, typical_range=(0.5, 20),
                    description="死库容对应的水位"
                ),
                "flood_level": ParameterSpec(
                    name="防洪限制水位", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=1, max_value=500, typical_range=(10, 150),
                    description="防洪调度的限制水位"
                )
            },
            typical_configurations=[
                {"type": "small", "capacity": "10000 m3", "max_level": "10 m"},
                {"type": "medium", "capacity": "1000000 m3", "max_level": "50 m"},
                {"type": "large", "capacity": "100000000 m3", "max_level": "150 m"}
            ],
            engineering_constraints=[
                "初始水位应在最低和最高水位之间",
                "死水位应低于最低运行水位",
                "防洪限制水位应低于最高水位"
            ],
            common_connections=["Gate", "Spillway", "Pump", "Turbine", "Canal", "Pipe"]
        )
        
        # 闸门模板
        templates["Gate"] = ComponentTemplate(
            type="Gate",
            category=ComponentCategory.CONTROL,
            required_parameters=["max_flow_rate", "opening"],
            optional_parameters=["width", "height", "type", "control_mode", "response_time"],
            parameter_specs={
                "max_flow_rate": ParameterSpec(
                    name="最大过流能力", type=ParameterType.HYDRAULIC, unit="m3/s",
                    min_value=0.1, max_value=10000, typical_range=(1, 1000),
                    description="闸门全开时的最大过流能力"
                ),
                "opening": ParameterSpec(
                    name="开度", type=ParameterType.OPERATIONAL, unit="%",
                    min_value=0, max_value=100, typical_range=(0, 100),
                    default_value=50, description="闸门当前开度百分比"
                ),
                "width": ParameterSpec(
                    name="闸门宽度", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.5, max_value=50, typical_range=(2, 20),
                    description="闸门净宽"
                ),
                "height": ParameterSpec(
                    name="闸门高度", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.5, max_value=30, typical_range=(1, 10),
                    description="闸门净高"
                )
            },
            typical_configurations=[
                {"type": "small", "max_flow_rate": "5 m3/s", "width": "2 m", "height": "2 m"},
                {"type": "medium", "max_flow_rate": "50 m3/s", "width": "5 m", "height": "5 m"},
                {"type": "large", "max_flow_rate": "500 m3/s", "width": "15 m", "height": "10 m"}
            ],
            engineering_constraints=[
                "开度应在0-100%之间",
                "最大流量与闸门尺寸应匹配",
                "响应时间应合理"
            ],
            common_connections=["Reservoir", "Canal", "Pipe", "River"]
        )
        
        # 泵站模板
        templates["PumpStation"] = ComponentTemplate(
            type="PumpStation",
            category=ComponentCategory.POWER,
            required_parameters=["pump_count", "max_flow_rate", "max_head", "efficiency"],
            optional_parameters=["power", "speed", "impeller_diameter", "backup_pumps", "control_mode"],
            parameter_specs={
                "pump_count": ParameterSpec(
                    name="水泵台数", type=ParameterType.MECHANICAL, unit="台",
                    min_value=1, max_value=20, typical_range=(1, 8),
                    description="泵站内水泵总台数"
                ),
                "max_flow_rate": ParameterSpec(
                    name="设计流量", type=ParameterType.HYDRAULIC, unit="m3/s",
                    min_value=0.01, max_value=1000, typical_range=(0.1, 100),
                    description="单台泵或泵站总设计流量"
                ),
                "max_head": ParameterSpec(
                    name="设计扬程", type=ParameterType.HYDRAULIC, unit="m",
                    min_value=1, max_value=2000, typical_range=(10, 200),
                    description="水泵设计扬程"
                ),
                "efficiency": ParameterSpec(
                    name="效率", type=ParameterType.MECHANICAL, unit="%",
                    min_value=50, max_value=95, typical_range=(70, 90),
                    description="水泵效率"
                ),
                "power": ParameterSpec(
                    name="功率", type=ParameterType.ELECTRICAL, unit="kW",
                    min_value=1, max_value=50000, typical_range=(10, 5000),
                    description="电机额定功率",
                    calculation_formula="P = ρ * g * Q * H / η"
                )
            },
            typical_configurations=[
                {"type": "small", "pump_count": 2, "max_flow_rate": "0.5 m3/s", "max_head": "20 m", "efficiency": "75%"},
                {"type": "medium", "pump_count": 4, "max_flow_rate": "5 m3/s", "max_head": "50 m", "efficiency": "85%"},
                {"type": "large", "pump_count": 6, "max_flow_rate": "50 m3/s", "max_head": "100 m", "efficiency": "90%"}
            ],
            engineering_constraints=[
                "效率应在合理范围内",
                "功率与流量扬程应匹配",
                "备用泵数量应合理"
            ],
            common_connections=["Reservoir", "Canal", "Pipe", "PowerSupply"]
        )
        
        # 管道模板
        templates["Pipe"] = ComponentTemplate(
            type="Pipe",
            category=ComponentCategory.CONVEYANCE,
            required_parameters=["diameter", "length", "roughness"],
            optional_parameters=["material", "thickness", "slope", "max_pressure", "insulation"],
            parameter_specs={
                "diameter": ParameterSpec(
                    name="管径", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.05, max_value=10, typical_range=(0.1, 3),
                    description="管道内径"
                ),
                "length": ParameterSpec(
                    name="长度", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=1, max_value=100000, typical_range=(10, 5000),
                    description="管道长度"
                ),
                "roughness": ParameterSpec(
                    name="粗糙度", type=ParameterType.HYDRAULIC, unit="mm",
                    min_value=0.01, max_value=10, typical_range=(0.1, 2),
                    description="管道内壁绝对粗糙度"
                ),
                "slope": ParameterSpec(
                    name="坡度", type=ParameterType.GEOMETRIC, unit="m/m",
                    min_value=-0.1, max_value=0.5, typical_range=(0, 0.01),
                    description="管道纵坡"
                )
            },
            typical_configurations=[
                {"type": "small", "diameter": "0.2 m", "length": "100 m", "roughness": "0.5 mm"},
                {"type": "medium", "diameter": "1 m", "length": "1000 m", "roughness": "1 mm"},
                {"type": "large", "diameter": "3 m", "length": "5000 m", "roughness": "2 mm"}
            ],
            engineering_constraints=[
                "流速应在合理范围内(0.5-3 m/s)",
                "压力损失应可接受",
                "管径与流量应匹配"
            ],
            common_connections=["Reservoir", "PumpStation", "Valve", "Junction"]
        )
        
        # 渠道模板
        templates["Canal"] = ComponentTemplate(
            type="Canal",
            category=ComponentCategory.CONVEYANCE,
            required_parameters=["width", "depth", "length", "slope", "roughness"],
            optional_parameters=["side_slope", "lining_type", "freeboard", "design_flow"],
            parameter_specs={
                "width": ParameterSpec(
                    name="渠底宽", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.5, max_value=100, typical_range=(1, 20),
                    description="渠道底部宽度"
                ),
                "depth": ParameterSpec(
                    name="设计水深", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.2, max_value=20, typical_range=(0.5, 5),
                    description="渠道设计水深"
                ),
                "length": ParameterSpec(
                    name="长度", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=10, max_value=200000, typical_range=(100, 10000),
                    description="渠道长度"
                ),
                "slope": ParameterSpec(
                    name="纵坡", type=ParameterType.GEOMETRIC, unit="m/m",
                    min_value=0.0001, max_value=0.1, typical_range=(0.001, 0.01),
                    description="渠道纵向坡度"
                ),
                "roughness": ParameterSpec(
                    name="糙率", type=ParameterType.HYDRAULIC, unit="-",
                    min_value=0.01, max_value=0.1, typical_range=(0.02, 0.05),
                    description="曼宁糙率系数"
                )
            },
            typical_configurations=[
                {"type": "small", "width": "2 m", "depth": "1 m", "length": "500 m", "slope": "0.002"},
                {"type": "medium", "width": "5 m", "depth": "2 m", "length": "2000 m", "slope": "0.001"},
                {"type": "large", "width": "15 m", "depth": "5 m", "length": "10000 m", "slope": "0.0005"}
            ],
            engineering_constraints=[
                "流速应在合理范围内(0.3-2 m/s)",
                "弗劳德数应小于1(亚临界流)",
                "边坡应稳定"
            ],
            common_connections=["Reservoir", "Gate", "Pump", "Junction"]
        )
        
        # 阀门模板
        templates["Valve"] = ComponentTemplate(
            type="Valve",
            category=ComponentCategory.CONTROL,
            required_parameters=["diameter", "opening", "cv_value"],
            optional_parameters=["type", "material", "max_pressure", "control_mode", "response_time"],
            parameter_specs={
                "diameter": ParameterSpec(
                    name="公称直径", type=ParameterType.GEOMETRIC, unit="m",
                    min_value=0.02, max_value=3, typical_range=(0.05, 1),
                    description="阀门公称直径"
                ),
                "opening": ParameterSpec(
                    name="开度", type=ParameterType.OPERATIONAL, unit="%",
                    min_value=0, max_value=100, typical_range=(0, 100),
                    default_value=100, description="阀门开度百分比"
                ),
                "cv_value": ParameterSpec(
                    name="流量系数", type=ParameterType.HYDRAULIC, unit="-",
                    min_value=0.1, max_value=10000, typical_range=(1, 1000),
                    description="阀门流量系数"
                )
            },
            typical_configurations=[
                {"type": "small", "diameter": "0.1 m", "cv_value": "10"},
                {"type": "medium", "diameter": "0.5 m", "cv_value": "100"},
                {"type": "large", "diameter": "1.5 m", "cv_value": "1000"}
            ],
            engineering_constraints=[
                "开度应在0-100%之间",
                "压降应在合理范围内",
                "流量系数应与阀门类型匹配"
            ],
            common_connections=["Pipe", "PumpStation", "Reservoir"]
        )
        
        # 传感器模板
        templates["Sensor"] = ComponentTemplate(
            type="Sensor",
            category=ComponentCategory.MONITORING,
            required_parameters=["sensor_type", "measurement_range", "accuracy"],
            optional_parameters=["response_time", "output_signal", "power_supply", "communication_protocol"],
            parameter_specs={
                "measurement_range": ParameterSpec(
                    name="测量范围", type=ParameterType.OPERATIONAL, unit="-",
                    description="传感器测量范围"
                ),
                "accuracy": ParameterSpec(
                    name="精度", type=ParameterType.OPERATIONAL, unit="%",
                    min_value=0.1, max_value=10, typical_range=(0.5, 2),
                    description="测量精度"
                ),
                "response_time": ParameterSpec(
                    name="响应时间", type=ParameterType.OPERATIONAL, unit="s",
                    min_value=0.001, max_value=60, typical_range=(0.1, 5),
                    description="传感器响应时间"
                )
            },
            typical_configurations=[
                {"type": "flow", "sensor_type": "electromagnetic", "accuracy": "0.5%"},
                {"type": "level", "sensor_type": "ultrasonic", "accuracy": "1%"},
                {"type": "pressure", "sensor_type": "piezoresistive", "accuracy": "0.25%"}
            ],
            engineering_constraints=[
                "精度应满足工程要求",
                "测量范围应覆盖工况",
                "响应时间应适当"
            ],
            common_connections=["ControlSystem", "DataLogger", "SCADA"]
        )
        
        return templates
    
    def _initialize_parameter_specifications(self) -> Dict[str, ParameterSpec]:
        """初始化参数规格库"""
        specs = {}
        
        # 从组件模板中提取所有参数规格
        for template in self.component_templates.values():
            specs.update(template.parameter_specs)
        
        # 添加通用参数规格
        common_specs = {
            "flow_rate": ParameterSpec(
                name="流量", type=ParameterType.HYDRAULIC, unit="m3/s",
                min_value=0, max_value=10000, typical_range=(0.1, 1000),
                description="体积流量"
            ),
            "velocity": ParameterSpec(
                name="流速", type=ParameterType.HYDRAULIC, unit="m/s",
                min_value=0, max_value=20, typical_range=(0.5, 5),
                description="平均流速"
            ),
            "pressure": ParameterSpec(
                name="压力", type=ParameterType.HYDRAULIC, unit="Pa",
                min_value=0, max_value=1e8, typical_range=(1e4, 1e6),
                description="静压力"
            ),
            "temperature": ParameterSpec(
                name="温度", type=ParameterType.ENVIRONMENTAL, unit="°C",
                min_value=-50, max_value=200, typical_range=(0, 50),
                description="水温或环境温度"
            ),
            "density": ParameterSpec(
                name="密度", type=ParameterType.ENVIRONMENTAL, unit="kg/m3",
                min_value=800, max_value=1200, typical_range=(990, 1010),
                default_value=1000, description="水的密度"
            ),
            "viscosity": ParameterSpec(
                name="粘度", type=ParameterType.ENVIRONMENTAL, unit="Pa·s",
                min_value=1e-6, max_value=1e-2, typical_range=(1e-6, 1e-3),
                default_value=1e-6, description="动力粘度"
            )
        }
        
        specs.update(common_specs)
        return specs
    
    def _initialize_engineering_standards(self) -> Dict[str, Dict[str, Any]]:
        """初始化工程标准"""
        standards = {
            "design_standards": {
                "flow_velocity": {
                    "pipe": {"min": 0.5, "max": 3.0, "optimal": 1.5, "unit": "m/s"},
                    "canal": {"min": 0.3, "max": 2.0, "optimal": 1.0, "unit": "m/s"},
                    "tunnel": {"min": 1.0, "max": 5.0, "optimal": 2.5, "unit": "m/s"}
                },
                "pump_efficiency": {
                    "centrifugal": {"min": 60, "max": 90, "optimal": 80, "unit": "%"},
                    "axial": {"min": 70, "max": 95, "optimal": 85, "unit": "%"},
                    "mixed_flow": {"min": 65, "max": 88, "optimal": 78, "unit": "%"}
                },
                "pipe_roughness": {
                    "steel": {"new": 0.05, "used": 0.2, "old": 1.0, "unit": "mm"},
                    "concrete": {"smooth": 0.2, "normal": 1.0, "rough": 3.0, "unit": "mm"},
                    "cast_iron": {"new": 0.25, "used": 1.0, "old": 2.5, "unit": "mm"},
                    "pvc": {"new": 0.01, "used": 0.05, "old": 0.1, "unit": "mm"}
                },
                "canal_manning": {
                    "concrete_lined": {"smooth": 0.012, "normal": 0.015, "rough": 0.018},
                    "earth": {"clean": 0.025, "normal": 0.030, "weedy": 0.040},
                    "rock": {"smooth": 0.030, "jagged": 0.040, "boulder": 0.050},
                    "natural": {"straight": 0.030, "winding": 0.040, "sluggish": 0.070}
                }
            },
            
            "safety_factors": {
                "structural": {"concrete": 2.5, "steel": 2.0, "earth": 1.5},
                "hydraulic": {"normal": 1.2, "flood": 1.5, "extreme": 2.0},
                "mechanical": {"pump": 1.3, "valve": 1.5, "gate": 2.0}
            },
            
            "design_criteria": {
                "reservoir": {
                    "freeboard": {"min": 0.5, "normal": 1.0, "max": 3.0, "unit": "m"},
                    "dead_storage_ratio": {"min": 0.05, "normal": 0.10, "max": 0.20},
                    "flood_storage_ratio": {"min": 0.10, "normal": 0.20, "max": 0.40}
                },
                "pump_station": {
                    "redundancy": {"min": 1, "normal": 2, "critical": 3, "unit": "pumps"},
                    "capacity_factor": {"min": 1.2, "normal": 1.5, "max": 2.0},
                    "efficiency_threshold": {"min": 70, "target": 85, "unit": "%"}
                },
                "gate": {
                    "discharge_coefficient": {"sharp_crested": 0.6, "broad_crested": 0.85, "sluice": 0.95},
                    "submergence_ratio": {"free": 0.0, "partial": 0.7, "full": 1.0}
                }
            }
        }
        return standards
    
    def _initialize_typical_configurations(self) -> Dict[str, List[Dict[str, Any]]]:
        """初始化典型配置模式"""
        configurations = {
            "irrigation_system": [
                {
                    "name": "小型灌溉系统",
                    "components": {
                        "reservoir": {"capacity": "50000 m3", "max_level": "15 m"},
                        "pump_station": {"pump_count": 2, "max_flow_rate": "2 m3/s", "max_head": "30 m"},
                        "main_canal": {"width": "3 m", "depth": "1.5 m", "length": "2000 m"},
                        "distribution_pipes": {"diameter": "0.3 m", "length": "5000 m"}
                    },
                    "connections": [
                        {"source": "reservoir", "target": "pump_station", "type": "flow"},
                        {"source": "pump_station", "target": "main_canal", "type": "flow"},
                        {"source": "main_canal", "target": "distribution_pipes", "type": "flow"}
                    ]
                },
                {
                    "name": "大型灌溉系统",
                    "components": {
                        "reservoir": {"capacity": "10000000 m3", "max_level": "80 m"},
                        "pump_station": {"pump_count": 6, "max_flow_rate": "20 m3/s", "max_head": "60 m"},
                        "main_canal": {"width": "10 m", "depth": "4 m", "length": "15000 m"},
                        "secondary_canals": {"width": "5 m", "depth": "2 m", "length": "30000 m"},
                        "control_gates": {"max_flow_rate": "50 m3/s", "width": "8 m"}
                    }
                }
            ],
            
            "flood_control_system": [
                {
                    "name": "城市防洪系统",
                    "components": {
                        "retention_pond": {"capacity": "500000 m3", "max_level": "25 m"},
                        "spillway": {"max_flow_rate": "200 m3/s", "width": "20 m"},
                        "pump_station": {"pump_count": 4, "max_flow_rate": "15 m3/s", "max_head": "20 m"},
                        "drainage_pipes": {"diameter": "2 m", "length": "10000 m"}
                    }
                }
            ],
            
            "water_supply_system": [
                {
                    "name": "城市供水系统",
                    "components": {
                        "raw_water_reservoir": {"capacity": "2000000 m3", "max_level": "40 m"},
                        "treatment_plant": {"capacity": "100000 m3/day"},
                        "clear_water_reservoir": {"capacity": "50000 m3", "max_level": "20 m"},
                        "high_lift_pumps": {"pump_count": 4, "max_flow_rate": "3 m3/s", "max_head": "80 m"},
                        "distribution_network": {"total_length": "200000 m", "pressure_zones": 3}
                    }
                }
            ],
            
            "hydropower_system": [
                {
                    "name": "小水电站",
                    "components": {
                        "reservoir": {"capacity": "5000000 m3", "max_level": "60 m"},
                        "intake": {"max_flow_rate": "50 m3/s"},
                        "penstock": {"diameter": "3 m", "length": "1000 m"},
                        "turbine": {"type": "Francis", "rated_power": "5000 kW", "efficiency": "90%"},
                        "tailrace": {"width": "8 m", "length": "500 m"}
                    }
                }
            ]
        }
        return configurations
    
    def _initialize_calculation_formulas(self) -> Dict[str, Dict[str, str]]:
        """初始化计算公式"""
        formulas = {
            "hydraulic_formulas": {
                "continuity_equation": "Q = A * V",  # 流量 = 面积 × 流速
                "bernoulli_equation": "H1 + V1²/(2g) + P1/(ρg) = H2 + V2²/(2g) + P2/(ρg) + hf",
                "darcy_weisbach": "hf = f * (L/D) * (V²/(2g))",  # 沿程损失
                "manning_equation": "V = (1/n) * R^(2/3) * S^(1/2)",  # 曼宁公式
                "hazen_williams": "V = 0.849 * C * R^0.63 * S^0.54",  # 海曾-威廉公式
                "orifice_equation": "Q = Cd * A * sqrt(2gh)",  # 孔口出流
                "weir_equation": "Q = Cd * L * H^(3/2)",  # 堰流公式
                "pump_power": "P = ρ * g * Q * H / η",  # 泵功率
                "reynolds_number": "Re = ρ * V * D / μ",  # 雷诺数
                "froude_number": "Fr = V / sqrt(g * h)",  # 弗劳德数
                "hydraulic_radius": "R = A / P",  # 水力半径
                "critical_depth": "hc = (Q² / (g * B²))^(1/3)",  # 临界水深
                "specific_energy": "E = h + V²/(2g)",  # 比能
                "momentum_equation": "F = ρ * Q * (V2 - V1)",  # 动量方程
                "pipe_friction_factor": "f = 64/Re (laminar), f = 0.316/Re^0.25 (turbulent)"
            },
            
            "pump_formulas": {
                "affinity_laws_flow": "Q2/Q1 = (N2/N1) * (D2/D1)³",
                "affinity_laws_head": "H2/H1 = (N2/N1)² * (D2/D1)²",
                "affinity_laws_power": "P2/P1 = (N2/N1)³ * (D2/D1)⁵",
                "specific_speed": "Ns = N * sqrt(Q) / H^(3/4)",
                "suction_specific_speed": "S = N * sqrt(Q) / NPSH^(3/4)",
                "pump_efficiency": "η = (ρ * g * Q * H) / P",
                "npsh_required": "NPSH = (P_atm - P_vapor)/ρg + V²/(2g) - H_suction"
            },
            
            "reservoir_formulas": {
                "storage_equation": "dS/dt = I - O - E",  # 水量平衡
                "level_storage_relation": "S = f(H)",  # 库容-水位关系
                "evaporation": "E = A * e",  # 蒸发量
                "seepage": "S = k * A * sqrt(h)",  # 渗漏量
                "residence_time": "T = V / Q",  # 停留时间
                "turnover_rate": "R = Q / V",  # 换水率
            },
            
            "channel_formulas": {
                "manning_open_channel": "Q = (1/n) * A * R^(2/3) * S^(1/2)",
                "chezy_equation": "V = C * sqrt(R * S)",
                "critical_slope": "Sc = n² * g / (R^(4/3) * V²)",
                "normal_depth": "yn = (Q * n / (S^(1/2) * B))^(3/5)",
                "hydraulic_jump": "h2/h1 = 0.5 * (-1 + sqrt(1 + 8*Fr1²))",
                "gradually_varied_flow": "dy/dx = (S0 - Sf) / (1 - Fr²)"
            },
            
            "gate_formulas": {
                "free_flow": "Q = Cd * A * sqrt(2gh)",
                "submerged_flow": "Q = Cd * A * sqrt(2g(h1-h2))",
                "gate_coefficient": "Cd = f(opening_ratio, submergence)",
                "contraction_coefficient": "Cc = effective_area / gate_area",
                "velocity_coefficient": "Cv = actual_velocity / theoretical_velocity"
            }
        }
        return formulas
    
    def _initialize_design_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """初始化设计指南"""
        guidelines = {
            "reservoir_design": {
                "capacity_determination": {
                    "method": "mass_curve_analysis",
                    "safety_factor": 1.2,
                    "dead_storage_ratio": 0.1,
                    "flood_storage_ratio": 0.2
                },
                "geometry": {
                    "length_width_ratio": {"min": 2, "max": 5, "optimal": 3},
                    "side_slope": {"earth": "1:3", "rock": "1:1.5", "concrete": "1:0.5"},
                    "freeboard": {"normal": "1.0 m", "flood": "1.5 m", "extreme": "2.0 m"}
                },
                "outlet_works": {
                    "number_of_outlets": {"min": 1, "recommended": 2, "large_reservoir": 3},
                    "capacity_ratio": 0.1,  # 出口能力与库容的比例
                    "elevation": "multiple_levels"
                }
            },
            
            "pump_station_design": {
                "pump_selection": {
                    "specific_speed_range": {"centrifugal": "500-4000", "axial": "4000-20000"},
                    "efficiency_target": 85,
                    "npsh_margin": 1.5
                },
                "layout": {
                    "pump_spacing": "2 * pump_diameter",
                    "suction_pipe_velocity": {"max": 2.0, "recommended": 1.5},
                    "discharge_pipe_velocity": {"max": 3.0, "recommended": 2.0}
                },
                "redundancy": {
                    "backup_pumps": {"small": 1, "medium": 2, "large": 3},
                    "capacity_factor": 1.3,  # 总能力与需求的比例
                    "maintenance_allowance": 0.2
                }
            },
            
            "canal_design": {
                "cross_section": {
                    "trapezoidal": {"side_slope": "1:1.5 to 1:3", "bottom_width": "0.5 to 20 m"},
                    "rectangular": {"width_depth_ratio": "2:1 to 4:1"},
                    "triangular": {"side_slope": "1:1 to 1:2"}
                },
                "hydraulic_design": {
                    "velocity_range": {"min": 0.3, "max": 2.0, "optimal": 1.0},
                    "froude_number": {"max": 0.8, "recommended": 0.5},
                    "freeboard": {"small": "0.3 m", "medium": "0.5 m", "large": "1.0 m"}
                },
                "lining": {
                    "concrete": {"thickness": "0.1-0.3 m", "roughness": 0.015},
                    "stone": {"thickness": "0.3-0.5 m", "roughness": 0.025},
                    "earth": {"compaction": "95%", "roughness": 0.030}
                }
            },
            
            "pipe_design": {
                "sizing": {
                    "velocity_range": {"min": 0.5, "max": 3.0, "economic": 1.5},
                    "diameter_calculation": "D = sqrt(4Q/(π*V))",
                    "pressure_rating": "1.5 * max_operating_pressure"
                },
                "layout": {
                    "minimum_cover": "1.0 m",
                    "maximum_slope": "30%",
                    "bend_radius": "5 * diameter",
                    "support_spacing": "function_of_diameter_and_material"
                },
                "materials": {
                    "steel": {"pressure": "high", "diameter": "large", "cost": "high"},
                    "concrete": {"pressure": "medium", "diameter": "large", "cost": "medium"},
                    "pvc": {"pressure": "low", "diameter": "small", "cost": "low"},
                    "hdpe": {"pressure": "medium", "diameter": "medium", "cost": "medium"}
                }
            }
        }
        return guidelines
    
    def _initialize_operational_patterns(self) -> Dict[str, Dict[str, Any]]:
        """初始化运行模式"""
        patterns = {
            "pump_operation": {
                "constant_speed": {
                    "description": "恒速运行",
                    "efficiency": "medium",
                    "control_complexity": "low",
                    "energy_consumption": "high",
                    "applications": ["简单系统", "负荷稳定"]
                },
                "variable_speed": {
                    "description": "变频调速",
                    "efficiency": "high",
                    "control_complexity": "medium",
                    "energy_consumption": "low",
                    "applications": ["负荷变化", "节能要求"]
                },
                "staged_operation": {
                    "description": "分级运行",
                    "efficiency": "medium",
                    "control_complexity": "high",
                    "energy_consumption": "medium",
                    "applications": ["多泵系统", "负荷分级"]
                }
            },
            
            "reservoir_operation": {
                "flood_control": {
                    "priority": "safety",
                    "target_level": "flood_control_level",
                    "release_strategy": "maximum_safe_discharge",
                    "season": "flood_season"
                },
                "water_supply": {
                    "priority": "reliability",
                    "target_level": "normal_pool_level",
                    "release_strategy": "demand_based",
                    "season": "dry_season"
                },
                "power_generation": {
                    "priority": "efficiency",
                    "target_level": "optimal_head",
                    "release_strategy": "peak_shaving",
                    "season": "all_year"
                },
                "multi_purpose": {
                    "priority": "balanced",
                    "target_level": "rule_curve",
                    "release_strategy": "optimization_based",
                    "season": "all_year"
                }
            },
            
            "gate_operation": {
                "manual": {
                    "control_type": "human_operated",
                    "response_time": "minutes",
                    "precision": "low",
                    "cost": "low"
                },
                "automatic": {
                    "control_type": "sensor_based",
                    "response_time": "seconds",
                    "precision": "high",
                    "cost": "high"
                },
                "remote": {
                    "control_type": "scada_controlled",
                    "response_time": "seconds",
                    "precision": "medium",
                    "cost": "medium"
                }
            },
            
            "system_operation": {
                "normal": {
                    "description": "正常运行模式",
                    "efficiency_target": 85,
                    "maintenance_schedule": "planned",
                    "monitoring_level": "standard"
                },
                "emergency": {
                    "description": "应急运行模式",
                    "efficiency_target": 70,
                    "maintenance_schedule": "deferred",
                    "monitoring_level": "intensive"
                },
                "maintenance": {
                    "description": "维护模式",
                    "efficiency_target": 0,
                    "maintenance_schedule": "active",
                    "monitoring_level": "minimal"
                }
            }
        }
        return patterns
    
    def get_component_template(self, component_type: str) -> Optional[ComponentTemplate]:
        """获取组件模板"""
        return self.component_templates.get(component_type)
    
    def get_parameter_spec(self, parameter_name: str) -> Optional[ParameterSpec]:
        """获取参数规格"""
        return self.parameter_specifications.get(parameter_name)
    
    def get_typical_value(self, component_type: str, parameter_name: str) -> Optional[float]:
        """获取典型值"""
        template = self.get_component_template(component_type)
        if template and parameter_name in template.parameter_specs:
            spec = template.parameter_specs[parameter_name]
            if spec.typical_range:
                return (spec.typical_range[0] + spec.typical_range[1]) / 2
            return spec.default_value
        return None
    
    def validate_parameter_value(self, component_type: str, parameter_name: str, value: float) -> bool:
        """验证参数值是否合理"""
        template = self.get_component_template(component_type)
        if template and parameter_name in template.parameter_specs:
            spec = template.parameter_specs[parameter_name]
            if spec.min_value is not None and value < spec.min_value:
                return False
            if spec.max_value is not None and value > spec.max_value:
                return False
            return True
        return True
    
    def get_engineering_constraint(self, component_type: str) -> List[str]:
        """获取工程约束"""
        template = self.get_component_template(component_type)
        return template.engineering_constraints if template else []
    
    def get_common_connections(self, component_type: str) -> List[str]:
        """获取常见连接"""
        template = self.get_component_template(component_type)
        return template.common_connections if template else []
    
    def search_terminology(self, term: str) -> Dict[str, Any]:
        """搜索术语"""
        term_lower = term.lower()
        results = {}
        
        for category, terms in self.terminology.items():
            for key, info in terms.items():
                if (term_lower in key.lower() or 
                    term_lower in info.get('en', '').lower() or
                    any(term_lower in syn.lower() for syn in info.get('synonyms', []))):
                    results[key] = info
                    results[key]['category'] = category
        
        return results
    
    def get_calculation_formula(self, formula_name: str) -> Optional[str]:
        """获取计算公式"""
        for category, formulas in self.calculation_formulas.items():
            if formula_name in formulas:
                return formulas[formula_name]
        return None
    
    def get_design_guideline(self, component_type: str, aspect: str) -> Optional[Dict[str, Any]]:
        """获取设计指南"""
        guidelines_key = f"{component_type.lower()}_design"
        if guidelines_key in self.design_guidelines:
            return self.design_guidelines[guidelines_key].get(aspect)
        return None
    
    def get_operational_pattern(self, component_type: str, pattern_name: str) -> Optional[Dict[str, Any]]:
        """获取运行模式"""
        operation_key = f"{component_type.lower()}_operation"
        if operation_key in self.operational_patterns:
            return self.operational_patterns[operation_key].get(pattern_name)
        return None
    
    def suggest_typical_configuration(self, system_type: str, scale: str = "medium") -> Optional[Dict[str, Any]]:
        """建议典型配置"""
        if system_type in self.typical_configurations:
            configs = self.typical_configurations[system_type]
            for config in configs:
                if scale in config.get('name', '').lower():
                    return config
            return configs[0] if configs else None
        return None
    
    def get_engineering_standard(self, category: str, item: str) -> Optional[Dict[str, Any]]:
        """获取工程标准"""
        if category in self.engineering_standards:
            return self.engineering_standards[category].get(item)
        return None
    
    def calculate_parameter(self, formula_name: str, **kwargs) -> Optional[float]:
        """根据公式计算参数"""
        formula = self.get_calculation_formula(formula_name)
        if not formula:
            return None
        
        try:
            # 简单的公式计算实现
            if formula_name == "pump_power":
                # P = ρ * g * Q * H / η
                rho = kwargs.get('density', 1000)  # kg/m³
                g = 9.81  # m/s²
                Q = kwargs.get('flow_rate', 0)  # m³/s
                H = kwargs.get('head', 0)  # m
                eta = kwargs.get('efficiency', 0.8)  # 效率
                return rho * g * Q * H / eta / 1000  # kW
            
            elif formula_name == "reynolds_number":
                # Re = ρ * V * D / μ
                rho = kwargs.get('density', 1000)
                V = kwargs.get('velocity', 0)
                D = kwargs.get('diameter', 0)
                mu = kwargs.get('viscosity', 1e-6)
                return rho * V * D / mu
            
            elif formula_name == "froude_number":
                # Fr = V / sqrt(g * h)
                V = kwargs.get('velocity', 0)
                h = kwargs.get('depth', 0)
                g = 9.81
                return V / math.sqrt(g * h) if h > 0 else 0
            
            elif formula_name == "hydraulic_radius":
                # R = A / P
                A = kwargs.get('area', 0)
                P = kwargs.get('perimeter', 0)
                return A / P if P > 0 else 0
            
        except (ZeroDivisionError, ValueError, TypeError):
            return None
        
        return None
    
    def get_component_category(self, component_type: str) -> Optional[ComponentCategory]:
        """获取组件类别"""
        template = self.get_component_template(component_type)
        return template.category if template else None
    
    def get_parameter_type(self, parameter_name: str) -> Optional[ParameterType]:
        """获取参数类型"""
        spec = self.get_parameter_spec(parameter_name)
        return spec.type if spec else None
    
    def get_unit_conversion_factor(self, from_unit: str, to_unit: str) -> Optional[float]:
        """获取单位转换系数"""
        # 简化的单位转换
        conversions = {
            ('m3/s', 'L/s'): 1000,
            ('L/s', 'm3/s'): 0.001,
            ('m3/h', 'm3/s'): 1/3600,
            ('m3/s', 'm3/h'): 3600,
            ('kPa', 'Pa'): 1000,
            ('Pa', 'kPa'): 0.001,
            ('MPa', 'Pa'): 1e6,
            ('Pa', 'MPa'): 1e-6,
            ('mm', 'm'): 0.001,
            ('m', 'mm'): 1000,
            ('cm', 'm'): 0.01,
            ('m', 'cm'): 100,
            ('kW', 'W'): 1000,
            ('W', 'kW'): 0.001,
            ('MW', 'kW'): 1000,
            ('kW', 'MW'): 0.001
        }
        
        return conversions.get((from_unit, to_unit))
    
    def export_knowledge_summary(self) -> Dict[str, Any]:
        """导出知识库摘要"""
        summary = {
            "terminology_count": sum(len(terms) for terms in self.terminology.values()),
            "component_templates_count": len(self.component_templates),
            "parameter_specifications_count": len(self.parameter_specifications),
            "calculation_formulas_count": sum(len(formulas) for formulas in self.calculation_formulas.values()),
            "typical_configurations_count": sum(len(configs) for configs in self.typical_configurations.values()),
            "categories": {
                "terminology": list(self.terminology.keys()),
                "component_types": list(self.component_templates.keys()),
                "formula_categories": list(self.calculation_formulas.keys()),
                "configuration_types": list(self.typical_configurations.keys())
            }
        }
        return summary

# 全局实例
enhanced_domain_knowledge = EnhancedDomainKnowledge()