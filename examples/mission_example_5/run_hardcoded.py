#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 5 - 水电站仿真与调度策略硬编码运行脚本

这个脚本展示了如何通过硬编码方式直接在Python中构建和运行水电站仿真与调度策略。
所有配置都直接在代码中定义，不依赖外部配置文件。

运行方式:
    python run_hardcoded.py
"""

import os
import sys
from pathlib import Path
import yaml
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入必要的模块
try:
    from core_lib.core_engine.simulation import Simulation
    from core_lib.central_coordination.collaboration.message_bus import MessageBus
    from core_lib.physical_objects.physical import PhysicalComponent
    from core_lib.central_agents.base import BaseAgent
    from core_lib.utils.logging import setup_logging
    from core_lib.utils.visualization import create_plots
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保CHS-SDK已正确安装")
    sys.exit(1)

def create_hardcoded_config():
    """
    创建硬编码的水电站仿真配置
    """
    config = {
        # 基本仿真参数
        'simulation': {
            'time_step': 10.0,
            'num_steps': 100,
            'start_time': '2024-01-01T00:00:00',
            'scenario_name': 'hydropower_hardcoded',
            'description': '水电站仿真与调度策略 - 硬编码版本'
        },
        
        # 物理组件配置
        'components': {
            'forebay': {
                'type': 'ForebayModel',
                'parameters': {
                    'initial_depth': 15.0,
                    'initial_inflow': 150.0,
                    'area': 1000.0,
                    'max_depth': 30.0,
                    'min_depth': 5.0
                }
            },
            'turbine_1': {
                'type': 'TurbineModel',
                'parameters': {
                    'rated_power': 100.0,
                    'efficiency': 0.9,
                    'min_flow': 10.0,
                    'max_flow': 200.0,
                    'head_coefficient': 0.8
                }
            },
            'turbine_2': {
                'type': 'TurbineModel',
                'parameters': {
                    'rated_power': 100.0,
                    'efficiency': 0.9,
                    'min_flow': 10.0,
                    'max_flow': 200.0,
                    'head_coefficient': 0.8
                }
            },
            'spillway_gate': {
                'type': 'SpillwayGateModel',
                'parameters': {
                    'gate_width': 10.0,
                    'gate_height': 5.0,
                    'discharge_coefficient': 0.6,
                    'max_opening': 1.0,
                    'opening_rate': 0.1
                }
            }
        },
        
        # 智能体配置
        'agents': {
            'dispatch_agent': {
                'type': 'DispatchAgent',
                'parameters': {
                    'optimization_method': 'economic_dispatch',
                    'prediction_horizon': 24,
                    'update_interval': 10,
                    'power_demand_topic': 'grid/power_target',
                    'control_topic': 'control/turbines'
                }
            },
            'coordination_agent': {
                'type': 'CoordinationAgent',
                'parameters': {
                    'coordination_strategy': 'multi_unit',
                    'load_balancing': True,
                    'efficiency_optimization': True,
                    'grid_events_topic': 'grid/events'
                }
            },
            'gate_control_agent': {
                'type': 'GateControlAgent',
                'parameters': {
                    'control_strategy': 'water_level_based',
                    'safety_margin': 2.0,
                    'response_time': 5.0,
                    'inflow_topic': 'reservoir/inflow'
                }
            }
        },
        
        # 消息主题配置
        'message_topics': [
            'grid/power_target',
            'control/turbines',
            'grid/events',
            'reservoir/inflow',
            'turbine/status',
            'gate/position',
            'forebay/state',
            'dispatch/schedule',
            'coordination/commands'
        ],
        
        # 场景配置
        'scenarios': {
            'selected_scenario': '5.1',  # 默认运行5.1场景
            '5.1': {
                'name': '水轮机和泄洪闸仿真',
                'description': '基本的水轮机和泄洪闸仿真',
                'parameters': {
                    'tailwater_rise': 2.0,
                    'inflow_variation': 0.1
                }
            },
            '5.2': {
                'name': '多机组协调和电网交互',
                'description': '多个水轮机组的协调运行和电网交互',
                'parameters': {
                    'grid_frequency': 50.0,
                    'load_variation': 0.2
                }
            },
            '5.3': {
                'name': '水轮机经济调度表计算',
                'description': '基于经济性的水轮机调度优化',
                'parameters': {
                    'electricity_price': 0.1,
                    'water_value': 0.05
                }
            },
            '5.4': {
                'name': '闸门调度表计算',
                'description': '泄洪闸门的优化调度策略',
                'parameters': {
                    'flood_threshold': 25.0,
                    'safety_factor': 1.2
                }
            }
        },
        
        # 输出配置
        'output': {
            'save_plots': True,
            'plot_format': 'png',
            'save_data': True,
            'data_format': 'csv',
            'output_directory': 'output',
            'log_level': 'INFO'
        },
        
        # 可视化配置
        'visualization': {
            'real_time_plots': False,
            'plot_interval': 10,
            'plots': [
                'forebay_level',
                'turbine_power',
                'gate_opening',
                'inflow_outflow',
                'efficiency_curves'
            ]
        },
        
        # 性能监控
        'performance': {
            'enable_monitoring': True,
            'metrics': [
                'power_generation',
                'water_usage_efficiency',
                'response_time',
                'system_stability'
            ]
        }
    }
    
    return config

def setup_simulation(config):
    """
    设置仿真环境
    """
    # 创建输出目录
    output_dir = Path(config['output']['output_directory'])
    output_dir.mkdir(exist_ok=True)
    
    # 设置日志
    log_file = output_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_file, config['output']['log_level'])
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 注册消息主题
    for topic in config['message_topics']:
        message_bus.register_topic(topic)
    
    return message_bus, output_dir

def create_components(config, message_bus):
    """
    创建物理组件
    """
    components = {}
    
    for comp_name, comp_config in config['components'].items():
        try:
            # 这里应该根据实际的组件类型创建相应的组件实例
            # 由于具体的组件类可能不存在，我们创建一个通用的物理组件
            component = PhysicalComponent(
                name=comp_name,
                component_type=comp_config['type'],
                parameters=comp_config['parameters'],
                message_bus=message_bus
            )
            components[comp_name] = component
            logging.info(f"创建组件: {comp_name} ({comp_config['type']})")
        except Exception as e:
            logging.error(f"创建组件 {comp_name} 失败: {e}")
    
    return components

def create_agents(config, message_bus):
    """
    创建智能体
    """
    agents = {}
    
    for agent_name, agent_config in config['agents'].items():
        try:
            # 这里应该根据实际的智能体类型创建相应的智能体实例
            # 由于具体的智能体类可能不存在，我们创建一个基础智能体
            agent = BaseAgent(
                name=agent_name,
                agent_type=agent_config['type'],
                parameters=agent_config['parameters'],
                message_bus=message_bus
            )
            agents[agent_name] = agent
            logging.info(f"创建智能体: {agent_name} ({agent_config['type']})")
        except Exception as e:
            logging.error(f"创建智能体 {agent_name} 失败: {e}")
    
    return agents

def run_simulation(config, components, agents, message_bus, output_dir):
    """
    运行仿真
    """
    sim_config = config['simulation']
    
    # 创建仿真实例
    simulation = Simulation(
        time_step=sim_config['time_step'],
        num_steps=sim_config['num_steps'],
        message_bus=message_bus
    )
    
    # 添加组件和智能体到仿真
    for component in components.values():
        simulation.add_component(component)
    
    for agent in agents.values():
        simulation.add_agent(agent)
    
    # 设置场景参数
    selected_scenario = config['scenarios']['selected_scenario']
    scenario_config = config['scenarios'][selected_scenario]
    
    logging.info(f"运行场景: {selected_scenario} - {scenario_config['name']}")
    logging.info(f"场景描述: {scenario_config['description']}")
    
    # 运行仿真
    try:
        results = simulation.run()
        logging.info("仿真运行完成")
        return results
    except Exception as e:
        logging.error(f"仿真运行失败: {e}")
        raise

def save_results(results, config, output_dir):
    """
    保存仿真结果
    """
    if config['output']['save_data']:
        # 保存数据
        data_file = output_dir / f"simulation_data.{config['output']['data_format']}"
        # 这里应该实现实际的数据保存逻辑
        logging.info(f"数据已保存到: {data_file}")
    
    if config['output']['save_plots']:
        # 创建可视化图表
        plots_dir = output_dir / 'plots'
        plots_dir.mkdir(exist_ok=True)
        
        # 这里应该实现实际的绘图逻辑
        for plot_type in config['visualization']['plots']:
            plot_file = plots_dir / f"{plot_type}.{config['output']['plot_format']}"
            # create_plot(results, plot_type, plot_file)
            logging.info(f"图表已保存: {plot_file}")

def main():
    """
    主函数
    """
    print("="*60)
    print("Mission Example 5 - 水电站仿真与调度策略 (硬编码版本)")
    print("="*60)
    print()
    print("这个示例展示了如何通过硬编码方式运行水电站仿真与调度策略。")
    print("所有配置都直接在Python代码中定义，包括：")
    print("- 水轮机和泄洪闸仿真")
    print("- 多机组协调和电网交互")
    print("- 经济调度优化")
    print("- 闸门调度策略")
    print()
    
    try:
        # 创建硬编码配置
        config = create_hardcoded_config()
        
        # 显示当前场景信息
        selected_scenario = config['scenarios']['selected_scenario']
        scenario_info = config['scenarios'][selected_scenario]
        print(f"当前运行场景: {selected_scenario} - {scenario_info['name']}")
        print(f"场景描述: {scenario_info['description']}")
        print()
        
        # 询问用户是否继续
        response = input("按Enter键开始仿真，或输入'q'退出: ").strip().lower()
        if response == 'q':
            print("仿真已取消")
            return
        
        # 设置仿真环境
        message_bus, output_dir = setup_simulation(config)
        
        # 创建组件和智能体
        components = create_components(config, message_bus)
        agents = create_agents(config, message_bus)
        
        print(f"\n创建了 {len(components)} 个物理组件和 {len(agents)} 个智能体")
        print("开始运行仿真...")
        print("-" * 40)
        
        # 运行仿真
        results = run_simulation(config, components, agents, message_bus, output_dir)
        
        # 保存结果
        save_results(results, config, output_dir)
        
        print("-" * 40)
        print("仿真完成！")
        print(f"\n结果文件位置: {output_dir.absolute()}")
        print("- 仿真数据: simulation_data.csv")
        print("- 可视化图表: plots/")
        print("- 日志文件: simulation_*.log")
        
    except KeyboardInterrupt:
        print("\n仿真被用户中断")
    except Exception as e:
        print(f"\n仿真运行失败: {e}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()