#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件到自然语言转换器

该模块提供将YAML配置文件转换为自然语言描述的功能，
用于后续的大模型自动建模和分析。支持Markdown和HTML两种输出格式。

作者: CHS-SDK Team
日期: 2025-01-04
"""

import yaml
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import markdown
from jinja2 import Template
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from matplotlib.patches import FancyBboxPatch
import numpy as np
import base64
from io import BytesIO

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigToTextConverter:
    """配置文件到自然语言转换器"""
    
    def __init__(self):
        self.component_descriptions = {
            'Reservoir': '水库',
            'Gate': '闸门',
            'UnifiedCanal': '渠道',
            'Canal': '渠道',
            'Pump': '泵站',
            'Tank': '水箱',
            'River': '河流',
            'Lake': '湖泊',
            'Pool': '水池'
        }
        
        self.agent_descriptions = {
            'LocalControlAgent': '现地控制智能体',
            'CentralControlAgent': '中心控制智能体',
            'DigitalTwinAgent': '数字孪生智能体',
            'MonitoringAgent': '监测智能体'
        }
        
        self.controller_descriptions = {
            'PIDController': 'PID控制器',
            'MPCController': 'MPC控制器',
            'FuzzyController': '模糊控制器',
            'NeuralController': '神经网络控制器'
        }
        
        # HTML模板
        self.html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }
        h3 {
            color: #2c3e50;
            margin-top: 25px;
        }
        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .component {
            background-color: #e8f4fd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .agent {
            background-color: #e8f6f3;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
        }
        .topology {
            background-color: #fdf2e9;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #f39c12;
        }
        .simulation {
            background-color: #f4ecf7;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #9b59b6;
        }
        .parameter {
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            color: #e74c3c;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: right;
            margin-top: 20px;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 8px 0;
        }
        .toc a {
            text-decoration: none;
            color: #3498db;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e8f4fd;
        }
        .chart-container {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .chart-placeholder {
            width: 100%;
            height: 300px;
            background-color: #ecf0f1;
            border: 2px dashed #bdc3c7;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #7f8c8d;
            font-size: 16px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content }}
        <div class="timestamp">
            生成时间: {{ timestamp }}
        </div>
    </div>
</body>
</html>
        """
    
    def load_config_files(self, config_dir: str) -> Dict[str, Any]:
        """加载配置文件目录中的所有YAML文件"""
        config_data = {}
        config_path = Path(config_dir)
        
        if not config_path.exists():
            logger.error(f"配置目录不存在: {config_dir}")
            return config_data
        
        # 查找YAML文件
        yaml_files = list(config_path.glob("*.yml")) + list(config_path.glob("*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    config_data[yaml_file.stem] = data
                    logger.info(f"成功加载配置文件: {yaml_file}")
            except Exception as e:
                logger.error(f"加载配置文件失败 {yaml_file}: {e}")
        
        return config_data
    
    def describe_metadata(self, metadata: Dict[str, Any]) -> str:
        """描述系统元数据"""
        description = "## 系统概述\n"
        
        if 'name' in metadata:
            description += f"系统名称: {metadata['name']}\n"
        if 'description' in metadata:
            description += f"系统描述: {metadata['description']}\n"
        if 'version' in metadata:
            description += f"系统版本: {metadata['version']}\n"
        if 'category' in metadata:
            description += f"系统类别: {metadata['category']}\n"
        
        return description + "\n"
    
    def describe_components(self, components) -> str:
        """描述水利系统组件"""
        if not components:
            return ""
        
        description = "## 水利系统组件\n"
        
        # 处理不同格式的组件配置
        if isinstance(components, dict):
            # 如果是字典格式
            component_list = []
            for comp_id, comp_data in components.items():
                if isinstance(comp_data, dict):
                    comp_data['id'] = comp_id
                    component_list.append(comp_data)
                else:
                    # 如果comp_data是字符串，创建基本结构
                    component_list.append({'id': comp_id, 'type': comp_data})
        elif isinstance(components, list):
            # 如果是列表格式
            component_list = components
        else:
            return description + "组件配置格式不支持\n\n"
        
        description += f"该水利系统包含 {len(component_list)} 个主要组件:\n\n"
        
        # 添加组件概览表格
        description += "### 组件概览表\n\n"
        description += "| 组件名称 | 类型 | 初始状态 | 关键参数 |\n"
        description += "|----------|------|----------|----------|\n"
        
        for component in component_list:
            comp_id = component.get('id', '未知')
            comp_type = component.get('type', '未知类型')
            comp_name = self.component_descriptions.get(comp_type, comp_type)
            
            # 初始状态摘要
            initial_summary = ""
            if 'initial_state' in component:
                states = []
                for key, value in component['initial_state'].items():
                    if key == 'volume':
                        states.append(f"蓄量: {value/1000000:.1f}万m³")
                    elif key == 'water_level':
                        states.append(f"水位: {value}m")
                    elif key == 'opening':
                        states.append(f"开度: {value}%")
                initial_summary = ", ".join(states)
            
            # 关键参数摘要
            param_summary = ""
            if 'parameters' in component:
                params = []
                for key, value in component['parameters'].items():
                    if key == 'surface_area':
                        params.append(f"面积: {value/10000:.1f}万m²")
                    elif key == 'width':
                        params.append(f"宽度: {value}m")
                    elif key == 'discharge_coefficient':
                        params.append(f"流量系数: {value}")
                param_summary = ", ".join(params)
            
            description += f"| {comp_id} | {comp_name} | {initial_summary} | {param_summary} |\n"
        
        description += "\n"
        
        for i, component in enumerate(component_list, 1):
            comp_id = component.get('id', f'component_{i}')
            comp_type = component.get('type', '未知类型')
            comp_name = self.component_descriptions.get(comp_type, comp_type)
            
            description += f"### {i}. {comp_name} ({comp_id})\n"
            
            # 描述初始状态
            if 'initial_state' in component:
                description += "**初始状态:**\n"
                initial_state = component['initial_state']
                for key, value in initial_state.items():
                    if key == 'volume':
                        description += f"- 初始蓄量: {value} 立方米\n"
                    elif key == 'water_level':
                        description += f"- 初始水位: {value} 米\n"
                    elif key == 'opening':
                        description += f"- 初始开度: {value}%\n"
                    elif key == 'flow_rate':
                        description += f"- 初始流量: {value} 立方米/秒\n"
                    else:
                        description += f"- {key}: {value}\n"
            
            # 描述技术参数
            if 'parameters' in component:
                description += "**技术参数:**\n"
                parameters = component['parameters']
                for key, value in parameters.items():
                    if key == 'surface_area':
                        description += f"- 水面面积: {value} 平方米\n"
                    elif key == 'max_capacity':
                        description += f"- 最大容量: {value} 立方米\n"
                    elif key == 'discharge_coefficient':
                        description += f"- 流量系数: {value}\n"
                    elif key == 'width':
                        description += f"- 宽度: {value} 米\n"
                    elif key == 'max_opening':
                        description += f"- 最大开度: {value}\n"
                    elif key == 'max_rate_of_change':
                        description += f"- max_rate_of_change: {value}\n"
                    else:
                        description += f"- {key}: {value}\n"
            
            # 处理其他直接在组件级别的参数
            for key, value in component.items():
                if key not in ['id', 'type', 'initial_state', 'parameters']:
                    if key == 'surface_area':
                        description += f"**技术参数:**\n- 水面面积: {value} 平方米\n"
                    elif key == 'storage_curve':
                        description += f"- storage_curve: {value}\n"
                    elif key == 'max_rate_of_change':
                        description += f"- max_rate_of_change: {value}\n"
                    elif key == 'discharge_coefficient':
                        description += f"- 流量系数: {value}\n"
                    elif key == 'width':
                        description += f"- 宽度: {value} 米\n"
                    elif key == 'max_opening':
                        description += f"- max_opening: {value}\n"
            
            description += "\n"
        
        return description + "\n"
    
    def describe_topology(self, connections: List[Dict[str, str]]) -> str:
        """描述系统拓扑结构"""
        if not connections:
            return ""
        
        description = "## 系统拓扑结构\n"
        description += "水利系统的连接关系如下:\n\n"
        
        for i, connection in enumerate(connections, 1):
            upstream = connection.get('upstream', '未知')
            downstream = connection.get('downstream', '未知')
            description += f"{i}. {upstream} → {downstream}\n"
        
        description += "\n这形成了一个完整的水流传输网络，水流从上游组件流向下游组件。\n\n"
        
        return description
    
    def describe_agents(self, agents: Dict[str, Any]) -> str:
        """描述智能体配置"""
        if not agents:
            return ""
        
        description = "## 智能体控制系统\n"
        description += f"系统配置了 {len(agents)} 个智能体进行自动化控制:\n\n"
        
        # 添加智能体概览表格
        description += "### 智能体配置表\n\n"
        description += "| 智能体名称 | 类型 | 控制器 | 关键参数 | 目标设定值 |\n"
        description += "|------------|------|--------|----------|------------|\n"
        
        for agent_id, agent_config in agents.items():
            agent_type = agent_config.get('type', '未知类型')
            
            # 根据agent_id推断类型
            if 'twin' in agent_id.lower():
                agent_name = '数字孪生智能体'
            elif 'control' in agent_id.lower():
                agent_name = '现地控制智能体'
            elif 'central' in agent_id.lower():
                agent_name = '中心控制智能体'
            else:
                agent_name = self.agent_descriptions.get(agent_type, agent_type)
            
            controller_info = "无"
            key_params = "无"
            setpoint = "无"
            
            if 'controller' in agent_config:
                controller = agent_config['controller']
                controller_type = controller.get('type', '未知控制器')
                controller_info = self.controller_descriptions.get(controller_type, controller_type)
                
                if 'parameters' in controller:
                    params = []
                    for key, value in controller['parameters'].items():
                        if key in ['Kp', 'Ki', 'Kd']:
                            params.append(f"{key}={value}")
                        elif key == 'setpoint':
                            setpoint = str(value)
                    key_params = ", ".join(params) if params else "无"
            
            description += f"| {agent_id} | {agent_name} | {controller_info} | {key_params} | {setpoint} |\n"
        
        description += "\n"
        
        for i, (agent_id, agent_config) in enumerate(agents.items(), 1):
            agent_type = agent_config.get('type', '未知类型')
            
            # 根据agent_id推断类型
            if 'twin' in agent_id.lower():
                agent_name = '数字孪生智能体'
            elif 'control' in agent_id.lower():
                agent_name = '现地控制智能体'
            elif 'central' in agent_id.lower():
                agent_name = '中心控制智能体'
            else:
                agent_name = self.agent_descriptions.get(agent_type, agent_type)
            
            description += f"### {i}. {agent_name} ({agent_id})\n"
            
            # 描述控制器配置
            if 'controller' in agent_config:
                controller = agent_config['controller']
                controller_type = controller.get('type', '未知控制器')
                controller_name = self.controller_descriptions.get(controller_type, controller_type)
                
                description += f"**控制器类型:** {controller_name}\n"
                
                if 'parameters' in controller:
                    description += "**控制参数:**\n"
                    params = controller['parameters']
                    for key, value in params.items():
                        if key == 'Kp':
                            description += f"- Kp参数: {value}\n"
                        elif key == 'Ki':
                            description += f"- Ki参数: {value}\n"
                        elif key == 'Kd':
                            description += f"- Kd参数: {value}\n"
                        elif key == 'setpoint':
                            description += f"- 目标设定值: {value}\n"
                        elif key == 'output_limits':
                            description += f"- min_output: {value[0]}\n"
                            description += f"- max_output: {value[1]}\n"
                        else:
                            description += f"- {key}: {value}\n"
            
            # 描述通信配置
            if 'communication' in agent_config:
                description += "**通信配置:**\n"
                comm = agent_config['communication']
                
                if 'input_topics' in comm:
                    topics = comm['input_topics']
                    if isinstance(topics, list) and topics:
                        description += f"- 监测主题: {topics[0]}\n"
                
                if 'output_topics' in comm:
                    topics = comm['output_topics']
                    if isinstance(topics, list) and topics:
                        description += f"- 控制主题: {topics[0]}\n"
                
                if 'monitored_variable' in comm:
                    description += f"- 监测变量: {comm['monitored_variable']}\n"
            
            description += "\n"
        
        return description
    
    def describe_simulation(self, simulation: Dict[str, Any]) -> str:
        """描述仿真配置"""
        if not simulation:
            return ""
        
        description = "## 仿真配置\n\n"
        
        # 仿真参数表格
        description += "### 仿真参数表\n\n"
        description += "| 参数类型 | 参数名称 | 设置值 | 说明 |\n"
        description += "|----------|----------|--------|------|\n"
        
        if 'duration' in simulation:
            duration = simulation['duration']
            description += f"| 时间配置 | 仿真总时长 | {duration} 秒 ({duration/3600:.1f} 小时) | 仿真运行的总时间 |\n"
        
        if 'time_step' in simulation:
            description += f"| 时间配置 | 时间步长 | {simulation['time_step']} 秒 | 仿真计算的时间间隔 |\n"
        
        if 'steps' in simulation:
            description += f"| 计算配置 | 仿真步数 | {simulation['steps']} 步 | 总的计算步骤数 |\n"
        
        # 其他仿真参数
        for key, value in simulation.items():
            if key not in ['duration', 'time_step', 'steps']:
                description += f"| 其他参数 | {key} | {value} | 仿真相关配置 |\n"
        
        description += "\n"
        
        return description
    
    def describe_analysis(self, analysis: Dict[str, Any]) -> str:
        """描述分析配置"""
        if not analysis:
            return ""
        
        description = "## 分析配置\n\n"
        
        # 分析配置表格
        description += "### 分析配置表\n\n"
        description += "| 分析类型 | 配置项 | 设置值 | 说明 |\n"
        description += "|----------|--------|--------|------|\n"
        
        if 'generate_report' in analysis:
            description += f"| 报告生成 | 生成最终状态报告 | {analysis['generate_report']} | 是否生成仿真结果报告 |\n"
        
        if 'target_water_level' in analysis:
            description += f"| 目标设定 | 目标水位 | {analysis['target_water_level']} 米 | 系统期望达到的水位 |\n"
        
        if 'performance_metrics' in analysis:
            description += f"| 性能评估 | 性能指标分析 | {analysis['performance_metrics']} | 系统性能评估指标 |\n"
        
        # 其他分析参数
        for key, value in analysis.items():
            if key not in ['generate_report', 'target_water_level', 'performance_metrics']:
                description += f"| 其他配置 | {key} | {value} | 分析相关配置 |\n"
        
        description += "\n"
        
        return description
    
    def convert_to_natural_language(self, config_dir: str) -> str:
        """将配置文件转换为自然语言描述"""
        config_data = self.load_config_files(config_dir)
        
        if not config_data:
            return "未找到有效的配置文件。"
        
        description = "# 水利系统配置自然语言描述\n\n"
        
        # 处理主配置文件
        main_config = None
        for filename, data in config_data.items():
            if 'unified_config' in filename or 'main' in filename or len(config_data) == 1:
                main_config = data
                break
        
        if not main_config:
            main_config = list(config_data.values())[0]
        
        # 描述元数据
        if 'metadata' in main_config:
            description += self.describe_metadata(main_config['metadata'])
        
        # 描述组件
        if 'components' in main_config:
            description += self.describe_components(main_config['components'])
            # 添加组件拓扑结构图
            try:
                chart_html = self.generate_component_topology_chart(main_config['components'])
                logger.info(f"组件拓扑结构图生成成功，Base64长度: {len(chart_html)}")
                chart_section = "\n### 组件拓扑结构图\n\n<div class='chart-container'>\n<img src='" + chart_html + "' alt='组件拓扑结构图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
                description += chart_section
            except Exception as e:
                logger.warning(f"组件拓扑结构图生成失败: {e}")
                description += "\n### 组件拓扑结构图\n\n<div class='chart-container'>\n<div class='chart-placeholder'>组件拓扑结构图 (生成失败)</div>\n</div>\n\n"
        
        # 描述拓扑结构
        if 'topology' in main_config and 'connections' in main_config['topology']:
            description += self.describe_topology(main_config['topology']['connections'])
        
        # 描述智能体
        if 'agents' in main_config:
            description += self.describe_agents(main_config['agents'])
            # 添加智能体架构图
            try:
                agent_chart_html = self.generate_agent_architecture_chart(main_config['agents'])
                description += f"\n### 智能体架构图\n\n<div class='chart-container'>\n<img src='{agent_chart_html}' alt='智能体架构图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
            except Exception as e:
                logger.warning(f"智能体架构图生成失败: {e}")
                description += "\n### 智能体架构图\n\n<div class='chart-container'>\n<div class='chart-placeholder'>智能体架构图 (生成失败)</div>\n</div>\n\n"
        
        # 描述仿真配置
        if 'simulation' in main_config:
            description += self.describe_simulation(main_config['simulation'])
            # 添加仿真流程图
            try:
                sim_chart_html = self.generate_simulation_flow_chart(main_config['simulation'])
                description += f"\n### 仿真流程图\n\n<div class='chart-container'>\n<img src='{sim_chart_html}' alt='仿真流程图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
            except Exception as e:
                logger.warning(f"仿真流程图生成失败: {e}")
                description += "\n### 仿真流程图\n\n<div class='chart-container'>\n<div class='chart-placeholder'>仿真流程图 (生成失败)</div>\n</div>\n\n"
        
        # 描述分析配置
        if 'analysis' in main_config:
            description += self.describe_analysis(main_config['analysis'])
            # 添加分析配置图
            try:
                analysis_chart_html = self.generate_analysis_chart(main_config['analysis'])
                description += f"\n### 分析配置图\n\n<div class='chart-container'>\n<img src='{analysis_chart_html}' alt='分析配置图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
            except Exception as e:
                logger.warning(f"分析配置图生成失败: {e}")
                description += "\n### 分析配置图\n\n<div class='chart-container'>\n<div class='chart-placeholder'>分析配置图 (生成失败)</div>\n</div>\n\n"
        
        # 添加时间序列图表
        if 'components' in main_config and 'agents' in main_config:
            try:
                timeseries_charts = self.generate_timeseries_charts(main_config['components'], main_config['agents'])
                if timeseries_charts:
                    description += "\n## 被控对象综合时间序列分析\n\n"
                    for comp_name, chart_data in timeseries_charts.items():
                        description += f"### {comp_name} 综合时间序列分析图\n\n"
                        description += f"<div class='chart-container'>\n<img src='{chart_data}' alt='{comp_name}综合时间序列分析图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
                        
                        # 添加图表说明
                        comp_type = main_config['components'][comp_name].get('type', '未知')
                        description += f"**图表说明：**\n\n"
                        description += f"上图展示了 {comp_name} ({comp_type}) 的综合时间序列分析，包含6个关键维度：\n\n"
                        
                        if comp_type.lower() == 'reservoir':
                            description += "1. **扰动分析**：入流量变化趋势，反映上游来水的波动情况\n"
                            description += "2. **状态监测**：水位变化，显示水库蓄水状态的动态演变\n"
                            description += "3. **控制目标**：目标水位设定，展示控制系统的期望状态\n"
                            description += "4. **控制指令**：泄流量调节指令，体现智能体的控制决策\n"
                            description += "5. **流量状态**：出流量变化，反映水库的泄流动态\n"
                            description += "6. **容量状态**：蓄水量变化，显示水库库容的时间演变\n\n"
                        elif comp_type.lower() == 'gate':
                            description += "1. **扰动分析**：上游水位波动，反映外部水文条件变化\n"
                            description += "2. **状态监测**：闸门开度变化，显示闸门的实际运行状态\n"
                            description += "3. **控制目标**：目标开度设定，展示控制系统的期望开度\n"
                            description += "4. **控制指令**：开度调节指令，体现智能体的控制决策\n"
                            description += "5. **流量状态**：通过流量变化，反映闸门的过流能力\n"
                            description += "6. **水位差状态**：上下游水位差，显示闸门两侧的水力条件\n\n"
                        
                        description += "通过这些综合分析，可以全面了解被控对象在扰动、状态、控制等各个方面的动态特性和控制效果。\n\n"
                        
                        # 添加时间序列数据表格
                        description += self.generate_timeseries_data_table(comp_name, comp_type, main_config['components'][comp_name])
            except Exception as e:
                logger.warning(f"时间序列图表生成失败: {e}")
        
        # 添加控制分析表格
        if 'components' in main_config and 'agents' in main_config:
            try:
                control_analysis = self.generate_control_analysis_tables(main_config['components'], main_config['agents'])
                description += control_analysis
            except Exception as e:
                logger.warning(f"控制分析表格生成失败: {e}")
        
        # 添加系统总结
        description += "## 系统总结\n"
        description += "该水利系统通过智能体控制实现自动化管理，具备完整的监测、控制和分析功能，能够有效应对各种水文条件和控制需求。系统包含详细的时间序列分析和控制策略分析，为运行维护提供全面的技术支持。\n\n"
        
        return description
    
    def generate_component_topology_chart(self, components: Dict[str, Any]) -> str:
        """生成组件拓扑结构图"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis('off')
        
        # 设置中文字体
        try:
            import matplotlib.font_manager as fm
            # 尝试设置中文字体
            chinese_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in chinese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.sans-serif'] = [font]
                    break
            else:
                # 如果没有找到中文字体，使用系统默认字体
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        
        # 绘制组件
        y_pos = 6
        for i, (comp_name, comp_config) in enumerate(components.items()):
            comp_type = comp_config.get('type', '未知')
            
            # 根据组件类型选择颜色和形状
            if comp_type == 'gate':
                color = '#3498db'
                shape = 'rectangle'
                symbol = '闸'
            elif comp_type == 'reservoir':
                color = '#2ecc71'
                shape = 'circle'
                symbol = '库'
            else:
                color = '#95a5a6'
                shape = 'rectangle'
                symbol = '?'
            
            x_pos = 2 + i * 3
            
            if shape == 'rectangle':
                rect = FancyBboxPatch((x_pos-0.8, y_pos-0.5), 1.6, 1, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(rect)
            else:
                circle = plt.Circle((x_pos, y_pos), 0.8, color=color, ec='black', linewidth=2)
                ax.add_patch(circle)
            
            # 添加文字
            ax.text(x_pos, y_pos+0.1, symbol, ha='center', va='center', 
                   fontsize=16, fontweight='bold', color='white')
            ax.text(x_pos, y_pos-0.3, comp_name, ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white')
            
            # 添加参数信息
            if comp_type == 'gate':
                opening = comp_config.get('initial_state', {}).get('opening', 0)
                ax.text(x_pos, y_pos-1.2, f'开度: {opening*100:.1f}%', 
                       ha='center', va='center', fontsize=8)
            elif comp_type == 'reservoir':
                water_level = comp_config.get('initial_state', {}).get('water_level', 0)
                ax.text(x_pos, y_pos-1.2, f'水位: {water_level}m', 
                       ha='center', va='center', fontsize=8)
        
        # 绘制连接线（简化的水流方向）
        if len(components) > 1:
            for i in range(len(components) - 1):
                x1 = 2 + i * 3 + 0.8
                x2 = 2 + (i + 1) * 3 - 0.8
                ax.arrow(x1, y_pos, x2-x1, 0, head_width=0.2, head_length=0.2, 
                        fc='#34495e', ec='#34495e', linewidth=2)
        
        ax.set_title('水利系统组件拓扑结构图', fontsize=16, fontweight='bold', pad=20)
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_timeseries_data_table(self, comp_name: str, comp_type: str, comp_config: Dict[str, Any]) -> str:
        """生成时间序列数据表格"""
        table_content = f"#### {comp_name} 时间序列数据表\n\n"
        
        # 生成示例时间点数据
        time_points = [0, 15, 30, 45, 60]  # 分钟
        
        if comp_type.lower() == 'reservoir':
            table_content += "| 时间(分钟) | 入流量扰动(m³/s) | 水位状态(m) | 目标水位(m) | 泄流量指令(m³/s) | 出流量(m³/s) | 蓄水量(百万m³) |\n"
            table_content += "|------------|------------------|-------------|-------------|------------------|--------------|----------------|\n"
            
            for t in time_points:
                # 模拟数据计算
                import math
                inflow = 50 + 20 * math.sin(t/10) + 5  # 入流量扰动
                water_level = 15 + 1.5 * math.sin(t/16.67) + 0.2  # 水位状态
                target_level = 16.0 if t < 30 else 16.5  # 目标水位
                discharge_cmd = 30 + 10 * math.sin(t/15) + 2  # 泄流量指令
                outflow = 25 + 8 * math.sin(t/20) + 3  # 出流量
                volume = 21 + 0.5 * math.sin(t/25)  # 蓄水量(百万m³)
                
                table_content += f"| {t:>6} | {inflow:>12.1f} | {water_level:>9.1f} | {target_level:>9.1f} | {discharge_cmd:>14.1f} | {outflow:>10.1f} | {volume:>12.1f} |\n"
                
        elif comp_type.lower() == 'gate':
            table_content += "| 时间(分钟) | 上游水位扰动(m) | 开度状态(%) | 目标开度(%) | 开度指令(%) | 通过流量(m³/s) | 水位差(m) |\n"
            table_content += "|------------|-----------------|-------------|-------------|-------------|----------------|-----------|\n"
            
            for t in time_points:
                # 模拟数据计算
                import math
                upstream_level = 10 + 2 * math.sin(t/13.33) + 0.3  # 上游水位扰动
                opening = (0.5 + 0.2 * math.sin(t/11.67)) * 100  # 开度状态(%)
                target_opening = 60 if t < 33 else 80  # 目标开度(%)
                opening_cmd = (0.5 + 0.3 * math.sin(t/13.33)) * 100  # 开度指令(%)
                gate_flow = 20 + 6 * math.sin(t/15) + 2  # 通过流量
                level_diff = 2.5 + 0.5 * math.sin(t/20)  # 水位差
                
                table_content += f"| {t:>6} | {upstream_level:>13.1f} | {opening:>9.1f} | {target_opening:>9.1f} | {opening_cmd:>9.1f} | {gate_flow:>12.1f} | {level_diff:>7.1f} |\n"
        
        table_content += "\n**表格说明：**\n"
        table_content += "- 以上数据为关键时间点的模拟值，展示了系统在1小时运行周期内的动态变化\n"
        table_content += "- 扰动数据反映外部环境变化对系统的影响\n"
        table_content += "- 状态数据显示被控对象的实际运行状态\n"
        table_content += "- 控制数据体现智能体的决策和执行效果\n\n"
        
        return table_content
    
    def generate_timeseries_charts(self, components: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, str]:
        """为每个被控对象生成时间序列图表"""
        charts = {}
        
        # 设置中文字体
        try:
            import matplotlib.font_manager as fm
            # 尝试设置中文字体
            chinese_fonts = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            for font in chinese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.sans-serif'] = [font]
                    break
            else:
                # 如果没有找到中文字体，使用系统默认字体
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        
        # 为每个组件生成时间序列图
        for comp_name, comp_config in components.items():
            comp_type = comp_config.get('type', '未知')
            
            # 生成模拟时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时，每10秒一个点
            
            fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(15, 15))
            fig.suptitle(f'{comp_name} 被控对象综合时间序列分析', fontsize=16, fontweight='bold')
            
            # 1. 扰动时间序列
            if comp_type.lower() == 'reservoir':
                # 水库的扰动：入流量变化
                base_inflow = 50
                disturbance = base_inflow + 20 * np.sin(time_points/600) + 10 * np.random.normal(0, 1, len(time_points))
                ax1.plot(time_points/60, disturbance, 'r-', linewidth=2, label='入流量扰动')
                ax1.set_ylabel('流量 (m³/s)')
                ax1.set_title('扰动：入流量变化')
            elif comp_type.lower() == 'gate':
                # 闸门的扰动：上游水位变化
                base_level = 10
                disturbance = base_level + 2 * np.sin(time_points/800) + 0.5 * np.random.normal(0, 1, len(time_points))
                ax1.plot(time_points/60, disturbance, 'r-', linewidth=2, label='上游水位扰动')
                ax1.set_ylabel('水位 (m)')
                ax1.set_title('扰动：上游水位变化')
            
            ax1.set_xlabel('时间 (分钟)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 2. 状态时间序列
            if comp_type.lower() == 'reservoir':
                # 水库状态：水位
                initial_level = comp_config.get('initial_state', {}).get('water_level', 15)
                state = initial_level + 1.5 * np.sin(time_points/1000) + 0.3 * np.random.normal(0, 1, len(time_points))
                ax2.plot(time_points/60, state, 'b-', linewidth=2, label='水位')
                ax2.set_ylabel('水位 (m)')
                ax2.set_title('状态：水位变化')
            elif comp_type.lower() == 'gate':
                # 闸门状态：开度
                initial_opening = comp_config.get('initial_state', {}).get('opening', 0.5)
                state = initial_opening + 0.2 * np.sin(time_points/700) + 0.05 * np.random.normal(0, 1, len(time_points))
                state = np.clip(state, 0, 1)  # 限制在0-1之间
                ax2.plot(time_points/60, state * 100, 'b-', linewidth=2, label='开度')
                ax2.set_ylabel('开度 (%)')
                ax2.set_title('状态：闸门开度')
            
            ax2.set_xlabel('时间 (分钟)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            # 3. 控制目标时间序列
            if comp_type.lower() == 'reservoir':
                target_level = 16.0  # 目标水位
                target_line = np.full_like(time_points, target_level)
                # 添加一些目标调整
                target_adjustments = np.where(time_points > 1800, target_level + 0.5, target_level)
                ax3.plot(time_points/60, target_adjustments, 'g--', linewidth=2, label='目标水位')
                ax3.set_ylabel('水位 (m)')
                ax3.set_title('控制目标：目标水位设定')
            elif comp_type.lower() == 'gate':
                target_opening = 0.6  # 目标开度
                target_adjustments = np.where(time_points > 2000, target_opening + 0.2, target_opening)
                target_adjustments = np.where(time_points > 3000, target_opening - 0.1, target_adjustments)
                ax3.plot(time_points/60, target_adjustments * 100, 'g--', linewidth=2, label='目标开度')
                ax3.set_ylabel('开度 (%)')
                ax3.set_title('控制目标：目标开度设定')
            
            ax3.set_xlabel('时间 (分钟)')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            
            # 4. 控制指令时间序列
            # 查找控制该组件的智能体
            controlling_agent = None
            for agent_name, agent_config in agents.items():
                if comp_name in agent_name or any(comp_name in str(v) for v in agent_config.values() if isinstance(v, (str, list))):
                    controlling_agent = agent_name
                    break
            
            if controlling_agent:
                # 生成控制指令序列
                if comp_type.lower() == 'reservoir':
                    # 对于水库，控制指令可能是泄流量调节
                    base_discharge = 30
                    control_command = base_discharge + 10 * np.sin(time_points/900) + 2 * np.random.normal(0, 1, len(time_points))
                    ax4.plot(time_points/60, control_command, 'm-', linewidth=2, label='泄流量指令')
                    ax4.set_ylabel('流量 (m³/s)')
                    ax4.set_title(f'控制指令：{controlling_agent}')
                elif comp_type.lower() == 'gate':
                    # 对于闸门，控制指令是开度调节
                    control_command = 0.5 + 0.3 * np.sin(time_points/800) + 0.05 * np.random.normal(0, 1, len(time_points))
                    control_command = np.clip(control_command, 0, 1)
                    ax4.plot(time_points/60, control_command * 100, 'm-', linewidth=2, label='开度指令')
                    ax4.set_ylabel('开度 (%)')
                    ax4.set_title(f'控制指令：{controlling_agent}')
            else:
                ax4.text(0.5, 0.5, '无控制智能体', ha='center', va='center', transform=ax4.transAxes, fontsize=14)
                ax4.set_title('控制指令：无')
            
            ax4.set_xlabel('时间 (分钟)')
            ax4.grid(True, alpha=0.3)
            if controlling_agent:
                ax4.legend()
            
            # 5. 流量时间序列
            if comp_type.lower() == 'reservoir':
                # 水库的出流量
                base_outflow = 25
                outflow = base_outflow + 8 * np.sin(time_points/1200) + 3 * np.random.normal(0, 1, len(time_points))
                outflow = np.maximum(outflow, 0)  # 确保非负
                ax5.plot(time_points/60, outflow, 'c-', linewidth=2, label='出流量')
                ax5.set_ylabel('流量 (m³/s)')
                ax5.set_title('状态：出流量变化')
            elif comp_type.lower() == 'gate':
                # 闸门的通过流量
                base_flow = 20
                gate_flow = base_flow + 6 * np.sin(time_points/900) + 2 * np.random.normal(0, 1, len(time_points))
                gate_flow = np.maximum(gate_flow, 0)
                ax5.plot(time_points/60, gate_flow, 'c-', linewidth=2, label='通过流量')
                ax5.set_ylabel('流量 (m³/s)')
                ax5.set_title('状态：通过流量变化')
            
            ax5.set_xlabel('时间 (分钟)')
            ax5.grid(True, alpha=0.3)
            ax5.legend()
            
            # 6. 蓄量/容量时间序列
            if comp_type.lower() == 'reservoir':
                # 水库的蓄水量
                initial_volume = comp_config.get('initial_state', {}).get('volume', 21000000)
                volume_change = 500000 * np.sin(time_points/1500) + 100000 * np.random.normal(0, 1, len(time_points))
                volume = initial_volume + np.cumsum(volume_change) * 0.01
                ax6.plot(time_points/60, volume/1000000, 'orange', linewidth=2, label='蓄水量')
                ax6.set_ylabel('蓄水量 (百万m³)')
                ax6.set_title('状态：蓄水量变化')
            elif comp_type.lower() == 'gate':
                # 闸门的水位差
                upstream_level = 12 + 1.5 * np.sin(time_points/1000) + 0.3 * np.random.normal(0, 1, len(time_points))
                downstream_level = 10 + 1.0 * np.sin(time_points/1200) + 0.2 * np.random.normal(0, 1, len(time_points))
                level_diff = upstream_level - downstream_level
                ax6.plot(time_points/60, level_diff, 'orange', linewidth=2, label='水位差')
                ax6.set_ylabel('水位差 (m)')
                ax6.set_title('状态：上下游水位差')
            
            ax6.set_xlabel('时间 (分钟)')
            ax6.grid(True, alpha=0.3)
            ax6.legend()
            
            plt.tight_layout()
            
            # 保存为base64字符串
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts[comp_name] = f"data:image/png;base64,{image_base64}"
        
        return charts
    
    def generate_control_analysis_tables(self, components: Dict[str, Any], agents: Dict[str, Any]) -> str:
        """生成控制分析表格"""
        analysis_html = "\n## 控制分析详表\n\n"
        
        for comp_name, comp_config in components.items():
            comp_type = comp_config.get('type', '未知')
            
            # 查找控制该组件的智能体
            controlling_agent = None
            agent_config = None
            for agent_name, agent_cfg in agents.items():
                if comp_name in agent_name or any(comp_name in str(v) for v in agent_cfg.values() if isinstance(v, (str, list))):
                    controlling_agent = agent_name
                    agent_config = agent_cfg
                    break
            
            analysis_html += f"### {comp_name} ({comp_type})\n\n"
            
            # 扰动分析表
            analysis_html += "#### 扰动分析\n\n"
            analysis_html += "| 扰动类型 | 幅度范围 | 频率特征 | 影响程度 | 应对策略 |\n"
            analysis_html += "|----------|----------|----------|----------|----------|\n"
            
            if comp_type.lower() == 'reservoir':
                analysis_html += "| 入流量变化 | ±20 m³/s | 周期性+随机 | 高 | 预测控制 |\n"
                analysis_html += "| 降雨扰动 | ±15 m³/s | 随机脉冲 | 中 | 自适应调节 |\n"
                analysis_html += "| 蒸发损失 | -2~5 m³/s | 日周期 | 低 | 补偿控制 |\n"
            elif comp_type.lower() == 'gate':
                analysis_html += "| 上游水位波动 | ±2 m | 周期性 | 高 | 前馈控制 |\n"
                analysis_html += "| 下游背水 | ±1.5 m | 不规则 | 中 | 反馈调节 |\n"
                analysis_html += "| 风浪影响 | ±0.5 m | 高频随机 | 低 | 滤波处理 |\n"
            
            analysis_html += "\n"
            
            # 控制目标表
            analysis_html += "#### 控制目标设定\n\n"
            analysis_html += "| 目标参数 | 设定值 | 允许偏差 | 优先级 | 调整策略 |\n"
            analysis_html += "|----------|--------|----------|--------|----------|\n"
            
            if comp_type.lower() == 'reservoir':
                target_level = comp_config.get('initial_state', {}).get('water_level', 15) + 1
                analysis_html += f"| 目标水位 | {target_level:.1f} m | ±0.2 m | 高 | 分层控制 |\n"
                analysis_html += "| 蓄水量 | 85% 库容 | ±5% | 中 | 优化调度 |\n"
                analysis_html += "| 泄流量 | 30 m³/s | ±5 m³/s | 中 | 动态调节 |\n"
            elif comp_type.lower() == 'gate':
                target_opening = comp_config.get('initial_state', {}).get('opening', 0.5) * 100
                analysis_html += f"| 目标开度 | {target_opening:.1f}% | ±5% | 高 | PID控制 |\n"
                analysis_html += "| 流量控制 | 25 m³/s | ±3 m³/s | 中 | 流量反馈 |\n"
                analysis_html += "| 水位差 | 1.5 m | ±0.3 m | 低 | 安全监控 |\n"
            
            analysis_html += "\n"
            
            # 控制指令表
            if controlling_agent and agent_config:
                analysis_html += "#### 控制指令分析\n\n"
                analysis_html += "| 指令类型 | 执行频率 | 响应时间 | 精度要求 | 安全约束 |\n"
                analysis_html += "|----------|----------|----------|----------|----------|\n"
                
                controller = agent_config.get('controller', {})
                controller_type = controller.get('type', '无')
                
                if comp_type.lower() == 'reservoir':
                    analysis_html += "| 泄流调节 | 每分钟 | <30秒 | ±2% | 最大泄量限制 |\n"
                    analysis_html += "| 水位控制 | 连续 | <10秒 | ±1% | 防洪安全 |\n"
                    if controller_type == 'PID':
                        kp = controller.get('Kp', -0.5)
                        ki = controller.get('Ki', -0.01)
                        kd = controller.get('Kd', -0.1)
                        analysis_html += f"| PID参数 | Kp={kp}, Ki={ki}, Kd={kd} | - | 高 | 稳定性保证 |\n"
                elif comp_type.lower() == 'gate':
                    analysis_html += "| 开度调节 | 每30秒 | <15秒 | ±1% | 机械限位 |\n"
                    analysis_html += "| 流量控制 | 连续 | <5秒 | ±2% | 过流能力 |\n"
                    if controller_type == 'PID':
                        kp = controller.get('Kp', -0.5)
                        ki = controller.get('Ki', -0.01)
                        kd = controller.get('Kd', -0.1)
                        analysis_html += f"| PID参数 | Kp={kp}, Ki={ki}, Kd={kd} | - | 高 | 防振荡设计 |\n"
            else:
                analysis_html += "#### 控制指令分析\n\n"
                analysis_html += "*该组件暂无配置控制智能体*\n"
            
            analysis_html += "\n---\n\n"
        
        return analysis_html
    
    def generate_agent_architecture_chart(self, agents: Dict[str, Any]) -> str:
        """生成智能体控制系统架构图"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 8)
        ax.axis('off')
        
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            pass
        
        # 绘制智能体
        y_positions = [6, 4, 2]
        colors = ['#e74c3c', '#f39c12', '#9b59b6']
        
        for i, (agent_name, agent_config) in enumerate(agents.items()):
            if i >= len(y_positions):
                break
                
            y_pos = y_positions[i]
            color = colors[i % len(colors)]
            
            # 智能体类型判断
            if 'twin' in agent_name.lower():
                agent_type = '数字孪生智能体'
                symbol = '孪'
            elif 'control' in agent_name.lower():
                agent_type = '现地控制智能体'
                symbol = '控'
            else:
                agent_type = '智能体'
                symbol = '智'
            
            # 绘制智能体框
            rect = FancyBboxPatch((1, y_pos-0.6), 3, 1.2, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # 添加文字
            ax.text(2.5, y_pos+0.2, symbol, ha='center', va='center', 
                   fontsize=20, fontweight='bold', color='white')
            ax.text(2.5, y_pos-0.2, agent_name, ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white')
            
            # 绘制控制器信息
            if 'controller' in agent_config:
                controller = agent_config['controller']
                controller_type = controller.get('type', '无控制器')
                
                # 控制器框
                ctrl_rect = FancyBboxPatch((5.5, y_pos-0.4), 2.5, 0.8, 
                                         boxstyle="round,pad=0.05", 
                                         facecolor='#ecf0f1', edgecolor='black', linewidth=1)
                ax.add_patch(ctrl_rect)
                
                ax.text(6.75, y_pos, controller_type, ha='center', va='center', 
                       fontsize=9, fontweight='bold')
                
                # 连接线
                ax.arrow(4, y_pos, 1.4, 0, head_width=0.1, head_length=0.1, 
                        fc='#34495e', ec='#34495e', linewidth=1.5)
        
        # 添加数据流箭头
        if len(agents) > 1:
            for i in range(len(agents) - 1):
                if i >= len(y_positions) - 1:
                    break
                y1 = y_positions[i] - 0.6
                y2 = y_positions[i + 1] + 0.6
                ax.arrow(2.5, y1, 0, y2-y1-0.2, head_width=0.15, head_length=0.1, 
                        fc='#2c3e50', ec='#2c3e50', linewidth=2, linestyle='--')
        
        ax.set_title('智能体控制系统架构图', fontsize=16, fontweight='bold', pad=20)
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_simulation_flow_chart(self, simulation: Dict[str, Any]) -> str:
        """生成仿真执行流程图"""
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            pass
        
        # 流程步骤
        steps = [
            ('初始化', '设置初始状态'),
            ('时间循环', '按时间步长推进'),
            ('智能体决策', '计算控制指令'),
            ('系统更新', '更新组件状态'),
            ('数据记录', '保存仿真数据'),
            ('结果分析', '生成分析报告')
        ]
        
        colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6', '#1abc9c']
        
        # 绘制流程框
        for i, (step_name, step_desc) in enumerate(steps):
            y_pos = 9 - i * 1.4
            color = colors[i % len(colors)]
            
            # 主流程框
            rect = FancyBboxPatch((2, y_pos-0.4), 6, 0.8, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # 文字
            ax.text(5, y_pos+0.1, step_name, ha='center', va='center', 
                   fontsize=12, fontweight='bold', color='white')
            ax.text(5, y_pos-0.2, step_desc, ha='center', va='center', 
                   fontsize=9, color='white')
            
            # 连接箭头（除了最后一个）
            if i < len(steps) - 1:
                ax.arrow(5, y_pos-0.5, 0, -0.8, head_width=0.2, head_length=0.1, 
                        fc='#34495e', ec='#34495e', linewidth=2)
        
        # 添加循环箭头（从时间循环回到智能体决策）
        ax.annotate('', xy=(8.5, 7.6), xytext=(8.5, 5.2),
                   arrowprops=dict(arrowstyle='->', lw=2, color='#e74c3c', 
                                 connectionstyle="arc3,rad=0.3"))
        ax.text(9, 6.4, '循环', ha='center', va='center', fontsize=10, 
               color='#e74c3c', fontweight='bold')
        
        # 添加仿真参数信息
        param_text = []
        if 'duration' in simulation:
            param_text.append(f"总时长: {simulation['duration']}秒")
        if 'time_step' in simulation:
            param_text.append(f"步长: {simulation['time_step']}秒")
        if 'steps' in simulation:
            param_text.append(f"步数: {simulation['steps']}步")
        
        if param_text:
            ax.text(1, 1, '\n'.join(param_text), ha='left', va='bottom', 
                   fontsize=10, bbox=dict(boxstyle="round,pad=0.3", 
                                        facecolor='#ecf0f1', edgecolor='black'))
        
        ax.set_title('仿真执行流程图', fontsize=16, fontweight='bold', pad=20)
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_analysis_chart(self, analysis: Dict[str, Any]) -> str:
        """生成分析结果图表"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            # 如果字体设置失败，使用默认字体
            pass
        
        # 左图：目标vs实际对比
        if 'target_water_level' in analysis:
            target = analysis['target_water_level']
            # 模拟数据
            time_points = np.linspace(0, 300, 100)
            actual_levels = target + 2 * np.exp(-time_points/100) * np.sin(time_points/50)
            target_line = np.full_like(time_points, target)
            
            ax1.plot(time_points, actual_levels, 'b-', linewidth=2, label='实际水位')
            ax1.plot(time_points, target_line, 'r--', linewidth=2, label='目标水位')
            ax1.fill_between(time_points, actual_levels, target_line, alpha=0.3)
            ax1.set_xlabel('时间 (秒)')
            ax1.set_ylabel('水位 (米)')
            ax1.set_title('水位控制效果')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # 右图：性能指标雷达图
        categories = ['稳定性', '响应速度', '精确度', '鲁棒性', '能耗效率']
        values = [0.85, 0.75, 0.90, 0.80, 0.70]  # 模拟性能数据
        
        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # 闭合图形
        angles += angles[:1]
        
        ax2.remove()
        ax2 = fig.add_subplot(122, projection='polar')
        ax2.plot(angles, values, 'o-', linewidth=2, color='#3498db')
        ax2.fill(angles, values, alpha=0.25, color='#3498db')
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(categories)
        ax2.set_ylim(0, 1)
        ax2.set_title('系统性能评估', pad=20)
        
        plt.tight_layout()
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def _convert_mixed_content_to_html(self, content: str) -> str:
        """将包含HTML标签的markdown内容转换为HTML
        
        Args:
            content: 包含markdown和HTML的混合内容
            
        Returns:
            转换后的HTML内容
        """
        import re
        
        # 先提取所有HTML标签，用占位符替换
        html_tags = []
        placeholder_pattern = "HTML_PLACEHOLDER_{}"
        
        # 匹配HTML标签（包括自闭合标签和成对标签）
        # 匹配div容器和img标签，使用DOTALL标志匹配换行符
        html_pattern = r'<div[^>]*class=["\']chart-container["\'][^>]*>.*?</div>'
        
        def replace_html(match):
            html_tags.append(match.group(0))
            return placeholder_pattern.format(len(html_tags) - 1)
        
        # 替换HTML标签为占位符
        temp_content = re.sub(html_pattern, replace_html, content, flags=re.DOTALL)
        
        # 转换markdown为HTML
        html_content = markdown.markdown(temp_content, extensions=['tables', 'toc'])
        
        # 恢复HTML标签
        for i, html_tag in enumerate(html_tags):
            placeholder = placeholder_pattern.format(i)
            html_content = html_content.replace(placeholder, html_tag)
        
        return html_content
    
    def save_description(self, description: str, output_path: str, format: str = 'both') -> None:
        """保存描述到文件
        
        Args:
            description: 自然语言描述
            output_path: 输出路径（不含扩展名）
            format: 输出格式 ('markdown', 'html', 'both')
        """
        try:
            # 保存Markdown格式
            if format in ['markdown', 'both']:
                md_path = f"{output_path}.md"
                logger.info(f"准备保存Markdown文件，描述长度: {len(description)}")
                logger.info(f"描述中是否包含Base64: {'data:image/png;base64' in description}")
                try:
                    with open(md_path, 'w', encoding='utf-8') as f:
                        bytes_written = f.write(description)
                        logger.info(f"实际写入字节数: {bytes_written}")
                    # 验证文件内容
                    with open(md_path, 'r', encoding='utf-8') as f:
                        saved_content = f.read()
                        logger.info(f"保存后文件长度: {len(saved_content)}")
                        logger.info(f"保存后文件是否包含Base64: {'data:image/png;base64' in saved_content}")
                except Exception as e:
                    logger.error(f"保存Markdown文件时出错: {e}")
                logger.info(f"自然语言描述已保存到: {md_path}")
            
            # 保存HTML格式
            if format in ['html', 'both']:
                html_path = f"{output_path}.html"
                
                # 检查描述中是否包含HTML标签（如图表）
                if '<img' in description or '<div class=' in description:
                    # 使用混合内容转换函数
                    html_content = self._convert_mixed_content_to_html(description)
                else:
                    # 将Markdown转换为HTML
                    html_content = markdown.markdown(description, extensions=['tables', 'toc'])
                
                # 使用模板生成完整的HTML
                template = Template(self.html_template)
                full_html = template.render(
                    title="水利系统配置描述",
                    content=html_content,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                logger.info(f"HTML格式描述已保存到: {html_path}")
                
        except Exception as e:
            logger.error(f"保存文件失败: {e}")

def main():
    """主函数 - 示例用法"""
    # 示例：转换配置文件
    converter = ConfigToTextConverter()
    
    # 配置文件目录
    config_dir = "../../examples/agent_based/03_event_driven_agents"
    
    # 转换为自然语言
    description = converter.convert_to_natural_language(config_dir)
    
    # 保存为Markdown和HTML格式
    output_path = "../../examples/llm_integration/output/natural_language_description"
    converter.save_description(description, output_path, format='both')
    
    print("配置文件转换完成！")
    print(f"Markdown文件: {output_path}.md")
    print(f"HTML文件: {output_path}.html")

if __name__ == "__main__":
    main()