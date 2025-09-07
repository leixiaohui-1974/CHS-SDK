#!/usr/bin/env python3
"""
Refactored Example: Hierarchical Control System using SimulationBuilder.

This script demonstrates how to use SimulationBuilder to simplify the setup
of a two-level hierarchical control system.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent

def create_hierarchical_control_system():
    """
    Creates a hierarchical control system using SimulationBuilder.
    
    Returns:
        SimulationBuilder: Configured simulation builder
    """
    # Initialize builder with simulation configuration
    config = {'end_time': 5000, 'dt': 1.0}  # 使用1秒时间步长
    builder = SimulationBuilder(config)
    
    # Communication topics
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"
    
    # Add physical components using builder methods
    builder.add_reservoir(
        component_id="reservoir_1",
        water_level=19.0,
        surface_area=1.5e6,
        volume=28.5e6
    )
    
    # 直接创建闸门对象，设置正确的物理参数
    from core_lib.physical_objects.gate import Gate
    gate = Gate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters={
            'discharge_coefficient': 3.0,  # 大幅增加流量系数
            'width': 50.0,  # 增加闸门宽度
            'max_opening': 2.0,
            'max_rate_of_change': 2.0
        },
        message_bus=builder.harness.message_bus,
        action_topic=GATE_ACTION_TOPIC,
        action_key='control_signal'
    )
    builder.harness.add_component("gate_1", gate)
    
    # Connect components
    builder.connect_components([("reservoir_1", "gate_1")])
    
    # Add digital twin agents
    reservoir_twin = DigitalTwinAgent(
        agent_id="twin_reservoir_1",
        simulated_object=builder.harness.components["reservoir_1"],
        message_bus=builder.harness.message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )
    
    gate_twin = DigitalTwinAgent(
        agent_id="twin_gate_1",
        simulated_object=builder.harness.components["gate_1"],
        message_bus=builder.harness.message_bus,
        state_topic=GATE_STATE_TOPIC
    )
    
    # Add PID controller and unified gate control agent
    pid = PIDController(
        Kp=5.0, Ki=1.0, Kd=0.2,  # 进一步增强控制参数
        setpoint=15.0,
        min_output=0.0,
        max_output=2.0  # 与主脚本保持一致
    )
    
    lca = UnifiedGateControlAgent(
        agent_id="lca_gate_1",
        controller=pid,
        message_bus=builder.harness.message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=config['dt'],
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC,
        target_component='gate_1',
        control_type='gate_control'
    )
    
    # Add central dispatcher
    dispatcher = CentralDispatcherAgent(
        agent_id="dispatcher_1",
        message_bus=builder.harness.message_bus,
        mode="rule",
        subscribed_topic=RESERVOIR_STATE_TOPIC,
        observation_key="water_level",
        command_topic=GATE_COMMAND_TOPIC,
        dispatcher_params={
            "low_level": 12.0,
            "high_level": 18.0,
            "low_setpoint": 15.0,
            "high_setpoint": 10.0  # 降低防洪目标水位
        }
    )
    
    # Add all agents to the builder
    builder.add_agent(reservoir_twin)
    builder.add_agent(gate_twin)
    builder.add_agent(lca)
    builder.add_agent(dispatcher)
    
    return builder

def analyze_and_visualize_results(builder, config):
    """
    分析和可视化分层控制系统的结果
    """
    print("\n--- Analyzing Hierarchical Control Results ---")
    
    # 获取历史数据
    history = builder.get_history()
    if not history:
        print("No simulation history available")
        return None
    
    # 提取数据
    time_data = []
    water_levels = []
    gate_openings = []
    setpoints = []
    
    for i, step_data in enumerate(history):
        time_data.append(i * config['dt'])
        
        if 'reservoir_1' in step_data:
            water_levels.append(step_data['reservoir_1']['water_level'])
        else:
            water_levels.append(0)
            
        if 'gate_1' in step_data:
            gate_openings.append(step_data['gate_1']['opening'])
        else:
            gate_openings.append(0)
        
        # 动态目标水位：正常操作15.0m，防洪12.0m
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
    
    # 计算控制信号统计
    if gate_openings:
        avg_opening = np.mean(gate_openings)
        max_opening = np.max(gate_openings)
        min_opening = np.min(gate_openings)
        print(f"Gate Opening Stats - Avg: {avg_opening:.3f}, Max: {max_opening:.3f}, Min: {min_opening:.3f}")
    
    # 创建可视化图表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 水位控制图
    ax1.plot(time_data, water_levels, 'b-', linewidth=2, label='Actual Water Level')
    ax1.plot(time_data, setpoints, 'r--', linewidth=2, label='Target Setpoint')
    ax1.axhline(y=18.0, color='orange', linestyle=':', linewidth=2, label='Flood Control Threshold')
    ax1.set_title('Hierarchical Control: Water Level Response', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Water Level (m)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 闸门开度图
    ax2.plot(time_data, gate_openings, 'g-', linewidth=2, label='Gate Opening')
    ax2.set_title('Gate Opening Response', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)', fontsize=12)
    ax2.set_ylabel('Gate Opening', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 控制误差图
    errors = [abs(level - target_level) for level in water_levels]
    ax3.plot(time_data, errors, 'r-', linewidth=2, label='Control Error')
    ax3.axhline(y=1.0, color='orange', linestyle='--', linewidth=2, label='Acceptable Error Threshold')
    ax3.set_title('Control Error Over Time', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (s)', fontsize=12)
    ax3.set_ylabel('Absolute Error (m)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 分层控制状态图
    control_modes = ['Normal' if level <= 18.0 else 'Flood Control' for level in water_levels]
    mode_colors = ['blue' if mode == 'Normal' else 'red' for mode in control_modes]
    
    # 创建模式变化图
    mode_changes = []
    current_mode = control_modes[0]
    for i, mode in enumerate(control_modes):
        if mode != current_mode:
            mode_changes.append((time_data[i], current_mode, mode))
            current_mode = mode
    
    ax4.text(0.05, 0.95, f'Control Mode Changes: {len(mode_changes)}', 
             transform=ax4.transAxes, fontsize=12, verticalalignment='top')
    ax4.text(0.05, 0.85, f'Final Mode: {control_modes[-1]}', 
             transform=ax4.transAxes, fontsize=12, verticalalignment='top')
    ax4.text(0.05, 0.75, f'Flood Control Active: {high_level_periods > 0}', 
             transform=ax4.transAxes, fontsize=12, verticalalignment='top')
    
    # 显示模式变化时间点
    for i, (time, old_mode, new_mode) in enumerate(mode_changes[:5]):  # 只显示前5个变化
        ax4.text(0.05, 0.65 - i*0.08, f'{time:.0f}s: {old_mode} → {new_mode}', 
                 transform=ax4.transAxes, fontsize=10, verticalalignment='top')
    
    ax4.set_title('Hierarchical Control Mode Analysis', fontsize=14, fontweight='bold')
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    
    # 保存图表
    save_path = '04_hierarchical_control_refactored_results.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nResults visualization saved as '{save_path}'")
    
    plt.show()
    
    return {
        'final_error': final_error,
        'mae': mae,
        'rmse': rmse,
        'flood_control_activated': high_level_periods > 0,
        'mode_changes': len(mode_changes)
    }

def run_hierarchical_simulation():
    """
    Sets up and runs the hierarchical control simulation.
    """
    print("\n--- Setting up Hierarchical Control Simulation (Refactored) ---")
    
    # Create the simulation system
    config = {'end_time': 50000, 'dt': 1.0}  # 使用合理的时间步长
    builder = create_hierarchical_control_system()
    
    # Build and run the simulation
    builder.build()
    
    print("\n--- Running Hierarchical Simulation ---")
    builder.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    # Print final results
    builder.print_final_states()
    
    # Get specific final values
    history = builder.get_history()
    if history:
        final_level = history[-1]['reservoir_1']['water_level']
        final_opening = history[-1]['gate_1']['opening']
        print(f"\nFinal reservoir water level: {final_level:.2f} m")
        print(f"Final gate opening: {final_opening:.2f} m")
    
    # 分析和可视化结果
    results = analyze_and_visualize_results(builder, config)
    
    # 验证控制正确性
    if results:
        print(f"\n=== Control Correctness Verification ===")
        if results['final_error'] < 1.0:
            print("✓ PASS: Control error is acceptable (< 1.0 m)")
        else:
            print("✗ FAIL: Control error is too large (>= 1.0 m)")
        
        if results['flood_control_activated']:
            print("✓ PASS: Flood control system activated when needed")
        else:
            print("ℹ INFO: Flood control not activated (water level stayed below 18m)")
        
        print(f"✓ INFO: Control mode changes: {results['mode_changes']}")
    
    return results

if __name__ == "__main__":
    run_hierarchical_simulation()