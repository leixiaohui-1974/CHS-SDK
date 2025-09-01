#!/usr/bin/env python3
"""
Configuration-driven pipe and valve simulation script.

This script demonstrates the physical dynamics of a Pipe and Valve system,
loaded from a YAML configuration file.
"""

import sys
import os
import yaml
import math
import time as pytime
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.pipe import Pipe
from core_lib.physical_objects.valve import Valve

def load_config(config_path):
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def create_components(config):
    """Create components based on configuration."""
    components = {}
    
    for name, comp_config in config['components'].items():
        comp_type = comp_config['type']
        initial_state = comp_config.get('initial_state', {})
        parameters = comp_config.get('parameters', {})
        
        if comp_type == 'Pipe':
            components[name] = Pipe(
                name=name,
                initial_state=initial_state,
                parameters=parameters
            )
        elif comp_type == 'Valve':
            components[name] = Valve(
                name=name,
                initial_state=initial_state,
                parameters=parameters
            )
        else:
            raise ValueError(f"Unknown component type: {comp_type}")
    
    return components

def calculate_valve_opening(time, control_config):
    """Calculate valve opening based on control pattern."""
    pattern = control_config['valve_opening_pattern']
    
    if pattern['type'] == 'sinusoidal':
        amplitude = pattern['amplitude']
        period = pattern['period']
        offset = pattern['offset']
        return offset + amplitude * math.sin(2 * math.pi * time / period)
    else:
        raise ValueError(f"Unknown control pattern: {pattern['type']}")

def run_simulation(config):
    """Run the pipe-valve simulation."""
    print("--- Setting up Pipe and Valve Simulation ---")
    
    # Create components
    components = create_components(config)
    pipe = components['pipe_1']
    valve = components['valve_1']
    
    # Simulation parameters
    sim_config = config['simulation']
    duration = sim_config['duration']
    dt = sim_config['dt']
    upstream_head = sim_config['upstream_head']
    downstream_head = sim_config['downstream_head']
    
    # Output settings
    output_config = config['output']
    print_interval = output_config['print_interval']
    delay = output_config['delay']
    
    # Data storage for visualization
    time_data = []
    valve_opening_data = []
    pipe_outflow_data = []
    pipe_head_loss_data = []
    
    print("\n--- Running Simulation ---")
    print(f"{'Time (s)':<10} | {'Valve Opening (%)':<20} | {'Pipe Outflow (m3/s)':<25} | {'Pipe Head Loss (m)':<20}")
    print("-" * 80)
    
    for i in range(int(duration / dt)):
        current_time = i * dt
        
        # Calculate valve opening based on control pattern
        valve_opening = calculate_valve_opening(current_time, config['control'])
        valve.step({'control_signal': valve_opening}, dt)
        
        # Calculate valve flow
        valve_action = {'upstream_head': upstream_head, 'downstream_head': downstream_head}
        valve_state = valve.step(valve_action, dt)
        flow = valve_state['outflow']
        
        # Calculate pipe head loss
        pipe_action = {'outflow': flow}
        pipe_state = pipe.step(pipe_action, dt)
        
        # Store data for visualization
        time_data.append(current_time)
        valve_opening_data.append(valve_state['opening'])
        pipe_outflow_data.append(pipe_state['outflow'])
        pipe_head_loss_data.append(pipe_state['head_loss'])
        
        # Print results at specified intervals
        if int(current_time) % print_interval == 0:
            print(f"{current_time:<10.1f} | {valve_state['opening']:<20.2f} | {pipe_state['outflow']:<25.4f} | {pipe_state['head_loss']:<20.4f}")
        
        # Small delay
        pytime.sleep(delay)
    
    print("\n--- Simulation Complete ---")
    
    # Generate visualization if enabled
    if config['visualization']['enabled']:
        generate_plots(config, time_data, valve_opening_data, pipe_outflow_data, pipe_head_loss_data)
    
    return {
        'time': time_data,
        'valve_opening': valve_opening_data,
        'pipe_outflow': pipe_outflow_data,
        'pipe_head_loss': pipe_head_loss_data
    }

def generate_plots(config, time_data, valve_opening_data, pipe_outflow_data, pipe_head_loss_data):
    """Generate visualization plots."""
    viz_config = config['visualization']
    plots_config = viz_config['plots']
    
    # Data mapping
    data_map = {
        'time': time_data,
        'valve_opening': valve_opening_data,
        'pipe_outflow': pipe_outflow_data,
        'pipe_head_loss': pipe_head_loss_data
    }
    
    # Create subplots
    fig, axes = plt.subplots(len(plots_config), 1, figsize=(12, 4 * len(plots_config)))
    if len(plots_config) == 1:
        axes = [axes]
    
    for i, plot_config in enumerate(plots_config):
        x_data = data_map[plot_config['x_data']]
        y_data = data_map[plot_config['y_data']]
        
        axes[i].plot(x_data, y_data, 'b-', linewidth=2)
        axes[i].set_title(plot_config['title'], fontsize=14, fontweight='bold')
        axes[i].set_xlabel('Time (s)', fontsize=12)
        axes[i].set_ylabel(plot_config['ylabel'], fontsize=12)
        axes[i].grid(True, alpha=0.3)
        axes[i].tick_params(axis='both', which='major', labelsize=10)
    
    plt.tight_layout()
    
    # Save plot
    save_path = viz_config['save_path']
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nResults plot saved as '{save_path}'")
    
    plt.close()

def main():
    """Main function."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
    config = load_config(config_path)
    
    # Run simulation
    results = run_simulation(config)
    
    print("\n=== Pipe and Valve System Example Complete ===")
    print(f"Configuration: {config_path}")
    print(f"Total simulation time: {config['simulation']['duration']} seconds")
    print(f"Time step: {config['simulation']['dt']} seconds")
    
if __name__ == "__main__":
    main()