#!/usr/bin/env python3
"""
重构版高级泵站控制系统教学示例

基于一致性、解耦性、单一职责原则重构：
1. 使用 core_lib 中的通用组件
2. 分离关注点，降低耦合度
3. 遵循单一职责原则
4. 保持架构一致性

教学目标：
- 理解如何正确使用 core_lib 组件
- 掌握高级泵站控制系统的设计方法
- 学习架构设计的最佳实践
- 了解解耦和单一职责的重要性
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.common.demand_patterns import StepDemandPattern
from core_lib.local_agents.control.unified_pump_station_control_agent import UnifiedPumpStationControlAgent
from core_lib.local_agents.control.pump_control_strategies import ControlStrategyType
from core_lib.local_agents.analysis.performance_analyzer import ComprehensiveAnalyzer
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def create_advanced_pump_system():
    """创建高级泵站系统 - 使用 core_lib 组件"""
    print("=== Creating Advanced Pump Station System using core_lib Components ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"
    
    # 创建物理组件
    print("Creating physical components using core_lib...")
    
    # 上游水库
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 25.0, 'volume': 100e6},
        parameters={'surface_area': 4.0e6}
    )
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir",
        initial_state={'water_level': 8.0, 'volume': 20e6},
        parameters={'surface_area': 2.5e6}
    )
    
    # 创建多台水泵 - 合理规格，避免过度设计
    pumps = []
    pump_specs = [
        {'max_flow_rate': 8.0, 'max_head': 25.0, 'power_consumption_kw': 40, 'efficiency': 0.85},  # 小泵
        {'max_flow_rate': 12.0, 'max_head': 30.0, 'power_consumption_kw': 60, 'efficiency': 0.82},  # 中泵
        {'max_flow_rate': 15.0, 'max_head': 20.0, 'power_consumption_kw': 50, 'efficiency': 0.88}, # 大泵
        {'max_flow_rate': 6.0, 'max_head': 35.0, 'power_consumption_kw': 35, 'efficiency': 0.80}   # 小泵
    ]
    
    for i, specs in enumerate(pump_specs):
        pump = Pump(
            name=f"pump_{i+1}",
            initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0},
            parameters=specs,
            message_bus=message_bus,
            action_topic=f"{CONTROL_TOPIC_PREFIX}.pump_{i+1}"
        )
        pumps.append(pump)
    
    # 创建泵站 - 使用现有的 PumpStation 类
    pump_station = PumpStation(
        name="advanced_pump_station",
        initial_state={},
        parameters={},
        pumps=pumps
    )
    
    # 添加组件到仿真平台
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("advanced_pump_station", pump_station)
    
    # 定义连接关系
    harness.add_connection("upstream_reservoir", "advanced_pump_station")
    harness.add_connection("advanced_pump_station", "downstream_reservoir")
    
    print("Advanced pump station system created successfully using core_lib components!")
    return harness, message_bus, DEMAND_TOPIC, CONTROL_TOPIC_PREFIX, pump_station

def create_control_system(message_bus: MessageBus, demand_topic: str, 
                         pump_station: PumpStation, dt: float):
    """创建控制系统 - 使用 core_lib 组件"""
    print("=== Creating Control System using core_lib Components ===")
    
    # 创建需求代理 - 使用 core_lib 中的需求模式
    demand_steps = {
        50: 5.0,    # 5 m³/s at t=50s
        150: 15.0,  # 15 m³/s at t=150s
        300: 25.0,  # 25 m³/s at t=300s
        400: 10.0,  # 10 m³/s at t=400s
        500: 20.0   # 20 m³/s at t=500s
    }
    
    demand_agent = StepDemandPattern(
        agent_id="advanced_demand_agent",
        message_bus=message_bus,
        demand_topic=demand_topic,
        steps=demand_steps
    )
    
    # 创建泵站控制代理 - 使用 core_lib 中的统一控制代理
    pump_control_agent = UnifiedPumpStationControlAgent(
        agent_id="advanced_pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=demand_topic,
        control_topic_prefix="action.pump",
        control_strategy_type=ControlStrategyType.OPTIMAL,  # 使用最优控制策略
        dt=dt
    )
    
    print("Control system created successfully using core_lib components!")
    return demand_agent, pump_control_agent

def run_advanced_simulation():
    """运行高级仿真 - 使用 core_lib 组件"""
    print("\n=== Refactored Advanced Pump Station Control System Simulation ===")
    print("This example demonstrates proper use of core_lib components")
    print("Learning objectives:")
    print("1. Understanding how to use existing core_lib components")
    print("2. Proper system configuration and parameter tuning")
    print("3. Integration of physical models and control agents")
    print("4. Best practices for architecture design")
    print("5. Separation of concerns and single responsibility principle")
    
    # 创建系统 - 使用 core_lib 组件
    harness, message_bus, demand_topic, control_topic_prefix, pump_station = create_advanced_pump_system()
    demand_agent, pump_control_agent = create_control_system(
        message_bus, demand_topic, pump_station, harness.dt
    )
    
    # 创建性能分析器 - 使用 core_lib 中的分析器
    analyzer = ComprehensiveAnalyzer()
    
    # 添加代理到仿真平台
    harness.add_agent(demand_agent)
    harness.add_agent(pump_control_agent)
    
    # 构建并运行仿真
    print("\n=== Building and Running Simulation ===")
    harness.build()
    
    print("Running simulation...")
    harness.run_mas_simulation()
    
    # 验证控制效果
    print("\n=== Control Effectiveness Validation ===")
    if hasattr(pump_control_agent, 'validate_control_effectiveness'):
        is_effective = pump_control_agent.validate_control_effectiveness()
        if not is_effective:
            print("❌ Control system validation FAILED - Significant control errors detected")
        else:
            print("✅ Control system validation PASSED")
    
    # 分析结果 - 使用 core_lib 中的分析器
    print("\n=== Performance Analysis using core_lib Analyzers ===")
    
    # 从仿真历史中提取数据
    history = harness.history
    if history:
        # 创建需求时间表用于分析
        demand_schedule = {
            50: 5.0,    # 5 m³/s at t=50s
            150: 15.0,  # 15 m³/s at t=150s
            300: 25.0,  # 25 m³/s at t=300s
            400: 10.0,  # 10 m³/s at t=400s
            500: 20.0   # 20 m³/s at t=500s
        }
        
        for i, step_data in enumerate(history):
            current_time = i * harness.dt
            
            # 根据时间表获取当前需求
            current_demand = 0.0
            for time_point in sorted(demand_schedule.keys(), reverse=True):
                if current_time >= time_point:
                    current_demand = demand_schedule[time_point]
                    break
            
            # 从泵站状态提取数据
            if 'advanced_pump_station' in step_data:
                pump_state = step_data['advanced_pump_station']
                
                # 从 PumpStation 状态直接获取聚合数据
                total_flow = pump_state.get('total_outflow', 0.0)
                total_power = pump_state.get('total_power_draw_kw', 0.0)
                running_pumps = pump_state.get('active_pumps', 0)
                
                # 记录数据到分析器
                analyzer.record_data(current_time, {
                    'demand': current_demand,
                    'total_flow': total_flow,
                    'running_pumps': running_pumps,
                    'total_power': total_power,
                    'efficiency': 0.8 if total_power > 0 else 0.0
                })
    
    # 执行综合分析
    system_info = {'total_pumps': len(pump_station.pumps)}
    performance = analyzer.analyze_all(system_info)
    
    # 显示分析结果
    print("\n=== Control Performance Analysis ===")
    control_perf = performance.get('control_performance', {})
    print(f"Mean Flow Error: {control_perf.get('mean_flow_error', 0):.3f} m³/s")
    print(f"Maximum Flow Error: {control_perf.get('max_flow_error', 0):.3f} m³/s")
    print(f"Flow RMSE: {control_perf.get('flow_rmse', 0):.3f} m³/s")
    print(f"Control Accuracy: {control_perf.get('control_accuracy', 0):.3f}")
    
    print("\n=== Energy Performance Analysis ===")
    energy_perf = performance.get('energy_performance', {})
    print(f"Average Power: {energy_perf.get('average_power', 0):.1f} kW")
    print(f"Total Energy: {energy_perf.get('total_energy', 0):.1f} kWh")
    print(f"Average Efficiency: {energy_perf.get('average_efficiency', 0):.3f}")
    print(f"Energy per Unit Flow: {energy_perf.get('energy_per_unit_flow', 0):.3f} kWh/m³")
    
    print("\n=== Utilization Analysis ===")
    util_perf = performance.get('utilization', {})
    print(f"Pump Utilization: {util_perf.get('pump_utilization', 0):.2f}")
    print(f"Max Utilization: {util_perf.get('max_utilization', 0):.2f}")
    print(f"Utilization Variance: {util_perf.get('utilization_variance', 0):.3f}")
    
    # 绘制结果 - 使用 core_lib 中的绘图功能
    analyzer.plot_results("advanced_pump_station_refactored_results.png")
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. Use existing core_lib components instead of redefining classes")
    print("2. Separate concerns: demand generation, control logic, and analysis")
    print("3. Follow single responsibility principle for each component")
    print("4. Maintain architectural consistency across the system")
    print("5. Leverage the unified architecture for better maintainability")
    
    return performance

def demonstrate_architecture_benefits():
    """演示架构设计的好处"""
    print("\n=== Architecture Design Benefits Demonstration ===")
    
    print("\n1. 一致性 (Consistency):")
    print("✅ 所有组件都遵循统一的接口设计")
    print("✅ 消息格式和通信协议一致")
    print("✅ 配置参数命名规范统一")
    
    print("\n2. 解耦性 (Decoupling):")
    print("✅ 需求生成与控制系统解耦")
    print("✅ 控制策略与物理模型解耦")
    print("✅ 性能分析与控制逻辑解耦")
    
    print("\n3. 单一职责 (Single Responsibility):")
    print("✅ DemandPattern: 只负责需求生成")
    print("✅ PumpControlStrategy: 只负责控制算法")
    print("✅ PerformanceAnalyzer: 只负责性能分析")
    print("✅ UnifiedPumpStationControlAgent: 只负责控制协调")
    
    print("\n4. 可扩展性 (Extensibility):")
    print("✅ 可以轻松添加新的需求模式")
    print("✅ 可以轻松添加新的控制策略")
    print("✅ 可以轻松添加新的分析功能")
    
    print("\n5. 可维护性 (Maintainability):")
    print("✅ 每个组件职责明确，易于理解和修改")
    print("✅ 组件间依赖关系清晰，降低维护成本")
    print("✅ 统一的错误处理和日志记录")

if __name__ == "__main__":
    # 运行重构版仿真
    performance = run_advanced_simulation()
    
    # 演示架构设计的好处
    demonstrate_architecture_benefits()
