#!/usr/bin/env python3
"""
Example simulation script for a pump station with multiple pumps.

This script demonstrates how a UnifiedPumpControlAgent can manage multiple pump units
to meet a fluctuating flow demand following CHS-SDK standards.
"""

import sys
import os
import math
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.physical_objects.pipe import Pipe
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent

# 仿真配置常量
class SimulationConfig:
    """仿真配置常量类 - 遵循禁止魔数规范"""
    START_TIME = 0.0
    END_TIME = 600.0
    TIME_STEP = 1.0
    
    # 需求调度配置
    DEMAND_CHANGE_TIME_1 = 100.0  # 第一次需求变化时间
    DEMAND_CHANGE_TIME_2 = 400.0  # 第二次需求变化时间
    INITIAL_DEMAND = 0.0          # 初始需求
    HIGH_DEMAND = 25.0            # 高需求
    LOW_DEMAND = 8.0              # 低需求

# 物理参数常量
class PhysicalConstants:
    """物理参数常量类 - 遵循禁止魔数规范"""
    # 水库参数
    SOURCE_WATER_LEVEL = 10.0      # 源水库水位 (m)
    SOURCE_SURFACE_AREA = 1.0e6    # 源水库表面积 (m²)
    SOURCE_VOLUME = 10.0e6         # 源水库库容 (m³)
    
    DOWNSTREAM_WATER_LEVEL = 25.0  # 下游水库水位 (m)
    DOWNSTREAM_SURFACE_AREA = 1.0e6 # 下游水库表面积 (m²)
    DOWNSTREAM_VOLUME = 25.0e6     # 下游水库库容 (m³)
    
    # 泵参数
    PUMP_MAX_FLOW_RATE = 10.0      # 单泵最大流量 (m³/s)
    PUMP_MAX_HEAD = 20.0           # 单泵最大扬程 (m)
    PUMP_POWER_CONSUMPTION = 50.0  # 单泵功率 (kW)
    NUM_PUMPS = 3                  # 泵数量
    
    # 管道参数
    PIPE_LENGTH = 50.0             # 管道长度 (m)
    PIPE_DIAMETER = 1.5            # 管道直径 (m)
    PIPE_FRICTION_FACTOR = 0.02    # 摩擦系数

class ConfigurableDemandAgent(Agent):
    """可配置的需求代理 - 支持通用需求调度"""
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str, 
                 demand_schedule: Optional[Dict[float, float]] = None):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        
        # 使用传入的调度或默认调度
        self.demand_schedule = demand_schedule or {
            SimulationConfig.START_TIME: SimulationConfig.INITIAL_DEMAND,
            SimulationConfig.DEMAND_CHANGE_TIME_1: SimulationConfig.HIGH_DEMAND,
            SimulationConfig.DEMAND_CHANGE_TIME_2: SimulationConfig.LOW_DEMAND
        }
        
        print(f"ConfigurableDemandAgent created with schedule: {self.demand_schedule}")

    def run(self, current_time: float):
        """根据配置的调度发布需求变化"""
        if current_time in self.demand_schedule:
            demand = self.demand_schedule[current_time]
            print(f"--- DEMAND AGENT: New demand at t={current_time}s: {demand} m³/s ---")
            self.bus.publish(self.demand_topic, {'value': demand})

def run_pump_station_simulation():
    """
    Sets up and runs the pump station simulation following CHS-SDK standards.
    
    Adheres to three principles:
    1. No magic numbers, hardcoding, or implicit defaults
    2. Physical model rationality
    3. Generic solutions rather than case-specific implementations
    """
    print("--- Setting up Pump Station Control Simulation ---")

    # 1. --- Simulation Configuration (遵循标准参数命名) ---
    simulation_config = {
        'start_time': SimulationConfig.START_TIME,
        'end_time': SimulationConfig.END_TIME, 
        'time_step': SimulationConfig.TIME_STEP
    }
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. --- Communication Topics (避免硬编码字符串) ---
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"

    # 3. --- Physical Components with Proper Parameters ---
    # 源水库 - 具有完整的物理参数
    source_reservoir = Reservoir(
        name="source_reservoir",
        initial_state={
            'volume': PhysicalConstants.SOURCE_VOLUME,
            'water_level': PhysicalConstants.SOURCE_WATER_LEVEL
        },
        parameters={
            'surface_area': PhysicalConstants.SOURCE_SURFACE_AREA,
            'storage_curve': [
                [0, 0], 
                [PhysicalConstants.SOURCE_VOLUME * 2, PhysicalConstants.SOURCE_WATER_LEVEL * 2]
            ]
        },
        message_bus=message_bus
    )
    
    # 下游水库 - 具有完整的物理参数
    downstream_reservoir = Reservoir(
        name="downstream_reservoir", 
        initial_state={
            'volume': PhysicalConstants.DOWNSTREAM_VOLUME,
            'water_level': PhysicalConstants.DOWNSTREAM_WATER_LEVEL
        },
        parameters={
            'surface_area': PhysicalConstants.DOWNSTREAM_SURFACE_AREA,
            'storage_curve': [
                [0, 0], 
                [PhysicalConstants.DOWNSTREAM_VOLUME * 2, PhysicalConstants.DOWNSTREAM_WATER_LEVEL * 2]
            ]
        },
        message_bus=message_bus
    )
    
    # 连接管道 - 提供物理连接和边界条件
    inlet_pipe = Pipe(
        name="inlet_pipe",
        initial_state={'flow': 0.0},
        parameters={
            'length': PhysicalConstants.PIPE_LENGTH,
            'diameter': PhysicalConstants.PIPE_DIAMETER,
            'friction_factor': PhysicalConstants.PIPE_FRICTION_FACTOR
        }
    )
    
    outlet_pipe = Pipe(
        name="outlet_pipe", 
        initial_state={'flow': 0.0},
        parameters={
            'length': PhysicalConstants.PIPE_LENGTH,
            'diameter': PhysicalConstants.PIPE_DIAMETER, 
            'friction_factor': PhysicalConstants.PIPE_FRICTION_FACTOR
        }
    )

    # 创建标准化的泵组 - 避免硬编码数量
    pump_params = {
        'max_flow_rate': PhysicalConstants.PUMP_MAX_FLOW_RATE,
        'max_head': PhysicalConstants.PUMP_MAX_HEAD,
        'power_consumption_kw': PhysicalConstants.PUMP_POWER_CONSUMPTION,
        'efficiency': 0.8
    }
    
    pumps = []
    for i in range(PhysicalConstants.NUM_PUMPS):
        pump = Pump(
            name=f"pump_{i+1}",
            initial_state={'status': 0, 'outflow': 0.0},
            parameters=pump_params,
            message_bus=message_bus,
            action_topic=f"{CONTROL_TOPIC_PREFIX}.pump_{i+1}",
            default_upstream_level=PhysicalConstants.SOURCE_WATER_LEVEL,
            default_downstream_level=PhysicalConstants.DOWNSTREAM_WATER_LEVEL
        )
        pumps.append(pump)
    
    pump_station = PumpStation(
        name="pump_station",
        initial_state={},
        parameters={},
        pumps=pumps
    )

    # 建立物理拓扑连接
    harness.add_component("source_reservoir", source_reservoir)
    harness.add_component("inlet_pipe", inlet_pipe)
    harness.add_component("pump_station", pump_station)
    harness.add_component("outlet_pipe", outlet_pipe)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    
    # 拓扑连接: 源水库 -> 进水管 -> 泵站 -> 出水管 -> 下游水库
    harness.add_connection("source_reservoir", "inlet_pipe")
    harness.add_connection("inlet_pipe", "pump_station")
    harness.add_connection("pump_station", "outlet_pipe")
    harness.add_connection("outlet_pipe", "downstream_reservoir")

    # 4. --- Agent Setup (使用标准接口) ---
    # 可配置的需求代理
    demand_agent = ConfigurableDemandAgent(
        agent_id="demand_agent",
        message_bus=message_bus,
        demand_topic=DEMAND_TOPIC
    )

    # 统一泵控制代理 - 使用标准接口
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX,
        time_step=simulation_config['time_step'],
        max_pumps=PhysicalConstants.NUM_PUMPS,
        min_pumps=0
    )

    harness.add_agent(demand_agent)
    harness.add_agent(pump_control_agent)

    # 5. --- Build and Run Simulation (使用标准MAS框架) ---
    harness.build()

    print("\n--- Running MAS Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # 6. --- Performance Analysis ---
    analyze_pump_station_performance(harness.history)
    
    return harness.history

def analyze_pump_station_performance(history: list) -> Dict[str, Any]:
    """
    分析泵站性能指标 - 遵循通用性原则
    
    Args:
        history: 仿真历史数据
        
    Returns:
        性能分析结果字典
    """
    if not history:
        print("Warning: No simulation history available for analysis")
        return {}
    
    print("\n--- Pump Station Performance Analysis ---")
    
    # 提取关键性能数据
    times = [h['time'] for h in history]
    station_states = [h.get('pump_station', {}) for h in history]
    
    # 计算性能指标
    total_flows = [s.get('total_outflow', 0) for s in station_states]
    active_pumps = [s.get('active_pumps', 0) for s in station_states]
    total_powers = [s.get('total_power_draw_kw', 0) for s in station_states]
    
    # 计算平均值和效率
    avg_flow = sum(total_flows) / len(total_flows) if total_flows else 0
    avg_power = sum(total_powers) / len(total_powers) if total_powers else 0
    max_active_pumps = max(active_pumps) if active_pumps else 0
    
    # 能效比 (功率/流量)
    efficiency_ratio = avg_power / avg_flow if avg_flow > 0 else float('inf')
    
    performance_results = {
        'simulation_duration': times[-1] if times else 0,
        'average_flow_rate': avg_flow,
        'average_power_consumption': avg_power,
        'max_active_pumps': max_active_pumps,
        'energy_efficiency_ratio': efficiency_ratio,
        'total_energy_consumed': avg_power * (times[-1] / 3600) if times else 0  # kWh
    }
    
    # 输出性能报告
    print(f"Simulation Duration: {performance_results['simulation_duration']:.1f}s")
    print(f"Average Flow Rate: {performance_results['average_flow_rate']:.2f} m³/s")
    print(f"Average Power Consumption: {performance_results['average_power_consumption']:.2f} kW")
    print(f"Maximum Active Pumps: {performance_results['max_active_pumps']}")
    print(f"Energy Efficiency Ratio: {performance_results['energy_efficiency_ratio']:.2f} kW/(m³/s)")
    print(f"Total Energy Consumed: {performance_results['total_energy_consumed']:.2f} kWh")
    
    # 性能评估
    if performance_results['average_flow_rate'] > 15.0 and performance_results['energy_efficiency_ratio'] < 5.0:
        print("\n✅ PERFORMANCE: Excellent - High flow rate with good efficiency")
    elif performance_results['average_flow_rate'] > 10.0:
        print("\n⚠️  PERFORMANCE: Good - Adequate flow rate")
    else:
        print("\n❌ PERFORMANCE: Poor - Low flow rate or poor efficiency")
    
    return performance_results

if __name__ == "__main__":
    run_pump_station_simulation()
