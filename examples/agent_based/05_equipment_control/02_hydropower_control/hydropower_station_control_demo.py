#!/usr/bin/env python3
"""
水电站控制系统演示示例

本示例展示如何基于 core_lib 框架实现一个标准的水电站控制系统，包括：
1. 水库水位感知器
2. 坝后水位感知器  
3. 2台水轮机
4. 1个闸门
5. 电力需求发布方
6. 水电站控制智能体

教学目标：
- 理解水电站控制系统的架构设计
- 掌握多组件协调控制方法
- 学习电力需求响应控制策略
- 了解水位-流量-发电功率的耦合关系
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.hydropower_station import HydropowerStation
from core_lib.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent
from core_lib.local_agents.control.hydropower_station_control_agent import HydropowerStationControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class PowerDemandAgent(Agent):
    """电力需求发布代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_schedule = {
            0: 0.0,      # 初始无需求
            50: 20.0,    # 20MW at t=50s
            150: 40.0,   # 40MW at t=150s
            300: 60.0,   # 60MW at t=300s
            450: 30.0,   # 30MW at t=450s
            550: 0.0     # 0MW at t=550s
        }
        
    def run(self, current_time: float):
        """根据时间表发布电力需求"""
        if int(current_time) in self.demand_schedule:
            demand = self.demand_schedule[int(current_time)]
            print(f"--- POWER DEMAND: {demand} MW at t={current_time:.0f}s ---")
            self.bus.publish(self.demand_topic, {
                'target_power_generation': demand * 1e6,  # 转换为瓦特
                'target_total_outflow': 0.0  # 流量目标由控制逻辑决定
            })

class DownstreamReservoirPerceptionAgent(Agent):
    """坝后水位感知代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, 
                 downstream_reservoir: Reservoir, state_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.reservoir = downstream_reservoir
        self.state_topic = state_topic
        
    def run(self, current_time: float):
        """发布坝后水位状态"""
        state = self.reservoir.get_state()
        downstream_head = state.get('water_level', 0.0)
        
        # 发布坝后水位信息
        self.bus.publish(self.state_topic, {
            'downstream_head': downstream_head,
            'downstream_volume': state.get('volume', 0.0)
        })

def create_hydropower_system():
    """创建水电站系统"""
    print("=== Creating Hydropower Station System ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    POWER_DEMAND_TOPIC = "demand.power"
    UPSTREAM_STATE_TOPIC = "state.upstream_reservoir"
    DOWNSTREAM_STATE_TOPIC = "state.downstream_reservoir"
    HYDROPOWER_STATE_TOPIC = "state.hydropower_station"
    GOAL_TOPIC = "goal.hydropower_station"
    
    # 创建物理组件
    print("Creating physical components...")
    
    # 上游水库（坝前）
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 100.0, 'volume': 500e6},  # 100m水位，5亿立方米
        parameters={'surface_area': 5e6}  # 5平方公里
    )
    
    # 下游水库（坝后）
    downstream_reservoir = Reservoir(
        name="downstream_reservoir", 
        initial_state={'water_level': 20.0, 'volume': 50e6},   # 20m水位，5千万立方米
        parameters={'surface_area': 2.5e6}  # 2.5平方公里
    )
    
    # 水轮机参数
    turbine1_params = {
        'efficiency': 0.85,
        'max_flow_rate': 50.0,  # m³/s
        'rated_power': 25e6     # 25MW
    }
    
    turbine2_params = {
        'efficiency': 0.88,
        'max_flow_rate': 60.0,  # m³/s
        'rated_power': 30e6     # 30MW
    }
    
    # 创建水轮机
    turbine1 = WaterTurbine(
        name="turbine_1",
        initial_state={'outflow': 0.0, 'power': 0.0},
        parameters=turbine1_params
    )
    
    turbine2 = WaterTurbine(
        name="turbine_2", 
        initial_state={'outflow': 0.0, 'power': 0.0},
        parameters=turbine2_params
    )
    
    # 闸门参数
    gate_params = {
        'width': 10.0,  # 闸门宽度 10m
        'height': 5.0,  # 闸门高度 5m
        'discharge_coefficient': 0.6
    }
    
    # 创建闸门
    gate = Gate(
        name="spillway_gate",
        initial_state={'opening': 0.0, 'outflow': 0.0},
        parameters=gate_params
    )
    
    # 创建水电站
    hydropower_station = HydropowerStation(
        name="hydropower_station",
        initial_state={},
        parameters={},
        turbines=[turbine1, turbine2],
        gates=[gate]
    )
    
    # 添加组件到仿真平台
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("hydropower_station", hydropower_station)
    
    # 定义连接关系
    harness.add_connection("upstream_reservoir", "hydropower_station")
    harness.add_connection("hydropower_station", "downstream_reservoir")
    
    print("Hydropower system created successfully!")
    return (harness, message_bus, POWER_DEMAND_TOPIC, UPSTREAM_STATE_TOPIC, 
            DOWNSTREAM_STATE_TOPIC, HYDROPOWER_STATE_TOPIC, GOAL_TOPIC, 
            upstream_reservoir, downstream_reservoir, hydropower_station)

def create_control_system(message_bus: MessageBus, upstream_reservoir: Reservoir,
                         downstream_reservoir: Reservoir, hydropower_station: HydropowerStation,
                         power_demand_topic: str, upstream_state_topic: str,
                         downstream_state_topic: str, hydropower_state_topic: str,
                         goal_topic: str, dt: float):
    """创建控制系统"""
    print("=== Creating Control System ===")
    
    # 创建代理
    agents = []
    
    # 1. 电力需求代理
    power_demand_agent = PowerDemandAgent("power_demand_agent", message_bus, power_demand_topic)
    agents.append(power_demand_agent)
    
    # 2. 上游水库感知代理
    upstream_perception_agent = ReservoirPerceptionAgent(
        "upstream_perception_agent", message_bus, upstream_reservoir, upstream_state_topic
    )
    agents.append(upstream_perception_agent)
    
    # 3. 下游水库感知代理
    downstream_perception_agent = DownstreamReservoirPerceptionAgent(
        "downstream_perception_agent", message_bus, downstream_reservoir, downstream_state_topic
    )
    agents.append(downstream_perception_agent)
    
    # 4. 水电站控制代理
    turbine_action_topics = [
        "action.turbine.turbine_1",
        "action.turbine.turbine_2"
    ]
    gate_action_topics = [
        "action.gate.spillway_gate"
    ]
    
    hydropower_control_agent = HydropowerStationControlAgent(
        agent_id="hydropower_control_agent",
        message_bus=message_bus,
        goal_topic=goal_topic,
        state_topic=hydropower_state_topic,
        turbine_action_topics=turbine_action_topics,
        gate_action_topics=gate_action_topics,
        turbine_efficiency=0.85,  # 平均效率
        rho=1000,  # 水密度 kg/m³
        g=9.81     # 重力加速度 m/s²
    )
    agents.append(hydropower_control_agent)
    
    print("Control system created successfully!")
    return agents

def analyze_results(harness: SimulationHarness, agents: List[Agent]):
    """分析仿真结果"""
    print("\n=== Analyzing Results ===")
    
    history = harness.history
    if not history:
        print("No simulation history available")
        return
    
    # 提取数据
    time_data = []
    upstream_level_data = []
    downstream_level_data = []
    power_data = []
    total_flow_data = []
    turbine_flow_data = []
    gate_flow_data = []
    
    for i, step_data in enumerate(history):
        time_data.append(i * harness.dt)
        
        # 上游水位
        if 'upstream_reservoir' in step_data:
            upstream_state = step_data['upstream_reservoir']
            upstream_level_data.append(upstream_state.get('water_level', 0))
        else:
            upstream_level_data.append(0)
        
        # 下游水位
        if 'downstream_reservoir' in step_data:
            downstream_state = step_data['downstream_reservoir']
            downstream_level_data.append(downstream_state.get('water_level', 0))
        else:
            downstream_level_data.append(0)
        
        # 水电站状态
        if 'hydropower_station' in step_data:
            station_state = step_data['hydropower_station']
            power_data.append(station_state.get('total_power_generation', 0) / 1e6)  # 转换为MW
            total_flow_data.append(station_state.get('total_outflow', 0))
            turbine_flow_data.append(station_state.get('turbine_outflow', 0))
            gate_flow_data.append(station_state.get('spillway_outflow', 0))
        else:
            power_data.append(0)
            total_flow_data.append(0)
            turbine_flow_data.append(0)
            gate_flow_data.append(0)
    
    # 计算性能指标
    if power_data:
        avg_power = np.mean(power_data)
        max_power = np.max(power_data)
        avg_flow = np.mean(total_flow_data)
        max_flow = np.max(total_flow_data)
        
        print(f"Performance Analysis:")
        print(f"  Average Power: {avg_power:.2f} MW")
        print(f"  Maximum Power: {max_power:.2f} MW")
        print(f"  Average Flow: {avg_flow:.2f} m³/s")
        print(f"  Maximum Flow: {max_flow:.2f} m³/s")
        
        # 绘制结果
        plot_results(time_data, upstream_level_data, downstream_level_data, 
                    power_data, total_flow_data, turbine_flow_data, gate_flow_data)
    
    return {
        'avg_power': avg_power if power_data else 0,
        'max_power': max_power if power_data else 0,
        'avg_flow': avg_flow if total_flow_data else 0,
        'max_flow': max_flow if total_flow_data else 0
    }

def plot_results(time_data, upstream_level_data, downstream_level_data, 
                power_data, total_flow_data, turbine_flow_data, gate_flow_data):
    """绘制结果"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 水位变化
    ax1.plot(time_data, upstream_level_data, 'b-', linewidth=2, label='Upstream Level')
    ax1.plot(time_data, downstream_level_data, 'r-', linewidth=2, label='Downstream Level')
    ax1.set_title('Reservoir Water Levels', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Water Level (m)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 发电功率
    ax2.plot(time_data, power_data, 'g-', linewidth=2, label='Power Generation')
    ax2.set_title('Power Generation', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Power (MW)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 流量分配
    ax3.plot(time_data, total_flow_data, 'purple', linewidth=2, label='Total Flow')
    ax3.plot(time_data, turbine_flow_data, 'orange', linewidth=2, label='Turbine Flow')
    ax3.plot(time_data, gate_flow_data, 'brown', linewidth=2, label='Gate Flow')
    ax3.set_title('Flow Distribution', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Flow Rate (m³/s)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 水头-功率关系
    head_data = [u - d for u, d in zip(upstream_level_data, downstream_level_data)]
    ax4.scatter(head_data, power_data, alpha=0.6, s=20)
    ax4.set_title('Head vs Power Relationship', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Head (m)')
    ax4.set_ylabel('Power (MW)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("hydropower_station_control_results.png", dpi=300, bbox_inches='tight')
    print("Results saved to hydropower_station_control_results.png")
    plt.show()

def run_hydropower_simulation():
    """运行水电站仿真"""
    print("\n=== Hydropower Station Control System Simulation ===")
    print("This example demonstrates hydropower station control using core_lib")
    print("Learning objectives:")
    print("1. Understanding hydropower station control architecture")
    print("2. Multi-component coordination control methods")
    print("3. Power demand response control strategies")
    print("4. Water level-flow-power coupling relationships")
    
    # 创建系统
    (harness, message_bus, power_demand_topic, upstream_state_topic,
     downstream_state_topic, hydropower_state_topic, goal_topic,
     upstream_reservoir, downstream_reservoir, hydropower_station) = create_hydropower_system()
    
    # 创建控制系统
    agents = create_control_system(
        message_bus, upstream_reservoir, downstream_reservoir, hydropower_station,
        power_demand_topic, upstream_state_topic, downstream_state_topic,
        hydropower_state_topic, goal_topic, harness.dt
    )
    
    # 添加代理
    for agent in agents:
        harness.add_agent(agent)
    
    # 构建并运行仿真
    print("\n=== Building and Running Simulation ===")
    harness.build()
    
    print("Running simulation...")
    harness.run_mas_simulation()
    
    # 分析结果
    performance = analyze_results(harness, agents)
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. Hydropower stations require coordinated control of turbines and gates")
    print("2. Power generation depends on water head and flow rate")
    print("3. Reservoir levels affect available head and power capacity")
    print("4. Multi-agent coordination enables complex control strategies")
    
    return performance

if __name__ == "__main__":
    performance = run_hydropower_simulation()
