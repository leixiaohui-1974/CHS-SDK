#!/usr/bin/env python3
"""
Configuration-driven multi-agent system (MAS) simulation script.

This script demonstrates the multi-agent system architecture loaded from
a YAML configuration file, where components are fully decoupled and
communicate only via a MessageBus.
"""

import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.adaptive_pid_controller import AdaptivePIDController
from core_lib.local_agents.control.smart_pid_controller import SmartPIDController
from core_lib.local_agents.control.unified_gate_control_agent import UnifiedGateControlAgent
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
            
            agent = DigitalTwinAgent(
                agent_id=agent_id,
                simulated_object=simulated_object,
                message_bus=message_bus,
                state_topic=topics['reservoir_state']  # 使用正确的主题
            )
            agents.append(agent)
            
        elif agent_type == 'UnifiedGateControlAgent':
            # Create controller
            controller_config = agent_config['controller']
            if controller_config['type'] == 'PIDController':
                params = controller_config['parameters']
                controller = PIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=params['setpoint'],
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            elif controller_config['type'] == 'AdaptivePIDController':
                params = controller_config['parameters']
                controller = AdaptivePIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=params['setpoint'],
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            elif controller_config['type'] == 'SmartPIDController':
                params = controller_config['parameters']
                controller = SmartPIDController(
                    Kp=params['Kp'],
                    Ki=params['Ki'],
                    Kd=params['Kd'],
                    setpoint=params['setpoint'],
                    min_output=params['min_output'],
                    max_output=params['max_output']
                )
            else:
                raise ValueError(f"Unknown controller type: {controller_config['type']}")
            
            # 增强控制逻辑：增加积分抗饱和和微分滤波
            if hasattr(controller, 'integral_windup_limit'):
                controller.integral_windup_limit = params.get('windup_limit', 0.5)
            if hasattr(controller, 'filter_time_constant'):
                controller.filter_time_constant = params.get('filter_constant', 0.1)
            
            # 使用统一配置的topics
            agent = UnifiedGateControlAgent(
                agent_id=agent_id,
                controller=controller,
                message_bus=message_bus,
                observation_topic=topics['reservoir_state'],
                observation_key='water_level',
                action_topic=topics['gate_action'],
                dt=config['simulation']['dt'],
                target_component='gate_1',
                control_type='water_level_control'
            )
            
            if config['debug']['enabled']:
                agent.enable_control_logging(
                    enabled=True,
                    state_topic=topics['digital_twin_state'],
                    interval=config['debug']['log_interval']
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
    """Analyze simulation results."""
    print("\n--- Analyzing Results ---")
    
    if config['analysis']['final_state_report']:
        target_level = config['analysis']['target_water_level']
        final_level = data['reservoir_water_level'][-1] if data['reservoir_water_level'] else 0
        final_volume = data['reservoir_volume'][-1] if data['reservoir_volume'] else 0
        final_opening = data['gate_opening'][-1] if data['gate_opening'] else 0
        
        print(f"\n=== Multi-Agent System Performance Analysis ===")
        print(f"Target water level: {target_level:.2f} m")
        print(f"Final water level: {final_level:.2f} m")
        print(f"Final reservoir volume: {final_volume:.0f} m³")
        print(f"Final gate opening: {final_opening:.3f}")
        
        # Calculate steady-state error
        steady_state_error = abs(final_level - target_level)
        print(f"Steady-state error: {steady_state_error:.3f} m")
        
        # Performance validation
        print("\n=== Control Performance Validation ===")
        if steady_state_error < 0.5:
            print("✓ PASS: Steady-state error is acceptable (< 0.5 m)")
        else:
            print("✗ FAIL: Steady-state error is too large (>= 0.5 m)")

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
        'end_time': config['simulation']['duration'],  # 使用end_time而不是duration
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
    analyze_results(config, data)
    
    # Generate visualization
    generate_plots(config, data)
    
    print("\n=== Multi-Agent System Example Complete ===")
    print(f"Configuration: {config_path}")
    print(f"Simulation duration: {config['simulation']['duration']} seconds")
    print(f"Time step: {config['simulation']['dt']} seconds")
    
if __name__ == "__main__":
    main()