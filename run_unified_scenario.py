#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一仿真场景运行器

这个脚本提供了一个通用的接口来运行任何基于单一YAML配置文件的仿真场景。
它支持两种运行方式：
1. 命令行方式：python run_unified_scenario.py <config_file_path>
2. 程序调用方式：run_simulation_from_config(config_path)

主要特点：
- 支持单一YAML配置文件格式
- 自动创建物理组件和智能体
- 集成验证和分析功能
- 提供详细的仿真进度和结果报告
"""

import time
import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入核心库
import yaml
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.integral_delay_canal import IntegralDelayCanal
from core_lib.physical_objects.disturbance_node import DisturbanceNode
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_agents.central_mpc_agent import CentralMPCAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.disturbances.rainfall_agent import RainfallAgent
from core_lib.disturbances.water_use_agent import WaterUseAgent
# from core_lib.disturbances.inflow_forecaster_agent import InflowForecasterAgent  # Module not found
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
# Debug modules removed for release
# from core_lib.debug.log_manager import get_log_manager, setup_logging
# from core_lib.debug.debug_collector import collect_debug_data, DataType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_simulation_config(config_path: str) -> Dict[str, Any]:
    """加载仿真配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_components_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """根据配置创建物理组件"""
    components = {}
    
    if 'components' not in config:
        return components
    
    components_config = config['components']
    
    # 处理列表格式的components配置（universal_config格式）
    if isinstance(components_config, list):
        for comp_config in components_config:
            comp_id = comp_config.get('id')
            comp_class = comp_config.get('class', '')
            
            if not comp_id:
                logger.warning("组件配置缺少id字段，跳过")
                continue
            
            # 根据class字段确定组件类型
            if 'unified_canal.UnifiedCanal' in comp_class or 'UnifiedCanal' in comp_class:
                components[comp_id] = UnifiedCanal(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=comp_config.get('parameters', {}).get('model_type', 'canal'),
                    parameters=comp_config.get('parameters', {})
                )
            elif 'gate.Gate' in comp_class or 'Gate' in comp_class:
                components[comp_id] = Gate(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif 'water_turbine.WaterTurbine' in comp_class or 'WaterTurbine' in comp_class:
                components[comp_id] = WaterTurbine(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif 'reservoir.Reservoir' in comp_class or 'Reservoir' in comp_class:
                components[comp_id] = Reservoir(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif 'IntegralDelayCanal' in comp_class:
                # IntegralDelayCanal已弃用，映射到UnifiedCanal
                components[comp_id] = UnifiedCanal(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type='integral_delay',
                    parameters=comp_config.get('parameters', {})
                )
            elif 'disturbance_node.DisturbanceNode' in comp_class or 'DisturbanceNode' in comp_class:
                components[comp_id] = DisturbanceNode(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            else:
                logger.warning(f"未知的组件类型: {comp_class}，跳过组件 {comp_id}")
    
    # 处理字典格式的components配置（传统格式）
    elif isinstance(components_config, dict):
        for comp_name, comp_config in components_config.items():
            comp_type = comp_config.get('type')
            
            if comp_type == 'UnifiedCanal':
                components[comp_name] = UnifiedCanal(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=comp_config.get('model_type', 'canal'),
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == 'Gate':
                components[comp_name] = Gate(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == 'WaterTurbine':
                components[comp_name] = WaterTurbine(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == 'Reservoir':
                components[comp_name] = Reservoir(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == 'IntegralDelayCanal':
                # IntegralDelayCanal已弃用，映射到UnifiedCanal
                components[comp_name] = UnifiedCanal(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type='integral_delay',
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == 'DisturbanceNode':
                components[comp_name] = DisturbanceNode(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            else:
                logger.warning(f"未知的组件类型: {comp_type}，跳过组件 {comp_name}")
    
    return components

def create_agents_from_config(config: Dict[str, Any], components: Dict[str, Any], 
                             message_bus: MessageBus) -> Dict[str, Any]:
    """根据配置创建智能体"""
    agents = {}
    
    if 'agents' not in config:
        return agents
    
    agents_config = config['agents']
    
    # 处理列表格式的agents配置（universal_config格式）
    if isinstance(agents_config, list):
        for agent_config in agents_config:
            agent_class = agent_config.get('class', '')
            agent_id = agent_config.get('id')
            
            if not agent_id:
                logger.warning("智能体配置缺少id字段，跳过")
                continue
            
            try:
                if agent_class == 'PIDControlAgent':
                    # 将PIDControlAgent映射到LocalControlAgent + PIDController
                    from core_lib.local_agents.control.pid_controller import PIDController
                    
                    # 提取PID参数
                    params = agent_config.get('parameters', {})
                    observation_topic = agent_config.get('observation_topic', '')
                    action_topic = agent_config.get('action_topic', '')
                    
                    # 创建PID控制器配置
                    controller_config = {
                        'class': 'PIDController',
                        'config': {
                            'Kp': params.get('kp', 1.0),
                            'Ki': params.get('ki', 0.1),
                            'Kd': params.get('kd', 0.05),
                            'setpoint': params.get('setpoint', 0.0),
                            'min_output': params.get('output_limits', [0.0, 1.0])[0],
                            'max_output': params.get('output_limits', [0.0, 1.0])[1]
                        }
                    }
                    
                    # 创建LocalControlAgent
                    agents[agent_id] = LocalControlAgent(
                        agent_id=agent_id,
                        message_bus=message_bus,
                        dt=1.0,  # 默认时间步长
                        target_component='',  # 将从observation_topic推断
                        control_type='pid',
                        data_sources={'observation_topic': observation_topic},
                        control_targets={'action_topic': action_topic},
                        allocation_config={},
                        controller_config=controller_config
                    )
                else:
                    logger.warning(f"未知的智能体类型: {agent_class}，跳过智能体 {agent_id}")
            except Exception as e:
                logger.error(f"创建智能体 {agent_id} 失败: {e}")
        return agents
    
    # 处理字典格式的agents配置（传统格式）
    for agent_name, agent_config in agents_config.items():
        agent_type = agent_config.get('type')
        agent_id = agent_config.get('agent_id', agent_name)
        
        try:
            if agent_type == 'PhysicalIOAgent':
                agents[agent_name] = PhysicalIOAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif agent_type == 'LocalControlAgent':
                config_data = agent_config.get('config', {})
                # 提取必需的参数
                dt = config_data.get('dt', 1.0)
                target_component = config_data.get('target_component', '')
                control_type = config_data.get('control_type', 'default')
                data_sources = config_data.get('data_sources', {})
                control_targets = config_data.get('control_targets', {})
                allocation_config = config_data.get('allocation_config', {})
                controller_config = config_data.get('controller_config', {})
                
                agents[agent_name] = LocalControlAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    dt=dt,
                    target_component=target_component,
                    control_type=control_type,
                    data_sources=data_sources,
                    control_targets=control_targets,
                    allocation_config=allocation_config,
                    controller_config=controller_config,
                    **{k: v for k, v in config_data.items() if k not in [
                        'dt', 'target_component', 'control_type', 'data_sources',
                        'control_targets', 'allocation_config', 'controller_config'
                    ]}
                )
            elif agent_type == 'DigitalTwinAgent':
                target_component = components.get(agent_config.get('target_component'))
                if target_component:
                    agents[agent_name] = DigitalTwinAgent(
                        agent_id=agent_id,
                        simulated_object=target_component,
                        message_bus=message_bus,
                        **agent_config.get('config', {})
                    )
            elif agent_type == 'CentralMPCAgent':
                agents[agent_name] = CentralMPCAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif agent_type == 'CentralDispatcher':
                agents[agent_name] = CentralDispatcherAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif agent_type == 'RainfallAgent':
                agents[agent_name] = RainfallAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif agent_type == 'WaterUseAgent':
                agents[agent_name] = WaterUseAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif agent_type == 'InflowForecasterAgent':
                agents[agent_name] = InflowForecasterAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            else:
                logger.warning(f"未知的智能体类型: {agent_type}，跳过智能体 {agent_name}")
        except Exception as e:
            logger.error(f"创建智能体 {agent_name} 失败: {e}")
    
    return agents

def setup_connections(harness: SimulationHarness, config: Dict[str, Any], 
                     components: Dict[str, Any]):
    """设置组件连接"""
    if 'connections' not in config:
        return
    
    for connection in config['connections']:
        from_comp = connection.get('from')
        to_comp = connection.get('to')
        
        if from_comp in components and to_comp in components:
            harness.add_connection(from_comp, to_comp)
            logger.info(f"添加连接: {from_comp} -> {to_comp}")
        else:
            logger.warning(f"连接中的组件不存在: {from_comp} -> {to_comp}")

def perform_analysis(config: Dict[str, Any], harness: SimulationHarness) -> Dict[str, Any]:
    """执行仿真结果分析和验证"""
    analysis_results = {}
    
    if 'analysis' not in config or not config['analysis'].get('enable_validation', False):
        return analysis_results
    
    analysis_config = config['analysis']
    history = harness.history
    
    # 基本统计
    analysis_results['simulation_steps'] = len(history)
    analysis_results['simulation_duration'] = len(history) * config.get('simulation', {}).get('time_step', 60)
    
    # 性能指标计算
    if 'performance_metrics' in analysis_config:
        metrics = {}
        for metric in analysis_config['performance_metrics']:
            if metric == 'water_level_stability':
                # 计算水位稳定性
                water_levels = [step.get('water_level', 0) for step in history]
                if water_levels:
                    metrics['water_level_mean'] = sum(water_levels) / len(water_levels)
                    metrics['water_level_std'] = (sum((x - metrics['water_level_mean'])**2 for x in water_levels) / len(water_levels))**0.5
            elif metric == 'control_performance':
                # 计算控制性能
                control_actions = [step.get('control_action', 0) for step in history]
                if control_actions:
                    metrics['control_actions_count'] = len([x for x in control_actions if abs(x) > 0.01])
        
        analysis_results['performance_metrics'] = metrics
    
    # 预期行为验证
    if 'expected_behavior' in analysis_config:
        expected = analysis_config['expected_behavior']
        validation_results = {}
        
        # 检查最终状态
        if history and 'final_water_level_range' in expected:
            final_level = history[-1].get('water_level', 0)
            level_range = expected['final_water_level_range']
            validation_results['final_water_level_in_range'] = level_range[0] <= final_level <= level_range[1]
        
        analysis_results['validation_results'] = validation_results
    
    return analysis_results

def run_simulation_from_config(config_path: str, show_progress: bool = True, 
                              show_summary: bool = True) -> Dict[str, Any]:
    """从配置文件运行仿真的主函数"""
    start_time = time.time()
    
    try:
        # 加载配置
        if show_progress:
            print(f"\n=== 🚀 开始仿真 ===\n")
            print(f"📁 配置文件: {config_path}")
        
        config = load_simulation_config(config_path)
        
        # 获取仿真参数
        sim_config = config.get('simulation', {})
        end_time = sim_config.get('end_time', 3600)
        time_step = sim_config.get('time_step', 60)
        start_time = sim_config.get('start_time', 0)
        description = sim_config.get('description', '未命名仿真')
        
        if show_progress:
            print(f"📋 仿真描述: {description}")
            print(f"⏱️  仿真时长: {end_time}秒 (时间步长: {time_step}秒)")
        
        # 设置基础设施
        message_bus = MessageBus()
        harness = SimulationHarness(config={'start_time': start_time, 'end_time': end_time, 'time_step': time_step})
        
        # 创建组件
        if show_progress:
            print(f"\n🔧 创建物理组件...")
        components = create_components_from_config(config)
        
        for comp_name, component in components.items():
            harness.add_component(comp_name, component)
            if show_progress:
                print(f"  ✅ {comp_name}: {type(component).__name__}")
        
        # 设置连接
        if show_progress:
            print(f"\n🔗 设置组件连接...")
        setup_connections(harness, config, components)
        
        # 创建智能体
        if show_progress:
            print(f"\n🤖 创建智能体...")
        agents = create_agents_from_config(config, components, message_bus)
        
        for agent_name, agent in agents.items():
            harness.add_agent(agent)
            if show_progress:
                print(f"  ✅ {agent_name}: {type(agent).__name__}")
        
        # 构建仿真
        if show_progress:
            print(f"\n⚙️  构建仿真环境...")
        harness.build()
        
        # 运行仿真
        if show_progress:
            print(f"\n🏃 运行仿真...")
        harness.run_mas_simulation()
        
        # 分析结果
        if show_progress:
            print(f"\n📊 分析仿真结果...")
        analysis_results = perform_analysis(config, harness)
        
        # 计算运行时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 显示总结
        if show_summary:
            print(f"\n=== 📈 仿真完成总结 ===\n")
            print(f"✅ 仿真状态: 成功完成")
            print(f"⏱️  执行时间: {execution_time:.2f}秒")
            print(f"📊 仿真步数: {len(harness.history)}")
            print(f"🔧 物理组件: {len(components)}个")
            print(f"🤖 智能体: {len(agents)}个")
            
            if analysis_results:
                print(f"\n📋 分析结果:")
                if 'performance_metrics' in analysis_results:
                    for metric, value in analysis_results['performance_metrics'].items():
                        print(f"  📈 {metric}: {value}")
                
                if 'validation_results' in analysis_results:
                    print(f"\n✅ 验证结果:")
                    for check, result in analysis_results['validation_results'].items():
                        status = "✅ 通过" if result else "❌ 失败"
                        print(f"  {check}: {status}")
        
        return {
            'success': True,
            'execution_time': execution_time,
            'components_count': len(components),
            'agents_count': len(agents),
            'simulation_steps': len(harness.history),
            'analysis_results': analysis_results,
            'history': harness.history
        }
    
    except Exception as e:
        error_msg = f"仿真运行失败: {str(e)}"
        logger.error(error_msg)
        if show_summary:
            print(f"\n❌ {error_msg}")
        return {
            'success': False,
            'error': str(e),
            'execution_time': time.time() - start_time
        }

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="运行基于YAML配置文件的仿真场景")
    parser.add_argument("config_path", type=str, help="YAML配置文件的路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，不显示进度信息")
    parser.add_argument("--no-summary", action="store_true", help="不显示仿真总结")
    
    args = parser.parse_args()
    
    # 运行仿真
    result = run_simulation_from_config(
        config_path=args.config_path,
        show_progress=not args.quiet,
        show_summary=not args.no_summary
    )
    
    # 设置退出码
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()