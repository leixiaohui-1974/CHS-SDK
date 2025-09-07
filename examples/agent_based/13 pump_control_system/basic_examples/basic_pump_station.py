#!/usr/bin/env python3
"""
Example simulation script for a pump station with multiple pumps.

This script demonstrates how a PumpControlAgent can manage multiple pump units
to meet a fluctuating flow demand.
"""

import sys
import os
import math

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
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

def run_pump_station_simulation():
    """
    Sets up and runs the pump station simulation.
    """
    print("--- Setting up Pump Station Control Simulation ---")

    # 1. --- Simulation Harness and Message Bus ---
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. --- Communication Topics ---
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"

    # 3. --- Physical Components ---
    source_reservoir = Reservoir("source_res", {'water_level': 10.0}, {'surface_area': 1.0e6})
    downstream_reservoir = Reservoir("downstream_res", {'water_level': 25.0}, {'surface_area': 1.0e6})

    # Create three identical pumps
    pump_params = {'max_flow_rate': 10.0, 'max_head': 20.0, 'power_consumption_kw': 50}
    pumps = [
        Pump(f"p{i}", {}, pump_params, message_bus, f"{CONTROL_TOPIC_PREFIX}.p{i}")
        for i in range(1, 4)
    ]
    pump_station = PumpStation("ps1", {}, {}, pumps)

    harness.add_component("source_res", source_reservoir)
    harness.add_component("downstream_res", downstream_reservoir)
    harness.add_component("ps1", pump_station)
    # The PumpStation itself is a conceptual wrapper, the physical connection is from source to the pumps' manifold,
    # and from there to the downstream reservoir. This is simplified in the harness.
    harness.add_connection("source_res", "ps1")
    harness.add_connection("ps1", "downstream_res")

    # 4. --- Agent Setup ---
    demand_agent = DemandAgent("demand_agent", message_bus, DEMAND_TOPIC)

    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX,
        dt=simulation_config['dt']
    )

    harness.add_agent(demand_agent)
    # The PumpControlAgent's logic is called manually in the loop, so it's not added to the harness agents list.

    # 5. --- Build and Run Simulation ---
    harness.build()

    print("\n--- Running Simulation ---")
    num_steps = int(simulation_config['end_time'] / simulation_config['dt'])
    for i in range(num_steps):
        current_time = i * simulation_config['dt']
        print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

        # Agents run first
        demand_agent.run(current_time)
        # UnifiedPumpControlAgent handles control logic automatically via message bus

        # Then physical models are stepped
        harness._step_physical_models(simulation_config['dt'])

        # Store and print history
        step_history = {'time': current_time}
        for cid in harness.sorted_components:
            step_history[cid] = harness.components[cid].get_state()
        harness.history.append(step_history)

        print("  State Update:")
        station_state = harness.components['ps1'].get_state()
        print(f"    Pump Station: Active Pumps={station_state['active_pumps']}, Total Outflow={station_state['total_outflow']:.2f} m^3/s")

    print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    run_pump_station_simulation()
