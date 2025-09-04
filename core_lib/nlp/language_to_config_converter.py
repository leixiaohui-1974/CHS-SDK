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
            '水库': 'Reservoir',
            '闸门': 'Gate',
            '水泵': 'Pump',
            '泵站': 'PumpStation',
            '阀门': 'Valve',
            '阀站': 'ValveStation',
            '管道': 'Pipe',
            '渠道': 'Canal',
            '河道': 'Channel',
            '汇流点': 'Junction',
            '传感器': 'Sensor',
            '受控系统': 'ControlledSystem',
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
                'area': 10000          # 水面面积 (m²)
            },
            'Gate': {
                'max_flow': 1000,      # 最大流量 (m³/s)
                'initial_opening': 0.5, # 初始开度
                'min_opening': 0,      # 最小开度
                'max_opening': 1       # 最大开度
            },
            'Pump': {
                'max_flow': 500,       # 最大流量 (m³/s)
                'efficiency': 0.85,    # 效率
                'power': 1000,         # 功率 (kW)
                'initial_speed': 0     # 初始转速
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
        
        # 提取数值参数
        number_patterns = [
            r'(\d+\.?\d*)\s*m³',
            r'(\d+\.?\d*)\s*立方米',
            r'(\d+\.?\d*)\s*m³/s',
            r'(\d+\.?\d*)\s*立方米每秒',
            r'(\d+\.?\d*)\s*m',
            r'(\d+\.?\d*)\s*米',
            r'(\d+\.?\d*)\s*kW',
            r'(\d+\.?\d*)\s*千瓦'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, line)
            if matches:
                value = float(matches[0])
                # 根据组件类型和单位推断参数
                if component_type == 'Reservoir':
                    if 'm³' in line or '立方米' in line:
                        parameters['capacity'] = value
                    elif 'm' in line or '米' in line:
                        parameters['initial_level'] = value
                elif component_type in ['Pump', 'Gate']:
                    if 'm³/s' in line or '立方米每秒' in line:
                        parameters['max_flow'] = value
                    elif 'kW' in line or '千瓦' in line:
                        parameters['power'] = value
        
        return parameters
    
    def _generate_components_from_statistics(self, description: str) -> List[ComponentInfo]:
        """从统计信息生成组件"""
        components = []
        
        # 查找组件统计信息
        stat_patterns = [
            r'([水库闸门水泵泵站阀门管道渠道河道汇流点传感器受控系统水轮机])[：:]\s*(\d+)\s*个',
            r'(\d+)\s*个\s*([水库闸门水泵泵站阀门管道渠道河道汇流点传感器受控系统水轮机])'
        ]
        
        for pattern in stat_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if len(match) == 2:
                    if match[0].isdigit():
                        count, chinese_type = int(match[0]), match[1]
                    else:
                        chinese_type, count = match[0], int(match[1])
                    
                    english_type = self.component_type_reverse_map.get(chinese_type)
                    if english_type:
                        for i in range(count):
                            component = ComponentInfo(
                                name=f"{chinese_type}{i+1}",
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
        
        # 查找连接描述 - 支持更多格式
        connection_patterns = [
            r'(\w+)\s*→\s*(\w+)',  # 箭头连接
            r'(\w+)\s*->\s*(\w+)',  # 箭头连接
            r'(\w+)\s*连接\s*(\w+)',
            r'(\w+)\s*到\s*(\w+)',
            r'从\s*(\w+)\s*到\s*(\w+)',
            r'(\w+)\s*流向\s*(\w+)',
            r'(\w+)\s*输出到\s*(\w+)',
            r'(\w+)\s*接入\s*(\w+)',
            r'(\w+)\s*与\s*(\w+)\s*相连'
        ]
        
        # 首先查找具体的连接关系描述
        lines = description.split('\n')
        connection_found = False
        for line in lines:
            if '连接关系' in line or '拓扑' in line or '→' in line or '->' in line:
                connection_found = True
                for pattern in connection_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if len(match) == 2 and match[0] != match[1]:  # 避免自连接
                            # 提取连接类型
                            conn_type = 'flow'
                            if '流量' in line:
                                conn_type = 'flow'
                            elif '信号' in line:
                                conn_type = 'signal'
                            elif '控制' in line:
                                conn_type = 'control'
                            elif '数据' in line:
                                conn_type = 'data'
                            
                            connection = ConnectionInfo(
                                from_component=match[0].strip(),
                                to_component=match[1].strip(),
                                connection_type=conn_type
                            )
                            connections.append(connection)
        
        # 如果没有找到具体连接，尝试从整体描述中提取
        if not connection_found:
            for pattern in connection_patterns:
                matches = re.findall(pattern, description)
                for match in matches:
                    if len(match) == 2 and match[0] != match[1]:
                        connection = ConnectionInfo(
                            from_component=match[0].strip(),
                            to_component=match[1].strip(),
                            connection_type="flow"
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