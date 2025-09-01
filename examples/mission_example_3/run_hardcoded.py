#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mission Example 3 - 增强感知智能体硬编码运行脚本

这个脚本展示了如何通过硬编码方式直接在Python中构建和运行增强感知智能体仿真。
不依赖外部配置文件，所有参数都在代码中直接定义。

运行方式:
    python run_hardcoded.py
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
    from core_lib.core_engine.mas_runner import MASRunner
    from core_lib.central_agents.enhanced_perception_agent import EnhancedPerceptionAgent
    from core_lib.hydro_nodes.reservoir import Reservoir
    from core_lib.utils.logger import setup_logger
    from core_lib.utils.visualization import plot_simulation_results
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保CHS-SDK已正确安装并且在Python路径中")
    sys.exit(1)

def setup_logging():
    """设置日志系统"""
    log_dir = Path("logs/example_3/hardcoded")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "simulation.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_reservoir_component():
    """创建水库物理组件"""
    reservoir_config = {
        'name': 'reservoir',
        'type': 'reservoir',
        'parameters': {
            'initial_depth': 10.0,      # 初始水深 (m)
            'surface_area': 1000000.0,  # 表面积 (m²)
            'max_depth': 50.0,          # 最大水深 (m)
            'min_depth': 2.0,           # 最小水深 (m)
            'inflow_rate': 100.0,       # 入流量 (m³/s)
            'outflow_rate': 80.0,       # 出流量 (m³/s)
            'evaporation_rate': 0.001,  # 蒸发率 (m/day)
            'seepage_rate': 0.0001,     # 渗漏率 (m/day)
        }
    }
    
    reservoir = Reservoir(
        name=reservoir_config['name'],
        **reservoir_config['parameters']
    )
    
    return reservoir

def create_enhanced_perception_agent():
    """创建增强感知智能体"""
    agent_config = {
        'name': 'enhanced_perception_agent',
        'type': 'enhanced_perception',
        'parameters': {
            'perception_range': 1000.0,     # 感知范围 (m)
            'sensor_accuracy': 0.95,        # 传感器精度
            'noise_level': 0.05,           # 噪声水平
            'update_frequency': 1.0,        # 更新频率 (Hz)
            'memory_capacity': 1000,        # 记忆容量
            'learning_rate': 0.01,         # 学习率
            'adaptation_threshold': 0.1,    # 适应阈值
            'fault_detection_enabled': True, # 故障检测
            'predictive_analysis': True,    # 预测分析
            'anomaly_detection': True,      # 异常检测
        },
        'topics': {
            'subscribe': ['perception/reservoir/state'],
            'publish': ['perception/analysis/result', 'perception/alert/anomaly']
        }
    }
    
    agent = EnhancedPerceptionAgent(
        name=agent_config['name'],
        **agent_config['parameters']
    )
    
    # 设置订阅和发布主题
    for topic in agent_config['topics']['subscribe']:
        agent.subscribe(topic)
    
    for topic in agent_config['topics']['publish']:
        agent.setup_publisher(topic)
    
    return agent

def setup_fault_injection(simulation, fault_time=5):
    """设置故障注入"""
    def inject_sensor_fault():
        """注入传感器故障"""
        logger = logging.getLogger(__name__)
        logger.warning(f"在第{fault_time}步注入传感器故障")
        
        # 这里可以添加具体的故障注入逻辑
        # 例如：修改传感器读数、增加噪声等
        
    # 在指定时间注入故障
    simulation.schedule_event(fault_time, inject_sensor_fault)

def run_simulation():
    """运行仿真"""
    logger = setup_logging()
    logger.info("开始增强感知智能体硬编码仿真")
    
    try:
        # 仿真参数
        simulation_params = {
            'duration': 20,              # 仿真步数
            'time_step': 1.0,           # 时间步长 (秒)
            'real_time_factor': 1.0,    # 实时因子
            'output_directory': 'results/example_3/hardcoded',
            'save_history': True,
            'enable_visualization': True,
            'enable_logging': True,
        }
        
        # 创建仿真构建器
        builder = SimulationBuilder()
        
        # 设置仿真参数
        builder.set_time_parameters(
            duration=simulation_params['duration'],
            time_step=simulation_params['time_step']
        )
        
        builder.set_output_parameters(
            output_directory=simulation_params['output_directory'],
            save_history=simulation_params['save_history']
        )
        
        # 创建并添加物理组件
        logger.info("创建水库组件")
        reservoir = create_reservoir_component()
        builder.add_component(reservoir)
        
        # 创建并添加智能体
        logger.info("创建增强感知智能体")
        agent = create_enhanced_perception_agent()
        builder.add_agent(agent)
        
        # 设置消息主题
        builder.add_message_topic('perception/reservoir/state')
        builder.add_message_topic('perception/analysis/result')
        builder.add_message_topic('perception/alert/anomaly')
        
        # 构建仿真
        logger.info("构建仿真系统")
        simulation = builder.build()
        
        # 设置故障注入
        setup_fault_injection(simulation, fault_time=5)
        
        # 创建MAS运行器
        runner = MASRunner(simulation)
        
        # 设置回调函数
        def step_callback(step, time, state):
            if step % 5 == 0:  # 每5步输出一次
                logger.info(f"仿真步骤: {step}, 时间: {time:.1f}s")
                
                # 输出水库状态
                if 'reservoir' in state:
                    depth = state['reservoir'].get('depth', 0)
                    logger.info(f"  水库深度: {depth:.2f}m")
                
                # 输出智能体状态
                if 'enhanced_perception_agent' in state:
                    agent_state = state['enhanced_perception_agent']
                    logger.info(f"  智能体状态: {agent_state}")
        
        runner.set_step_callback(step_callback)
        
        # 运行仿真
        logger.info("开始运行仿真")
        start_time = time.time()
        
        results = runner.run()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"仿真完成，耗时: {execution_time:.2f}秒")
        
        # 保存结果
        output_dir = Path(simulation_params['output_directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存仿真历史
        if results and 'history' in results:
            history_file = output_dir / "simulation_history.json"
            import json
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(results['history'], f, indent=2, ensure_ascii=False)
            logger.info(f"仿真历史已保存到: {history_file}")
        
        # 生成可视化图表
        if simulation_params['enable_visualization'] and results:
            try:
                plot_file = output_dir / "simulation_results.png"
                plot_simulation_results(results, str(plot_file))
                logger.info(f"可视化图表已保存到: {plot_file}")
            except Exception as e:
                logger.warning(f"生成可视化图表失败: {e}")
        
        # 输出仿真统计信息
        logger.info("=== 仿真统计信息 ===")
        logger.info(f"总仿真步数: {simulation_params['duration']}")
        logger.info(f"时间步长: {simulation_params['time_step']}秒")
        logger.info(f"总仿真时间: {simulation_params['duration'] * simulation_params['time_step']}秒")
        logger.info(f"执行时间: {execution_time:.2f}秒")
        logger.info(f"实时因子: {(simulation_params['duration'] * simulation_params['time_step']) / execution_time:.2f}")
        
        # 输出组件信息
        logger.info("=== 组件信息 ===")
        logger.info(f"物理组件数量: 1 (水库)")
        logger.info(f"智能体数量: 1 (增强感知智能体)")
        logger.info(f"消息主题数量: 3")
        
        # 输出结果文件位置
        logger.info("=== 输出文件 ===")
        logger.info(f"结果目录: {output_dir.absolute()}")
        logger.info(f"日志文件: {log_dir / 'simulation.log'}")
        
        return results
        
    except Exception as e:
        logger.error(f"仿真运行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """主函数"""
    print("="*60)
    print("Mission Example 3 - 增强感知智能体硬编码仿真")
    print("="*60)
    print()
    print("这个示例展示了如何通过硬编码方式运行增强感知智能体仿真。")
    print("所有参数都在代码中直接定义，不依赖外部配置文件。")
    print()
    print("仿真特性:")
    print("- 水库物理组件仿真")
    print("- 增强感知智能体")
    print("- 传感器故障注入")
    print("- 实时监控和日志")
    print("- 结果可视化")
    print()
    
    # 询问用户是否继续
    try:
        response = input("按Enter键开始仿真，或输入'q'退出: ").strip().lower()
        if response == 'q':
            print("仿真已取消")
            return
    except KeyboardInterrupt:
        print("\n仿真已取消")
        return
    
    # 运行仿真
    results = run_simulation()
    
    if results:
        print("\n仿真成功完成！")
        print("请查看日志文件和结果目录获取详细信息。")
    else:
        print("\n仿真失败，请查看日志文件获取错误信息。")
        sys.exit(1)

if __name__ == "__main__":
    main()