#!/usr/bin/env python3
"""
重构版基础水泵控制系统教学示例

本示例展示如何正确使用 core_lib 中的组件，而不是重复定义类：
1. 使用现有的 UnifiedPumpControlAgent
2. 使用现有的 PIDController
3. 使用现有的物理对象
4. 最小化自定义代码，专注于教学目的

教学目标：
- 理解如何正确使用 core_lib 组件
- 掌握泵控制的基本配置方法
- 学习系统集成和参数调优
- 了解架构设计的最佳实践
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
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# 最小化的需求代理 - 仅用于演示
class SimpleDemandAgent(Agent):
    """简单的需求代理 - 仅用于教学演示"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_schedule = {
            50: 5.0,   # 5 m³/s at t=50s
            150: 15.0, # 15 m³/s at t=150s
            300: 8.0,  # 8 m³/s at t=300s
            450: 20.0  # 20 m³/s at t=450s
        }
        
    def run(self, current_time: float):
        """根据时间表发布需求"""
        if int(current_time) in self.demand_schedule:
            demand = self.demand_schedule[int(current_time)]
            print(f"--- DEMAND CHANGE: New demand at t={current_time:.0f}s: {demand} m³/s ---")
            self.bus.publish(self.demand_topic, {'value': demand})

def create_pump_system():
    """创建水泵系统 - 使用 core_lib 组件"""
    print("=== Creating Pump System using core_lib Components ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"
    
    # 创建物理组件 - 使用现有的物理对象
    print("Creating physical components using core_lib...")
    
    # 上游水库
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 20.0, 'volume': 50e6},
        parameters={'surface_area': 2.5e6}
    )
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir",
        initial_state={'water_level': 5.0, 'volume': 10e6},
        parameters={'surface_area': 2.0e6}
    )
    
    # 水泵参数 - 基于实际水泵特性
    pump_params = {
        'max_flow_rate': 25.0,      # 最大流量 m³/s
        'max_head': 30.0,          # 最大扬程 m
        'power_consumption_kw': 100, # 额定功率 kW
        'efficiency_curve': {      # 效率特性曲线
            'flow_points': [0, 5, 10, 15, 20, 25],
            'efficiency_points': [0, 65, 80, 85, 80, 70]
        }
    }
    
    # 创建水泵 - 使用现有的 Pump 类
    pump = Pump(
        name="main_pump",
        initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0},
        parameters=pump_params,
        message_bus=message_bus,
        action_topic=f"{CONTROL_TOPIC_PREFIX}.main_pump"
    )
    
    # 创建泵站 - 使用现有的 PumpStation 类
    pump_station = PumpStation(
        name="pump_station_1",
        initial_state={},
        parameters={},
        pumps=[pump]
    )
    
    # 添加组件到仿真平台
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("pump_station_1", pump_station)
    
    # 定义连接关系
    harness.add_connection("upstream_reservoir", "pump_station_1")
    harness.add_connection("pump_station_1", "downstream_reservoir")
    
    print("Pump system created successfully using core_lib components!")
    return harness, message_bus, DEMAND_TOPIC, CONTROL_TOPIC_PREFIX, pump_station

def create_control_system(message_bus: MessageBus, demand_topic: str, 
                         pump_station: PumpStation, dt: float):
    """创建控制系统 - 使用 core_lib 组件"""
    print("=== Creating Control System using core_lib Components ===")
    
    # 创建需求代理 - 最小化自定义代码
    demand_agent = SimpleDemandAgent("demand_agent", message_bus, demand_topic)
    
    # 创建水泵控制代理 - 使用现有的 UnifiedPumpControlAgent
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=demand_topic,
        control_topic_prefix="action.pump",
        dt=dt,
        # 泵站特定配置
        max_pumps=1,  # 单泵系统
        min_pumps=0
        # 注意：control_strategy 由父类自动设置为 DISCRETE，不需要手动指定
    )
    
    print("Control system created successfully using core_lib components!")
    return demand_agent, pump_control_agent

def analyze_results(harness: SimulationHarness):
    """分析仿真结果 - 使用现有数据结构"""
    print("\n=== Analyzing Results using core_lib Data Structures ===")
    
    history = harness.history
    if not history:
        print("No simulation history available")
        return
    
    # 提取数据 - 使用现有的数据结构
    time_data = []
    demand_data = []
    flow_data = []
    power_data = []
    
    for i, step_data in enumerate(history):
        time_data.append(i * harness.dt)
        
        # 从泵站状态提取数据
        if 'pump_station_1' in step_data:
            pump_state = step_data['pump_station_1']
            flow_data.append(pump_state.get('total_outflow', 0))
            power_data.append(pump_state.get('total_power_draw_kw', 0))
        else:
            flow_data.append(0)
            power_data.append(0)
        
        # 需求数据（简化处理）
        demand_data.append(10.0)  # 简化需求模式
    
    # 计算性能指标
    if flow_data:
        avg_flow = np.mean(flow_data)
        avg_power = np.mean(power_data)
        max_flow = np.max(flow_data)
        
        print(f"Performance Analysis:")
        print(f"  Average Flow: {avg_flow:.2f} m³/s")
        print(f"  Maximum Flow: {max_flow:.2f} m³/s")
        print(f"  Average Power: {avg_power:.2f} kW")
        
        # 绘制结果
        plot_results(time_data, demand_data, flow_data, power_data)
    
    return {
        'avg_flow': avg_flow if flow_data else 0,
        'avg_power': avg_power if power_data else 0,
        'max_flow': max_flow if flow_data else 0
    }

def plot_results(time_data, demand_data, flow_data, power_data):
    """绘制结果 - 简化版本"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 流量响应
    ax1.plot(time_data, demand_data, 'r--', linewidth=2, label='Demand')
    ax1.plot(time_data, flow_data, 'b-', linewidth=2, label='Actual Flow')
    ax1.set_title('Pump Flow Control Response', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Flow Rate (m³/s)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 功率消耗
    ax2.plot(time_data, power_data, 'purple', linewidth=2, label='Power Consumption')
    ax2.set_title('Power Consumption', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Power (kW)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("basic_pump_control_refactored_results.png", dpi=300, bbox_inches='tight')
    print("Results saved to basic_pump_control_refactored_results.png")
    plt.show()

def run_refactored_simulation():
    """运行重构版仿真"""
    print("\n=== Refactored Basic Pump Control System Simulation ===")
    print("This example demonstrates proper use of core_lib components")
    print("Learning objectives:")
    print("1. Understanding how to use existing core_lib components")
    print("2. Proper system configuration and parameter tuning")
    print("3. Integration of physical models and control agents")
    print("4. Best practices for architecture design")
    
    # 创建系统 - 使用 core_lib 组件
    harness, message_bus, demand_topic, control_topic_prefix, pump_station = create_pump_system()
    demand_agent, pump_control_agent = create_control_system(
        message_bus, demand_topic, pump_station, harness.dt
    )
    
    # 添加代理
    harness.add_agent(demand_agent)
    
    # 构建并运行仿真
    print("\n=== Building and Running Simulation ===")
    harness.build()
    
    print("Running simulation...")
    harness.run_mas_simulation()
    
    # 分析结果
    performance = analyze_results(harness)
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. Use existing core_lib components instead of redefining classes")
    print("2. Configure components through parameters, not custom code")
    print("3. Leverage the unified architecture for consistency")
    print("4. Focus on system integration rather than implementation details")
    
    return performance

if __name__ == "__main__":
    performance = run_refactored_simulation()
