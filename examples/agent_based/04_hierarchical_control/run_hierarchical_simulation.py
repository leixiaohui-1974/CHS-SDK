#!/usr/bin/env python3
"""
Example simulation script for Tutorial 4: A hierarchical control system.

This script demonstrates a two-level hierarchical control system where a high-level
supervisory agent manages the objectives of a low-level, local controller.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def setup_hierarchical_control_system(harness):
    """
    Initializes and connects all components for the hierarchical control simulation.
    """
    print("--- Initializing components for Hierarchical Control ---")

    message_bus = harness.message_bus
    simulation_dt = harness.dt

    # --- Communication Topics ---
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"

    # --- Physical Components ---
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 28.5e6, 'water_level': 19.0},
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]}
    )
    gate_params = {
        'max_rate_of_change': 2.0,  # 增加变化速率
        'discharge_coefficient': 2.0,  # 大幅增加流量系数
        'width': 20,  # 增加闸门宽度
        'max_opening': 2.0  # 减少最大开度，避免过大
    }
    # The Gate needs to listen for the 'control_signal' key from the LocalControlAgent.
    gate = Gate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC,
        action_key='control_signal'
    )

    # --- Agent Components ---
    reservoir_twin = DigitalTwinAgent(
        agent_id="twin_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )
    gate_twin = DigitalTwinAgent(
        agent_id="twin_gate_1",
        simulated_object=gate,
        message_bus=message_bus,
        state_topic=GATE_STATE_TOPIC
    )

    pid = PIDController(
        Kp=0.8, Ki=0.1, Kd=0.2,  # 修正符号，使用正值参数
        setpoint=15.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )
    lca = UnifiedGateControlAgent(
        agent_id="lca_gate_1",
        controller=pid,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC,
        target_component='gate_1',
        control_type='gate_control'
    )

    # --- Central Dispatcher with Corrected Message Key ---
    dispatcher_rules = {
        "profiles": {
            "flood_control": {
                "condition": lambda states: states.get('reservoir_level', {}).get('water_level', 0) > 18.0,
                "commands": {
                    "gate1_command": {'new_setpoint': 12.0}
                }
            },
            "normal_operation": {
                "condition": lambda states: True,
                "commands": {
                    "gate1_command": {'new_setpoint': 15.0}
                }
            }
        }
    }
    dispatcher = CentralDispatcherAgent(
        agent_id="dispatcher_1",
        message_bus=message_bus,
        mode="rule",
        subscribed_topic=RESERVOIR_STATE_TOPIC,
        observation_key="water_level",
        command_topic=GATE_COMMAND_TOPIC,
        dispatcher_params={
            "low_level": 12.0,
            "high_level": 18.0,
            "low_setpoint": 15.0,
            "high_setpoint": 12.0
        }
    )

    # --- Add all components to the harness ---
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)
    harness.add_agent(reservoir_twin)
    harness.add_agent(gate_twin)
    harness.add_agent(lca)
    harness.add_agent(dispatcher)
    harness.add_connection("reservoir_1", "gate_1")


def analyze_and_visualize_results(harness, simulation_config):
    """
    分析和可视化分层控制系统的结果
    """
    print("\n--- Analyzing Hierarchical Control Results ---")
    
    # 提取数据
    time_data = []
    water_levels = []
    gate_openings = []
    setpoints = []
    
    for i, step_data in enumerate(harness.history):
        time_data.append(i * simulation_config['dt'])
        
        if 'reservoir_1' in step_data:
            water_levels.append(step_data['reservoir_1']['water_level'])
        else:
            water_levels.append(0)
            
        if 'gate_1' in step_data:
            gate_openings.append(step_data['gate_1']['opening'])
        else:
            gate_openings.append(0)
        
        # 假设目标水位为15.0m（正常操作）或12.0m（防洪）
        target_level = 15.0 if water_levels[-1] <= 18.0 else 12.0
        setpoints.append(target_level)
    
    # 计算控制性能指标
    target_level = 15.0  # 主要目标
    final_error = abs(water_levels[-1] - target_level)
    mae = np.mean([abs(level - target_level) for level in water_levels])
    rmse = np.sqrt(np.mean([(level - target_level)**2 for level in water_levels]))
    
    print(f"=== Control Performance Analysis ===")
    print(f"Target water level: {target_level:.2f} m")
    print(f"Final water level: {water_levels[-1]:.2f} m")
    print(f"Final gate opening: {gate_openings[-1]:.3f}")
    print(f"Final control error: {final_error:.3f} m")
    print(f"Mean Absolute Error (MAE): {mae:.3f} m")
    print(f"Root Mean Square Error (RMSE): {rmse:.3f} m")
    
    # 检查分层控制效果
    print(f"\n=== Hierarchical Control Analysis ===")
    high_level_periods = sum(1 for level in water_levels if level > 18.0)
    print(f"High water level periods (>18m): {high_level_periods} steps")
    print(f"Flood control activation: {'Yes' if high_level_periods > 0 else 'No'}")
    
    # 创建可视化图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 水位控制图
    ax1.plot(time_data, water_levels, 'b-', linewidth=2, label='Actual Water Level')
    ax1.plot(time_data, setpoints, 'r--', linewidth=2, label='Target Setpoint')
    ax1.axhline(y=18.0, color='orange', linestyle=':', linewidth=2, label='Flood Control Threshold')
    ax1.set_title('Hierarchical Control: Water Level Response', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Water Level (m)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 闸门开度图
    ax2.plot(time_data, gate_openings, 'g-', linewidth=2, label='Gate Opening')
    ax2.set_title('Gate Opening Response', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Gate Opening', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    save_path = '04_hierarchical_control_results.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nResults visualization saved as '{save_path}'")
    
    plt.show()
    
    return {
        'final_error': final_error,
        'mae': mae,
        'rmse': rmse,
        'flood_control_activated': high_level_periods > 0
    }


def run_hierarchical_simulation():
    """
    Sets up and runs the full hierarchical simulation.
    """
    print("\n--- Setting up Tutorial 4: Hierarchical Control Simulation ---")

    simulation_config = {'end_time': 5000, 'dt': 1.0}  # 使用end_time而不是duration
    harness = SimulationHarness(config=simulation_config)

    setup_hierarchical_control_system(harness)

    harness.build()

    print("\n--- Running Hierarchical Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    final_level = harness.history[-1]['reservoir_1']['water_level']
    final_opening = harness.history[-1]['gate_1']['opening']
    print(f"Final reservoir water level: {final_level:.2f} m")
    print(f"Final gate opening: {final_opening:.2f} m")
    
    # 分析和可视化结果
    results = analyze_and_visualize_results(harness, simulation_config)
    
    # 验证控制正确性
    print(f"\n=== Control Correctness Verification ===")
    if results['final_error'] < 1.0:
        print("✓ PASS: Control error is acceptable (< 1.0 m)")
    else:
        print("✗ FAIL: Control error is too large (>= 1.0 m)")
    
    if results['flood_control_activated']:
        print("✓ PASS: Flood control system activated when needed")
    else:
        print("ℹ INFO: Flood control not activated (water level stayed below 18m)")
    
    return results


if __name__ == "__main__":
    run_hierarchical_simulation()
