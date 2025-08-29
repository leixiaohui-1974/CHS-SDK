#!/usr/bin/env python3
"""
Example simulation script for Tutorial 3: A multi-agent, event-driven simulation.

This script demonstrates the multi-agent system (MAS) architecture. Components
are fully decoupled and communicate only via a MessageBus.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def run_mas_simulation():
    """
    Sets up and runs the multi-agent system simulation.
    """
    print("--- Setting up Tutorial 3: Event-Driven Agents Simulation ---")

    # 1. --- Simulation Harness and Message Bus Setup ---
    simulation_config = {'duration': 300, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. --- Communication Topics ---
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"

    # 3. --- Physical Components ---
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 21e6, 'water_level': 14.0},
        parameters={'surface_area': 1.5e6}
    )
    gate_params = {
        'max_rate_of_change': 0.1,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 1.0
    }
    # The Gate is made message-aware by passing the bus and an action topic
    gate = Gate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. --- Agent Components ---
    # Digital Twin Agent for the Reservoir
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # PID Controller (the "brain" of the control agent)
    pid_controller = PIDController(
        Kp=-0.5, Ki=-0.01, Kd=-0.1,
        setpoint=12.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )

    # Local Control Agent for the Gate
    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=harness.dt
    )

    # 5. --- Harness Final Setup ---
    harness.add_component(reservoir)
    harness.add_component(gate)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)
    harness.add_connection("reservoir_1", "gate_1")
    harness.build()

    # 6. --- Run Simulation ---
    print("\n--- Running MAS Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    # Note: In a real script, you would likely process or view the results.
    # For this example, we just confirm completion.
    # The data is in harness.history.
    print(f"Final reservoir water level: {harness.history[-1]['reservoir_1']['water_level']:.2f} m")


if __name__ == "__main__":
    run_mas_simulation()
