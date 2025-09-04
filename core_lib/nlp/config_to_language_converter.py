#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件到自然语言转换器

这个模块提供了一个通用的配置文件到自然语言转换系统，支持CHS-SDK中的所有配置文件类型：
1. 传统多配置文件方式（config.yml, components.yml, topology.yml, agents.yml）
2. 统一配置文件方式（unified_config.yml）
3. 通用配置文件方式（universal_config.yml）
4. 硬编码方式（Python代码）

主要功能：
- 自动检测配置文件类型
- 解析配置文件内容
- 生成自然语言描述（建模、情景、查询、分析）
- 支持反向转换（自然语言到配置文件）
- 提供Web界面交互

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import os
import sys
import yaml
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder
from core_lib.config.enhanced_yaml_loader import EnhancedSimulationBuilder
from core_lib.config.unified_config_manager import UnifiedConfigManager, ConfigType, ConfigInfo
from core_lib.io.object_factory import ObjectFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NaturalLanguageDescription:
    """自然语言描述数据类"""
    modeling_description: str      # 建模描述
    scenario_description: str      # 情景描述
    query_description: str         # 查询描述
    analysis_description: str      # 分析描述
    summary: str                   # 总结
    technical_details: Dict[str, Any]  # 技术细节
    
class ConfigToLanguageConverter:
    """配置文件到自然语言转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = UnifiedConfigManager()
        self.object_factory = ObjectFactory()
        
        # 组件类型映射
        self.component_type_map = {
            'Reservoir': '水库',
            'Gate': '闸门',
            'Pump': '水泵',
            'PumpStation': '泵站',
            'Valve': '阀门',
            'ValveStation': '阀站',
            'Pipe': '管道',
            'Canal': '渠道',
            'Channel': '河道',
            'Junction': '汇流点',
            'Sensor': '传感器',
            'ControlledSystem': '受控系统',
            'WaterTurbine': '水轮机',
            'TurbineStation': '水轮机组'
        }
        
        # 智能体类型映射
        self.agent_type_map = {
            'PIDAgent': 'PID控制智能体',
            'MPCAgent': '模型预测控制智能体',
            'CentralMPCAgent': '中心MPC调度智能体',
            'FuzzyAgent': '模糊控制智能体',
            'NeuralAgent': '神经网络控制智能体',
            'OptimizationAgent': '优化控制智能体',
            'RuleBasedAgent': '规则控制智能体',
            'AdaptiveAgent': '自适应控制智能体',
            'LearningAgent': '学习型智能体',
            'CooperativeAgent': '协作智能体',
            'DigitalTwinAgent': '数字孪生智能体',
            'PIDControllerAgent': 'PID控制器智能体',
            'SensorAgent': '传感器智能体',
            'ActuatorAgent': '执行器智能体',
            'CentralControlAgent': '中央控制智能体',
            'LocalControlAgent': '本地控制智能体',
            'DistributedControlAgent': '分布式控制智能体',
            'MonitoringAgent': '监控智能体',
            'ControlAgent': '控制智能体'
        }
        
        # 控制策略映射
        self.control_strategy_map = {
            'pid': 'PID控制',
            'mpc': '模型预测控制',
            'fuzzy': '模糊控制',
            'neural': '神经网络控制',
            'optimization': '优化控制',
            'rule_based': '规则控制',
            'adaptive': '自适应控制',
            'centralized': '集中式控制',
            'distributed': '分布式控制',
            'hierarchical': '分层控制'
        }
        
    def convert_config_to_language(self, config_path: Union[str, Path]) -> NaturalLanguageDescription:
        """将配置文件转换为自然语言描述
        
        Args:
            config_path: 配置文件或目录路径
            
        Returns:
            NaturalLanguageDescription: 自然语言描述对象
        """
        # 检测配置类型
        config_info = self.config_manager.detect_config_type(config_path)
        
        if config_info.config_type == ConfigType.UNKNOWN:
            raise ValueError(f"无法识别的配置类型: {config_path}")
        
        # 加载配置数据
        config_data = self.config_manager.load_config(config_info)
        
        # 生成自然语言描述
        return self._generate_natural_language_description(config_info, config_data)
    
    def _generate_natural_language_description(self, config_info: ConfigInfo, 
                                             config_data: Dict[str, Any]) -> NaturalLanguageDescription:
        """生成自然语言描述"""
        
        # 根据配置类型生成描述
        if config_info.config_type == ConfigType.TRADITIONAL_MULTI:
            return self._describe_traditional_config(config_info, config_data)
        elif config_info.config_type == ConfigType.UNIFIED_SINGLE:
            return self._describe_unified_config(config_info, config_data)
        elif config_info.config_type == ConfigType.UNIVERSAL_CONFIG:
            return self._describe_universal_config(config_info, config_data)
        elif config_info.config_type == ConfigType.HARDCODED:
            return self._describe_hardcoded_config(config_info, config_data)
        else:
            raise ValueError(f"不支持的配置类型: {config_info.config_type}")
    
    def _describe_traditional_config(self, config_info: ConfigInfo, 
                                   config_data: Dict[str, Any]) -> NaturalLanguageDescription:
        """描述传统多配置文件"""
        
        # 提取基本信息
        simulation_config = config_data.get('config', {})
        components_config = config_data.get('components', {})
        topology_config = config_data.get('topology', {})
        agents_config = config_data.get('agents', {})
        
        # 生成建模描述
        modeling_desc = self._generate_modeling_description(components_config, topology_config, agents_config)
        
        # 生成情景描述
        scenario_desc = self._generate_scenario_description(simulation_config, config_info.metadata)
        
        # 生成查询描述
        query_desc = self._generate_query_description(simulation_config, components_config)
        
        # 生成分析描述
        analysis_desc = self._generate_analysis_description(agents_config, simulation_config)
        
        # 生成总结
        summary = self._generate_summary(config_info, "传统多配置文件")
        
        # 技术细节
        technical_details = {
            'config_type': '传统多配置文件',
            'files_count': len(config_info.config_files),
            'components_count': len(components_config.get('components', [])) if isinstance(components_config.get('components'), list) else len(components_config),
            'simulation_duration': simulation_config.get('simulation', {}).get('duration', 'N/A'),
            'time_step': simulation_config.get('simulation', {}).get('dt', 'N/A')
        }
        
        return NaturalLanguageDescription(
            modeling_description=modeling_desc,
            scenario_description=scenario_desc,
            query_description=query_desc,
            analysis_description=analysis_desc,
            summary=summary,
            technical_details=technical_details
        )
    
    def _describe_unified_config(self, config_info: ConfigInfo, 
                               config_data: Dict[str, Any]) -> NaturalLanguageDescription:
        """描述统一配置文件"""
        
        # 提取配置信息
        simulation_config = config_data.get('simulation', {})
        components_config = config_data.get('components', {})
        topology_config = config_data.get('topology', {})
        agents_config = config_data.get('agents', {})
        control_config = config_data.get('control', {})
        optimization_config = config_data.get('optimization', {})
        
        # 生成建模描述
        modeling_desc = self._generate_modeling_description(components_config, topology_config, agents_config)
        
        # 生成情景描述
        scenario_desc = self._generate_scenario_description(simulation_config, config_info.metadata)
        if control_config:
            scenario_desc += f"\n\n控制策略：{self._describe_control_strategy(control_config)}"
        if optimization_config:
            scenario_desc += f"\n\n优化目标：{self._describe_optimization_strategy(optimization_config)}"
        
        # 生成查询描述
        query_desc = self._generate_query_description(simulation_config, components_config)
        if 'output' in config_data:
            query_desc += f"\n\n输出配置：{self._describe_output_config(config_data['output'])}"
        
        # 生成分析描述
        analysis_desc = self._generate_analysis_description(agents_config, simulation_config)
        if optimization_config:
            analysis_desc += f"\n\n优化分析：{self._describe_optimization_analysis(optimization_config)}"
        
        # 生成总结
        summary = self._generate_summary(config_info, "统一配置文件")
        
        # 技术细节
        technical_details = {
            'config_type': '统一配置文件',
            'components_count': len(components_config),
            'simulation_duration': simulation_config.get('duration', 'N/A'),
            'time_step': simulation_config.get('time_step', 'N/A'),
            'has_control': bool(control_config),
            'has_optimization': bool(optimization_config)
        }
        
        return NaturalLanguageDescription(
            modeling_description=modeling_desc,
            scenario_description=scenario_desc,
            query_description=query_desc,
            analysis_description=analysis_desc,
            summary=summary,
            technical_details=technical_details
        )
    
    def _describe_universal_config(self, config_info: ConfigInfo, 
                                 config_data: Dict[str, Any]) -> NaturalLanguageDescription:
        """描述通用配置文件"""
        
        # 提取配置信息
        simulation_config = config_data.get('simulation', {})
        components_config = config_data.get('components', {})
        topology_config = config_data.get('topology', {})
        agents_config = config_data.get('agents', {})
        debug_config = config_data.get('debug', {})
        performance_config = config_data.get('performance', {})
        visualization_config = config_data.get('visualization', {})
        analysis_config = config_data.get('analysis', {})
        
        # 生成建模描述
        modeling_desc = self._generate_modeling_description(components_config, topology_config, agents_config)
        
        # 生成情景描述
        scenario_desc = self._generate_scenario_description(simulation_config, config_info.metadata)
        if debug_config.get('enabled'):
            scenario_desc += f"\n\n调试配置：启用了调试功能，日志级别为{debug_config.get('log_level', 'INFO')}"
        if performance_config.get('enabled'):
            scenario_desc += "\n\n性能监控：启用了性能监控功能"
        
        # 生成查询描述
        query_desc = self._generate_query_description(simulation_config, components_config)
        if visualization_config.get('enabled'):
            query_desc += f"\n\n可视化配置：{self._describe_visualization_config(visualization_config)}"
        
        # 生成分析描述
        analysis_desc = self._generate_analysis_description(agents_config, simulation_config)
        if analysis_config:
            analysis_desc += f"\n\n高级分析：{self._describe_analysis_config(analysis_config)}"
        
        # 生成总结
        summary = self._generate_summary(config_info, "通用配置文件")
        
        # 技术细节
        technical_details = {
            'config_type': '通用配置文件',
            'components_count': len(components_config),
            'simulation_duration': simulation_config.get('time', {}).get('end_time', 'N/A'),
            'time_step': simulation_config.get('time', {}).get('time_step', 'N/A'),
            'debug_enabled': debug_config.get('enabled', False),
            'performance_enabled': performance_config.get('enabled', False),
            'visualization_enabled': visualization_config.get('enabled', False),
            'analysis_enabled': bool(analysis_config)
        }
        
        return NaturalLanguageDescription(
            modeling_description=modeling_desc,
            scenario_description=scenario_desc,
            query_description=query_desc,
            analysis_description=analysis_desc,
            summary=summary,
            technical_details=technical_details
        )
    
    def _describe_hardcoded_config(self, config_info: ConfigInfo, 
                                 config_data: Dict[str, Any]) -> NaturalLanguageDescription:
        """描述硬编码配置"""
        
        python_file = config_data.get('python_file', '')
        
        # 尝试分析Python文件内容
        modeling_desc = "硬编码建模：通过Python代码直接构建仿真系统"
        scenario_desc = f"硬编码情景：使用Python脚本 {Path(python_file).name} 定义仿真场景"
        query_desc = "硬编码查询：通过代码逻辑控制数据输出和查询"
        analysis_desc = "硬编码分析：分析逻辑直接嵌入在Python代码中"
        
        # 尝试读取Python文件获取更多信息
        if os.path.exists(python_file):
            try:
                with open(python_file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                    
                # 简单的代码分析
                if 'Reservoir' in code_content:
                    modeling_desc += "，包含水库组件"
                if 'Gate' in code_content:
                    modeling_desc += "，包含闸门组件"
                if 'Agent' in code_content:
                    analysis_desc += "，包含智能体控制逻辑"
                    
            except Exception as e:
                self.logger.warning(f"无法读取Python文件 {python_file}: {e}")
        
        # 生成总结
        summary = self._generate_summary(config_info, "硬编码配置")
        
        # 技术细节
        technical_details = {
            'config_type': '硬编码配置',
            'python_file': python_file,
            'language': 'Python'
        }
        
        return NaturalLanguageDescription(
            modeling_description=modeling_desc,
            scenario_description=scenario_desc,
            query_description=query_desc,
            analysis_description=analysis_desc,
            summary=summary,
            technical_details=technical_details
        )
    
    def _generate_modeling_description(self, components_config: Dict[str, Any], 
                                     topology_config: Dict[str, Any],
                                     agents_config: Dict[str, Any] = None) -> str:
        """生成建模描述"""
        if not components_config:
            return "建模描述：未定义系统组件"
        
        desc = "建模描述：\n"
        
        # 处理组件配置
        if isinstance(components_config, dict):
            if 'components' in components_config:
                # 传统格式
                components = components_config['components']
            else:
                # 统一格式
                components = components_config
        else:
            components = components_config
        
        # 统计组件类型
        component_types = {}
        component_details = []
        
        if isinstance(components, list):
            for comp in components:
                # 确保comp是字典类型
                if not isinstance(comp, dict):
                    self.logger.warning(f"跳过非字典类型的组件: {comp}")
                    continue
                    
                comp_type = comp.get('class', comp.get('type', '未知'))
                comp_name = comp.get('id', comp.get('name', '未命名'))
                component_types[comp_type] = component_types.get(comp_type, 0) + 1
                
                # 获取中文名称
                chinese_type = self.component_type_map.get(comp_type, comp_type)
                component_details.append(f"  - {comp_name}：{chinese_type}")
                
        elif isinstance(components, dict):
            for comp_name, comp_config in components.items():
                # 确保comp_config是字典类型
                if not isinstance(comp_config, dict):
                    self.logger.warning(f"跳过非字典类型的组件配置: {comp_name} -> {comp_config}")
                    continue
                    
                comp_type = comp_config.get('class', comp_config.get('type', '未知'))
                component_types[comp_type] = component_types.get(comp_type, 0) + 1
                
                # 获取中文名称
                chinese_type = self.component_type_map.get(comp_type, comp_type)
                component_details.append(f"  - {comp_name}：{chinese_type}")
        
        # 生成组件类型统计
        if component_types:
            desc += "系统包含以下组件类型：\n"
            for comp_type, count in component_types.items():
                chinese_type = self.component_type_map.get(comp_type, comp_type)
                desc += f"  - {chinese_type}：{count}个\n"
            
            desc += "\n具体组件：\n"
            desc += "\n".join(component_details)
        
        # 处理拓扑连接
        if topology_config:
            connections = topology_config.get('connections', topology_config.get('topology', []))
            if connections:
                desc += f"\n\n系统拓扑：包含{len(connections)}个连接关系\n"
                desc += "具体连接关系：\n"
                for i, conn in enumerate(connections, 1):
                    # 确保conn是字典类型
                    if not isinstance(conn, dict):
                        self.logger.warning(f"跳过非字典类型的连接: {conn}")
                        continue
                        
                    # 支持多种连接格式
                    upstream = conn.get('upstream', conn.get('from', conn.get('source', '未知')))
                    downstream = conn.get('downstream', conn.get('to', conn.get('target', '未知')))
                    conn_type = conn.get('type', conn.get('connection_type', '流量'))
                    desc += f"  {i}. {upstream} → {downstream} ({conn_type}连接)\n"
        
        # 处理智能体配置
        if agents_config:
            agents = agents_config
            if isinstance(agents_config, dict) and 'agents' in agents_config:
                agents = agents_config['agents']
            
            if agents:
                desc += f"\n\n智能体系统：包含{len(agents) if isinstance(agents, (list, dict)) else 0}个智能体\n"
                desc += "具体智能体：\n"
                
                if isinstance(agents, list):
                    for i, agent in enumerate(agents, 1):
                        # 确保agent是字典类型
                        if not isinstance(agent, dict):
                            self.logger.warning(f"跳过非字典类型的智能体: {agent}")
                            continue
                            
                        agent_id = agent.get('id', f'agent_{i}')
                        agent_class = agent.get('class', agent.get('type', '未知类型'))
                        agent_config = agent.get('config', {})
                        
                        # 获取中文描述
                        chinese_type = self.agent_type_map.get(agent_class, agent_class)
                        desc += f"  {i}. {agent_id}：{chinese_type}\n"
                        
                        # 添加智能体配置详情
                        if agent_config:
                            if 'simulated_object_id' in agent_config:
                                desc += f"     - 监控对象：{agent_config['simulated_object_id']}\n"
                            if 'state_topic' in agent_config:
                                desc += f"     - 状态主题：{agent_config['state_topic']}\n"
                            if 'subscribed_topic' in agent_config:
                                desc += f"     - 订阅主题：{agent_config['subscribed_topic']}\n"
                            if 'controlled_object_id' in agent_config:
                                desc += f"     - 控制对象：{agent_config['controlled_object_id']}\n"
                            if 'target_setpoint' in agent_config:
                                desc += f"     - 目标设定值：{agent_config['target_setpoint']}\n"
                            if 'pid_gains' in agent_config:
                                gains = agent_config['pid_gains']
                                desc += f"     - PID参数：Kp={gains.get('kp', 'N/A')}, Ki={gains.get('ki', 'N/A')}, Kd={gains.get('kd', 'N/A')}\n"
                                
                elif isinstance(agents, dict):
                    for i, (agent_id, agent_config) in enumerate(agents.items(), 1):
                        # 确保agent_config是字典类型
                        if not isinstance(agent_config, dict):
                            self.logger.warning(f"跳过非字典类型的智能体配置: {agent_id} -> {agent_config}")
                            continue
                            
                        agent_class = agent_config.get('class', agent_config.get('type', '未知类型'))
                        
                        # 获取中文描述
                        chinese_type = self.agent_type_map.get(agent_class, agent_class)
                        desc += f"  {i}. {agent_id}：{chinese_type}\n"
                        
                        # 添加智能体配置详情
                        if isinstance(agent_config, dict):
                            if 'target' in agent_config:
                                desc += f"     - 控制目标：{agent_config['target']}\n"
                            if 'parameters' in agent_config:
                                params = agent_config['parameters']
                                if isinstance(params, dict):
                                    for key, value in params.items():
                                        desc += f"     - {key}：{value}\n"
        
        return desc
    
    def _generate_scenario_description(self, simulation_config: Dict[str, Any], 
                                     metadata: Dict[str, Any]) -> str:
        """生成情景描述"""
        desc = "情景描述：\n"
        
        # 从元数据获取基本信息
        if metadata:
            name = metadata.get('name', '')
            description = metadata.get('description', '')
            if name:
                desc += f"仿真名称：{name}\n"
            if description:
                desc += f"仿真描述：{description}\n"
        
        # 从仿真配置获取时间信息
        if simulation_config:
            # 处理不同的时间配置格式
            time_config = simulation_config.get('time', simulation_config)
            
            duration = time_config.get('duration', time_config.get('end_time', 'N/A'))
            time_step = time_config.get('dt', time_config.get('time_step', 'N/A'))
            
            if duration != 'N/A':
                desc += f"仿真时长：{duration}秒\n"
            if time_step != 'N/A':
                desc += f"时间步长：{time_step}秒\n"
            
            # 求解器信息
            solver = simulation_config.get('solver', time_config.get('solver', {}))
            if solver:
                if isinstance(solver, str):
                    desc += f"求解器：{solver}\n"
                elif isinstance(solver, dict):
                    solver_type = solver.get('type', solver.get('method', 'N/A'))
                    if solver_type != 'N/A':
                        desc += f"求解器：{solver_type}\n"
        
        return desc
    
    def _generate_query_description(self, simulation_config: Dict[str, Any], 
                                  components_config: Dict[str, Any]) -> str:
        """生成查询描述"""
        desc = "查询描述：\n"
        desc += "系统将输出以下数据：\n"
        desc += "  - 各组件的状态变量时间序列\n"
        desc += "  - 系统性能指标\n"
        desc += "  - 控制信号和响应\n"
        
        # 根据组件类型添加具体的输出描述
        if components_config:
            desc += "\n具体输出变量包括：\n"
            
            # 分析组件类型并生成相应的输出描述
            component_types = set()
            if isinstance(components_config, dict):
                if 'components' in components_config:
                    components = components_config['components']
                else:
                    components = components_config
                    
                if isinstance(components, list):
                    for comp in components:
                        if isinstance(comp, dict):
                            comp_type = comp.get('class', comp.get('type', ''))
                            component_types.add(comp_type)
                elif isinstance(components, dict):
                    for comp_config in components.values():
                        if isinstance(comp_config, dict):
                            comp_type = comp_config.get('class', comp_config.get('type', ''))
                            component_types.add(comp_type)
            
            # 根据组件类型生成输出描述
            for comp_type in component_types:
                if comp_type in ['Reservoir', 'reservoir']:
                    desc += "  - 水库水位、库容、入流、出流\n"
                elif comp_type in ['Gate', 'gate']:
                    desc += "  - 闸门开度、流量、水位差\n"
                elif comp_type in ['Pump', 'pump', 'PumpStation']:
                    desc += "  - 水泵功率、流量、效率\n"
                elif comp_type in ['ControlledSystem']:
                    desc += "  - 系统状态、控制输入、输出响应\n"
        
        return desc
    
    def _generate_analysis_description(self, agents_config: Dict[str, Any], 
                                     simulation_config: Dict[str, Any]) -> str:
        """生成分析描述"""
        desc = "分析描述：\n"
        
        if not agents_config:
            desc += "系统采用开环控制，主要进行系统响应分析\n"
            desc += "分析内容包括：\n"
            desc += "  - 系统动态响应特性\n"
            desc += "  - 稳态性能评估\n"
            desc += "  - 参数敏感性分析\n"
        else:
            desc += "系统采用智能体控制，进行闭环控制分析\n"
            
            # 分析智能体类型
            agent_types = set()
            if isinstance(agents_config, dict):
                if 'agents' in agents_config:
                    agents = agents_config['agents']
                else:
                    agents = agents_config
                    
                if isinstance(agents, list):
                    for agent in agents:
                        if isinstance(agent, dict):
                            agent_type = agent.get('class', agent.get('type', ''))
                            agent_types.add(agent_type)
                elif isinstance(agents, dict):
                    for agent_config in agents.values():
                        if isinstance(agent_config, dict):
                            agent_type = agent_config.get('class', agent_config.get('type', ''))
                            agent_types.add(agent_type)
            
            desc += "控制策略分析：\n"
            for agent_type in agent_types:
                chinese_type = self.agent_type_map.get(agent_type, agent_type)
                desc += f"  - {chinese_type}性能分析\n"
            
            desc += "\n控制性能评估：\n"
            desc += "  - 跟踪精度分析\n"
            desc += "  - 稳定性评估\n"
            desc += "  - 鲁棒性测试\n"
            desc += "  - 控制效率分析\n"
        
        return desc
    
    def _describe_control_strategy(self, control_config: Dict[str, Any]) -> str:
        """描述控制策略"""
        if not control_config:
            return "无特定控制策略"
        
        strategy_type = control_config.get('type', '')
        chinese_strategy = self.control_strategy_map.get(strategy_type, strategy_type)
        
        desc = f"采用{chinese_strategy}"
        
        if control_config.get('enabled'):
            desc += "（已启用）"
        
        return desc
    
    def _describe_optimization_strategy(self, optimization_config: Dict[str, Any]) -> str:
        """描述优化策略"""
        if not optimization_config:
            return "无优化配置"
        
        desc = "优化目标："
        
        objective = optimization_config.get('objective', {})
        if isinstance(objective, dict):
            obj_type = objective.get('type', '')
            if obj_type:
                desc += f"采用{obj_type}优化"
        
        target_vars = optimization_config.get('target_variables', [])
        if target_vars:
            desc += f"，优化变量包括{len(target_vars)}个参数"
        
        return desc
    
    def _describe_output_config(self, output_config: Dict[str, Any]) -> str:
        """描述输出配置"""
        if not output_config:
            return "默认输出配置"
        
        # 确保output_config是字典类型
        if not isinstance(output_config, dict):
            self.logger.warning(f"输出配置不是字典类型: {type(output_config)}")
            return "输出配置格式错误"
        
        desc = ""
        
        output_format = output_config.get('format', '')
        if output_format:
            desc += f"输出格式：{output_format}"
        
        save_path = output_config.get('save_path', '')
        if save_path:
            desc += f"，保存路径：{save_path}"
        
        variables = output_config.get('variables', [])
        if variables:
            desc += f"，输出变量：{len(variables)}个"
        
        return desc
    
    def _describe_visualization_config(self, viz_config: Dict[str, Any]) -> str:
        """描述可视化配置"""
        if not viz_config:
            return "未启用可视化"
        
        # 确保viz_config是字典类型
        if not isinstance(viz_config, dict):
            self.logger.warning(f"可视化配置不是字典类型: {type(viz_config)}")
            return "可视化配置格式错误"
        
        if not viz_config.get('enabled'):
            return "未启用可视化"
        
        desc = "启用了可视化功能"
        
        plots_config = viz_config.get('plots', {})
        if isinstance(plots_config, dict) and plots_config.get('enabled'):
            desc += "，包括图表绘制"
        
        real_time = viz_config.get('real_time', {})
        if isinstance(real_time, dict) and real_time.get('enabled'):
            desc += "，支持实时可视化"
        
        return desc
    
    def _describe_analysis_config(self, analysis_config: Dict[str, Any]) -> str:
        """描述分析配置"""
        if not analysis_config:
            return "无高级分析配置"
        
        # 确保analysis_config是字典类型
        if not isinstance(analysis_config, dict):
            self.logger.warning(f"分析配置不是字典类型: {type(analysis_config)}")
            return "分析配置格式错误"
        
        desc = "包含以下分析功能："
        
        if analysis_config.get('control_performance', {}).get('enabled'):
            desc += "\n  - 控制性能分析"
        
        if analysis_config.get('system_identification', {}).get('enabled'):
            desc += "\n  - 系统辨识"
        
        if analysis_config.get('statistical_analysis', {}).get('enabled'):
            desc += "\n  - 统计分析"
        
        return desc
    
    def _describe_optimization_analysis(self, optimization_config: Dict[str, Any]) -> str:
        """描述优化分析"""
        if not optimization_config:
            return "无优化分析"
        
        desc = "优化分析包括："
        desc += "\n  - 目标函数收敛性分析"
        desc += "\n  - 约束满足情况评估"
        desc += "\n  - 优化算法性能评价"
        
        return desc
    
    def _generate_summary(self, config_info: ConfigInfo, config_type_name: str) -> str:
        """生成总结"""
        summary = f"配置文件总结：\n"
        summary += f"配置类型：{config_type_name}\n"
        summary += f"配置路径：{config_info.config_path}\n"
        summary += f"配置描述：{config_info.description}\n"
        
        if config_info.metadata:
            name = config_info.metadata.get('name', '')
            if name:
                summary += f"仿真名称：{name}\n"
        
        # 推荐的运行器
        runner = self.config_manager.get_runner_recommendation(config_info)
        summary += f"推荐运行器：{runner}\n"
        
        return summary
    
    def save_description_to_file(self, description: NaturalLanguageDescription, 
                               output_path: Union[str, Path]) -> None:
        """保存自然语言描述到文件
        
        Args:
            description: 自然语言描述对象
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成Markdown格式的报告
        content = f"# 配置文件自然语言描述报告\n\n"
        content += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        content += f"## {description.summary}\n\n"
        
        content += f"## 建模描述\n\n{description.modeling_description}\n\n"
        
        content += f"## 情景描述\n\n{description.scenario_description}\n\n"
        
        content += f"## 查询描述\n\n{description.query_description}\n\n"
        
        content += f"## 分析描述\n\n{description.analysis_description}\n\n"
        
        content += f"## 技术细节\n\n"
        for key, value in description.technical_details.items():
            content += f"- **{key}**: {value}\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"自然语言描述已保存到: {output_path}")


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='配置文件到自然语言转换器')
    parser.add_argument('config_path', help='配置文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件路径', default='config_description.md')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建转换器
        converter = ConfigToLanguageConverter()
        
        # 转换配置文件
        description = converter.convert_config_to_language(args.config_path)
        
        # 保存结果
        converter.save_description_to_file(description, args.output)
        
        print(f"转换完成！结果已保存到: {args.output}")
        
    except Exception as e:
        print(f"转换失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()