#!/usr/bin/env python3
"""
Pump station control simulation using SimulationBuilder and common agents.

This demonstrates how the combination of SimulationBuilder and common agent classes
further reduces boilerplate code and provides a more maintainable solution.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from core_lib.core_engine.testing.simulation_builder import create_pump_station_system
from core_lib.core_engine.testing.common_agents import DemandAgent, MonitoringAgent
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent

def run_pump_station_with_common_agents():
    """
    Pump station simulation using SimulationBuilder and common agent classes.
    """
    print("--- Setting up Pump Station with Common Agents ---")

    # 1. Create simulation using builder pattern
    simulation_config = {'end_time': 600, 'dt': 1.0}
    builder = create_pump_station_system(simulation_config)
    
    # 2. Communication Topics
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"

    # 3. Create demand schedule
    demand_schedule = {
        100.0: 25.0,  # Increase demand at t=100s
        400.0: 8.0    # Decrease demand at t=400s
    }
    
    # 4. Add agents using common agent classes
    demand_agent = DemandAgent(
        agent_id="demand_agent",
        message_bus=builder.harness.message_bus,
        demand_topic=DEMAND_TOPIC,
        demand_schedule=demand_schedule
    )
    builder.add_agent(demand_agent)
    
    # Add monitoring agent to track system performance
    monitoring_agent = MonitoringAgent(
        agent_id="monitor_agent",
        components={
            "source_res": builder.get_component("source_res"),
            "downstream_res": builder.get_component("downstream_res"),
            "ps1": builder.get_component("ps1")
        },
        monitoring_interval=50.0  # Monitor every 50 seconds
    )
    builder.add_agent(monitoring_agent)
    
    # Get the pump station component
    pump_station = builder.get_component("ps1")
    
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=builder.harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX,
        dt=simulation_config['dt']
    )

    # 5. Build and run simulation
    builder.build()
    
    print("\n--- Running Simulation with Common Agents ---")
    num_steps = int(simulation_config['end_time'] / simulation_config['dt'])
    
    for i in range(num_steps):
        current_time = i * simulation_config['dt']
        
        # Run all agents (including monitoring)
        for agent in builder.agents:
            agent.run(current_time)
        
        # UnifiedPumpControlAgent handles control logic automatically via message bus
        
        # Step physical models
        builder.harness._step_physical_models(simulation_config['dt'])
        
        # Store history
        step_history = {'time': current_time}
        for cid in builder.harness.sorted_components:
            step_history[cid] = builder.harness.components[cid].get_state()
        builder.harness.history.append(step_history)

    # Print final results
    print("\n--- Simulation Complete ---")
    builder.print_final_states()
    
    # Show monitoring data summary
    monitoring_data = monitoring_agent.get_monitoring_data()
    print(f"\nMonitoring Summary:")
    print(f"  Total monitoring entries: {len(monitoring_data)}")
    
    if monitoring_data:
        first_entry = monitoring_data[0]
        last_entry = monitoring_data[-1]
        
        print(f"  Initial pump station state: {first_entry.get('ps1', {})}")
        print(f"  Final pump station state: {last_entry.get('ps1', {})}")
        
        # Calculate average power consumption
        total_power = sum(entry.get('ps1', {}).get('total_power_draw_kw', 0) 
                         for entry in monitoring_data)
        avg_power = total_power / len(monitoring_data) if monitoring_data else 0
        print(f"  Average power consumption: {avg_power:.2f} kW")
    
    final_station_state = pump_station.get_state()
    print(f"\nFinal Pump Station Status:")
    print(f"  Active Pumps: {final_station_state['active_pumps']}")
    print(f"  Total Outflow: {final_station_state['total_outflow']:.2f} m^3/s")
    print(f"  Power Draw: {final_station_state['total_power_draw_kw']:.2f} kW")

if __name__ == "__main__":
    run_pump_station_with_common_agents()