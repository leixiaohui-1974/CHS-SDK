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
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]}
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
        message_bus=message_bus,
        dt=harness.dt,
        target_component="gate_1",
        control_type="gate_control",
        data_sources={"primary_data": RESERVOIR_STATE_TOPIC},
        control_targets={"primary_target": GATE_ACTION_TOPIC},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC
    )

    # 5. --- Harness Final Setup ---
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)
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

    # --- Evaluate Control Performance ---
    print("\n--- Control Performance Evaluation ---")
    
    # Extract water level data from history
    target_level = 12.0  # Target water level from PID controller
    water_levels = []
    
    for step in harness.history:
        if 'reservoir_1' in step and 'water_level' in step['reservoir_1']:
            water_levels.append(step['reservoir_1']['water_level'])
    
    # Calculate evaluation metrics
    # 1. Final Control Error (FCE)
    final_error = abs(water_levels[-1] - target_level)
    
    # 2. Mean Absolute Error (MAE)
    absolute_errors = [abs(level - target_level) for level in water_levels]
    mae = sum(absolute_errors) / len(absolute_errors) if absolute_errors else 0
    
    # 3. Root Mean Square Error (RMSE)
    squared_errors = [(level - target_level) ** 2 for level in water_levels]
    rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5 if squared_errors else 0
    
    # 4. Overshoot
    overshoots = [level - target_level for level in water_levels if level > target_level]
    max_overshoot = max(overshoots) if overshoots else 0
    percent_overshoot = (max_overshoot / target_level) * 100 if target_level > 0 else 0
    
    # Print evaluation results
    print(f"Target water level: {target_level:.2f} m")
    print(f"1. Final Control Error (FCE): {final_error:.4f} m")
    print(f"2. Mean Absolute Error (MAE): {mae:.4f} m")
    print(f"3. Root Mean Square Error (RMSE): {rmse:.4f} m")
    print(f"4. Max Overshoot: {max_overshoot:.4f} m ({percent_overshoot:.2f}%)")
    
    # Additional stability analysis
    # Check if system is stable (water level within 0.1m of target for last 10% of simulation)
    stable_threshold = 0.1  # m
    stability_check_window = int(len(water_levels) * 0.1)
    if stability_check_window > 0:
        recent_errors = [abs(level - target_level) for level in water_levels[-stability_check_window:]]
        is_stable = all(error <= stable_threshold for error in recent_errors)
        print(f"Stability: {'Stable' if is_stable else 'Not Stable'} (within {stable_threshold}m for last {stability_check_window} steps)")


if __name__ == "__main__":
    run_mas_simulation()
