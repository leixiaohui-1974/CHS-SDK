#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言到配置文件转换器

这个模块提供了从自然语言描述生成CHS-SDK配置文件的功能，支持所有配置文件类型：
1. 传统多配置文件方式（config.yml, components.yml, topology.yml, agents.yml）
2. 统一配置文件方式（unified_config.yml）
3. 通用配置文件方式（universal_config.yml）
4. 硬编码方式（Python代码生成）

主要功能：
- 解析自然语言描述
- 提取系统组件和参数
- 生成对应的配置文件
- 支持多种输出格式
- 提供配置验证功能

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import os
import sys
import yaml
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
import logging
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.config.unified_config_manager import ConfigType

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType
from core_lib.nlp.config_to_language_converter import NaturalLanguageDescription

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ComponentInfo:
    """组件信息数据类"""
    name: str
    type: str
    parameters: Dict[str, Any]
    initial_state: Dict[str, Any] = None
    
@dataclass
class AgentInfo:
    """智能体信息数据类"""
    name: str
    type: str
    target_component: str
    parameters: Dict[str, Any]
    
@dataclass
class ConnectionInfo:
    """连接信息数据类"""
    from_component: str
    to_component: str
    connection_type: str = "flow"
    parameters: Dict[str, Any] = None

class LanguageToConfigConverter:
    """自然语言到配置文件转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = UnifiedConfigManager()
        
        # 中文到英文组件类型映射（包括英文类名的直接映射）
        self.component_type_reverse_map = {
            # 基础水利设施
            '水库': 'Reservoir',
            '蓄水池': 'Reservoir',
            '水池': 'Reservoir',
            '湖泊': 'Lake',
            '池塘': 'Pond',
            
            # 控制设施
            '闸门': 'Gate',
            '水闸': 'Gate',
            '闸': 'Gate',
            '调节闸': 'Gate',
            '泄洪闸': 'Gate',
            '进水闸': 'Gate',
            '出水闸': 'Gate',
            
            # 泵站设施
            '水泵': 'Pump',
            '泵': 'Pump',
            '泵站': 'PumpStation',
            '抽水站': 'PumpStation',
            '提升泵站': 'PumpStation',
            
            # 阀门设施
            '阀门': 'Valve',
            '阀': 'Valve',
            '调节阀': 'Valve',
            '控制阀': 'Valve',
            '阀站': 'ValveStation',
            
            # 输水设施
            '管道': 'Pipe',
            '管': 'Pipe',
            '输水管': 'Pipe',
            '压力管': 'Pipe',
            '渠道': 'Canal',
            '渠': 'Canal',
            '输水渠': 'Canal',
            '统一渠道': 'UnifiedCanal',
            '河道': 'RiverChannel',
            '河': 'RiverChannel',
            '河流': 'RiverChannel',
            '水道': 'RiverChannel',
            
            # 连接设施
            '汇流点': 'Junction',
            '分流点': 'Junction',
            '节点': 'Junction',
            '连接点': 'Junction',
            
            # 监测设施
            '传感器': 'Sensor',
            '水位计': 'Sensor',
            '流量计': 'Sensor',
            '压力计': 'Sensor',
            '监测点': 'Sensor',
            
            # 发电设施
            '水轮机': 'WaterTurbine',
            '水电站': 'HydropowerStation',
            '发电机组': 'HydropowerStation',
            '机组': 'HydropowerStation',
            
            # 控制系统
            '受控系统': 'ControlledSystem',
            '控制系统': 'ControlledSystem',
            '被控对象': 'ControlledSystem',
            '水轮机': 'WaterTurbine',
            '水轮机组': 'TurbineStation',
            # 添加英文类名的直接映射
            'Reservoir': 'Reservoir',
            'Gate': 'Gate',
            'Pump': 'Pump',
            'PumpStation': 'Pump',
            'Valve': 'Valve',
            'ValveStation': 'Valve',
            'Pipe': 'Pipe',
            'Canal': 'Canal',
            'UnifiedCanal': 'Canal',
            'Channel': 'Channel',
            'RiverChannel': 'Channel',
            'IntegralDelayCanal': 'Canal',
            'Junction': 'Junction',
            'Sensor': 'Sensor',
            'DisturbanceNode': 'DisturbanceNode',
            'ControlledSystem': 'ControlledSystem',
            'WaterTurbine': 'ControlledSystem',
            'TurbineStation': 'ControlledSystem'
        }
        
        # 中文到英文智能体类型映射
        self.agent_type_reverse_map = {
            'PID控制智能体': 'PIDAgent',
            '模型预测控制智能体': 'MPCAgent',
            '中心MPC调度智能体': 'CentralMPCAgent',
            '模糊控制智能体': 'FuzzyAgent',
            '神经网络控制智能体': 'NeuralAgent',
            '优化控制智能体': 'OptimizationAgent',
            '规则控制智能体': 'RuleBasedAgent',
            '自适应控制智能体': 'AdaptiveAgent',
            '学习型智能体': 'LearningAgent',
            '协作智能体': 'CooperativeAgent'
        }
        
        # 控制策略映射
        self.control_strategy_reverse_map = {
            'PID控制': 'pid',
            '模型预测控制': 'mpc',
            '模糊控制': 'fuzzy',
            '神经网络控制': 'neural',
            '优化控制': 'optimization',
            '规则控制': 'rule_based',
            '自适应控制': 'adaptive',
            '集中式控制': 'centralized',
            '分布式控制': 'distributed',
            '分层控制': 'hierarchical'
        }
        
        # 默认参数模板
        self.default_parameters = {
            'Reservoir': {
                'capacity': 1000000,  # 库容 (m³)
                'initial_level': 50,   # 初始水位 (m)
                'min_level': 10,       # 最低水位 (m)
                'max_level': 100,      # 最高水位 (m)
                'area': 10000,         # 水面面积 (m²)
                'inflow': 0,           # 初始入流 (m³/s)
                'outflow': 0           # 初始出流 (m³/s)
            },
            'Lake': {
                'capacity': 5000000,   # 湖泊容量 (m³)
                'initial_level': 30,   # 初始水位 (m)
                'min_level': 5,        # 最低水位 (m)
                'max_level': 50,       # 最高水位 (m)
                'area': 50000          # 水面面积 (m²)
            },
            'Pond': {
                'capacity': 100000,    # 池塘容量 (m³)
                'initial_level': 10,   # 初始水位 (m)
                'min_level': 2,        # 最低水位 (m)
                'max_level': 15,       # 最高水位 (m)
                'area': 5000           # 水面面积 (m²)
            },
            'Gate': {
                'max_flow': 1000,      # 最大流量 (m³/s)
                'initial_opening': 0.5, # 初始开度
                'min_opening': 0,      # 最小开度
                'max_opening': 1,      # 最大开度
                'width': 10,           # 闸门宽度 (m)
                'height': 5,           # 闸门高度 (m)
                'discharge_coeff': 0.6 # 流量系数
            },
            'Pump': {
                'max_flow': 500,       # 最大流量 (m³/s)
                'efficiency': 0.85,    # 效率
                'power': 1000,         # 功率 (kW)
                'initial_speed': 0,    # 初始转速
                'head': 50,            # 扬程 (m)
                'response_time': 10    # 响应时间 (s)
            },
            'PumpStation': {
                'pump_count': 3,       # 泵机数量
                'max_flow': 1500,      # 总最大流量 (m³/s)
                'efficiency': 0.85,    # 效率
                'power': 3000,         # 总功率 (kW)
                'head': 50             # 扬程 (m)
            },
            'Valve': {
                'max_flow': 800,       # 最大流量 (m³/s)
                'initial_opening': 0.5, # 初始开度
                'min_opening': 0,      # 最小开度
                'max_opening': 1,      # 最大开度
                'cv': 100,             # 流量系数
                'response_time': 5     # 响应时间 (s)
            },
            'ValveStation': {
                'valve_count': 2,      # 阀门数量
                'max_flow': 1600,      # 总最大流量 (m³/s)
                'initial_opening': 0.5, # 初始开度
                'cv': 200              # 流量系数
            },
            'Pipe': {
                'length': 1000,        # 管道长度 (m)
                'diameter': 2,         # 管道直径 (m)
                'roughness': 0.001,    # 粗糙度 (m)
                'max_flow': 1000,      # 最大流量 (m³/s)
                'material': 'steel'    # 管道材质
            },
            'Canal': {
                'length': 5000,        # 渠道长度 (m)
                'bottom_width': 10,    # 底宽 (m)
                'side_slope': 1.5,     # 边坡系数
                'roughness': 0.025,    # 曼宁系数
                'slope': 0.001,        # 坡度
                'max_flow': 2000       # 最大流量 (m³/s)
            },
            'UnifiedCanal': {
                'length': 5000,        # 渠道长度 (m)
                'bottom_width': 10,    # 底宽 (m)
                'side_slope': 1.5,     # 边坡系数
                'roughness': 0.025,    # 曼宁系数
                'slope': 0.001,        # 坡度
                'max_flow': 2000       # 最大流量 (m³/s)
            },
            'RiverChannel': {
                'length': 10000,       # 河道长度 (m)
                'bottom_width': 50,    # 底宽 (m)
                'side_slope': 2.0,     # 边坡系数
                'roughness': 0.035,    # 曼宁系数
                'slope': 0.0005,       # 坡度
                'max_flow': 5000       # 最大流量 (m³/s)
            },
            'Junction': {
                'max_flow': 3000,      # 最大流量 (m³/s)
                'loss_coeff': 0.1,     # 损失系数
                'elevation': 100       # 高程 (m)
            },
            'Sensor': {
                'measurement_type': 'level',  # 测量类型
                'accuracy': 0.01,      # 精度
                'range_min': 0,        # 测量范围最小值
                'range_max': 100,      # 测量范围最大值
                'response_time': 1     # 响应时间 (s)
            },
            'WaterTurbine': {
                'rated_power': 50000,  # 额定功率 (kW)
                'efficiency': 0.9,     # 效率
                'rated_head': 100,     # 额定水头 (m)
                'rated_flow': 500,     # 额定流量 (m³/s)
                'min_head': 50,        # 最小水头 (m)
                'max_head': 150        # 最大水头 (m)
            },
            'HydropowerStation': {
                'turbine_count': 4,    # 机组数量
                'total_power': 200000, # 总装机容量 (kW)
                'efficiency': 0.9,     # 效率
                'rated_head': 100,     # 额定水头 (m)
                'total_flow': 2000     # 总流量 (m³/s)
            },
            'ControlledSystem': {
                'initial_state': [0, 0], # 初始状态
                'A': [[0, 1], [-1, -2]], # 状态矩阵
                'B': [[0], [1]],         # 输入矩阵
                'C': [[1, 0]],           # 输出矩阵
                'D': [[0]]               # 前馈矩阵
            }
        }
        
        # 默认智能体参数
        self.default_agent_parameters = {
            'PIDAgent': {
                'kp': 1.0,
                'ki': 0.1,
                'kd': 0.01,
                'setpoint': 50
            },
            'MPCAgent': {
                'prediction_horizon': 10,
                'control_horizon': 3,
                'weights': {'output': 1.0, 'input': 0.1}
            },
            'OptimizationAgent': {
                'algorithm': 'gradient_descent',
                'learning_rate': 0.01,
                'max_iterations': 100
            }
        }
    
    def convert_language_to_config(self, description: str, 
                                 config_type: ConfigType = ConfigType.UNIFIED_SINGLE,
                                 output_dir: Union[str, Path] = None) -> Dict[str, Any]:
        """将自然语言描述转换为配置文件
        
        Args:
            description: 自然语言描述
            config_type: 目标配置文件类型
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 生成的配置数据
        """
        # 解析自然语言描述
        parsed_info = self._parse_natural_language(description)
        
        # 根据配置类型生成配置
        if config_type == ConfigType.TRADITIONAL_MULTI:
            config_data = self._generate_traditional_config(parsed_info)
        elif config_type == ConfigType.UNIFIED_SINGLE:
            config_data = self._generate_unified_config(parsed_info)
        elif config_type == ConfigType.UNIVERSAL_CONFIG:
            config_data = self._generate_universal_config(parsed_info)
        elif config_type == ConfigType.HARDCODED:
            config_data = self._generate_hardcoded_config(parsed_info)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")
        
        # 保存配置文件
        if output_dir:
            self._save_config_files(config_data, config_type, output_dir)
        
        return config_data
    
    def _parse_natural_language(self, description: str) -> Dict[str, Any]:
        """解析自然语言描述"""
        parsed_info = {
            'simulation': {},
            'components': [],
            'agents': [],
            'connections': [],
            'control': {},
            'optimization': {},
            'analysis': {}
        }
        
        # 提取仿真基本信息
        parsed_info['simulation'] = self._extract_simulation_info(description)
        
        # 提取组件信息
        parsed_info['components'] = self._extract_components_info(description)
        
        # 提取智能体信息
        parsed_info['agents'] = self._extract_agents_info(description)
        
        # 提取连接信息
        parsed_info['connections'] = self._extract_connections_info(description)
        
        # 提取控制信息
        parsed_info['control'] = self._extract_control_info(description)
        
        # 提取优化信息
        parsed_info['optimization'] = self._extract_optimization_info(description)
        
        # 提取分析信息
        parsed_info['analysis'] = self._extract_analysis_info(description)
        
        return parsed_info
    
    def _extract_simulation_info(self, description: str) -> Dict[str, Any]:
        """提取仿真基本信息"""
        simulation_info = {
            'name': '自动生成的仿真',
            'description': '基于自然语言描述生成的仿真配置',
            'duration': 3600,  # 默认1小时
            'time_step': 1.0,  # 默认1秒
            'solver': 'rk4'
        }
        
        # 提取仿真时长
        duration_patterns = [
            r'仿真时长[：:](\d+)秒',
            r'仿真时间[：:](\d+)秒',
            r'持续时间[：:](\d+)秒',
            r'运行(\d+)秒',
            r'(\d+)秒仿真'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, description)
            if match:
                simulation_info['duration'] = int(match.group(1))
                break
        
        # 提取时间步长
        timestep_patterns = [
            r'时间步长[：:](\d+\.?\d*)秒',
            r'步长[：:](\d+\.?\d*)秒',
            r'dt[：:=](\d+\.?\d*)',
            r'时间间隔[：:](\d+\.?\d*)秒'
        ]
        
        for pattern in timestep_patterns:
            match = re.search(pattern, description)
            if match:
                simulation_info['time_step'] = float(match.group(1))
                break
        
        # 提取仿真名称
        name_patterns = [
            r'仿真名称[：:](.*?)\n',
            r'项目名称[：:](.*?)\n',
            r'系统名称[：:](.*?)\n'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, description)
            if match:
                simulation_info['name'] = match.group(1).strip()
                break
        
        # 提取求解器信息
        if 'runge' in description.lower() or 'rk4' in description.lower():
            simulation_info['solver'] = 'rk4'
        elif 'euler' in description.lower():
            simulation_info['solver'] = 'euler'
        elif 'adams' in description.lower():
            simulation_info['solver'] = 'adams'
        
        return simulation_info
    
    def _extract_components_info(self, description: str) -> List[ComponentInfo]:
        """提取组件信息"""
        components = []
        
        # 首先尝试提取具体的组件描述（支持英文类名）
        lines = description.split('\n')
        for line in lines:
            if '：' in line or ':' in line:
                # 解析 "组件名：组件类型" 格式
                parts = re.split('[：:]', line.strip())
                if len(parts) >= 2:
                    name = parts[0].strip().replace('-', '').replace('*', '').strip()
                    type_desc = parts[1].strip()
                    
                    # 首先尝试匹配完整的英文类名
                    english_type = self._extract_english_component_type(type_desc)
                    if english_type:
                        parameters = self._extract_component_parameters(line, english_type)
                        component = ComponentInfo(
                            name=name,
                            type=english_type,
                            parameters=parameters
                        )
                        components.append(component)
                        continue
                    
                    # 如果没有匹配到英文类名，尝试中文类型
                    for chinese_type, english_type in self.component_type_reverse_map.items():
                        if chinese_type in type_desc:
                            parameters = self._extract_component_parameters(line, english_type)
                            component = ComponentInfo(
                                name=name,
                                type=english_type,
                                parameters=parameters
                            )
                            components.append(component)
                            break
        
        # 如果没有找到具体组件，尝试从统计信息生成
        if not components:
            components = self._generate_components_from_statistics(description)
        
        return components
    
    def _extract_english_component_type(self, type_desc: str) -> str:
        """从类型描述中提取英文组件类型"""
        # 匹配完整的类路径，如 core_lib.physical_objects.reservoir.Reservoir
        class_patterns = [
            r'core_lib\.physical_objects\.reservoir\.Reservoir',
            r'core_lib\.physical_objects\.gate\.Gate', 
            r'core_lib\.physical_objects\.pump\.Pump',
            r'core_lib\.physical_objects\.valve\.Valve',
            r'core_lib\.physical_objects\.pipe\.Pipe',
            r'core_lib\.physical_objects\.canal\.Canal',
            r'core_lib\.physical_objects\.unified_canal\.UnifiedCanal',
            r'core_lib\.physical_objects\.channel\.Channel',
            r'core_lib\.physical_objects\.river_channel\.RiverChannel',
            r'core_lib\.physical_objects\.junction\.Junction',
            r'core_lib\.physical_objects\.sensor\.Sensor',
            r'core_lib\.physical_objects\.disturbance_node\.DisturbanceNode',
            r'core_lib\.physical_objects\.controlled_system\.ControlledSystem'
        ]
        
        # 类名到简化类型的映射（包括常见的英文类名）
        class_to_type_map = {
            'Reservoir': 'Reservoir',
            'Gate': 'Gate',
            'Pump': 'Pump', 
            'Valve': 'Valve',
            'Pipe': 'Pipe',
            'Canal': 'Canal',
            'UnifiedCanal': 'Canal',
            'Channel': 'Channel',
            'RiverChannel': 'Channel',  # 添加RiverChannel映射
            'IntegralDelayCanal': 'Canal',  # 添加IntegralDelayCanal映射
            'Junction': 'Junction',
            'Sensor': 'Sensor',
            'DisturbanceNode': 'DisturbanceNode',
            'ControlledSystem': 'ControlledSystem',
            'PumpStation': 'Pump',
            'ValveStation': 'Valve',
            'WaterTurbine': 'ControlledSystem',
            'TurbineStation': 'ControlledSystem'
        }
        
        # 首先尝试匹配完整的类路径
        for pattern in class_patterns:
            if re.search(pattern, type_desc):
                # 提取类名（最后一个点后的部分）
                class_name = pattern.split('\\.')[-1]
                return class_to_type_map.get(class_name, class_name)
        
        # 如果没有匹配到完整路径，尝试匹配简单的英文类名
        for class_name, mapped_type in class_to_type_map.items():
            if class_name in type_desc:
                return mapped_type
        
        return None
    
    def _extract_component_parameters(self, line: str, component_type: str) -> Dict[str, Any]:
        """提取组件参数"""
        parameters = self.default_parameters.get(component_type, {}).copy()
        
        # 更精确的数值和单位提取模式
        parameter_patterns = {
            # 容量相关
            'capacity': [
                r'容量[：:]?\s*(\d+\.?\d*)\s*[万]?\s*m³',
                r'库容[：:]?\s*(\d+\.?\d*)\s*[万]?\s*m³',
                r'总容量[：:]?\s*(\d+\.?\d*)\s*[万]?\s*立方米',
                r'(\d+\.?\d*)\s*[万]?\s*m³.*容量',
                r'(\d+\.?\d*)\s*[万]?\s*立方米.*容量'
            ],
            # 水位相关
            'initial_level': [
                r'初始水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'起始水位[：:]?\s*(\d+\.?\d*)\s*米',
                r'(\d+\.?\d*)\s*m.*水位',
                r'(\d+\.?\d*)\s*米.*水位'
            ],
            'max_level': [
                r'最高水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'最大水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'汛限水位[：:]?\s*(\d+\.?\d*)\s*米'
            ],
            'min_level': [
                r'最低水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'最小水位[：:]?\s*(\d+\.?\d*)\s*m',
                r'死水位[：:]?\s*(\d+\.?\d*)\s*米'
            ],
            # 流量相关
            'max_flow': [
                r'最大流量[：:]?\s*(\d+\.?\d*)\s*m³/s',
                r'额定流量[：:]?\s*(\d+\.?\d*)\s*m³/s',
                r'设计流量[：:]?\s*(\d+\.?\d*)\s*立方米每秒',
                r'(\d+\.?\d*)\s*m³/s.*流量',
                r'(\d+\.?\d*)\s*立方米每秒.*流量'
            ],
            'initial_flow': [
                r'初始流量[：:]?\s*(\d+\.?\d*)\s*m³/s',
                r'起始流量[：:]?\s*(\d+\.?\d*)\s*立方米每秒'
            ],
            # 功率相关
            'power': [
                r'功率[：:]?\s*(\d+\.?\d*)\s*[k]?W',
                r'额定功率[：:]?\s*(\d+\.?\d*)\s*[k]?W',
                r'装机容量[：:]?\s*(\d+\.?\d*)\s*[k]?W',
                r'(\d+\.?\d*)\s*[k]?W.*功率',
                r'(\d+\.?\d*)\s*千瓦.*功率'
            ],
            # 开度相关
            'initial_opening': [
                r'初始开度[：:]?\s*(\d+\.?\d*)%?',
                r'开度[：:]?\s*(\d+\.?\d*)%?',
                r'起始开度[：:]?\s*(\d+\.?\d*)%?'
            ],
            # 尺寸相关
            'length': [
                r'长度[：:]?\s*(\d+\.?\d*)\s*[k]?m',
                r'总长[：:]?\s*(\d+\.?\d*)\s*[k]?m',
                r'(\d+\.?\d*)\s*[k]?m.*长',
                r'(\d+\.?\d*)\s*[千]?米.*长'
            ],
            'width': [
                r'宽度[：:]?\s*(\d+\.?\d*)\s*m',
                r'底宽[：:]?\s*(\d+\.?\d*)\s*m',
                r'(\d+\.?\d*)\s*m.*宽',
                r'(\d+\.?\d*)\s*米.*宽'
            ],
            'height': [
                r'高度[：:]?\s*(\d+\.?\d*)\s*m',
                r'闸高[：:]?\s*(\d+\.?\d*)\s*m',
                r'(\d+\.?\d*)\s*m.*高',
                r'(\d+\.?\d*)\s*米.*高'
            ],
            'diameter': [
                r'直径[：:]?\s*(\d+\.?\d*)\s*m',
                r'管径[：:]?\s*(\d+\.?\d*)\s*m',
                r'(\d+\.?\d*)\s*m.*径',
                r'(\d+\.?\d*)\s*米.*径'
            ],
            # 效率相关
            'efficiency': [
                r'效率[：:]?\s*(\d+\.?\d*)%?',
                r'机械效率[：:]?\s*(\d+\.?\d*)%?',
                r'(\d+\.?\d*)%.*效率'
            ],
            # 扬程相关
            'head': [
                r'扬程[：:]?\s*(\d+\.?\d*)\s*m',
                r'水头[：:]?\s*(\d+\.?\d*)\s*m',
                r'设计水头[：:]?\s*(\d+\.?\d*)\s*米'
            ],
            # 坡度相关
            'slope': [
                r'坡度[：:]?\s*(\d+\.?\d*)',
                r'底坡[：:]?\s*(\d+\.?\d*)',
                r'纵坡[：:]?\s*(\d+\.?\d*)'
            ],
            # 粗糙度相关
            'roughness': [
                r'粗糙度[：:]?\s*(\d+\.?\d*)',
                r'曼宁系数[：:]?\s*(\d+\.?\d*)',
                r'糙率[：:]?\s*(\d+\.?\d*)'
            ]
        }
        
        # 遍历所有参数模式进行匹配
        for param_name, patterns in parameter_patterns.items():
            if param_name in parameters:  # 只处理该组件类型支持的参数
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        value = float(match.group(1))
                        
                        # 处理单位转换
                        if '万' in match.group(0):
                            value *= 10000
                        elif 'k' in match.group(0).lower():
                            value *= 1000
                        elif '千' in match.group(0):
                            value *= 1000
                        elif '%' in match.group(0):
                            value /= 100
                        
                        parameters[param_name] = value
                        break
        
        # 特殊处理：根据组件类型调整参数
        if component_type in ['Lake', 'Pond'] and 'capacity' not in line:
            # 如果是湖泊或池塘但没有明确容量，根据面积估算
            if 'area' in parameters:
                parameters['capacity'] = parameters['area'] * parameters.get('initial_level', 10)
        
        return parameters
    
    def _generate_components_from_statistics(self, description: str) -> List[ComponentInfo]:
        """从统计信息生成组件"""
        components = []
        
        # 扩展的组件统计信息匹配模式
        stat_patterns = [
            # 基本格式：组件类型：数量个
            r'([水库蓄水池水池湖泊池塘闸门水闸调节闸泄洪闸水泵泵抽水站泵站阀门阀调节阀阀站管道管输水管渠道渠输水渠河道河河流水道汇流点分流点节点传感器水位计流量计监测点水轮机水电站发电机组机组受控系统控制系统])[：:]?\s*(\d+)\s*[个台座处套]?',
            # 反向格式：数量个组件类型
            r'(\d+)\s*[个台座处套]?\s*([水库蓄水池水池湖泊池塘闸门水闸调节闸泄洪闸水泵泵抽水站泵站阀门阀调节阀阀站管道管输水管渠道渠输水渠河道河河流水道汇流点分流点节点传感器水位计流量计监测点水轮机水电站发电机组机组受控系统控制系统])',
            # 包含格式：包含/有数量个组件类型
            r'[包含有设置配置]\s*(\d+)\s*[个台座处套]?\s*([水库蓄水池水池湖泊池塘闸门水闸调节闸泄洪闸水泵泵抽水站泵站阀门阀调节阀阀站管道管输水管渠道渠输水渠河道河河流水道汇流点分流点节点传感器水位计流量计监测点水轮机水电站发电机组机组受控系统控制系统])',
            # 系统包含格式：系统包含组件类型数量个
            r'系统[包含有设置配置].*?([水库蓄水池水池湖泊池塘闸门水闸调节闸泄洪闸水泵泵抽水站泵站阀门阀调节阀阀站管道管输水管渠道渠输水渠河道河河流水道汇流点分流点节点传感器水位计流量计监测点水轮机水电站发电机组机组受控系统控制系统]).*?(\d+)\s*[个台座处套]?',
            # 列表格式：- 组件类型：数量个
            r'-\s*([水库蓄水池水池湖泊池塘闸门水闸调节闸泄洪闸水泵泵抽水站泵站阀门阀调节阀阀站管道管输水管渠道渠输水渠河道河河流水道汇流点分流点节点传感器水位计流量计监测点水轮机水电站发电机组机组受控系统控制系统])[：:]?\s*(\d+)\s*[个台座处套]?'
        ]
        
        # 用于去重的集合
        found_components = set()
        
        for pattern in stat_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if len(match) == 2:
                    # 判断哪个是数量，哪个是类型
                    if match[0].isdigit():
                        count, chinese_type = int(match[0]), match[1]
                    elif match[1].isdigit():
                        chinese_type, count = match[0], int(match[1])
                    else:
                        continue
                    
                    # 避免重复添加相同类型的组件
                    component_key = f"{chinese_type}_{count}"
                    if component_key in found_components:
                        continue
                    found_components.add(component_key)
                    
                    english_type = self.component_type_reverse_map.get(chinese_type)
                    if english_type:
                        for i in range(count):
                            # 生成更有意义的组件名称
                            if count == 1:
                                component_name = chinese_type
                            else:
                                component_name = f"{chinese_type}{i+1}"
                            
                            component = ComponentInfo(
                                name=component_name,
                                type=english_type,
                                parameters=self.default_parameters.get(english_type, {}).copy()
                            )
                            components.append(component)
        
        # 如果没有找到统计信息，尝试从描述中推断基本组件
        if not components:
            components = self._infer_basic_components(description)
        
        return components
    
    def _infer_basic_components(self, description: str) -> List[ComponentInfo]:
        """从描述中推断基本组件"""
        components = []
        
        # 基本推断规则
        inference_rules = {
            '水库': ['水库', '蓄水', '库容', '水位'],
            '闸门': ['闸门', '水闸', '调节', '控制流量', '开度'],
            '水泵': ['水泵', '抽水', '提升', '泵站'],
            '管道': ['管道', '输水', '传输'],
            '渠道': ['渠道', '明渠', '输水渠'],
            '河道': ['河道', '河流', '天然河道'],
            '传感器': ['传感器', '监测', '测量', '水位计', '流量计']
        }
        
        for chinese_type, keywords in inference_rules.items():
            if any(keyword in description for keyword in keywords):
                english_type = self.component_type_reverse_map.get(chinese_type)
                if english_type:
                    component = ComponentInfo(
                        name=chinese_type,
                        type=english_type,
                        parameters=self.default_parameters.get(english_type, {}).copy()
                    )
                    components.append(component)
        
        return components
    
    def _infer_connections_from_components(self, components: List[ComponentInfo]) -> List[ConnectionInfo]:
        """从组件信息推断连接关系"""
        connections = []
        
        if len(components) < 2:
            return connections
        
        # 根据组件类型推断典型的连接模式
        component_types = {comp.name: comp.type for comp in components}
        
        # 水利系统典型连接模式：水库 -> 闸门 -> 渠道 -> 闸门 -> 水库
        reservoirs = [comp.name for comp in components if 'reservoir' in comp.type.lower() or '水库' in comp.type]
        gates = [comp.name for comp in components if 'gate' in comp.type.lower() or '闸门' in comp.type]
        canals = [comp.name for comp in components if 'canal' in comp.type.lower() or '渠道' in comp.type]
        
        # 如果有水库和闸门，建立连接
        if reservoirs and gates:
            for i, reservoir in enumerate(reservoirs):
                if i < len(gates):
                    connections.append(ConnectionInfo(
                        from_component=reservoir,
                        to_component=gates[i],
                        connection_type='flow'
                    ))
        
        # 如果有闸门和渠道，建立连接
        if gates and canals:
            for i, gate in enumerate(gates):
                if i < len(canals):
                    connections.append(ConnectionInfo(
                        from_component=gate,
                        to_component=canals[i],
                        connection_type='flow'
                    ))
        
        # 如果有多个渠道，按顺序连接
        if len(canals) > 1:
            for i in range(len(canals) - 1):
                connections.append(ConnectionInfo(
                    from_component=canals[i],
                    to_component=canals[i + 1],
                    connection_type='flow'
                ))
        
        return connections
    
    def _extract_agents_info(self, description: str) -> List[AgentInfo]:
        """提取智能体信息"""
        agents = []
        
        # 查找智能体系统描述部分
        lines = description.split('\n')
        in_agent_section = False
        
        for line in lines:
            line = line.strip()
            
            # 检测智能体系统部分开始
            if '智能体系统' in line or '智能体：' in line or '具体智能体：' in line:
                in_agent_section = True
                continue
            
            # 检测其他部分开始，结束智能体部分
            if line.startswith('##') and in_agent_section:
                in_agent_section = False
                continue
            
            # 在智能体部分提取智能体信息
            if in_agent_section and line:
                # 匹配智能体条目格式："1. agent_id：智能体类型"
                agent_match = re.match(r'\s*\d+\.\s*([^：:]+)[：:]\s*([^\n]+)', line)
                if agent_match:
                    agent_id = agent_match.group(1).strip()
                    agent_type_chinese = agent_match.group(2).strip()
                    
                    # 查找对应的英文类型
                    agent_type_english = None
                    for chinese_type, english_type in self.agent_type_reverse_map.items():
                        if chinese_type in agent_type_chinese:
                            agent_type_english = english_type
                            break
                    
                    if not agent_type_english:
                        # 如果没找到映射，尝试从中文描述推断
                        if '数字孪生' in agent_type_chinese:
                            agent_type_english = 'DigitalTwinAgent'
                        elif 'PID' in agent_type_chinese:
                            agent_type_english = 'PIDControllerAgent'
                        elif '控制' in agent_type_chinese:
                            agent_type_english = 'ControlAgent'
                        elif '监控' in agent_type_chinese:
                            agent_type_english = 'MonitoringAgent'
                        else:
                            agent_type_english = 'Agent'  # 默认类型
                    
                    # 创建智能体信息
                    agent = AgentInfo(
                        name=agent_id,
                        type=agent_type_english,
                        target_component="component_1",  # 默认目标，后续可以从配置详情中提取
                        parameters=self.default_agent_parameters.get(agent_type_english, {}).copy()
                    )
                    agents.append(agent)
                    
                # 提取智能体配置详情
                elif line.startswith('-') and agents:
                    # 解析配置行："- 监控对象：target_reservoir"
                    config_match = re.match(r'\s*-\s*([^：:]+)[：:]\s*([^\n]+)', line)
                    if config_match:
                        config_key = config_match.group(1).strip()
                        config_value = config_match.group(2).strip()
                        
                        # 根据配置键设置智能体参数
                        last_agent = agents[-1]
                        if '监控对象' in config_key or '控制对象' in config_key:
                            last_agent.target_component = config_value
                        elif '状态主题' in config_key:
                            last_agent.parameters['state_topic'] = config_value
                        elif '订阅主题' in config_key:
                            last_agent.parameters['subscribed_topic'] = config_value
                        elif '目标设定值' in config_key:
                            try:
                                last_agent.parameters['target_setpoint'] = float(config_value)
                            except ValueError:
                                last_agent.parameters['target_setpoint'] = config_value
                        elif 'PID参数' in config_key:
                            # 解析PID参数："Kp=0.5, Ki=0.1, Kd=0.05"
                            pid_gains = {}
                            for param in config_value.split(','):
                                if '=' in param:
                                    key, value = param.split('=', 1)
                                    key = key.strip().lower()
                                    try:
                                        pid_gains[key] = float(value.strip())
                                    except ValueError:
                                        pass
                            if pid_gains:
                                last_agent.parameters['pid_gains'] = pid_gains
        
        # 如果没有找到智能体系统描述，尝试从控制策略描述中提取
        if not agents:
            control_patterns = [
                r'采用\s*([^，,\n]*?)\s*控制',
                r'使用\s*([^，,\n]*?)\s*智能体',
                r'([^，,\n]*?)\s*控制策略'
            ]
            
            for pattern in control_patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    control_desc = match.strip()
                    
                    # 查找对应的智能体类型
                    for chinese_type, english_type in self.agent_type_reverse_map.items():
                        if chinese_type in control_desc or any(keyword in control_desc for keyword in chinese_type.split()):
                            agent = AgentInfo(
                                name=f"{english_type}_1",
                                type=english_type,
                                target_component="component_1",  # 默认目标
                                parameters=self.default_agent_parameters.get(english_type, {}).copy()
                            )
                            agents.append(agent)
                            break
        
        return agents
    
    def _extract_connections_info(self, description: str) -> List[ConnectionInfo]:
        """提取连接信息"""
        connections = []
        
        # 扩展的连接模式 - 支持中文组件名和更多表达方式
        connection_patterns = [
            # 基本箭头连接
            r'([\w\u4e00-\u9fff]+)\s*(?:→|->|=>|⇒)\s*([\w\u4e00-\u9fff]+)',
            # 基本连接表达
            r'([\w\u4e00-\u9fff]+)\s*(?:连接到|连接至|连至|流向|流入|输出到|输送到|供水到|排水到)\s*([\w\u4e00-\u9fff]+)',
            # 从...到...表达
            r'从\s*([\w\u4e00-\u9fff]+)\s*(?:到|至|向|流向|输送到)\s*([\w\u4e00-\u9fff]+)',
            # 通过...连接表达
            r'([\w\u4e00-\u9fff]+)\s*通过\s*[\w\u4e00-\u9fff]*\s*(?:连接到|连至|流向)\s*([\w\u4e00-\u9fff]+)',
            # 经过表达
            r'([\w\u4e00-\u9fff]+)\s*经过\s*([\w\u4e00-\u9fff]+)',
            # 上游下游表达
            r'([\w\u4e00-\u9fff]+)\s*(?:的)?\s*(?:上游|下游)\s*(?:是|为|连接)\s*([\w\u4e00-\u9fff]+)',
            # 进出口表达
            r'([\w\u4e00-\u9fff]+)\s*(?:的)?\s*(?:出口|出水口|排水口)\s*(?:连接到|连至|流向)\s*([\w\u4e00-\u9fff]+)',
            r'([\w\u4e00-\u9fff]+)\s*(?:的)?\s*(?:进口|入口|进水口)\s*(?:来自|连接)\s*([\w\u4e00-\u9fff]+)',
            # 串联并联表达
            r'([\w\u4e00-\u9fff]+)\s*(?:与|和)\s*([\w\u4e00-\u9fff]+)\s*(?:串联|顺序连接)',
            r'([\w\u4e00-\u9fff]+)\s*(?:与|和)\s*([\w\u4e00-\u9fff]+)\s*(?:并联|并行连接)',
            # 控制关系表达
            r'([\w\u4e00-\u9fff]+)\s*(?:控制|调节|管理)\s*([\w\u4e00-\u9fff]+)',
            # 监测关系表达
            r'([\w\u4e00-\u9fff]+)\s*(?:监测|测量|检测)\s*([\w\u4e00-\u9fff]+)',
            # 列表格式连接
            r'-\s*([\w\u4e00-\u9fff]+)\s*(?:连接到|流向|输出到)\s*([\w\u4e00-\u9fff]+)',
            # 简单连接表达
            r'([\w\u4e00-\u9fff]+)\s*连接\s*([\w\u4e00-\u9fff]+)',
            r'([\w\u4e00-\u9fff]+)\s*到\s*([\w\u4e00-\u9fff]+)',
            r'([\w\u4e00-\u9fff]+)\s*接入\s*([\w\u4e00-\u9fff]+)',
            r'([\w\u4e00-\u9fff]+)\s*与\s*([\w\u4e00-\u9fff]+)\s*相连'
        ]
        
        # 用于去重的集合
        found_connections = set()
        
        # 首先查找具体的连接关系描述
        lines = description.split('\n')
        connection_found = False
        
        for line in lines:
            if any(keyword in line for keyword in ['连接关系', '拓扑', '→', '->', '连接', '流向', '输出']):
                connection_found = True
                for pattern in connection_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if len(match) == 2 and match[0] != match[1]:  # 避免自连接
                            source, target = match[0].strip(), match[1].strip()
                            
                            # 过滤掉无效的连接（如单字符或纯数字）
                            if len(source) < 2 or len(target) < 2 or source.isdigit() or target.isdigit():
                                continue
                            
                            # 避免重复添加相同的连接
                            connection_key = f"{source}->{target}"
                            if connection_key in found_connections:
                                continue
                            found_connections.add(connection_key)
                            
                            # 根据模式和上下文确定连接类型
                            conn_type = 'flow'  # 默认为流量连接
                            if any(keyword in line for keyword in ['控制', '调节', '管理']):
                                conn_type = 'control'
                            elif any(keyword in line for keyword in ['监测', '测量', '检测', '信号']):
                                conn_type = 'signal'
                            elif any(keyword in line for keyword in ['数据', '信息']):
                                conn_type = 'data'
                            elif any(keyword in line for keyword in ['流量', '水流', '流向', '输水']):
                                conn_type = 'flow'
                            
                            connection = ConnectionInfo(
                                from_component=source,
                                to_component=target,
                                connection_type=conn_type
                            )
                            connections.append(connection)
        
        # 如果没有找到具体连接，尝试从整体描述中提取
        if not connection_found:
            for pattern in connection_patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    if len(match) == 2 and match[0] != match[1]:
                        source, target = match[0].strip(), match[1].strip()
                        
                        # 过滤掉无效的连接
                        if len(source) < 2 or len(target) < 2 or source.isdigit() or target.isdigit():
                            continue
                        
                        # 避免重复添加相同的连接
                        connection_key = f"{source}->{target}"
                        if connection_key in found_connections:
                            continue
                        found_connections.add(connection_key)
                        
                        # 根据模式确定连接类型
                        conn_type = 'flow'
                        if '控制' in pattern or '调节' in pattern or '管理' in pattern:
                            conn_type = 'control'
                        elif '监测' in pattern or '测量' in pattern or '检测' in pattern:
                            conn_type = 'signal'
                        
                        connection = ConnectionInfo(
                            from_component=source,
                            to_component=target,
                            connection_type=conn_type
                        )
                        connections.append(connection)
        
        # 如果仍然没有找到连接，尝试从组件描述中推断
        if not connections:
            # 需要先提取组件信息
            components_info = self._extract_components_info(description)
            connections = self._infer_connections_from_components(components_info)
        
        # 去重
        unique_connections = []
        seen = set()
        for conn in connections:
            key = (conn.from_component, conn.to_component, conn.connection_type)
            if key not in seen:
                seen.add(key)
                unique_connections.append(conn)
        
        return unique_connections
    
    def _extract_control_info(self, description: str) -> Dict[str, Any]:
        """提取控制信息"""
        control_info = {}
        
        # 查找控制策略
        for chinese_strategy, english_strategy in self.control_strategy_reverse_map.items():
            if chinese_strategy in description:
                control_info['type'] = english_strategy
                control_info['enabled'] = True
                break
        
        return control_info
    
    def _extract_optimization_info(self, description: str) -> Dict[str, Any]:
        """提取优化信息"""
        optimization_info = {}
        
        # 查找优化相关关键词
        if any(keyword in description for keyword in ['优化', '最优', '最小化', '最大化']):
            optimization_info['enabled'] = True
            optimization_info['objective'] = {
                'type': 'minimize',
                'function': 'quadratic'
            }
        
        return optimization_info
    
    def _extract_analysis_info(self, description: str) -> Dict[str, Any]:
        """提取分析信息"""
        analysis_info = {}
        
        # 查找分析相关关键词
        if '性能分析' in description:
            analysis_info['control_performance'] = {'enabled': True}
        
        if '系统辨识' in description:
            analysis_info['system_identification'] = {'enabled': True}
        
        if '统计分析' in description:
            analysis_info['statistical_analysis'] = {'enabled': True}
        
        return analysis_info
    
    def _generate_traditional_config(self, parsed_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成传统多配置文件"""
        config_data = {
            'config.yml': {
                'simulation': {
                    'duration': parsed_info['simulation']['duration'],
                    'dt': parsed_info['simulation']['time_step'],
                    'solver': {
                        'type': parsed_info['simulation']['solver']
                    }
                }
            },
            'components.yml': {
                'components': []
            },
            'topology.yml': {
                'connections': []
            },
            'agents.yml': {
                'agents': []
            }
        }
        
        # 添加组件
        for comp in parsed_info['components']:
            component_config = {
                'id': comp.name,
                'class': comp.type,
                **comp.parameters
            }
            config_data['components.yml']['components'].append(component_config)
        
        # 添加连接
        for conn in parsed_info['connections']:
            connection_config = {
                'from': conn.from_component,
                'to': conn.to_component,
                'type': conn.connection_type
            }
            config_data['topology.yml']['connections'].append(connection_config)
        
        # 添加智能体
        for agent in parsed_info['agents']:
            agent_config = {
                'id': agent.name,
                'class': agent.type,
                'target': agent.target_component,
                **agent.parameters
            }
            config_data['agents.yml']['agents'].append(agent_config)
        
        return config_data
    
    def _generate_unified_config(self, parsed_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成统一配置文件"""
        config_data = {
            'simulation': {
                'name': parsed_info['simulation']['name'],
                'description': parsed_info['simulation']['description'],
                'duration': parsed_info['simulation']['duration'],
                'time_step': parsed_info['simulation']['time_step']
            },
            'components': {},
            'topology': {
                'connections': []
            },
            'agents': {}
        }
        
        # 添加组件
        for comp in parsed_info['components']:
            config_data['components'][comp.name] = {
                'type': comp.type,
                **comp.parameters
            }
        
        # 添加连接
        for conn in parsed_info['connections']:
            connection_config = {
                'from': conn.from_component,
                'to': conn.to_component,
                'type': conn.connection_type
            }
            config_data['topology']['connections'].append(connection_config)
        
        # 添加智能体
        for agent in parsed_info['agents']:
            config_data['agents'][agent.name] = {
                'type': agent.type,
                'target': agent.target_component,
                **agent.parameters
            }
        
        # 添加控制配置
        if parsed_info['control']:
            config_data['control'] = parsed_info['control']
        
        # 添加优化配置
        if parsed_info['optimization']:
            config_data['optimization'] = parsed_info['optimization']
        
        return config_data
    
    def _generate_universal_config(self, parsed_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成通用配置文件"""
        config_data = {
            'simulation': {
                'name': parsed_info['simulation']['name'],
                'description': parsed_info['simulation']['description'],
                'version': '1.5',
                'time': {
                    'start_time': 0,
                    'end_time': parsed_info['simulation']['duration'],
                    'time_step': parsed_info['simulation']['time_step']
                },
                'solver': {
                    'type': parsed_info['simulation']['solver'],
                    'tolerance': 1e-6
                }
            },
            'components': {},
            'topology': {
                'connections': []
            },
            'agents': {},
            'debug': {
                'enabled': True,
                'log_level': 'INFO',
                'log_file': 'simulation.log'
            },
            'performance': {
                'enabled': True,
                'time_tracking': True,
                'memory_monitoring': True
            },
            'visualization': {
                'enabled': True,
                'plots': {
                    'enabled': True,
                    'save_format': 'png'
                }
            }
        }
        
        # 添加组件
        for comp in parsed_info['components']:
            config_data['components'][comp.name] = {
                'type': comp.type,
                **comp.parameters
            }
        
        # 添加连接
        for conn in parsed_info['connections']:
            connection_config = {
                'from': conn.from_component,
                'to': conn.to_component,
                'type': conn.connection_type
            }
            config_data['topology']['connections'].append(connection_config)
        
        # 添加智能体
        for agent in parsed_info['agents']:
            config_data['agents'][agent.name] = {
                'type': agent.type,
                'target': agent.target_component,
                **agent.parameters
            }
        
        # 添加分析配置
        if parsed_info['analysis']:
            config_data['analysis'] = parsed_info['analysis']
        
        return config_data
    
    def _generate_hardcoded_config(self, parsed_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成硬编码配置（Python代码）"""
        python_code = self._generate_python_code(parsed_info)
        
        return {
            'python_file': 'generated_simulation.py',
            'code': python_code
        }
    
    def _generate_python_code(self, parsed_info: Dict[str, Any]) -> str:
        """生成Python代码"""
        code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成的仿真代码
基于自然语言描述生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_lib.core_engine.simulation_builder import SimulationBuilder
from core_lib.io.object_factory import ObjectFactory

def create_simulation():
    """创建仿真系统"""
    builder = SimulationBuilder()
    factory = ObjectFactory()
    
    # 设置仿真参数
    builder.set_simulation_time({duration})
    builder.set_time_step({time_step})
    
'''.format(
            duration=parsed_info['simulation']['duration'],
            time_step=parsed_info['simulation']['time_step']
        )
        
        # 添加组件创建代码
        for comp in parsed_info['components']:
            code += f'''    # 创建组件: {comp.name}
'''
            code += f'''    {comp.name.lower()} = factory.create_object('{comp.type}', {comp.parameters})\n'''
            code += f'''    builder.add_component('{comp.name}', {comp.name.lower()})\n\n'''
        
        # 添加连接代码
        for conn in parsed_info['connections']:
            code += f'''    # 连接: {conn.from_component} -> {conn.to_component}\n'''
            code += f'''    builder.connect('{conn.from_component}', '{conn.to_component}')\n\n'''
        
        # 添加智能体代码
        for agent in parsed_info['agents']:
            code += f'''    # 创建智能体: {agent.name}\n'''
            code += f'''    {agent.name.lower()} = factory.create_object('{agent.type}', {agent.parameters})\n'''
            code += f'''    builder.add_agent('{agent.name}', {agent.name.lower()})\n\n'''
        
        code += '''    # 构建并返回仿真系统
    return builder.build()

def main():
    """主函数"""
    simulation = create_simulation()
    simulation.run()
    simulation.save_results('results')

if __name__ == '__main__':
    main()
'''
        
        return code
    
    def _save_config_files(self, config_data: Dict[str, Any], 
                          config_type: ConfigType, output_dir: Union[str, Path]) -> None:
        """保存配置文件"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if config_type == ConfigType.TRADITIONAL_MULTI:
            # 保存多个配置文件
            for filename, data in config_data.items():
                file_path = output_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"已保存配置文件: {file_path}")
        
        elif config_type == ConfigType.UNIFIED_SINGLE:
            # 保存统一配置文件
            file_path = output_dir / 'unified_config.yml'
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"已保存统一配置文件: {file_path}")
        
        elif config_type == ConfigType.UNIVERSAL_CONFIG:
            # 保存通用配置文件
            file_path = output_dir / 'universal_config.yml'
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"已保存通用配置文件: {file_path}")
        
        elif config_type == ConfigType.HARDCODED:
            # 保存Python代码文件
            file_path = output_dir / config_data['python_file']
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(config_data['code'])
            self.logger.info(f"已保存Python代码文件: {file_path}")


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自然语言到配置文件转换器')
    parser.add_argument('description', help='自然语言描述文件路径或直接描述文本')
    parser.add_argument('-t', '--type', choices=['traditional', 'unified', 'universal', 'hardcoded'],
                       default='unified', help='目标配置文件类型')
    parser.add_argument('-o', '--output', help='输出目录', default='generated_config')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 读取描述文本
        if os.path.exists(args.description):
            with open(args.description, 'r', encoding='utf-8') as f:
                description = f.read()
        else:
            description = args.description
        
        # 确定配置类型
        config_type_map = {
            'traditional': ConfigType.TRADITIONAL_MULTI,
            'unified': ConfigType.UNIFIED_SINGLE,
            'universal': ConfigType.UNIVERSAL_CONFIG,
            'hardcoded': ConfigType.HARDCODED
        }
        config_type = config_type_map[args.type]
        
        # 创建转换器
        converter = LanguageToConfigConverter()
        
        # 转换配置文件
        config_data = converter.convert_language_to_config(
            description, config_type, args.output
        )
        
        print(f"转换完成！配置文件已保存到: {args.output}")
        
    except Exception as e:
        print(f"转换失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()