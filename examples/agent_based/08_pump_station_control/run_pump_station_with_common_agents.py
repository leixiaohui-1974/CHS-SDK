#!/usr/bin/env python3
"""
Pump station control simulation using SimulationBuilder and common agents.

This demonstrates how the combination of SimulationBuilder and common agent classes
further reduces boilerplate code and provides a maintainable solution following CHS-SDK standards.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from core_lib.core_engine.testing.simulation_builder import create_pump_station_system
from core_lib.core_engine.testing.common_agents import DemandAgent, MonitoringAgent
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent

# 仿真配置常量 - 遵循禁止魔数规范
class SimulationConfig:
    """仿真配置常量类 - 遵循禁止魔数规范"""
    START_TIME = 0.0
    END_TIME = 600.0
    TIME_STEP = 1.0
    
    # 需求调度配置
    DEMAND_CHANGE_TIME_1 = 100.0  # 第一次需求变化时间
    DEMAND_CHANGE_TIME_2 = 400.0  # 第二次需求变化时间
    HIGH_DEMAND = 25.0            # 高需求
    LOW_DEMAND = 8.0              # 低需求

# 监控配置常量
class MonitoringConfig:
    """监控配置常量类"""
    MONITORING_INTERVAL = 50.0    # 监控间隔 (秒)
    LOG_INTERVAL = 10.0           # 日志间隔 (秒)
    
# 控制配置常量
class ControlConfig:
    """控制配置常量类"""
    MIN_PUMPS = 0                 # 最少泵数量
    MAX_PUMPS = 3                 # 最大泵数量
    PUMP_STARTUP_DELAY = 0        # 泵启动延迟

def run_pump_station_with_common_agents():
    """
    Pump station simulation using SimulationBuilder and common agent classes.
    
    Adheres to three principles:
    1. No magic numbers, hardcoding, or implicit defaults
    2. Physical model rationality
    3. Generic solutions rather than case-specific implementations
    """
    print("--- Setting up Pump Station with Common Agents ---")

    # 1. Create simulation using builder pattern with proper configuration
    simulation_config = {
        'start_time': SimulationConfig.START_TIME,
        'end_time': SimulationConfig.END_TIME,
        'time_step': SimulationConfig.TIME_STEP
    }
    builder = create_pump_station_system(simulation_config)
    
    # 2. Communication Topics - avoid hardcoded strings
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"

    # 3. Create configurable demand schedule - no hardcoded values
    demand_schedule = {
        SimulationConfig.DEMAND_CHANGE_TIME_1: SimulationConfig.HIGH_DEMAND,
        SimulationConfig.DEMAND_CHANGE_TIME_2: SimulationConfig.LOW_DEMAND
    }
    
    # 4. Add agents using common agent classes with proper configuration
    demand_agent = DemandAgent(
        agent_id="demand_agent",
        message_bus=builder.harness.message_bus,
        demand_topic=DEMAND_TOPIC,
        demand_schedule=demand_schedule
    )
    builder.add_agent(demand_agent)
    
    # Add monitoring agent to track system performance with proper configuration
    monitoring_agent = MonitoringAgent(
        agent_id="monitor_agent",
        components={
            "source_res": builder.get_component("source_res"),
            "downstream_res": builder.get_component("downstream_res"),
            "ps1": builder.get_component("ps1")
        },
        monitoring_interval=MonitoringConfig.MONITORING_INTERVAL
    )
    builder.add_agent(monitoring_agent)
    
    # Get the pump station component safely
    pump_station = builder.get_component("ps1")
    if pump_station is None:
        raise ValueError("Failed to create pump station component")
    
    # Create unified pump control agent with proper configuration
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_control_agent",
        message_bus=builder.harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX,
        time_step=simulation_config['time_step'],
        max_pumps=ControlConfig.MAX_PUMPS,
        min_pumps=ControlConfig.MIN_PUMPS,
        pump_startup_delay=ControlConfig.PUMP_STARTUP_DELAY
    )
    builder.add_agent(pump_control_agent)

    # 5. Build and run simulation using standard MAS framework
    builder.build()
    
    print("\n--- Running MAS Simulation with Common Agents ---")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # 6. Performance analysis with proper validation
    analyze_system_performance(builder, pump_station, monitoring_agent)
    
    return builder.get_history()

def analyze_system_performance(builder, pump_station, monitoring_agent) -> Dict[str, Any]:
    """
    分析系统性能 - 遵循通用性原则
    
    Args:
        builder: 仿真构建器
        pump_station: 泵站组件
        monitoring_agent: 监控代理
        
    Returns:
        性能分析结果字典
    """
    print("\n--- System Performance Analysis ---")
    
    # Print final states using builder method
    builder.print_final_states()
    
    # Show monitoring data summary
    monitoring_data = monitoring_agent.get_monitoring_data()
    print(f"\nMonitoring Summary:")
    print(f"  Total monitoring entries: {len(monitoring_data)}")
    
    performance_results = {}
    
    if monitoring_data:
        first_entry = monitoring_data[0]
        last_entry = monitoring_data[-1]
        
        print(f"  Initial pump station state: {first_entry.get('ps1', {})}")
        print(f"  Final pump station state: {last_entry.get('ps1', {})}")
        
        # Calculate performance metrics
        total_power = sum(entry.get('ps1', {}).get('total_power_draw_kw', 0) 
                         for entry in monitoring_data)
        avg_power = total_power / len(monitoring_data) if monitoring_data else 0
        
        total_flow = sum(entry.get('ps1', {}).get('total_outflow', 0) 
                        for entry in monitoring_data)
        avg_flow = total_flow / len(monitoring_data) if monitoring_data else 0
        
        # Energy efficiency ratio
        efficiency_ratio = avg_power / avg_flow if avg_flow > 0 else float('inf')
        
        performance_results = {
            'average_flow_rate': avg_flow,
            'average_power_consumption': avg_power,
            'energy_efficiency_ratio': efficiency_ratio,
            'monitoring_entries': len(monitoring_data)
        }
        
        print(f"  Average power consumption: {avg_power:.2f} kW")
        print(f"  Average flow rate: {avg_flow:.2f} m³/s")
        print(f"  Energy efficiency ratio: {efficiency_ratio:.2f} kW/(m³/s)")
        
        # Performance evaluation using standard criteria
        if avg_flow > 15.0 and efficiency_ratio < 5.0:
            print("\n✅ SYSTEM PERFORMANCE: Excellent - High flow rate with good efficiency")
        elif avg_flow > 10.0:
            print("\n⚠️ SYSTEM PERFORMANCE: Good - Adequate flow rate")
        else:
            print("\n❌ SYSTEM PERFORMANCE: Poor - Low flow rate or poor efficiency")
    
    # Final pump station status
    final_station_state = pump_station.get_state()
    print(f"\nFinal Pump Station Status:")
    print(f"  Active Pumps: {final_station_state['active_pumps']}")
    print(f"  Total Outflow: {final_station_state['total_outflow']:.2f} m³/s")
    print(f"  Power Draw: {final_station_state['total_power_draw_kw']:.2f} kW")
    
    return performance_results

if __name__ == "__main__":
    run_pump_station_with_common_agents()