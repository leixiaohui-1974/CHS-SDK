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
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def run_mas_simulation():
    """
    Sets up and runs the multi-agent system simulation.
    """
    print("--- Setting up Tutorial 3: Event-Driven Agents Simulation ---")

    # 1. --- Simulation Harness and Message Bus Setup ---
    # 调整仿真时长为60000秒以给系统足够时间达到稳定状态
    # 使用较小的时间步长0.5秒提高控制精度
    simulation_config = {'end_time': 60000, 'dt': 0.5}  # 使用end_time而不是duration
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
        'max_rate_of_change': 0.5,  # 增加闸门最大变化速率，提高控制响应速度
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
    # 对于水库水位控制，PID输出应该直接对应闸门开度
    # 当水位高于目标时，需要增加闸门开度来排水
    # 当水位低于目标时，需要减少闸门开度来蓄水
    pid_controller = PIDController(
        Kp=5.0, Ki=0.5, Kd=0.0,  # 调整参数，避免过大的输出
        setpoint=12.0,
        min_output=0.0,  # 闸门开度不能为负
        max_output=gate_params['max_opening']
    )

    # Unified Gate Control Agent for the Gate
    control_agent = UnifiedGateControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=harness.dt,
        target_component="gate_1",
        control_type="gate_control"
    )
    
    # 启用控制日志记录，帮助观察控制效果
    control_agent.enable_control_logging(enabled=True, state_topic="control.state.debug", interval=5)

    # 5. --- Harness Final Setup ---
    print(f"\n--- Simulation Configuration Summary ---")
    print(f"- Reservoir initial level: {reservoir._state['water_level']:.2f} m")
    print(f"- Target water level: {pid_controller.setpoint:.2f} m")
    print(f"- Gate initial opening: {gate._state['opening']:.2f}")
    print(f"- Simulation duration: {simulation_config['end_time']} s")
    print(f"- Time step: {simulation_config['dt']} s")
    print(f"---------------------------------------")
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
    
    # Extract water level and gate opening data from history
    target_level = 12.0  # Target water level from PID controller
    water_levels = []
    gate_openings = []
    
    for step in harness.history:
        if 'reservoir_1' in step and 'water_level' in step['reservoir_1']:
            water_levels.append(step['reservoir_1']['water_level'])
        if 'gate_1' in step and 'opening' in step['gate_1']:
            gate_openings.append(step['gate_1']['opening'])
    
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
    
    # 5. Stability analysis
    # Check if system is stable (water level within 0.1m of target for last 10% of simulation)
    stable_threshold = 0.1  # m
    stability_check_window = int(len(water_levels) * 0.1)
    
    # 6. Settling time - time to reach within 5% of target and stay there
    settling_time = None
    settling_threshold = 0.05 * target_level  # 5% of target
    consecutive_stable_steps = 0
    required_consecutive_steps = 10  # Need 10 consecutive steps within threshold to consider settled
    
    for i, level in enumerate(water_levels):
        if abs(level - target_level) <= settling_threshold:
            consecutive_stable_steps += 1
        else:
            consecutive_stable_steps = 0
        
        if consecutive_stable_steps == required_consecutive_steps:
            settling_time = (i - required_consecutive_steps + 1) * simulation_config['dt']
            break
    
    # 7. Control signal statistics
    if gate_openings:
        avg_opening = sum(gate_openings) / len(gate_openings)
        max_opening = max(gate_openings)
        min_opening = min(gate_openings)
        # Calculate control signal changes (absolute differences between consecutive steps)
        if len(gate_openings) > 1:
            control_changes = [abs(gate_openings[i] - gate_openings[i-1]) for i in range(1, len(gate_openings))]
            avg_change = sum(control_changes) / len(control_changes) if control_changes else 0
        else:
            avg_change = 0
    else:
        avg_opening = max_opening = min_opening = avg_change = 0
    
    # Print evaluation results
    print(f"Target water level: {target_level:.2f} m")
    print(f"1. Final Control Error (FCE): {final_error:.4f} m")
    print(f"2. Mean Absolute Error (MAE): {mae:.4f} m")
    print(f"3. Root Mean Square Error (RMSE): {rmse:.4f} m")
    print(f"4. Max Overshoot: {max_overshoot:.4f} m ({percent_overshoot:.2f}%)")
    print(f"5. Settling Time: {settling_time:.1f} s" if settling_time is not None else "5. System did not settle within simulation time")
    print(f"6. Gate Opening Stats - Avg: {avg_opening:.3f}, Max: {max_opening:.3f}, Min: {min_opening:.3f}, Avg Change: {avg_change:.4f}")
    
    # Advanced stability analysis
    # Calculate variance of water levels in the second half of the simulation
    if len(water_levels) > 1:
        second_half_levels = water_levels[len(water_levels)//2:]
        level_variance = sum((l - target_level)**2 for l in second_half_levels) / len(second_half_levels)
        print(f"7. Level Variance (second half): {level_variance:.6f}")
        
        # Determine if system is stable in the last 10% of simulation
        if stability_check_window > 0:
            last_10_percent = water_levels[-stability_check_window:]
            is_stable = all(abs(l - target_level) <= stable_threshold for l in last_10_percent)
            print(f"8. System Stable in Last 10%: {is_stable}")
    if stability_check_window > 0:
        recent_errors = [abs(level - target_level) for level in water_levels[-stability_check_window:]]
        is_stable = all(error <= stable_threshold for error in recent_errors)
        print(f"Stability: {'Stable' if is_stable else 'Not Stable'} (within {stable_threshold}m for last {stability_check_window} steps)")


if __name__ == "__main__":
    run_mas_simulation()
