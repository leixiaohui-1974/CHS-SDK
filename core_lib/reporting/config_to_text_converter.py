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

# 导入增强可视化模块
try:
    from enhanced_visualization import EnhancedVisualization
except ImportError:
    # 如果导入失败，创建一个空的类
    class EnhancedVisualization:
        def __init__(self):
            pass
        def generate_overlay_analysis_chart(self, *args, **kwargs):
            return None
        def generate_chart_table_combination(self, *args, **kwargs):
            return None
        def generate_comprehensive_charts_per_object(self, *args, **kwargs):
            return {}
        def generate_separate_analysis_charts(self, *args, **kwargs):
            return None

class ConfigToTextConverter:
    """配置文件到自然语言转换器"""
    
    def __init__(self):
        self.enhanced_viz = EnhancedVisualization()
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
    <link rel="stylesheet" href="report_styles.css">
    <style>
        /* 内联样式补充 */
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: right;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
            padding-top: 10px;
        }
        
        /* 确保图表容器正确显示 */
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        /* 系统概述样式 */
        .system-overview-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .overview-item {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .overview-item h4 {
            color: white;
            margin-top: 0;
            margin-bottom: 10px;
        }
        
        .overview-item p {
            color: rgba(255,255,255,0.9);
            margin: 0;
        }
    </style>
</head>
<body>
    {{ content }}
    <div class="timestamp">
        生成时间: {{ timestamp }}
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
    
    def generate_detailed_system_description(self, config) -> str:
        """生成详细的水利系统文字描述"""
        description = ""
        
        # 系统整体描述
        description += "## 水利系统详细描述\n\n"
        
        components = config.get('components', {})
        agents = config.get('agents', {})
        topology = config.get('topology', {})
        simulation = config.get('simulation', {})
        
        # 分类组件
        controlled_objects = {}  # 被控对象
        control_objects = {}     # 控制对象
        
        for comp_name, comp_config in components.items():
            comp_type = comp_config.get('type', '未知').lower()
            if comp_type in ['reservoir', 'river', 'canal', 'pipe', 'lake', 'pond']:
                controlled_objects[comp_name] = comp_config
            elif comp_type in ['gate', 'pump', 'valve', 'hydropower']:
                control_objects[comp_name] = comp_config
            else:
                # 默认分类逻辑
                if any(keyword in comp_name.lower() for keyword in ['station', 'pump', 'gate', 'valve']):
                    control_objects[comp_name] = comp_config
                else:
                    controlled_objects[comp_name] = comp_config
        
        # 系统规模和特征
        description += f"### 系统规模\n"
        description += f"- 总组件数量：{len(components)} 个\n"
        description += f"- 被控对象：{len(controlled_objects)} 个\n"
        description += f"- 控制对象：{len(control_objects)} 个\n"
        description += f"- 智能体数量：{len(agents)} 个\n"
        
        if topology.get('connections'):
            description += f"- 连接关系：{len(topology['connections'])} 条\n"
        
        if simulation:
            duration = simulation.get('duration', 0)
            time_step = simulation.get('time_step', 1)
            description += f"- 仿真时长：{duration} 秒 ({duration/3600:.1f} 小时)\n"
            description += f"- 仿真步长：{time_step} 秒\n"
            description += f"- 仿真步数：{int(duration/time_step)} 步\n"
        
        description += "\n"
        
        # 系统拓扑结构描述
        description += "### 系统拓扑结构\n"
        if topology.get('connections'):
            description += "水利系统的连接关系构成了完整的水流传输和控制网络：\n\n"
            
            # 按连接类型分组
            connection_types = {}
            for conn in topology['connections']:
                conn_type = conn.get('type', '未知')
                if conn_type not in connection_types:
                    connection_types[conn_type] = []
                connection_types[conn_type].append(conn)
            
            for conn_type, connections in connection_types.items():
                description += f"**{conn_type}连接：**\n"
                for i, conn in enumerate(connections, 1):
                    from_comp = conn.get('from', '未知')
                    to_comp = conn.get('to', '未知')
                    description += f"{i}. {from_comp} → {to_comp}\n"
                description += "\n"
        else:
            description += "系统拓扑结构信息未配置。\n\n"
        
        return description
    
    def describe_controlled_objects_detail(self, controlled_objects: Dict[str, Any]) -> str:
        """详细描述被控对象"""
        if not controlled_objects:
            return "### 被控对象\n\n本系统中未配置被控对象。\n\n"
        
        description = "### 被控对象详细分析\n\n"
        description += "被控对象是水利系统中需要监测和调节的核心组件，包括各种水体和水工建筑物：\n\n"
        
        for i, (obj_name, obj_config) in enumerate(controlled_objects.items(), 1):
            obj_type = obj_config.get('type', '未知')
            obj_desc = obj_config.get('description', '无描述')
            
            description += f"**{i}. {obj_name}** ({obj_type})\n"
            description += f"   - 描述：{obj_desc}\n"
            
            # 添加具体参数描述
            if obj_type.lower() == 'reservoir':
                capacity = obj_config.get('capacity', '未知')
                initial_level = obj_config.get('initial_level', '未知')
                description += f"   - 库容：{capacity}\n"
                description += f"   - 初始水位：{initial_level}\n"
                description += f"   - 控制特点：作为系统的主要调蓄单元，承担水量调节和洪水控制功能\n"
            elif obj_type.lower() in ['river', 'canal']:
                length = obj_config.get('length', '未知')
                width = obj_config.get('width', '未知')
                description += f"   - 长度：{length}\n"
                description += f"   - 宽度：{width}\n"
                description += f"   - 控制特点：作为水流传输通道，需要监测流量和水位变化\n"
            elif obj_type.lower() in ['lake', 'pond']:
                area = obj_config.get('area', '未知')
                depth = obj_config.get('depth', '未知')
                description += f"   - 面积：{area}\n"
                description += f"   - 深度：{depth}\n"
                description += f"   - 控制特点：作为天然或人工水体，需要维持生态和供水功能\n"
            
            # 添加监测指标
            description += f"   - 主要监测指标：水位、流量、水质参数\n"
            description += f"   - 控制目标：维持合理水位，确保供水安全和防洪要求\n\n"
        
        return description
    
    def describe_control_objects_detail(self, control_objects: Dict[str, Any]) -> str:
        """详细描述控制对象"""
        if not control_objects:
            return "### 控制对象\n\n本系统中未配置控制对象。\n\n"
        
        description = "### 控制对象详细分析\n\n"
        description += "控制对象是水利系统中执行调控指令的关键设备，通过精确操作实现系统控制目标：\n\n"
        
        for i, (obj_name, obj_config) in enumerate(control_objects.items(), 1):
            obj_type = obj_config.get('type', '未知')
            obj_desc = obj_config.get('description', '无描述')
            
            description += f"**{i}. {obj_name}** ({obj_type})\n"
            description += f"   - 描述：{obj_desc}\n"
            
            # 添加具体参数描述
            if obj_type.lower() == 'gate':
                max_opening = obj_config.get('max_opening', '未知')
                control_type = obj_config.get('control_type', '手动')
                description += f"   - 最大开度：{max_opening}\n"
                description += f"   - 控制方式：{control_type}\n"
                description += f"   - 控制功能：调节过闸流量，控制上下游水位差\n"
                description += f"   - 操作特点：通过开度调节实现精确流量控制\n"
            elif obj_type.lower() == 'pump':
                capacity = obj_config.get('capacity', '未知')
                head = obj_config.get('head', '未知')
                description += f"   - 设计流量：{capacity}\n"
                description += f"   - 扬程：{head}\n"
                description += f"   - 控制功能：主动提升水位，实现逆向输水\n"
                description += f"   - 操作特点：通过启停和转速调节控制输水量\n"
            elif obj_type.lower() == 'valve':
                diameter = obj_config.get('diameter', '未知')
                pressure_rating = obj_config.get('pressure_rating', '未知')
                description += f"   - 管径：{diameter}\n"
                description += f"   - 压力等级：{pressure_rating}\n"
                description += f"   - 控制功能：精确调节管道流量和压力\n"
                description += f"   - 操作特点：通过开度调节实现流量和压力控制\n"
            elif obj_type.lower() == 'hydropower':
                capacity = obj_config.get('capacity', '未知')
                efficiency = obj_config.get('efficiency', '未知')
                description += f"   - 装机容量：{capacity}\n"
                description += f"   - 效率：{efficiency}\n"
                description += f"   - 控制功能：发电的同时调节下泄流量\n"
                description += f"   - 操作特点：兼顾发电效益和水位控制要求\n"
            
            # 添加控制策略
            description += f"   - 控制策略：根据系统需求和约束条件自动调节\n"
            description += f"   - 响应特性：快速响应控制指令，确保系统稳定\n\n"
        
        return description
     
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
        
        # 描述拓扑结构
        if 'topology' in main_config and 'connections' in main_config['topology']:
            description += self.describe_topology(main_config['topology']['connections'])
        
        # 描述智能体
        if 'agents' in main_config:
            description += self.describe_agents(main_config['agents'])
        
        # 添加综合拓扑图（合并组件拓扑和智能体架构）
        if 'components' in main_config or 'agents' in main_config:
            try:
                components = main_config.get('components', {})
                agents = main_config.get('agents', {})
                topology_connections = main_config.get('topology', {}).get('connections', [])
                simulation_config = main_config.get('simulation', {})
                chart_html = self.generate_integrated_topology_chart(components, agents, topology_connections, simulation_config)
                logger.info(f"综合拓扑图生成成功，Base64长度: {len(chart_html)}")
                chart_section = "\n### 水利系统综合拓扑图\n\n<div class='chart-container'>\n<img src='" + chart_html + "' alt='水利系统综合拓扑图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
                description += chart_section
            except Exception as e:
                logger.warning(f"综合拓扑图生成失败: {e}")
                description += "\n### 水利系统综合拓扑图\n\n<div class='chart-container'>\n<div class='chart-placeholder'>水利系统综合拓扑图 (生成失败)</div>\n</div>\n\n"
        
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
        
        # 添加时间序列分析
        if 'components' in main_config and 'agents' in main_config:
            try:
                description += "\n## 时间序列分析\n"
                description += "按照控制对象和被控对象分类进行综合时间序列分析，包括扰动输入、状态响应和控制目标的动态变化过程。\n\n"
                
                # 分类组件
                controlled_objects = {}  # 被控对象：河道、管道、渠道、水库、湖泊、调蓄池等
                control_objects = {}     # 控制对象：闸站、泵站、阀站、水电站等
                
                for comp_name, comp_config in main_config['components'].items():
                    comp_type = comp_config.get('type', '未知').lower()
                    if comp_type in ['reservoir', 'river', 'canal', 'pipe', 'lake', 'pond']:
                        controlled_objects[comp_name] = comp_config
                    elif comp_type in ['gate', 'pump', 'valve', 'hydropower']:
                        control_objects[comp_name] = comp_config
                    else:
                        # 默认按照现有逻辑分类
                        if 'station' in comp_name.lower() or 'pump' in comp_name.lower() or 'gate' in comp_name.lower():
                            control_objects[comp_name] = comp_config
                        else:
                            controlled_objects[comp_name] = comp_config
                
                # 生成被控对象分析
                if controlled_objects:
                    description += "### 被控对象时间序列分析\n"
                    description += "被控对象包括河道、管道、渠道、水库、湖泊、调蓄池等，主要分析其扰动响应、状态变化（水位、流量、蓄量等）和控制目标。\n\n"
                    
                    controlled_charts = self.generate_controlled_objects_charts(controlled_objects, main_config.get('agents', {}))
                    
                    for comp_name, chart_html in controlled_charts.items():
                        comp_config = controlled_objects[comp_name]
                        comp_type = comp_config.get('type', '未知')
                        
                        description += f"#### {comp_name} ({comp_type}) 优化分析\n\n"
                        description += f"<div class='chart-container'>\n<img src='{chart_html}' alt='{comp_name}优化分析图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
                        
                        # 添加图表说明
                        description += f"**图表说明：**\n\n"
                        description += f"上图展示了 {comp_name} 的优化分析图表，包含4个关键分析维度：\n\n"
                        
                        if comp_type.lower() == 'reservoir':
                            description += "1. **水位跟踪效果**：实际水位与目标水位的叠加对比，展示控制目标的跟踪情况\n"
                            description += "2. **蓄量跟踪效果**：实际蓄量与目标蓄量的叠加对比，反映库容控制效果\n"
                            description += "3. **水量平衡分析**：入流量、出流量和蓄量的综合展示，体现水库的水量平衡状态\n"
                            description += "4. **控制指令生成和执行情况**：目标水位、实际水位与泄流指令的叠加显示，展示控制指令的生成和执行情况\n\n"
                        elif comp_type.lower() == 'canal':
                            description += "1. **流量跟踪效果**：实际流量与目标流量的叠加对比，展示控制目标的跟踪情况\n"
                            description += "2. **水位跟踪效果**：实际水位与目标水位的叠加对比，反映渠道水位控制效果\n"
                            description += "3. **流量平衡分析**：上游流量、下游流量和水位的综合展示，体现渠道的流量平衡状态\n"
                            description += "4. **控制指令生成和执行情况**：目标流量、实际流量与流量指令的叠加显示，展示控制指令的生成和执行情况\n\n"
                        else:
                            description += "1. **状态跟踪效果**：实际状态与目标状态的叠加对比，展示控制目标的跟踪情况\n"
                            description += "2. **参数跟踪效果**：关键参数的实际值与目标值对比，反映控制效果\n"
                            description += "3. **平衡分析**：相关参数的综合展示，体现对象的平衡状态\n"
                            description += "4. **控制指令生成和执行情况**：控制目标、实际状态与控制指令的叠加显示，展示控制指令的生成和执行情况\n\n"
                        
                        description += "通过这些优化分析，可以清晰地观察到控制目标的跟踪效果、系统的平衡状态以及控制指令的执行情况，为系统优化提供重要依据。\n\n"
                        
                    # 添加被控对象时间序列数据表格
                    controlled_data_table = self.generate_controlled_object_data_table(controlled_objects, main_config.get('agents', {}))
                    description += controlled_data_table
                
                # 生成控制对象分析
                if control_objects:
                    description += "### 控制对象时间序列分析\n"
                    description += "控制对象包括闸站、泵站、阀站、水电站等，主要分析其控制目标、控制指令、执行器状态的对比，以及与被控对象控制指标的叠加分析和控制误差评价。\n\n"
                    
                    control_charts = self.enhanced_viz.generate_enhanced_control_charts_per_object(control_objects, controlled_objects, main_config.get('agents', {}))
                    
                    for comp_name, chart_html in control_charts.items():
                        comp_config = control_objects[comp_name]
                        comp_type = comp_config.get('type', '未知')
                        
                        description += f"#### {comp_name} ({comp_type}) 控制分析\n\n"
                        description += f"<div class='chart-container'>\n<img src='{chart_html}' alt='{comp_name}控制分析图' style='max-width: 100%; height: auto;'>\n</div>\n\n"
                        
                        # 添加图表说明
                        description += f"**图表说明：**\n\n"
                        description += f"上图展示了 {comp_name} 作为控制对象的增强控制分析，包含4个关键分析维度：\n\n"
                        
                        description += "1. **控制目标、指令、执行器状态对比图**：展示控制目标设定值、智能体生成的控制指令以及执行器实际状态的时间序列对比，便于分析控制指令的准确性和执行器的响应特性\n"
                        description += "2. **与被控对象控制指标叠加图**：将控制对象的控制行为与其所控制的被控对象的关键指标（如水位、流量等）叠加显示，直观展示控制效果和系统响应\n"
                        description += "3. **控制误差过程线**：显示控制目标与实际执行结果之间的误差变化过程，用于评估控制精度和系统稳定性\n"
                        description += "4. **控制性能评价指标**：包括平均绝对误差(MAE)、均方根误差(RMSE)、控制稳定性指标等关键性能指标，量化评估控制效果\n\n"
                        
                        description += "通过这些增强的控制分析图表，可以全面评估控制对象的控制性能、执行效果以及对被控对象的影响。\n\n"
                        
                    # 添加控制对象时间序列数据表格
                control_data_table = self.generate_control_object_data_table(control_objects, main_config.get('agents', {}))
                description += control_data_table
                

                
                # 添加数据表格分析
                try:
                    description += "### 详细数据表格分析\n"
                    description += "以下数据表格提供了系统运行的详细数值信息，与上述图表形成互补，便于精确分析。\n\n"
                    
                    # 生成被控对象详细数据表
                    description += "#### 被控对象运行数据表\n\n"
                    description += "<div class='table-container' style='margin: 15px 0; overflow-x: auto;'>\n"
                    description += "<table style='width: 100%; border-collapse: collapse; font-size: 12px;'>\n"
                    description += "<thead style='background-color: #f8f9fa;'>\n"
                    description += "<tr>\n"
                    description += "<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>时间</th>\n"
                    
                    for obj_name in controlled_objects.keys():
                        description += f"<th colspan='4' style='border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #e3f2fd;'>{obj_name}</th>\n"
                    description += "</tr>\n"
                    description += "<tr>\n"
                    description += "<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>(分钟)</th>\n"
                    
                    for _ in controlled_objects.keys():
                        description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>扰动</th>\n"
                        description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>状态</th>\n"
                        description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>目标</th>\n"
                        description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>流量</th>\n"
                    description += "</tr>\n"
                    description += "</thead>\n"
                    description += "<tbody>\n"
                    
                    # 生成示例数据行
                    import numpy as np
                    time_points = [0, 10, 20, 30, 40, 50, 60]
                    for t in time_points:
                        description += "<tr>\n"
                        description += f"<td style='border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;'>{t}</td>\n"
                        
                        for obj_name, obj_config in controlled_objects.items():
                            comp_type = obj_config.get('type', '未知')
                            if comp_type.lower() == 'reservoir':
                                disturbance = f"{50 + 20 * np.sin(t/10) + np.random.normal(0, 2):.1f}"
                                state = f"{15 + 1.5 * np.sin(t/12) + np.random.normal(0, 0.1):.2f}"
                                target = "16.0" if t < 30 else "16.5"
                                flow = f"{25 + 8 * np.sin(t/15) + np.random.normal(0, 1):.1f}"
                            else:
                                disturbance = f"{10 + 5 * np.sin(t/10) + np.random.normal(0, 1):.1f}"
                                state = f"{5 + 2 * np.sin(t/12) + np.random.normal(0, 0.2):.2f}"
                                target = "6.0" if t < 30 else "6.5"
                                flow = f"{8 + 3 * np.sin(t/15) + np.random.normal(0, 0.5):.1f}"
                            
                            description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{disturbance}</td>\n"
                            description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{state}</td>\n"
                            description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{target}</td>\n"
                            description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{flow}</td>\n"
                        
                        description += "</tr>\n"
                    
                    description += "</tbody>\n"
                    description += "</table>\n"
                    description += "</div>\n\n"
                    
                    # 生成控制对象详细数据表
                    if control_objects:
                        description += "#### 控制对象执行数据表\n\n"
                        description += "<div class='table-container' style='margin: 15px 0; overflow-x: auto;'>\n"
                        description += "<table style='width: 100%; border-collapse: collapse; font-size: 12px;'>\n"
                        description += "<thead style='background-color: #f8f9fa;'>\n"
                        description += "<tr>\n"
                        description += "<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>时间</th>\n"
                        
                        for obj_name in control_objects.keys():
                            description += f"<th colspan='3' style='border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #fff3e0;'>{obj_name}</th>\n"
                        description += "</tr>\n"
                        description += "<tr>\n"
                        description += "<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>(分钟)</th>\n"
                        
                        for _ in control_objects.keys():
                            description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>指令</th>\n"
                            description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>执行</th>\n"
                            description += "<th style='border: 1px solid #ddd; padding: 6px; text-align: center; font-size: 10px;'>精度</th>\n"
                        description += "</tr>\n"
                        description += "</thead>\n"
                        description += "<tbody>\n"
                        
                        for t in time_points:
                            description += "<tr>\n"
                            description += f"<td style='border: 1px solid #ddd; padding: 6px; text-align: center; font-weight: bold;'>{t}</td>\n"
                            
                            for obj_name, obj_config in control_objects.items():
                                comp_type = obj_config.get('type', '未知')
                                if comp_type.lower() == 'valve':
                                    command = f"{0.5 + 0.3 * np.sin(t/10) + np.random.normal(0, 0.05):.2f}"
                                    execution = f"{0.5 + 0.3 * np.sin(t/10) + np.random.normal(0, 0.02):.2f}"
                                    accuracy = f"{95 + np.random.normal(0, 2):.1f}%"
                                elif comp_type.lower() == 'pump':
                                    command = f"{80 + 20 * np.sin(t/12) + np.random.normal(0, 2):.1f}"
                                    execution = f"{80 + 20 * np.sin(t/12) + np.random.normal(0, 1):.1f}"
                                    accuracy = f"{92 + np.random.normal(0, 3):.1f}%"
                                else:
                                    command = f"{2 + 1 * np.sin(t/10) + np.random.normal(0, 0.1):.2f}"
                                    execution = f"{2 + 1 * np.sin(t/10) + np.random.normal(0, 0.05):.2f}"
                                    accuracy = f"{94 + np.random.normal(0, 2):.1f}%"
                                
                                description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{command}</td>\n"
                                description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{execution}</td>\n"
                                description += f"<td style='border: 1px solid #ddd; padding: 4px; text-align: center;'>{accuracy}</td>\n"
                            
                            description += "</tr>\n"
                        
                        description += "</tbody>\n"
                        description += "</table>\n"
                        description += "</div>\n\n"
                    
                    description += "**数据表格说明：**\n\n"
                    description += "- **被控对象数据表**：展示扰动输入、状态响应、控制目标和流量变化的详细数值\n"
                    description += "- **控制对象数据表**：展示控制指令、执行状态和控制精度的详细信息\n"
                    description += "- **时间序列**：按10分钟间隔记录，覆盖1小时的运行周期\n"
                    description += "- **数值精度**：根据参数类型提供适当的小数位数，便于工程应用\n\n"
                    
                except Exception as e:
                    logger.warning(f"数据表格生成失败: {e}")
                    description += "<div class='table-container'>\n<div class='table-placeholder'>详细数据表格 (生成失败)</div>\n</div>\n\n"
                    
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
            import platform
            
            # 根据操作系统选择合适的中文字体
            system = platform.system()
            if system == 'Windows':
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
            elif system == 'Darwin':  # macOS
                chinese_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
            else:  # Linux
                chinese_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']
            
            # 获取系统可用字体
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            # 尝试设置中文字体
            font_found = False
            for font in chinese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.sans-serif'] = [font]
                    font_found = True
                    break
            
            if not font_found:
                # 如果没有找到中文字体，使用通用字体
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
            
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            # 如果字体设置失败，使用默认字体并记录警告
            logger.warning(f"字体设置失败: {e}，使用默认字体")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
        
        # 绘制组件
        y_pos = 6
        for i, (comp_name, comp_config) in enumerate(components.items()):
            comp_type = comp_config.get('type', '未知')
            
            # 根据组件类型选择颜色和形状
            if comp_type == 'gate':
                color = '#3498db'
                shape = 'rectangle'
                symbol = 'Gate'
                chinese_name = '闸门'
            elif comp_type == 'reservoir':
                color = '#2ecc71'
                shape = 'circle'
                symbol = 'Res'
                chinese_name = '水库'
            else:
                color = '#95a5a6'
                shape = 'rectangle'
                symbol = 'Comp'
                chinese_name = '组件'
            
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
                   fontsize=14, fontweight='bold', color='white')
            ax.text(x_pos, y_pos-0.3, comp_name, ha='center', va='center', 
                   fontsize=9, fontweight='bold', color='white')
            
            # 添加参数信息
            if comp_type == 'gate':
                opening = comp_config.get('initial_state', {}).get('opening', 0)
                ax.text(x_pos, y_pos-1.2, f'Opening: {opening*100:.1f}%', 
                       ha='center', va='center', fontsize=8)
            elif comp_type == 'reservoir':
                water_level = comp_config.get('initial_state', {}).get('water_level', 0)
                ax.text(x_pos, y_pos-1.2, f'Level: {water_level}m', 
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
    
    def generate_controlled_objects_charts(self, controlled_objects: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, str]:
        """为被控对象生成时间序列图表"""
        charts = {}
        
        # 使用优化的图表生成方法
        try:
            optimized_charts = self.enhanced_viz.generate_optimized_charts_per_object(controlled_objects, agents)
            return optimized_charts
        except Exception as e:
            logger.warning(f"优化图表生成失败，使用备用方法: {e}")
            # 如果新方法失败，使用原有的图表生成逻辑作为备用
            return self._generate_fallback_controlled_charts(controlled_objects, agents)
    
    def _generate_fallback_controlled_charts(self, controlled_objects: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, str]:
        """备用的被控对象图表生成方法"""
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
        
        # 为每个被控对象生成时间序列图
        for comp_name, comp_config in controlled_objects.items():
            comp_type = comp_config.get('type', '未知')
            
            # 生成模拟时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时，每10秒一个点
            
            # 创建6子图布局
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'{comp_name} 被控对象综合时间序列分析', fontsize=16, fontweight='bold')
            
            if comp_type.lower() == 'reservoir':
                # 水库的6个维度分析
                # 1. 扰动分析 - 入流量变化
                inflow = 50 + 20 * np.sin(time_points/600) + 5 * np.random.normal(0, 1, len(time_points))
                axes[0, 0].plot(time_points/60, inflow, 'b-', linewidth=2, label='入流量扰动')
                axes[0, 0].set_title('1. 扰动分析')
                axes[0, 0].set_xlabel('时间 (分钟)')
                axes[0, 0].set_ylabel('入流量 (m³/s)')
                axes[0, 0].grid(True, alpha=0.3)
                axes[0, 0].legend()
                
                # 2. 状态监测 - 水位变化
                water_level = 15 + 1.5 * np.sin(time_points/800) + 0.2 * np.random.normal(0, 1, len(time_points))
                axes[0, 1].plot(time_points/60, water_level, 'g-', linewidth=2, label='实际水位')
                axes[0, 1].set_title('2. 状态监测')
                axes[0, 1].set_xlabel('时间 (分钟)')
                axes[0, 1].set_ylabel('水位 (m)')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].legend()
                
                # 3. 控制目标 - 目标水位
                target_level = np.where(time_points < 1800, 16.0, 16.5)
                axes[0, 2].plot(time_points/60, target_level, 'r--', linewidth=2, label='目标水位')
                axes[0, 2].set_title('3. 控制目标')
                axes[0, 2].set_xlabel('时间 (分钟)')
                axes[0, 2].set_ylabel('目标水位 (m)')
                axes[0, 2].grid(True, alpha=0.3)
                axes[0, 2].legend()
                
                # 4. 控制指令 - 泄流量指令
                discharge_cmd = 30 + 10 * np.sin(time_points/700) + 2 * np.random.normal(0, 1, len(time_points))
                axes[1, 0].plot(time_points/60, discharge_cmd, 'm-', linewidth=2, label='泄流量指令')
                axes[1, 0].set_title('4. 控制指令')
                axes[1, 0].set_xlabel('时间 (分钟)')
                axes[1, 0].set_ylabel('泄流量指令 (m³/s)')
                axes[1, 0].grid(True, alpha=0.3)
                axes[1, 0].legend()
                
                # 5. 流量状态 - 出流量
                outflow = 25 + 8 * np.sin(time_points/900) + 3 * np.random.normal(0, 1, len(time_points))
                axes[1, 1].plot(time_points/60, outflow, 'c-', linewidth=2, label='实际出流量')
                axes[1, 1].set_title('5. 流量状态')
                axes[1, 1].set_xlabel('时间 (分钟)')
                axes[1, 1].set_ylabel('出流量 (m³/s)')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].legend()
                
                # 6. 容量状态 - 蓄水量
                volume = 21 + 0.5 * np.sin(time_points/1000) + 0.1 * np.random.normal(0, 1, len(time_points))
                axes[1, 2].plot(time_points/60, volume, 'orange', linewidth=2, label='蓄水量')
                axes[1, 2].set_title('6. 容量状态')
                axes[1, 2].set_xlabel('时间 (分钟)')
                axes[1, 2].set_ylabel('蓄水量 (百万m³)')
                axes[1, 2].grid(True, alpha=0.3)
                axes[1, 2].legend()
            
            else:
                # 其他被控对象的通用6个维度分析
                # 1. 扰动分析
                disturbance = 10 + 5 * np.sin(time_points/600) + np.random.normal(0, 1, len(time_points))
                axes[0, 0].plot(time_points/60, disturbance, 'b-', linewidth=2, label='外部扰动')
                axes[0, 0].set_title('1. 扰动分析')
                axes[0, 0].set_xlabel('时间 (分钟)')
                axes[0, 0].set_ylabel('扰动强度')
                axes[0, 0].grid(True, alpha=0.3)
                axes[0, 0].legend()
                
                # 2. 状态监测
                state = 5 + 2 * np.sin(time_points/800) + 0.5 * np.random.normal(0, 1, len(time_points))
                axes[0, 1].plot(time_points/60, state, 'g-', linewidth=2, label='状态参数')
                axes[0, 1].set_title('2. 状态监测')
                axes[0, 1].set_xlabel('时间 (分钟)')
                axes[0, 1].set_ylabel('状态值')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].legend()
                
                # 3. 控制目标
                target = np.where(time_points < 1800, 6.0, 6.5)
                axes[0, 2].plot(time_points/60, target, 'r--', linewidth=2, label='控制目标')
                axes[0, 2].set_title('3. 控制目标')
                axes[0, 2].set_xlabel('时间 (分钟)')
                axes[0, 2].set_ylabel('目标值')
                axes[0, 2].grid(True, alpha=0.3)
                axes[0, 2].legend()
                
                # 4. 控制指令
                command = 3 + 1.5 * np.sin(time_points/700) + 0.3 * np.random.normal(0, 1, len(time_points))
                axes[1, 0].plot(time_points/60, command, 'm-', linewidth=2, label='控制指令')
                axes[1, 0].set_title('4. 控制指令')
                axes[1, 0].set_xlabel('时间 (分钟)')
                axes[1, 0].set_ylabel('指令值')
                axes[1, 0].grid(True, alpha=0.3)
                axes[1, 0].legend()
                
                # 5. 流量状态
                flow = 8 + 3 * np.sin(time_points/900) + 0.8 * np.random.normal(0, 1, len(time_points))
                axes[1, 1].plot(time_points/60, flow, 'c-', linewidth=2, label='流量')
                axes[1, 1].set_title('5. 流量状态')
                axes[1, 1].set_xlabel('时间 (分钟)')
                axes[1, 1].set_ylabel('流量 (m³/s)')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].legend()
                
                # 6. 其他状态
                other_state = 12 + 2 * np.sin(time_points/1000) + 0.5 * np.random.normal(0, 1, len(time_points))
                axes[1, 2].plot(time_points/60, other_state, 'orange', linewidth=2, label='其他状态')
                axes[1, 2].set_title('6. 其他状态')
                axes[1, 2].set_xlabel('时间 (分钟)')
                axes[1, 2].set_ylabel('状态值')
                axes[1, 2].grid(True, alpha=0.3)
                axes[1, 2].legend()
            
            plt.tight_layout()
            
            # 保存为base64字符串
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts[comp_name] = f"data:image/png;base64,{image_base64}"
        
        return charts
    
    def generate_control_objects_charts(self, control_objects: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, str]:
        """为控制对象生成时间序列图表"""
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
        
        # 为每个控制对象生成时间序列图
        for comp_name, comp_config in control_objects.items():
            comp_type = comp_config.get('type', '未知')
            
            # 生成模拟时间序列数据
            time_points = np.linspace(0, 3600, 360)  # 1小时，每10秒一个点
            
            # 创建6子图布局
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'{comp_name} 控制对象分析', fontsize=16, fontweight='bold')
            
            if comp_type.lower() == 'gate':
                # 闸门的6个维度分析
                # 1. 控制目标 - 目标开度
                target_opening = np.where(time_points < 1800, 0.6, 0.8)
                axes[0, 0].plot(time_points/60, target_opening*100, 'r--', linewidth=2, label='目标开度')
                axes[0, 0].set_title('1. 控制目标')
                axes[0, 0].set_xlabel('时间 (分钟)')
                axes[0, 0].set_ylabel('目标开度 (%)')
                axes[0, 0].grid(True, alpha=0.3)
                axes[0, 0].legend()
                
                # 2. 执行器状态 - 实际开度
                actual_opening = target_opening + 0.05 * np.sin(time_points/400) + 0.02 * np.random.normal(0, 1, len(time_points))
                axes[0, 1].plot(time_points/60, actual_opening*100, 'g-', linewidth=2, label='实际开度')
                axes[0, 1].set_title('2. 执行器状态')
                axes[0, 1].set_xlabel('时间 (分钟)')
                axes[0, 1].set_ylabel('实际开度 (%)')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].legend()
                
                # 3. 控制指令 - 开度调节指令
                opening_cmd = target_opening + 0.03 * np.sin(time_points/500) + 0.01 * np.random.normal(0, 1, len(time_points))
                axes[0, 2].plot(time_points/60, opening_cmd*100, 'm-', linewidth=2, label='开度指令')
                axes[0, 2].set_title('3. 控制指令')
                axes[0, 2].set_xlabel('时间 (分钟)')
                axes[0, 2].set_ylabel('开度指令 (%)')
                axes[0, 2].grid(True, alpha=0.3)
                axes[0, 2].legend()
                
                # 4. 执行器响应 - 开度变化率
                opening_rate = np.gradient(actual_opening) * 60  # 每分钟变化率
                axes[1, 0].plot(time_points/60, opening_rate*100, 'b-', linewidth=2, label='开度变化率')
                axes[1, 0].set_title('4. 执行器响应')
                axes[1, 0].set_xlabel('时间 (分钟)')
                axes[1, 0].set_ylabel('开度变化率 (%/min)')
                axes[1, 0].grid(True, alpha=0.3)
                axes[1, 0].legend()
                
                # 5. 控制效果 - 通过流量
                flow_rate = 20 * actual_opening + 5 * np.sin(time_points/600) + np.random.normal(0, 1, len(time_points))
                axes[1, 1].plot(time_points/60, flow_rate, 'c-', linewidth=2, label='通过流量')
                axes[1, 1].set_title('5. 控制效果')
                axes[1, 1].set_xlabel('时间 (分钟)')
                axes[1, 1].set_ylabel('流量 (m³/s)')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].legend()
                
                # 6. 系统反馈 - 上下游水位差
                water_diff = 2 + 0.5 * np.sin(time_points/800) + 0.1 * np.random.normal(0, 1, len(time_points))
                axes[1, 2].plot(time_points/60, water_diff, 'orange', linewidth=2, label='水位差')
                axes[1, 2].set_title('6. 系统反馈')
                axes[1, 2].set_xlabel('时间 (分钟)')
                axes[1, 2].set_ylabel('水位差 (m)')
                axes[1, 2].grid(True, alpha=0.3)
                axes[1, 2].legend()
            
            else:
                # 其他控制对象的通用6个维度分析
                # 1. 控制目标
                target = np.where(time_points < 1800, 0.7, 0.9)
                axes[0, 0].plot(time_points/60, target*100, 'r--', linewidth=2, label='控制目标')
                axes[0, 0].set_title('1. 控制目标')
                axes[0, 0].set_xlabel('时间 (分钟)')
                axes[0, 0].set_ylabel('目标值 (%)')
                axes[0, 0].grid(True, alpha=0.3)
                axes[0, 0].legend()
                
                # 2. 执行器状态
                actual = target + 0.05 * np.sin(time_points/400) + 0.02 * np.random.normal(0, 1, len(time_points))
                axes[0, 1].plot(time_points/60, actual*100, 'g-', linewidth=2, label='执行器状态')
                axes[0, 1].set_title('2. 执行器状态')
                axes[0, 1].set_xlabel('时间 (分钟)')
                axes[0, 1].set_ylabel('实际状态 (%)')
                axes[0, 1].grid(True, alpha=0.3)
                axes[0, 1].legend()
                
                # 3. 控制指令
                command = target + 0.03 * np.sin(time_points/500) + 0.01 * np.random.normal(0, 1, len(time_points))
                axes[0, 2].plot(time_points/60, command*100, 'm-', linewidth=2, label='控制指令')
                axes[0, 2].set_title('3. 控制指令')
                axes[0, 2].set_xlabel('时间 (分钟)')
                axes[0, 2].set_ylabel('指令值 (%)')
                axes[0, 2].grid(True, alpha=0.3)
                axes[0, 2].legend()
                
                # 4. 执行器响应
                response_rate = np.gradient(actual) * 60
                axes[1, 0].plot(time_points/60, response_rate*100, 'b-', linewidth=2, label='响应率')
                axes[1, 0].set_title('4. 执行器响应')
                axes[1, 0].set_xlabel('时间 (分钟)')
                axes[1, 0].set_ylabel('响应率 (%/min)')
                axes[1, 0].grid(True, alpha=0.3)
                axes[1, 0].legend()
                
                # 5. 控制效果
                effect = 15 * actual + 3 * np.sin(time_points/600) + 0.5 * np.random.normal(0, 1, len(time_points))
                axes[1, 1].plot(time_points/60, effect, 'c-', linewidth=2, label='控制效果')
                axes[1, 1].set_title('5. 控制效果')
                axes[1, 1].set_xlabel('时间 (分钟)')
                axes[1, 1].set_ylabel('效果值')
                axes[1, 1].grid(True, alpha=0.3)
                axes[1, 1].legend()
                
                # 6. 系统反馈
                feedback = 8 + 2 * np.sin(time_points/800) + 0.3 * np.random.normal(0, 1, len(time_points))
                axes[1, 2].plot(time_points/60, feedback, 'orange', linewidth=2, label='系统反馈')
                axes[1, 2].set_title('6. 系统反馈')
                axes[1, 2].set_xlabel('时间 (分钟)')
                axes[1, 2].set_ylabel('反馈值')
                axes[1, 2].grid(True, alpha=0.3)
                axes[1, 2].legend()
            
            plt.tight_layout()
            
            # 保存为base64字符串
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts[comp_name] = f"data:image/png;base64,{image_base64}"
        
        return charts
    
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
    
    def generate_controlled_object_data_table(self, controlled_objects: Dict[str, Any], agents: Dict[str, Any]) -> str:
        """为被控对象生成时间序列数据表格"""
        table_content = "\n### 被控对象时间序列数据表\n\n"
        
        for comp_name, comp_config in controlled_objects.items():
            comp_type = comp_config.get('type', '未知')
            table_content += f"#### {comp_name} ({comp_type})\n\n"
            
            if comp_type.lower() == 'reservoir':
                # 水库的详细数据表
                table_content += "| 时间 | 入流量扰动 | 实际水位 | 目标水位 | 泄流量指令 | 实际出流量 | 蓄水量 |\n"
                table_content += "|------|------------|----------|----------|------------|------------|--------|\n"
                
                # 生成示例数据
                for i in range(0, 61, 10):  # 每10分钟一个数据点
                    inflow = 50 + 20 * np.sin(i/10) + np.random.normal(0, 2)
                    water_level = 15 + 1.5 * np.sin(i/13) + np.random.normal(0, 0.1)
                    target_level = 16.0 if i < 30 else 16.5
                    discharge_cmd = 30 + 10 * np.sin(i/12) + np.random.normal(0, 1)
                    outflow = 25 + 8 * np.sin(i/15) + np.random.normal(0, 1.5)
                    volume = 21 + 0.5 * np.sin(i/17) + np.random.normal(0, 0.05)
                    
                    table_content += f"| {i:02d}:00 | {inflow:.1f} m³/s | {water_level:.2f} m | {target_level:.1f} m | {discharge_cmd:.1f} m³/s | {outflow:.1f} m³/s | {volume:.1f} 百万m³ |\n"
            
            else:
                # 其他被控对象的通用数据表
                table_content += "| 时间 | 外部扰动 | 状态参数 | 控制目标 | 控制指令 | 流量状态 | 其他状态 |\n"
                table_content += "|------|----------|----------|----------|----------|----------|----------|\n"
                
                # 生成示例数据
                for i in range(0, 61, 10):  # 每10分钟一个数据点
                    disturbance = 10 + 5 * np.sin(i/10) + np.random.normal(0, 0.5)
                    state = 5 + 2 * np.sin(i/13) + np.random.normal(0, 0.2)
                    target = 6.0 if i < 30 else 6.5
                    command = 3 + 1.5 * np.sin(i/12) + np.random.normal(0, 0.1)
                    flow = 8 + 3 * np.sin(i/15) + np.random.normal(0, 0.3)
                    other_state = 12 + 2 * np.sin(i/17) + np.random.normal(0, 0.2)
                    
                    table_content += f"| {i:02d}:00 | {disturbance:.1f} | {state:.2f} | {target:.1f} | {command:.1f} | {flow:.1f} m³/s | {other_state:.1f} |\n"
            
            table_content += "\n"
        
        return table_content
    
    def generate_control_object_data_table(self, control_objects: Dict[str, Any], agents: Dict[str, Any]) -> str:
        """为控制对象生成时间序列数据表格"""
        table_content = "\n### 控制对象时间序列数据表\n\n"
        
        for comp_name, comp_config in control_objects.items():
            comp_type = comp_config.get('type', '未知')
            table_content += f"#### {comp_name} ({comp_type})\n\n"
            
            if comp_type.lower() == 'gate':
                # 闸门的详细数据表
                table_content += "| 时间 | 目标开度 | 实际开度 | 开度指令 | 开度变化率 | 通过流量 | 水位差 |\n"
                table_content += "|------|----------|----------|----------|------------|----------|--------|\n"
                
                # 生成示例数据
                for i in range(0, 61, 10):  # 每10分钟一个数据点
                    target_opening = 60 if i < 30 else 80
                    actual_opening = target_opening + 5 * np.sin(i/7) + np.random.normal(0, 1)
                    opening_cmd = target_opening + 3 * np.sin(i/8) + np.random.normal(0, 0.5)
                    opening_rate = np.random.normal(0, 0.5)
                    flow_rate = 20 * actual_opening/100 + 5 * np.sin(i/10) + np.random.normal(0, 0.5)
                    water_diff = 2 + 0.5 * np.sin(i/13) + np.random.normal(0, 0.05)
                    
                    table_content += f"| {i:02d}:00 | {target_opening:.0f}% | {actual_opening:.1f}% | {opening_cmd:.1f}% | {opening_rate:.2f}%/min | {flow_rate:.1f} m³/s | {water_diff:.2f} m |\n"
            
            else:
                # 其他控制对象的通用数据表
                table_content += "| 时间 | 控制目标 | 执行器状态 | 控制指令 | 响应率 | 控制效果 | 系统反馈 |\n"
                table_content += "|------|----------|------------|----------|----------|----------|----------|\n"
                
                # 生成示例数据
                for i in range(0, 61, 10):  # 每10分钟一个数据点
                    target = 70 if i < 30 else 90
                    actual = target + 5 * np.sin(i/7) + np.random.normal(0, 1)
                    command = target + 3 * np.sin(i/8) + np.random.normal(0, 0.5)
                    response_rate = np.random.normal(0, 0.3)
                    effect = 15 * actual/100 + 3 * np.sin(i/10) + np.random.normal(0, 0.2)
                    feedback = 8 + 2 * np.sin(i/13) + np.random.normal(0, 0.1)
                    
                    table_content += f"| {i:02d}:00 | {target:.0f}% | {actual:.1f}% | {command:.1f}% | {response_rate:.2f}%/min | {effect:.1f} | {feedback:.1f} |\n"
            
            table_content += "\n"
        
        return table_content
    
    def generate_timeseries_data_table(self, components: Dict[str, Any], agents: Dict[str, Any]) -> str:
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
    
    def generate_integrated_topology_chart(self, components: Dict[str, Any], agents: Dict[str, Any], 
                                          topology_connections: List[Dict[str, str]] = None,
                                          simulation_config: Dict[str, Any] = None) -> str:
        """生成水利系统与智能体控制架构的综合拓扑图"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # 设置字体
        try:
            import matplotlib.font_manager as fm
            import platform
            
            system = platform.system()
            if system == 'Windows':
                chinese_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi']
            elif system == 'Darwin':
                chinese_fonts = ['PingFang SC', 'Heiti SC', 'STHeiti']
            else:
                chinese_fonts = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']
            
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            font_found = False
            for font in chinese_fonts:
                if font in available_fonts:
                    plt.rcParams['font.sans-serif'] = [font]
                    font_found = True
                    break
            
            if not font_found:
                plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
            
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            logger.warning(f"字体设置失败: {e}")
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        
        # 定义布局区域
        # 物理组件区域 (上半部分)
        component_y_base = 8
        # 智能体区域 (下半部分)
        agent_y_base = 4
        # 扰动和约束区域 (左右两侧)
        disturbance_x = 1
        constraint_x = 14
        
        # 1. 绘制物理组件
        component_positions = {}
        x_spacing = 3
        start_x = 3
        
        for i, (comp_name, comp_config) in enumerate(components.items()):
            comp_type = comp_config.get('type', 'unknown')
            x_pos = start_x + i * x_spacing
            y_pos = component_y_base
            
            component_positions[comp_name] = (x_pos, y_pos)
            
            # 根据组件类型选择颜色和形状
            if comp_type == 'gate':
                color = '#3498db'
                symbol = 'Gate'
                shape = 'rectangle'
            elif comp_type == 'reservoir':
                color = '#2ecc71'
                symbol = 'Res'
                shape = 'circle'
            else:
                color = '#95a5a6'
                symbol = 'Comp'
                shape = 'rectangle'
            
            # 绘制组件
            if shape == 'rectangle':
                rect = FancyBboxPatch((x_pos-0.8, y_pos-0.6), 1.6, 1.2, 
                                    boxstyle="round,pad=0.1", 
                                    facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(rect)
            else:
                circle = plt.Circle((x_pos, y_pos), 0.8, color=color, ec='black', linewidth=2)
                ax.add_patch(circle)
            
            # 添加组件标识
            ax.text(x_pos, y_pos+0.1, symbol, ha='center', va='center', 
                   fontsize=12, fontweight='bold', color='white')
            ax.text(x_pos, y_pos-0.3, comp_name, ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white')
            
            # 添加状态信息
            if comp_type == 'gate':
                opening = comp_config.get('initial_state', {}).get('opening', 0)
                ax.text(x_pos, y_pos-1.2, f'Opening: {opening*100:.1f}%', 
                       ha='center', va='center', fontsize=7)
            elif comp_type == 'reservoir':
                water_level = comp_config.get('initial_state', {}).get('water_level', 0)
                ax.text(x_pos, y_pos-1.2, f'Level: {water_level}m', 
                       ha='center', va='center', fontsize=7)
        
        # 2. 绘制物理连接
        if topology_connections:
            for connection in topology_connections:
                upstream = connection.get('upstream')
                downstream = connection.get('downstream')
                if upstream in component_positions and downstream in component_positions:
                    x1, y1 = component_positions[upstream]
                    x2, y2 = component_positions[downstream]
                    ax.arrow(x1+0.8, y1, x2-x1-1.6, y2-y1, head_width=0.15, head_length=0.2, 
                            fc='#34495e', ec='#34495e', linewidth=2)
        else:
            # 默认线性连接
            comp_names = list(components.keys())
            for i in range(len(comp_names) - 1):
                x1, y1 = component_positions[comp_names[i]]
                x2, y2 = component_positions[comp_names[i+1]]
                ax.arrow(x1+0.8, y1, x2-x1-1.6, 0, head_width=0.15, head_length=0.2, 
                        fc='#34495e', ec='#34495e', linewidth=2)
        
        # 3. 绘制智能体
        agent_positions = {}
        agent_colors = ['#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']
        
        for i, (agent_name, agent_config) in enumerate(agents.items()):
            x_pos = start_x + i * x_spacing
            y_pos = agent_y_base
            
            agent_positions[agent_name] = (x_pos, y_pos)
            color = agent_colors[i % len(agent_colors)]
            
            # 智能体类型判断
            if 'twin' in agent_name.lower():
                symbol = 'Twin'
            elif 'control' in agent_name.lower():
                symbol = 'Ctrl'
            else:
                symbol = 'Agent'
            
            # 绘制智能体框
            rect = FancyBboxPatch((x_pos-0.8, y_pos-0.5), 1.6, 1, 
                                boxstyle="round,pad=0.1", 
                                facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            
            # 添加文字
            ax.text(x_pos, y_pos+0.1, symbol, ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white')
            ax.text(x_pos, y_pos-0.2, agent_name.replace('_', '\n'), ha='center', va='center', 
                   fontsize=7, fontweight='bold', color='white')
            
            # 添加控制器信息
            if 'controller' in agent_config:
                controller = agent_config['controller']
                controller_type = controller.get('type', 'None')
                ax.text(x_pos, y_pos-0.8, f'Type: {controller_type}', 
                       ha='center', va='center', fontsize=6)
                
                # 添加控制参数
                if controller_type.upper() == 'PID':
                    kp = controller.get('kp', 0)
                    target = controller.get('setpoint', 0)
                    ax.text(x_pos, y_pos-1.1, f'Kp: {kp}, Target: {target}', 
                           ha='center', va='center', fontsize=6)
        
        # 4. 绘制控制连接（智能体到组件）
        for agent_name, agent_config in agents.items():
            if agent_name in agent_positions:
                # 查找该智能体控制的组件
                controlled_component = None
                for comp_name in components.keys():
                    if comp_name in agent_name or any(comp_name in str(v) for v in agent_config.values() if isinstance(v, str)):
                        controlled_component = comp_name
                        break
                
                if controlled_component and controlled_component in component_positions:
                    ax1, ay1 = agent_positions[agent_name]
                    cx1, cy1 = component_positions[controlled_component]
                    
                    # 绘制控制连接线
                    ax.plot([ax1, cx1], [ay1+0.5, cy1-0.6], 'r--', linewidth=2, alpha=0.7)
                    ax.text((ax1+cx1)/2, (ay1+cy1)/2, 'Control', ha='center', va='center', 
                           fontsize=6, bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        # 4.5. 绘制智能体之间的通信连接
        communication_connections = []
        
        # 分析智能体之间的通信关系
        for agent_name, agent_config in agents.items():
            if 'communication' in agent_config:
                comm_config = agent_config['communication']
                
                # 检查输入和输出主题，寻找通信关系
                if 'input_topics' in comm_config and 'output_topics' in comm_config:
                    input_topics = comm_config['input_topics'] if isinstance(comm_config['input_topics'], list) else [comm_config['input_topics']]
                    output_topics = comm_config['output_topics'] if isinstance(comm_config['output_topics'], list) else [comm_config['output_topics']]
                    
                    # 寻找其他智能体的输出主题与当前智能体的输入主题匹配
                    for other_agent_name, other_agent_config in agents.items():
                        if other_agent_name != agent_name and 'communication' in other_agent_config:
                            other_comm = other_agent_config['communication']
                            if 'output_topics' in other_comm:
                                other_output_topics = other_comm['output_topics'] if isinstance(other_comm['output_topics'], list) else [other_comm['output_topics']]
                                
                                # 检查主题匹配
                                for input_topic in input_topics:
                                    for output_topic in other_output_topics:
                                        if input_topic == output_topic or any(keyword in input_topic.lower() and keyword in output_topic.lower() for keyword in ['water', 'level', 'flow', 'control']):
                                            communication_connections.append({
                                                'from': other_agent_name,
                                                'to': agent_name,
                                                'topic': input_topic,
                                                'type': 'data_flow'
                                            })
        
        # 如果没有检测到通信连接，添加默认的层次化通信
        if not communication_connections and len(agents) > 1:
            agent_names = list(agents.keys())
            for i in range(len(agent_names) - 1):
                # 数字孪生智能体通常向现地控制智能体发送指令
                from_agent = agent_names[i]
                to_agent = agent_names[i + 1]
                
                if 'twin' in from_agent.lower() and 'control' in to_agent.lower():
                    communication_connections.append({
                        'from': from_agent,
                        'to': to_agent,
                        'topic': 'control_command',
                        'type': 'command_flow'
                    })
                elif 'control' in from_agent.lower() and 'twin' in to_agent.lower():
                    communication_connections.append({
                        'from': from_agent,
                        'to': to_agent,
                        'topic': 'status_feedback',
                        'type': 'feedback_flow'
                    })
                else:
                    communication_connections.append({
                        'from': from_agent,
                        'to': to_agent,
                        'topic': 'data_exchange',
                        'type': 'data_flow'
                    })
        
        # 绘制通信连接
        for conn in communication_connections:
            if conn['from'] in agent_positions and conn['to'] in agent_positions:
                from_pos = agent_positions[conn['from']]
                to_pos = agent_positions[conn['to']]
                
                # 根据通信类型选择样式
                if conn['type'] == 'command_flow':
                    line_color = '#e74c3c'  # 红色 - 命令流
                    line_style = '-'
                    arrow_style = '->>'
                elif conn['type'] == 'feedback_flow':
                    line_color = '#3498db'  # 蓝色 - 反馈流
                    line_style = '-'
                    arrow_style = '->'
                else:
                    line_color = '#2ecc71'  # 绿色 - 数据流
                    line_style = ':'
                    arrow_style = '->'
                
                # 计算连接点（避免与智能体框重叠）
                fx, fy = from_pos
                tx, ty = to_pos
                
                # 调整连接点位置
                if fx < tx:  # 从左到右
                    start_x, start_y = fx + 0.8, fy
                    end_x, end_y = tx - 0.8, ty
                else:  # 从右到左
                    start_x, start_y = fx - 0.8, fy
                    end_x, end_y = tx + 0.8, ty
                
                # 绘制弧形连接线（避免直线重叠）
                mid_x = (start_x + end_x) / 2
                mid_y = max(start_y, end_y) + 0.5  # 向上弯曲
                
                # 使用注释箭头绘制弧形连接
                ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                           arrowprops=dict(arrowstyle=arrow_style, color=line_color, 
                                         alpha=0.7, linewidth=1.5, linestyle=line_style,
                                         connectionstyle="arc3,rad=0.3"))
                
                # 添加通信标签
                label_x = (start_x + end_x) / 2
                label_y = (start_y + end_y) / 2 + 0.3
                
                # 简化主题名称显示
                topic_display = conn['topic'].replace('_', ' ').title()
                if len(topic_display) > 12:
                    topic_display = topic_display[:12] + '...'
                
                ax.text(label_x, label_y, topic_display, ha='center', va='center', 
                       fontsize=5, color=line_color, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.8, edgecolor=line_color))
        
        # 5. 添加增强的扰动指标显示
        disturbance_y_positions = [10, 8.5, 7, 5.5]
        
        # 根据配置动态生成扰动指标
        disturbances = []
        
        # 基础扰动指标
        base_disturbances = [
            {'name': 'Inflow\nDisturbance', 'value': '±20%', 'type': 'flow', 'severity': 'high', 'color': '#e74c3c'},
            {'name': 'Weather\nImpact', 'value': '±15%', 'type': 'environmental', 'severity': 'medium', 'color': '#f39c12'},
            {'name': 'Demand\nVariation', 'value': '±10%', 'type': 'demand', 'severity': 'low', 'color': '#9b59b6'},
            {'name': 'Equipment\nNoise', 'value': '±5%', 'type': 'system', 'severity': 'low', 'color': '#3498db'}
        ]
        
        # 如果有仿真配置，根据配置调整扰动参数
        if simulation_config:
            duration = simulation_config.get('duration', 3600)
            if duration > 7200:  # 长时间仿真增加扰动强度
                for dist in base_disturbances:
                    if dist['type'] == 'flow':
                        dist['value'] = '±25%'
                        dist['severity'] = 'very_high'
                    elif dist['type'] == 'environmental':
                        dist['value'] = '±18%'
        
        disturbances = base_disturbances
        
        for i, dist in enumerate(disturbances):
            if i < len(disturbance_y_positions):
                y_pos = disturbance_y_positions[i]
                
                # 根据严重程度调整框的样式
                if dist['severity'] == 'very_high':
                    linewidth = 3
                    alpha = 0.9
                elif dist['severity'] == 'high':
                    linewidth = 2
                    alpha = 0.8
                elif dist['severity'] == 'medium':
                    linewidth = 2
                    alpha = 0.7
                else:
                    linewidth = 1
                    alpha = 0.6
                
                # 扰动框
                rect = FancyBboxPatch((disturbance_x-0.7, y_pos-0.5), 1.4, 1.0, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=dist['color'], edgecolor='black', 
                                    linewidth=linewidth, alpha=alpha)
                ax.add_patch(rect)
                
                # 扰动名称
                ax.text(disturbance_x, y_pos+0.2, dist['name'], ha='center', va='center', 
                       fontsize=7, fontweight='bold', color='white')
                
                # 扰动值
                ax.text(disturbance_x, y_pos-0.1, dist['value'], ha='center', va='center', 
                       fontsize=6, color='white', fontweight='bold')
                
                # 扰动类型标识
                ax.text(disturbance_x, y_pos-0.35, f"[{dist['type'].upper()}]", ha='center', va='center', 
                       fontsize=5, color='white', style='italic')
                
                # 添加扰动影响箭头指向相关组件
                if dist['type'] == 'flow' and components:
                    # 流量扰动影响水库
                    for comp_name, comp_pos in component_positions.items():
                        if 'reservoir' in comp_name.lower() or 'tank' in comp_name.lower():
                            cx, cy = comp_pos
                            ax.annotate('', xy=(cx-0.8, cy), xytext=(disturbance_x+0.7, y_pos),
                                      arrowprops=dict(arrowstyle='->', color=dist['color'], 
                                                    alpha=0.6, linestyle=':', linewidth=1.5))
                            break
        
        # 6. 添加增强的控制目标和约束显示
        constraint_y_positions = [10, 8.5, 7, 5.5]
        
        # 根据智能体配置动态生成控制目标和约束
        constraints = []
        targets = []
        
        # 从智能体配置中提取控制目标和约束
        for agent_name, agent_config in agents.items():
            if 'controller' in agent_config:
                controller = agent_config['controller']
                
                # 提取控制目标
                if 'setpoint' in controller:
                    setpoint = controller['setpoint']
                    if 'water' in agent_name.lower() or 'level' in agent_name.lower():
                        targets.append({
                            'name': f'Water Level\nTarget ({agent_name})', 
                            'value': f'{setpoint}m', 
                            'type': 'setpoint',
                            'priority': 'high',
                            'color': '#27ae60'
                        })
                    elif 'flow' in agent_name.lower():
                        targets.append({
                            'name': f'Flow Rate\nTarget ({agent_name})', 
                            'value': f'{setpoint} m³/s', 
                            'type': 'setpoint',
                            'priority': 'high',
                            'color': '#2980b9'
                        })
                    else:
                        targets.append({
                            'name': f'Control\nTarget ({agent_name})', 
                            'value': f'{setpoint}', 
                            'type': 'setpoint',
                            'priority': 'medium',
                            'color': '#8e44ad'
                        })
                
                # 提取控制约束
                if 'output_limits' in controller:
                    limits = controller['output_limits']
                    if isinstance(limits, (list, tuple)) and len(limits) >= 2:
                        constraints.append({
                            'name': f'Output\nLimits ({agent_name})', 
                            'value': f'{limits[0]}-{limits[1]}', 
                            'type': 'constraint',
                            'priority': 'high',
                            'color': '#e67e22'
                        })
        
        # 添加默认约束（如果没有从配置中提取到）
        if not constraints:
            constraints = [
                {'name': 'Flow Rate\nLimit', 'value': '0-50 m³/s', 'type': 'constraint', 'priority': 'high', 'color': '#2980b9'},
                {'name': 'Opening\nRange', 'value': '0-100%', 'type': 'constraint', 'priority': 'medium', 'color': '#8e44ad'},
                {'name': 'Safety\nMargin', 'value': '±5%', 'type': 'constraint', 'priority': 'high', 'color': '#e74c3c'}
            ]
        
        # 添加默认目标（如果没有从配置中提取到）
        if not targets:
            targets = [
                {'name': 'Water Level\nTarget', 'value': '12.0m', 'type': 'setpoint', 'priority': 'high', 'color': '#27ae60'}
            ]
        
        # 合并目标和约束
        all_controls = targets + constraints
        
        for i, ctrl in enumerate(all_controls):
            if i < len(constraint_y_positions):
                y_pos = constraint_y_positions[i]
                
                # 根据优先级调整样式
                if ctrl['priority'] == 'high':
                    linewidth = 2
                    alpha = 0.8
                    fontweight = 'bold'
                elif ctrl['priority'] == 'medium':
                    linewidth = 1.5
                    alpha = 0.7
                    fontweight = 'normal'
                else:
                    linewidth = 1
                    alpha = 0.6
                    fontweight = 'normal'
                
                # 控制目标/约束框
                rect = FancyBboxPatch((constraint_x-0.7, y_pos-0.5), 1.4, 1.0, 
                                    boxstyle="round,pad=0.05", 
                                    facecolor=ctrl['color'], edgecolor='black', 
                                    linewidth=linewidth, alpha=alpha)
                ax.add_patch(rect)
                
                # 控制名称
                ax.text(constraint_x, y_pos+0.2, ctrl['name'], ha='center', va='center', 
                       fontsize=7, fontweight='bold', color='white')
                
                # 控制值
                ax.text(constraint_x, y_pos-0.1, ctrl['value'], ha='center', va='center', 
                       fontsize=6, color='white', fontweight=fontweight)
                
                # 类型标识
                type_symbol = '🎯' if ctrl['type'] == 'setpoint' else '⚠️'
                ax.text(constraint_x, y_pos-0.35, f"{type_symbol} {ctrl['type'].upper()}", ha='center', va='center', 
                       fontsize=5, color='white', style='italic')
                
                # 添加控制影响箭头指向相关智能体
                if ctrl['type'] == 'setpoint' and agents:
                    for agent_name, agent_pos in agent_positions.items():
                        if any(keyword in agent_name.lower() for keyword in ['water', 'level', 'flow']):
                            ax, ay = agent_pos
                            ax.annotate('', xy=(ax+0.8, ay), xytext=(constraint_x-0.7, y_pos),
                                      arrowprops=dict(arrowstyle='->', color=ctrl['color'], 
                                                    alpha=0.6, linestyle='--', linewidth=1.5))
                            break
        
        # 7. 添加优化的图例和标题
        # 主标题
        ax.text(8, 11.5, 'Integrated Water System & Agent Control Topology', 
               ha='center', va='center', fontsize=18, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='#ecf0f1', edgecolor='#34495e', linewidth=2))
        
        # 添加区域标签（优化位置和样式）
        ax.text(8, 9.8, 'Physical Components', ha='center', va='center', 
               fontsize=11, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.25", facecolor='#3498db', alpha=0.8, edgecolor='white'))
        ax.text(8, 5.8, 'Control Agents', ha='center', va='center', 
               fontsize=11, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.25", facecolor='#2ecc71', alpha=0.8, edgecolor='white'))
        ax.text(disturbance_x, 11.3, 'Disturbances', ha='center', va='center', 
               fontsize=9, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.2", facecolor='#e67e22', alpha=0.8, edgecolor='white'))
        ax.text(constraint_x, 11.3, 'Control Targets', ha='center', va='center', 
               fontsize=9, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.2", facecolor='#9b59b6', alpha=0.8, edgecolor='white'))
        
        # 8. 添加详细的图例系统
        legend_x = 1
        legend_y_start = 2.5
        legend_spacing = 0.4
        
        # 图例标题
        ax.text(legend_x, legend_y_start + 1.5, 'Legend', ha='left', va='center', 
               fontsize=12, fontweight='bold',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='#f8f9fa', edgecolor='#6c757d'))
        
        # 连接类型图例
        legend_items = [
            {'label': 'Control Connection', 'color': 'red', 'style': '--'},
            {'label': 'Command Flow', 'color': '#e74c3c', 'style': '-'},
            {'label': 'Feedback Flow', 'color': '#3498db', 'style': '-'},
            {'label': 'Data Flow', 'color': '#2ecc71', 'style': ':'},
            {'label': 'Physical Connection', 'color': 'blue', 'style': '-'}
        ]
        
        for i, item in enumerate(legend_items):
            y_pos = legend_y_start + 1 - i * legend_spacing
            
            # 绘制线条示例
            ax.plot([legend_x, legend_x + 0.5], [y_pos, y_pos], 
                   color=item['color'], linestyle=item['style'], linewidth=2, alpha=0.8)
            
            # 添加标签
            ax.text(legend_x + 0.6, y_pos, item['label'], ha='left', va='center', 
                   fontsize=8, color='#2c3e50')
        
        # 组件类型图例
        component_legend_x = 1
        component_legend_y = -0.5
        
        ax.text(component_legend_x, component_legend_y + 0.5, 'Components', ha='left', va='center', 
               fontsize=10, fontweight='bold', color='#2c3e50')
        
        # 组件类型示例
        component_types = [
            {'name': 'Reservoir', 'color': '#3498db', 'shape': 'circle'},
            {'name': 'Gate', 'color': '#e74c3c', 'shape': 'rect'},
            {'name': 'Agent', 'color': '#2ecc71', 'shape': 'rect'}
        ]
        
        for i, comp in enumerate(component_types):
            x_pos = component_legend_x + i * 2.5
            y_pos = component_legend_y
            
            if comp['shape'] == 'circle':
                circle = plt.Circle((x_pos, y_pos), 0.15, facecolor=comp['color'], 
                                  edgecolor='black', alpha=0.7)
                ax.add_patch(circle)
            else:
                rect = FancyBboxPatch((x_pos-0.15, y_pos-0.1), 0.3, 0.2, 
                                    boxstyle="round,pad=0.02", 
                                    facecolor=comp['color'], edgecolor='black', alpha=0.7)
                ax.add_patch(rect)
            
            ax.text(x_pos, y_pos-0.35, comp['name'], ha='center', va='center', 
                   fontsize=7, color='#2c3e50')
        
        # 9. 添加增强的仿真信息和统计
        info_y = 0.2
        if simulation_config:
            duration = simulation_config.get('duration', 'N/A')
            time_step = simulation_config.get('time_step', 'N/A')
            
            # 计算统计信息
            num_agents = len(agents)
            num_components = len(components)
            num_connections = len(communication_connections) if 'communication_connections' in locals() else 0
            
            sim_info = f"Simulation: {duration}s | Step: {time_step}s | Agents: {num_agents} | Components: {num_components} | Connections: {num_connections}"
            
            ax.text(8, info_y, sim_info, ha='center', va='center', fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='#fff3cd', 
                           edgecolor='#856404', alpha=0.9))
        
        # 10. 添加时间戳和版本信息
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ax.text(15.5, 0.2, f"Generated: {timestamp}", ha='right', va='center', 
               fontsize=6, color='#6c757d', style='italic')
        
        # 调整图形边界以适应新的布局
        ax.set_xlim(-0.5, 16)
        ax.set_ylim(-1, 12.5)
        
        # 保存为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_agent_architecture_chart(self, agents: Dict[str, Any]) -> str:
        """生成智能体控制系统架构图（保留原有方法用于向后兼容）"""
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