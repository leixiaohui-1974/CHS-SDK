#!/usr/bin/env python3
"""
Refactored Example: Complex Branched Network using SimulationBuilder.

This script demonstrates how to use SimulationBuilder to simplify the setup
of a complex, branched network topology.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent

def analyze_and_visualize_results(builder, config):
    """
    分析和可视化复杂网络控制系统的结果
    """
    print("\n--- Analyzing Complex Network Control Results (Refactored) ---")
    
    # 获取历史数据
    history = builder.get_history()
    if not history:
        print("No simulation history available")
        return None
    
    # 提取数据
    time_data = []
    res1_levels = []
    res2_levels = []
    g1_openings = []
    g2_openings = []
    
    for i, step_data in enumerate(history):
        time_data.append(i * config['dt'])
        
        if 'res1' in step_data:
            res1_levels.append(step_data['res1']['water_level'])
        else:
            res1_levels.append(0)
            
        if 'res2' in step_data:
            res2_levels.append(step_data['res2']['water_level'])
        else:
            res2_levels.append(0)
            
        if 'g1' in step_data:
            g1_openings.append(step_data['g1']['opening'])
        else:
            g1_openings.append(0)
            
        if 'g2' in step_data:
            g2_openings.append(step_data['g2']['opening'])
        else:
            g2_openings.append(0)
    
    # 计算控制性能指标
    target_res1 = 12.0
    target_res2 = 18.0
    
    final_error_res1 = abs(res1_levels[-1] - target_res1)
    final_error_res2 = abs(res2_levels[-1] - target_res2)
    
    mae_res1 = np.mean([abs(level - target_res1) for level in res1_levels])
    mae_res2 = np.mean([abs(level - target_res2) for level in res2_levels])
    
    print(f"=== Control Performance Analysis ===")
    print(f"Reservoir 1 - Target: {target_res1:.1f}m, Final: {res1_levels[-1]:.2f}m, Error: {final_error_res1:.3f}m, MAE: {mae_res1:.3f}m")
    print(f"Reservoir 2 - Target: {target_res2:.1f}m, Final: {res2_levels[-1]:.2f}m, Error: {final_error_res2:.3f}m, MAE: {mae_res2:.3f}m")
    
    # 创建可视化图表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 水库水位控制图
    ax1.plot(time_data, res1_levels, 'b-', linewidth=2, label='Reservoir 1 Level')
    ax1.plot(time_data, res2_levels, 'r-', linewidth=2, label='Reservoir 2 Level')
    ax1.axhline(y=target_res1, color='blue', linestyle='--', linewidth=2, label='Res1 Target')
    ax1.axhline(y=target_res2, color='red', linestyle='--', linewidth=2, label='Res2 Target')
    ax1.set_title('Reservoir Water Level Control (Refactored)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Water Level (m)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 闸门开度图
    ax2.plot(time_data, g1_openings, 'g-', linewidth=2, label='Gate 1 Opening')
    ax2.plot(time_data, g2_openings, 'orange', linewidth=2, label='Gate 2 Opening')
    ax2.set_title('Gate Opening Response', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Gate Opening', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 控制误差图
    errors_res1 = [abs(level - target_res1) for level in res1_levels]
    errors_res2 = [abs(level - target_res2) for level in res2_levels]
    ax3.plot(time_data, errors_res1, 'b-', linewidth=2, label='Res1 Error')
    ax3.plot(time_data, errors_res2, 'r-', linewidth=2, label='Res2 Error')
    ax3.axhline(y=1.0, color='orange', linestyle='--', linewidth=2, label='Acceptable Error')
    ax3.set_title('Control Error Over Time', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (s)', fontsize=12)
    ax3.set_ylabel('Absolute Error (m)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 控制性能总结
    ax4.text(0.05, 0.95, f'Reservoir 1 Control:', transform=ax4.transAxes, fontsize=12, fontweight='bold')
    ax4.text(0.05, 0.85, f'  Final Error: {final_error_res1:.3f} m', transform=ax4.transAxes, fontsize=11)
    ax4.text(0.05, 0.75, f'  MAE: {mae_res1:.3f} m', transform=ax4.transAxes, fontsize=11)
    ax4.text(0.05, 0.65, f'  Status: {"✓ Good" if final_error_res1 < 1.0 else "✗ Poor"}', transform=ax4.transAxes, fontsize=11)
    
    ax4.text(0.05, 0.45, f'Reservoir 2 Control:', transform=ax4.transAxes, fontsize=12, fontweight='bold')
    ax4.text(0.05, 0.35, f'  Final Error: {final_error_res2:.3f} m', transform=ax4.transAxes, fontsize=11)
    ax4.text(0.05, 0.25, f'  MAE: {mae_res2:.3f} m', transform=ax4.transAxes, fontsize=11)
    ax4.text(0.05, 0.15, f'  Status: {"✓ Good" if final_error_res2 < 1.0 else "✗ Poor"}', transform=ax4.transAxes, fontsize=11)
    
    ax4.set_title('Control Performance Summary (Refactored)', fontsize=14, fontweight='bold')
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    
    # 保存图表
    save_path = '05_complex_networks_refactored_results.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nResults visualization saved as '{save_path}'")
    
    plt.show()
    
    return {
        'res1_error': final_error_res1,
        'res2_error': final_error_res2,
        'res1_mae': mae_res1,
        'res2_mae': mae_res2
    }

def create_branched_network_system():
    """
    Creates a complex branched network system using SimulationBuilder.
    
    Returns:
        SimulationBuilder: Configured simulation builder
    """
    # Initialize builder with simulation configuration
    config = {'end_time': 10000, 'dt': 1.0}
    builder = SimulationBuilder(config)
    
    print("Initializing physical components...")
    
    # Add reservoirs using builder methods
    builder.add_reservoir(
        component_id="res1",
        water_level=10.0,
        surface_area=1.5e6,
        volume=15e6
    )
    
    builder.add_reservoir(
        component_id="res2",
        water_level=20.0,
        surface_area=1.5e6,
        volume=30e6
    )
    
    # 直接创建闸门对象，设置正确的物理参数
    from core_lib.physical_objects.gate import Gate
    
    g1 = Gate(
        name="g1",
        initial_state={'opening': 0.1},
        parameters={
            'width': 20.0, 
            'discharge_coefficient': 2.0, 
            'max_opening': 2.0, 
            'max_rate_of_change': 0.5
        },
        message_bus=builder.harness.message_bus,
        action_topic="action.g1.opening",
        action_key='control_signal'
    )
    builder.harness.add_component("g1", g1)
    
    g2 = Gate(
        name="g2",
        initial_state={'opening': 0.1},
        parameters={
            'width': 25.0, 
            'discharge_coefficient': 2.0, 
            'max_opening': 2.0, 
            'max_rate_of_change': 0.5
        },
        message_bus=builder.harness.message_bus,
        action_topic="action.g2.opening",
        action_key='control_signal'
    )
    builder.harness.add_component("g2", g2)
    
    g3 = Gate(
        name="g3",
        initial_state={'opening': 0.5},
        parameters={
            'width': 30.0, 
            'discharge_coefficient': 2.0, 
            'max_opening': 2.0, 
            'max_rate_of_change': 0.5
        }
    )
    builder.harness.add_component("g3", g3)
    
    # Add river channels manually (not in builder yet)
    trib_chan = RiverChannel(
        name="trib_chan",
        initial_state={'volume': 2e5, 'water_level': 2.0},
        parameters={'k': 0.0002}
    )
    
    main_chan = RiverChannel(
        name="main_chan",
        initial_state={'volume': 8e5, 'water_level': 8.0},
        parameters={'k': 0.0001}
    )
    
    builder.harness.add_component("trib_chan", trib_chan)
    builder.harness.add_component("main_chan", main_chan)
    
    print("Defining network connections...")
    
    # Define the complex network topology
    connections = [
        ("res1", "g1"),
        ("g1", "trib_chan"),
        ("res2", "g2"),
        ("trib_chan", "main_chan"),
        ("g2", "main_chan"),
        ("main_chan", "g3")
    ]
    
    builder.connect_components(connections)
    
    print("Setting up multi-agent control system...")
    
    # Add digital twin agents
    twin_agents = [
        DigitalTwinAgent(
            agent_id="twin_res1",
            simulated_object=builder.harness.components["res1"],
            message_bus=builder.harness.message_bus,
            state_topic="state.res1.level"
        ),
        DigitalTwinAgent(
            agent_id="twin_g1",
            simulated_object=builder.harness.components["g1"],
            message_bus=builder.harness.message_bus,
            state_topic="state.g1.opening"
        ),
        DigitalTwinAgent(
            agent_id="twin_res2",
            simulated_object=builder.harness.components["res2"],
            message_bus=builder.harness.message_bus,
            state_topic="state.res2.level"
        ),
        DigitalTwinAgent(
            agent_id="twin_g2",
            simulated_object=builder.harness.components["g2"],
            message_bus=builder.harness.message_bus,
            state_topic="state.g2.opening"
        )
    ]
    
    # Add PID controllers and unified gate control agents
    pid1 = PIDController(
        Kp=2.0, Ki=0.5, Kd=0.2,
        setpoint=12.0,
        min_output=0.0,
        max_output=2.0
    )
    
    pid2 = PIDController(
        Kp=1.5, Ki=0.3, Kd=0.15,
        setpoint=18.0,
        min_output=0.0,
        max_output=2.0
    )
    
    lca1 = UnifiedGateControlAgent(
        agent_id="lca_g1",
        controller=pid1,
        message_bus=builder.harness.message_bus,
        observation_topic="state.res1.level",
        observation_key="water_level",
        action_topic="action.g1.opening",
        dt=config['dt'],
        command_topic="command.res1.setpoint",
        target_component="g1",
        control_type="gate_control"
    )
    
    lca2 = UnifiedGateControlAgent(
        agent_id="lca_g2",
        controller=pid2,
        message_bus=builder.harness.message_bus,
        observation_topic="state.res2.level",
        observation_key="water_level",
        action_topic="action.g2.opening",
        dt=config['dt'],
        command_topic="command.res2.setpoint",
        target_component="g2",
        control_type="gate_control"
    )
    
    # Add central dispatcher for monitoring
    dispatcher = CentralDispatcherAgent(
        agent_id="central_dispatcher",
        message_bus=builder.harness.message_bus,
        mode="rule",
        subscribed_topic="state.res1.level",
        observation_key="water_level",
        command_topic="command.res1.setpoint",
        dispatcher_params={
            "low_level": 8.0,
            "high_level": 12.0,
            "low_setpoint": 10.0,
            "high_setpoint": 8.0
        }
    )
    
    # Add all agents to the builder
    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        builder.add_agent(agent)
    
    return builder

def run_branched_network_simulation():
    """
    Sets up and runs the branched network simulation.
    """
    print("\n--- Setting up Complex Networks Simulation (Refactored) ---")
    
    # Create the simulation system
    builder = create_branched_network_system()
    
    # Build and run the simulation
    print("\nBuilding simulation harness...")
    builder.build()
    
    print("Running simulation...")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # Print final results
    builder.print_final_states()
    
    # Get specific final values
    history = builder.get_history()
    if history:
        final_res1_level = history[-1]['res1']['water_level']
        final_res2_level = history[-1]['res2']['water_level']
        print(f"\nFinal reservoir 1 water level: {final_res1_level:.2f} m (Setpoint: 12.0 m)")
        print(f"Final reservoir 2 water level: {final_res2_level:.2f} m (Setpoint: 18.0 m)")
    
    # 分析和可视化结果
    config = {'end_time': 1000, 'dt': 1.0}
    results = analyze_and_visualize_results(builder, config)

if __name__ == "__main__":
    run_branched_network_simulation()