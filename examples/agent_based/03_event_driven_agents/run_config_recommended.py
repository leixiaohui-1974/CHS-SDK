#!/usr/bin/env python3
"""
Configuration-driven multi-agent system (MAS) simulation script - 推荐版本.

这个脚本演示了改进后的多智能体系统架构，解决了主题一致性问题。
所有主题都通过communication模块统一管理，避免了重复定义和不一致问题。
"""

import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.adaptive_pid_controller import AdaptivePIDController
from core_lib.local_agents.control.smart_pid_controller import SmartPIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def load_config(config_path):
    """加载YAML配置文件。"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def get_topic_path_by_key(topics_dict, topic_key):
    """
    通过键名获取主题路径，确保一致性。
    
    Args:
        topics_dict: 包含所有主题定义的字典
        topic_key: 主题键名
        
    Returns:
        对应的主题路径字符串
    """
    if topic_key not in topics_dict:
        raise KeyError(f"主题键 '{topic_key}' 未在communication模块中定义")
    topic_info = topics_dict[topic_key]
    if isinstance(topic_info, str):
        return topic_info
    return topic_info['path']

def get_config_value_by_path(config, path):
    """
    通过路径获取配置值，支持点分隔的路径。
    
    Args:
        config: 配置字典
        path: 点分隔的路径，如 "analysis.target_water_level"
        
    Returns:
        对应的配置值
    """
    keys = path.split('.')
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise KeyError(f"配置路径 '{path}' 未找到")
    return value

def create_components(config, message_bus):
    """根据配置创建组件。"""
    components = {}
    topics = config['communication']['topics']
    
    for name, comp_config in config['components'].items():
        comp_type = comp_config['type']
        initial_state = comp_config['initial_state']
        parameters = comp_config.get('parameters', {})
        
        if comp_type == 'Reservoir':
            # 检查组件是否配置了消息总线
            mb_config = comp_config.get('message_bus', {})
            if mb_config:
                # 通过键名获取主题路径
                state_topic_key = mb_config.get('state_topic_key')
                if state_topic_key:
                    state_topic = get_topic_path_by_key(topics, state_topic_key)
                    components[name] = Reservoir(
                        name=name,
                        initial_state=initial_state,
                        parameters=parameters,
                        message_bus=message_bus,
                        state_topic=state_topic
                    )
                else:
                    components[name] = Reservoir(
                        name=name,
                        initial_state=initial_state,
                        parameters=parameters
                    )
            else:
                components[name] = Reservoir(
                    name=name,
                    initial_state=initial_state,
                    parameters=parameters
                )
        elif comp_type == 'Gate':
            # 检查组件是否启用了消息总线
            mb_config = comp_config.get('message_bus', {})
            if mb_config:
                # 通过键名获取主题路径
                action_topic_key = mb_config.get('action_topic_key')
                if action_topic_key:
                    action_topic = get_topic_path_by_key(topics, action_topic_key)
                    components[name] = Gate(
                        name=name,
                        initial_state=initial_state,
                        parameters=parameters,
                        message_bus=message_bus,
                        action_topic=action_topic
                    )
                else:
                    components[name] = Gate(
                        name=name,
                        initial_state=initial_state,
                        parameters=parameters
                    )
            else:
                components[name] = Gate(
                    name=name,
                    initial_state=initial_state,
                    parameters=parameters
                )
        else:
            raise ValueError(f"未知的组件类型: {comp_type}")
    
    return components

def create_agents(config, components, message_bus):
    """根据配置创建智能体。"""
    agents = []
    topics = config['communication']['topics']
    
    for agent_name, agent_config in config['agents'].items():
        agent_type = agent_config['type']
        agent_id = agent_config['agent_id']
        
        if agent_type == 'DigitalTwinAgent':
            simulated_object_name = agent_config['simulated_object']
            simulated_object = components[simulated_object_name]
            
            # 通过键名获取主题路径
            mb_config = agent_config.get('message_bus', {})
            state_topic_key = mb_config.get('state_topic_key', 'reservoir_state')
            state_topic = get_topic_path_by_key(topics, state_topic_key)
            
            agent = DigitalTwinAgent(
                agent_id=agent_id,
                simulated_object=simulated_object,
                message_bus=message_bus,
                state_topic=state_topic
            )
            agents.append(agent)
            
        elif agent_type == 'UnifiedGateControlAgent':
            # 创建控制器
            controller_config = agent_config['controller']
            if controller_config['type'] == 'PIDController':
                params = controller_config['parameters']
                # 处理setpoint引用
                if 'setpoint_key' in params:
                    # 如果setpoint_key是配置路径引用，则获取实际值
                    setpoint = get_config_value_by_path(config, params['setpoint_key'])
                elif 'setpoint' in params:
                    setpoint = params['setpoint']
                else:
                    setpoint = 0.0  # 默认值
                    
                controller = PIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=setpoint,
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            elif controller_config['type'] == 'AdaptivePIDController':
                params = controller_config['parameters']
                # 处理setpoint引用
                if 'setpoint_key' in params:
                    # 如果setpoint_key是配置路径引用，则获取实际值
                    setpoint = get_config_value_by_path(config, params['setpoint_key'])
                elif 'setpoint' in params:
                    setpoint = params['setpoint']
                else:
                    setpoint = 0.0  # 默认值
                    
                controller = AdaptivePIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=setpoint,
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            elif controller_config['type'] == 'SmartPIDController':
                params = controller_config['parameters']
                # 处理setpoint引用
                if 'setpoint_key' in params:
                    # 如果setpoint_key是配置路径引用，则获取实际值
                    setpoint = get_config_value_by_path(config, params['setpoint_key'])
                elif 'setpoint' in params:
                    setpoint = params['setpoint']
                else:
                    setpoint = 0.0  # 默认值
                    
                controller = SmartPIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=setpoint,
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            else:
                raise ValueError(f"未知的控制器类型: {controller_config['type']}")
            
            # 增强控制逻辑：增加积分抗饱和和微分滤波
            if hasattr(controller, 'integral_windup_limit'):
                controller.integral_windup_limit = params.get('windup_limit', 0.5)
            if hasattr(controller, 'filter_time_constant'):
                controller.filter_time_constant = params.get('filter_constant', 0.1)
            
            # 通过键名获取主题路径
            mb_config = agent_config['message_bus']
            observation_topic_key = mb_config.get('observation_topic_key', 'reservoir_state')
            observation_topic = get_topic_path_by_key(topics, observation_topic_key)
            
            action_topic_key = mb_config.get('action_topic_key', 'gate_action')
            action_topic = get_topic_path_by_key(topics, action_topic_key)
            
            observation_key = mb_config.get('observation_field', 'water_level')
            
            # 使用统一配置的topics
            agent = UnifiedGateControlAgent(
                agent_id=agent_id,
                controller=controller,
                message_bus=message_bus,
                observation_topic=observation_topic,
                observation_key=observation_key,
                action_topic=action_topic,
                time_step=config['simulation']['time_step'],
                target_component=agent_config.get('target_component', 'gate_1'),
                control_type=agent_config.get('control_type', 'water_level_control')
            )
            
            # 调试配置
            debug_config = agent_config.get('debug', {})
            if debug_config.get('enabled', False):
                control_log_topic_key = debug_config.get('control_log_topic_key', 'control_log')
                control_log_topic = get_topic_path_by_key(topics, control_log_topic_key)
                agent.enable_control_logging(
                    enabled=True,
                    state_topic=control_log_topic,
                    interval=debug_config.get('log_interval', 5)
                )
            agents.append(agent)
            
        else:
            raise ValueError(f"未知的智能体类型: {agent_type}")
    
    return agents

def extract_simulation_data(history):
    """从仿真历史中提取数据用于分析。"""
    time_data = []
    reservoir_water_level = []
    reservoir_volume = []
    gate_opening = []
    
    for i, step_data in enumerate(history):
        time_data.append(i)  # 时间步索引
        
        # 提取水库数据
        if 'reservoir_1' in step_data:
            reservoir_water_level.append(step_data['reservoir_1']['water_level'])
            reservoir_volume.append(step_data['reservoir_1']['volume'])
        
        # 提取闸门数据
        if 'gate_1' in step_data:
            gate_opening.append(step_data['gate_1']['opening'])
    
    return {
        'time': time_data,
        'reservoir_water_level': reservoir_water_level,
        'reservoir_volume': reservoir_volume,
        'gate_opening': gate_opening
    }

def analyze_results(config, data):
    """分析仿真结果。"""
    print("\n--- 分析结果 ---")
    
    if config['analysis']['final_state_report']:
        target_level = config['analysis']['target_water_level']
        final_level = data['reservoir_water_level'][-1] if data['reservoir_water_level'] else 0
        final_volume = data['reservoir_volume'][-1] if data['reservoir_volume'] else 0
        final_opening = data['gate_opening'][-1] if data['gate_opening'] else 0
        
        print(f"\n=== 多智能体系统性能分析 ===")
        print(f"目标水位: {target_level:.2f} m")
        print(f"最终水位: {final_level:.2f} m")
        print(f"最终水库库容: {final_volume:.0f} m³")
        print(f"最终闸门开度: {final_opening:.3f}")
        
        # 计算稳态误差
        steady_state_error = abs(final_level - target_level)
        print(f"稳态误差: {steady_state_error:.3f} m")
        
        # 性能验证
        print("\n=== 控制性能验证 ===")
        if steady_state_error < 0.5:
            print("✓ 通过: 稳态误差可接受 (< 0.5 m)")
        else:
            print("✗ 未通过: 稳态误差过大 (>= 0.5 m)")

def generate_plots(config, data):
    """生成可视化图表。"""
    if not config['visualization']['enabled']:
        return
    
    viz_config = config['visualization']
    plots_config = viz_config['plots']
    topics = config['communication']['topics']
    
    # 创建子图
    fig, axes = plt.subplots(len(plots_config), 1, figsize=(12, 4 * len(plots_config)))
    if len(plots_config) == 1:
        axes = [axes]
    
    for i, plot_config in enumerate(plots_config):
        # 获取x轴数据
        x_data = data[plot_config['x_data']]
        
        # 获取y轴数据
        topic_key = plot_config['topic_key']
        field = plot_config['field']
        
        # 根据主题和字段获取数据
        if topic_key == 'reservoir_state' and field == 'water_level':
            y_data = data['reservoir_water_level']
        elif topic_key == 'reservoir_state' and field == 'volume':
            y_data = data['reservoir_volume']
        elif topic_key == 'gate_action' and field == 'opening':
            y_data = data['gate_opening']
        else:
            # 默认处理
            y_data = data.get(field, [])
        
        axes[i].plot(x_data, y_data, 'b-', linewidth=2, label='实际值')
        
        # 添加目标线（如果指定）
        if 'target_line_key' in plot_config:
            target_line_key = plot_config['target_line_key']
            target_value = get_config_value_by_path(config, target_line_key)
            axes[i].axhline(y=target_value, color='r', linestyle='--', linewidth=2, label=f'目标值 ({target_value})')
            axes[i].legend()
        
        axes[i].set_title(plot_config['title'], fontsize=14, fontweight='bold')
        axes[i].set_xlabel('时间步', fontsize=12)
        axes[i].set_ylabel(plot_config['ylabel'], fontsize=12)
        axes[i].grid(True, alpha=0.3)
        axes[i].tick_params(axis='both', which='major', labelsize=10)
    
    plt.tight_layout()
    
    # 保存图表
    save_path = viz_config['save_path']
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n结果图表已保存为 '{save_path}'")
    
    plt.close()

def run_simulation(config):
    """运行多智能体系统仿真。"""
    print("--- 设置多智能体系统仿真 ---")
    
    # 创建仿真框架
    simulation_config = {
        'end_time': config['simulation']['end_time'],
        'time_step': config['simulation']['time_step'],
        'start_time': config['simulation']['start_time']
    }

    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 创建组件
    components = create_components(config, message_bus)
    
    # 创建智能体
    agents = create_agents(config, components, message_bus)
    
    # 将组件添加到框架
    for name, component in components.items():
        harness.add_component(name, component)
    
    # 将智能体添加到框架
    for agent in agents:
        harness.add_agent(agent)
    
    # 添加连接
    for connection in config['connections']:
        harness.add_connection(connection['from'], connection['to'])
    
    # 构建并运行仿真
    harness.build()
    
    print("\n--- 运行MAS仿真 ---")
    harness.run_mas_simulation()
    print("\n--- 仿真完成 ---")
    
    return harness

def main():
    """主函数。"""
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'recommended_config.yml')
    config = load_config(config_path)
    
    # 运行仿真
    harness = run_simulation(config)
    
    # 提取和分析数据
    data = extract_simulation_data(harness.history)
    analyze_results(config, data)
    
    # 生成可视化
    generate_plots(config, data)
    
    print("\n=== 多智能体系统示例完成 ===")
    print(f"配置文件: {config_path}")
    print(f"仿真结束时间: {config['simulation']['end_time']} 秒")
    print(f"时间步长: {config['simulation']['time_step']} 秒")
    
if __name__ == "__main__":
    main()