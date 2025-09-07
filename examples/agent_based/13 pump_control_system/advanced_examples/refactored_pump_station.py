#!/usr/bin/env python3
"""
Refactored pump station control simulation using SimulationBuilder.

This demonstrates how the SimulationBuilder class reduces boilerplate code
and makes simulation setup more concise and readable.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from core_lib.core_engine.testing.simulation_builder import create_pump_station_system
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent
from core_lib.core.interfaces import Agent

class DemandAgent(Agent):
    """A simple agent to simulate changing flow demand."""
    def __init__(self, agent_id, message_bus, demand_topic):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic

    def run(self, current_time):
        # Simulate a step change in demand
        if int(current_time) == 100:
            demand = 25.0
            print(f"--- DEMAND AGENT: New demand at t={current_time}s: {demand} m^3/s ---")
            self.bus.publish(self.demand_topic, {'value': demand})
        elif int(current_time) == 400:
            demand = 8.0
            print(f"--- DEMAND AGENT: New demand at t={current_time}s: {demand} m^3/s ---")
            self.bus.publish(self.demand_topic, {'value': demand})

def run_pump_station_simulation_refactored():
    """
    Refactored pump station simulation using SimulationBuilder.
    """
    print("--- Setting up Refactored Pump Station Control Simulation ---")

    # 1. Create simulation using builder pattern
    simulation_config = {'end_time': 600, 'dt': 1.0}
    builder = create_pump_station_system(simulation_config)
    
    # 2. Communication Topics
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"

    # 3. Add agents
    demand_agent = DemandAgent("demand_agent", builder.harness.message_bus, DEMAND_TOPIC)
    builder.add_agent(demand_agent)
    
    # Get the pump station component
    pump_station = builder.get_component("ps1")
    
    pump_control_agent = PumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=builder.harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX
    )

    # 4. Build and run simulation
    builder.build()
    
    print("\n--- Running Refactored Simulation ---")
    num_steps = int(simulation_config['end_time'] / simulation_config['dt'])
    
    for i in range(num_steps):
        current_time = i * simulation_config['dt']
        
        # Run agents
        demand_agent.run(current_time)
        pump_control_agent.execute_control_logic()
        
        # Step physical models
        builder.harness._step_physical_models(simulation_config['dt'])
        
        # Store history
        step_history = {'time': current_time}
        for cid in builder.harness.sorted_components:
            step_history[cid] = builder.harness.components[cid].get_state()
        builder.harness.history.append(step_history)
        
        # Print status every 100 steps
        if i % 100 == 0:
            station_state = pump_station.get_state()
            print(f"Time {current_time:.0f}s: Active Pumps={station_state['active_pumps']}, "
                  f"Total Outflow={station_state['total_outflow']:.2f} m^3/s")

    # Print final results
    print("\n--- Simulation Complete ---")
    builder.print_final_states()
    
    final_station_state = pump_station.get_state()
    print(f"\nFinal Pump Station Status:")
    print(f"  Active Pumps: {final_station_state['active_pumps']}")
    print(f"  Total Outflow: {final_station_state['total_outflow']:.2f} m^3/s")

if __name__ == "__main__":
    run_pump_station_simulation_refactored()