#!/usr/bin/env python3
"""
Configuration-driven multi-agent system (MAS) simulation script.

This script demonstrates the multi-agent system architecture loaded from
a YAML configuration file, where components are fully decoupled and
communicate only via a MessageBus.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

import yaml
import matplotlib.pyplot as plt
import numpy as np


def _to_bool(value, default=False):
    """Best-effort conversion of configuration values to boolean."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default

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

def load_config(config_path):
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def create_components(config, message_bus):
    """Create components based on configuration."""
    components = {}
    topics = config['communication']['topics']
    
    for name, comp_config in config['components'].items():
        comp_type = comp_config['type']
        initial_state = comp_config.get('initial_state', {})
        parameters = comp_config.get('parameters', {})
        
        if comp_type == 'Reservoir':
            components[name] = Reservoir(
                name=name,
                initial_state=initial_state,
                parameters=parameters
            )
        elif comp_type == 'Gate':
            # Check if message bus is enabled for this component
            mb_config = comp_config.get('message_bus', {})
            if mb_config.get('enabled', False):
                action_topic = mb_config.get('action_topic', topics['gate_action'])
                components[name] = Gate(
                    name=name,
                    initial_state=initial_state,
                    parameters=parameters,
                    message_bus=message_bus,
                    action_topic=action_topic
                )
            else:
                components[name] = Gate(
                    name=name,
                    initial_state=initial_state,
                    parameters=parameters
                )
        else:
            raise ValueError(f"Unknown component type: {comp_type}")
    
    return components

def create_agents(config, components, message_bus):
    """Create agents based on configuration."""
    agents = []
    topics = config['communication']['topics']
    
    for agent_name, agent_config in config['agents'].items():
        agent_type = agent_config['type']
        agent_id = agent_config['agent_id']

        if agent_type == 'DigitalTwinAgent':
            simulated_object_name = agent_config['simulated_object']
            simulated_object = components[simulated_object_name]
            state_topic = agent_config['message_bus']['state_topic']
            
            agent = DigitalTwinAgent(
                agent_id=agent_id,
                simulated_object=simulated_object,
                message_bus=message_bus,
                state_topic=state_topic
            )
            agents.append(agent)
            
        elif agent_type == 'LocalControlAgent':
            controller_config = agent_config.get('controller', {})
            controller_type = controller_config.get('type')
            controller_params = controller_config.get('parameters', {})

            if controller_type == 'PIDController':
                controller = PIDController(
                    Kp=controller_params['Kp'],
                    Ki=controller_params['Ki'],
                    Kd=controller_params['Kd'],
                    setpoint=controller_params['setpoint'],
                    min_output=controller_params['min_output'],
                    max_output=controller_params['max_output']
                )
            else:
                raise ValueError(f"Unknown controller type: {controller_type}")

            mb_config = agent_config.get('message_bus', {})

            target_component = agent_config.get('target_component') or mb_config.get('target_component')
            if not target_component:
                raise ValueError("LocalControlAgent configuration requires 'target_component'.")

            control_type = agent_config.get('control_type', 'local_control')

            data_sources = agent_config.get('data_sources')
            if not data_sources:
                primary_observation = mb_config.get('observation_topic') or topics.get('reservoir_state')
                if not primary_observation:
                    raise ValueError("LocalControlAgent requires at least one observation topic defined.")
                data_sources = {'primary_data': primary_observation}

            control_targets = agent_config.get('control_targets')
            if not control_targets:
                primary_action = mb_config.get('action_topic') or topics.get('gate_action')
                if not primary_action:
                    raise ValueError("LocalControlAgent requires at least one action topic defined.")
                control_targets = {'primary_target': primary_action}

            allocation_config = agent_config.get('allocation_config') or agent_config.get('allocation') or {}

            resolved_controller_config = agent_config.get('controller_config') or {
                'type': controller_type,
                'parameters': controller_params,
            }

            observation_topic = mb_config.get('observation_topic', data_sources.get('primary_data'))
            observation_key = mb_config.get('observation_key')
            action_topic = mb_config.get('action_topic', control_targets.get('primary_target'))

            logging_config = agent_config.get('logging', {})
            log_observations = _to_bool(
                logging_config.get('log_observations', agent_config.get('log_observations', False))
            )

            agent = LocalControlAgent(
                agent_id=agent_id,
                message_bus=message_bus,
                dt=config['simulation']['dt'],
                target_component=target_component,
                control_type=control_type,
                data_sources=data_sources,
                control_targets=control_targets,
                allocation_config=allocation_config,
                controller_config=resolved_controller_config,
                controller=controller,
                observation_topic=observation_topic,
                observation_key=observation_key,
                action_topic=action_topic,
                command_topic=mb_config.get('command_topic'),
                feedback_topic=mb_config.get('feedback_topic'),
                log_observations=log_observations
            )
            agents.append(agent)

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    return agents

def extract_simulation_data(history):
    """Extract data from simulation history for analysis."""
    time_data = []
    reservoir_water_level = []
    reservoir_volume = []
    gate_opening = []
    
    for i, step_data in enumerate(history):
        time_data.append(i)  # Time step index
        
        # Extract reservoir data
        if 'reservoir_1' in step_data:
            reservoir_water_level.append(step_data['reservoir_1']['water_level'])
            reservoir_volume.append(step_data['reservoir_1']['volume'])
        
        # Extract gate data
        if 'gate_1' in step_data:
            gate_opening.append(step_data['gate_1']['opening'])
    
    return {
        'time': time_data,
        'reservoir_water_level': reservoir_water_level,
        'reservoir_volume': reservoir_volume,
        'gate_opening': gate_opening
    }

def analyze_results(config, data):
    """Analyze simulation results and compute validation metrics."""
    print("\n--- Analyzing Results ---")

    metrics = {}
    analysis_config = config.get('analysis', {})

    if analysis_config.get('final_state_report'):
        target_level = analysis_config.get('target_water_level')
        tolerance = analysis_config.get('steady_state_tolerance', 0.5)

        final_level = data['reservoir_water_level'][-1] if data['reservoir_water_level'] else None
        initial_level = data['reservoir_water_level'][0] if data['reservoir_water_level'] else None
        final_volume = data['reservoir_volume'][-1] if data['reservoir_volume'] else None
        final_opening = data['gate_opening'][-1] if data['gate_opening'] else None

        print(f"\n=== Multi-Agent System Performance Analysis ===")
        if target_level is not None:
            print(f"Target water level: {target_level:.2f} m")
        if final_level is not None:
            print(f"Final water level: {final_level:.2f} m")
        if final_volume is not None:
            print(f"Final reservoir volume: {final_volume:.0f} m³")
        if final_opening is not None:
            print(f"Final gate opening: {final_opening:.3f}")

        # Calculate steady-state error
        if target_level is not None and final_level is not None:
            steady_state_error = abs(final_level - target_level)
        else:
            steady_state_error = None

        if steady_state_error is not None:
            print(f"Steady-state error: {steady_state_error:.3f} m")

        min_level = min(data['reservoir_water_level']) if data['reservoir_water_level'] else None
        max_level = max(data['reservoir_water_level']) if data['reservoir_water_level'] else None

        metrics = {
            'target_level': target_level,
            'final_level': final_level,
            'initial_level': initial_level,
            'final_volume': final_volume,
            'final_opening': final_opening,
            'steady_state_error': steady_state_error,
            'tolerance': tolerance,
            'min_level': min_level,
            'max_level': max_level,
        }

        print("\n=== Control Performance Validation ===")
        if steady_state_error is not None and steady_state_error <= tolerance:
            print("✓ PASS: Steady-state error is acceptable (≤ tolerance)")
            score = 1.0
        else:
            print("✗ FAIL: Steady-state error exceeds tolerance")
            score = 0.0

        metrics['score'] = score
        metrics['status'] = 'PASS' if score >= 1.0 else 'FAIL'

        if min_level is not None and max_level is not None:
            print(f"Water level range during simulation: {min_level:.2f} m – {max_level:.2f} m")

    return metrics


def generate_markdown_report(config, data, metrics, output_path):
    """Generate a Markdown report summarizing simulation validation results."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    analysis_config = config.get('analysis', {})
    simulation_config = config.get('simulation', {})

    duration = simulation_config.get('duration')
    dt = simulation_config.get('dt')

    water_levels = data.get('reservoir_water_level', [])
    gate_openings = data.get('gate_opening', [])

    initial_level = metrics.get('initial_level') if metrics else (water_levels[0] if water_levels else None)
    final_level = metrics.get('final_level') if metrics else (water_levels[-1] if water_levels else None)
    steady_state_error = metrics.get('steady_state_error') if metrics else None
    target_level = metrics.get('target_level') if metrics else analysis_config.get('target_water_level')
    tolerance = metrics.get('tolerance') if metrics else analysis_config.get('steady_state_tolerance', 0.5)
    score = metrics.get('score') if metrics else None

    min_level = metrics.get('min_level') if metrics else (min(water_levels) if water_levels else None)
    max_level = metrics.get('max_level') if metrics else (max(water_levels) if water_levels else None)

    min_gate = min(gate_openings) if gate_openings else None
    max_gate = max(gate_openings) if gate_openings else None

    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')

    lines = [
        "# 事件驱动智能体示例自动验证报告",
        "",
        "本报告由 `run_config.py` 自动生成，用于记录 `agent_based/03_event_driven_agents` 示例的仿真验证结果。",
        "",
        "## 仿真配置",
        f"- 仿真时长：{duration} s" if duration is not None else "- 仿真时长：未配置",
        f"- 时间步长：{dt} s" if dt is not None else "- 时间步长：未配置",
        f"- 观测主题：{analysis_config.get('observation_topic', 'state.reservoir.level')}",
        f"- 动作主题：{analysis_config.get('action_topic', 'action.gate.opening')}",
        "",
        "## 核心结果",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 初始水位 | {initial_level:.3f} m |" if initial_level is not None else "| 初始水位 | 未记录 |",
        f"| 目标水位 | {target_level:.3f} m |" if target_level is not None else "| 目标水位 | 未设置 |",
        f"| 最终水位 | {final_level:.3f} m |" if final_level is not None else "| 最终水位 | 未记录 |",
        f"| 稳态误差 | {steady_state_error:.3f} m |" if steady_state_error is not None else "| 稳态误差 | 未计算 |",
        f"| 水位范围 | {min_level:.3f} m – {max_level:.3f} m |" if min_level is not None and max_level is not None else "| 水位范围 | 未记录 |",
        f"| 闸门开度范围 | {min_gate:.3f} – {max_gate:.3f} |" if min_gate is not None and max_gate is not None else "| 闸门开度范围 | 未记录 |",
        "",
        "## 验证与评分",
    ]

    if score is not None:
        lines.extend([
            f"- 稳态误差容差：{tolerance:.3f} m",
            f"- 评分：{score:.3f} （1.000 表示完全通过）",
            f"- 验证结论：{'通过 ✅' if score >= 1.0 else '未通过 ❌'}",
        ])
    else:
        lines.append("- 未计算评分。")

    lines.extend([
        "",
        "## 运行环境",
        f"- 报告生成时间：{timestamp}",
    ])

    output_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"Markdown report saved to '{output_path}'")

def generate_plots(config, data):
    """Generate visualization plots."""
    if not config['visualization']['enabled']:
        return
    
    viz_config = config['visualization']
    plots_config = viz_config['plots']
    
    # Create subplots
    fig, axes = plt.subplots(len(plots_config), 1, figsize=(12, 4 * len(plots_config)))
    if len(plots_config) == 1:
        axes = [axes]
    
    for i, plot_config in enumerate(plots_config):
        x_data = data[plot_config['x_data']]
        y_data = data[plot_config['y_data']]
        
        axes[i].plot(x_data, y_data, 'b-', linewidth=2, label='Actual')
        
        # Add target line if specified
        if 'target_line' in plot_config:
            target_value = plot_config['target_line']
            axes[i].axhline(y=target_value, color='r', linestyle='--', linewidth=2, label=f'Target ({target_value})')
            axes[i].legend()
        
        axes[i].set_title(plot_config['title'], fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Time Steps', fontsize=12)
        axes[i].set_ylabel(plot_config['ylabel'], fontsize=12)
        axes[i].grid(True, alpha=0.3)
        axes[i].tick_params(axis='both', which='major', labelsize=10)
    
    plt.tight_layout()
    
    # Save plot
    save_path = viz_config['save_path']
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nResults plot saved as '{save_path}'")
    
    plt.close()

def run_simulation(config):
    """Run the multi-agent system simulation."""
    print("--- Setting up Multi-Agent System Simulation ---")
    
    # Create simulation harness
    simulation_config = {
        'start_time': config['simulation'].get('start_time', 0),
        'end_time': config['simulation']['duration'],
        'dt': config['simulation']['dt']
    }
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # Create components
    components = create_components(config, message_bus)
    
    # Create agents
    agents = create_agents(config, components, message_bus)
    
    # Add components to harness
    for name, component in components.items():
        harness.add_component(name, component)
    
    # Add agents to harness
    for agent in agents:
        harness.add_agent(agent)
    
    # Add connections
    for connection in config['connections']:
        harness.add_connection(connection['from'], connection['to'])
    
    # Build and run simulation
    harness.build()
    
    print("\n--- Running MAS Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")
    
    return harness

def main():
    """Main function."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
    config = load_config(config_path)
    
    # Run simulation
    harness = run_simulation(config)
    
    # Extract and analyze data
    data = extract_simulation_data(harness.history)
    metrics = analyze_results(config, data)

    # Generate visualization
    generate_plots(config, data)

    analysis_config = config.get('analysis', {})
    report_filename = analysis_config.get('report_filename', 'event_driven_agents_report.md')
    report_path = Path(__file__).with_name(report_filename)
    generate_markdown_report(config, data, metrics, report_path)

    print("\n=== Multi-Agent System Example Complete ===")
    print(f"Configuration: {config_path}")
    print(f"Simulation duration: {config['simulation']['duration']} seconds")
    print(f"Time step: {config['simulation']['dt']} seconds")
    
if __name__ == "__main__":
    main()
