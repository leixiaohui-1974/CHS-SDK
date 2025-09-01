#!/usr/bin/env python3
"""
Configuration-driven version of Multi-Component Systems Example.

This script demonstrates how to run a complex multi-component simulation
using a YAML configuration file. The system includes:
- Reservoir -> Gate 1 -> RiverChannel -> Gate 2
- Two independent PID controllers for reservoir level and channel volume control

Usage:
    python run_config.py [--config CONFIG_FILE]
    
Example:
    python run_config.py --config config.yml
"""

import sys
import os
import argparse
import yaml
import math
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def load_config(config_file):
    """Load configuration from YAML file."""
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_component(comp_name, comp_config):
    """Create a component based on configuration."""
    comp_type = comp_config['type']
    initial_state = comp_config.get('initial_state', {})
    parameters = comp_config.get('parameters', {})
    
    if comp_type == 'Reservoir':
        return Reservoir(
            name=comp_name,
            initial_state=initial_state,
            parameters=parameters
        )
    elif comp_type == 'Gate':
        return Gate(
            name=comp_name,
            initial_state=initial_state,
            parameters=parameters
        )
    elif comp_type == 'RiverChannel':
        return RiverChannel(
            name=comp_name,
            initial_state=initial_state,
            parameters=parameters
        )
    else:
        raise ValueError(f"Unknown component type: {comp_type}")

def create_controller(ctrl_name, ctrl_config):
    """Create a controller based on configuration."""
    ctrl_type = ctrl_config['type']
    parameters = ctrl_config['parameters']
    
    if ctrl_type == 'PIDController':
        return PIDController(
            Kp=parameters['Kp'],
            Ki=parameters['Ki'],
            Kd=parameters['Kd'],
            setpoint=parameters['setpoint'],
            min_output=parameters['min_output'],
            max_output=parameters['max_output']
        )
    else:
        raise ValueError(f"Unknown controller type: {ctrl_type}")

def analyze_results(harness, config):
    """Analyze simulation results and generate performance metrics."""
    print("\n--- Analyzing Results ---")
    
    # Extract data from simulation history
    times = [step['time'] for step in harness.history]
    reservoir_levels = [step['reservoir_1']['water_level'] for step in harness.history]
    channel_volumes = [step['channel_1']['volume'] for step in harness.history]
    gate1_openings = [step['gate_1']['opening'] for step in harness.history]
    gate2_openings = [step['gate_2']['opening'] for step in harness.history]
    
    # Get analysis configuration
    analysis_config = config.get('analysis', {})
    metrics_config = analysis_config.get('performance_metrics', {})
    
    # Extract controller setpoints and thresholds
    reservoir_setpoint = config['controllers']['res_level_ctrl']['parameters']['setpoint']
    channel_setpoint = config['controllers']['chan_vol_ctrl']['parameters']['setpoint']
    
    reservoir_metrics = metrics_config.get('reservoir_control', {})
    channel_metrics = metrics_config.get('channel_control', {})
    
    reservoir_error_threshold = reservoir_metrics.get('steady_state_error_threshold', 0.5)
    reservoir_stability_threshold = reservoir_metrics.get('stability_threshold', 0.1)
    channel_error_threshold = channel_metrics.get('steady_state_error_threshold', 50000)
    channel_stability_threshold = channel_metrics.get('stability_threshold', 10000)
    
    # Calculate performance metrics for reservoir level control
    final_reservoir_level = reservoir_levels[-1]
    reservoir_steady_state_error = abs(final_reservoir_level - reservoir_setpoint)
    
    # Calculate performance metrics for channel volume control
    final_channel_volume = channel_volumes[-1]
    channel_steady_state_error = abs(final_channel_volume - channel_setpoint)
    
    # Calculate RMSE for both controllers
    reservoir_rmse = math.sqrt(sum((level - reservoir_setpoint)**2 for level in reservoir_levels) / len(reservoir_levels))
    channel_rmse = math.sqrt(sum((vol - channel_setpoint)**2 for vol in channel_volumes) / len(channel_volumes))
    
    # Calculate stability metrics (variation in final 10 steps)
    reservoir_variation = max(reservoir_levels[-10:]) - min(reservoir_levels[-10:]) if len(reservoir_levels) >= 10 else 0
    channel_variation = max(channel_volumes[-10:]) - min(channel_volumes[-10:]) if len(channel_volumes) >= 10 else 0
    
    # Print performance analysis
    print(f"\n=== Multi-Component PID Control Performance Analysis ===")
    print(f"\n--- Reservoir Level Control ---")
    print(f"Target water level (setpoint): {reservoir_setpoint:.2f} m")
    print(f"Initial water level: {reservoir_levels[0]:.2f} m")
    print(f"Final water level: {final_reservoir_level:.2f} m")
    print(f"Steady-state error: {reservoir_steady_state_error:.4f} m")
    print(f"RMSE: {reservoir_rmse:.4f} m")
    print(f"Final 10-step variation: {reservoir_variation:.4f} m")
    
    print(f"\n--- Channel Volume Control ---")
    print(f"Target volume (setpoint): {channel_setpoint:.0f} m³")
    print(f"Initial volume: {channel_volumes[0]:.0f} m³")
    print(f"Final volume: {final_channel_volume:.0f} m³")
    print(f"Steady-state error: {channel_steady_state_error:.0f} m³")
    print(f"RMSE: {channel_rmse:.0f} m³")
    print(f"Final 10-step variation: {channel_variation:.0f} m³")
    
    # Create visualization if enabled
    viz_config = analysis_config.get('visualization', {})
    if viz_config.get('enabled', True):
        create_visualization(times, reservoir_levels, channel_volumes, gate1_openings, gate2_openings, 
                           reservoir_setpoint, channel_setpoint, viz_config)
    
    # Validate control performance
    print("\n=== Control Performance Validation ===")
    
    passed_tests = 0
    total_tests = 4
    
    # Reservoir control validation
    if reservoir_steady_state_error < reservoir_error_threshold:
        print(f"✓ PASS: Reservoir steady-state error is acceptable (< {reservoir_error_threshold} m)")
        passed_tests += 1
    else:
        print(f"✗ FAIL: Reservoir steady-state error is too large (>= {reservoir_error_threshold} m)")
    
    # Channel control validation
    if channel_steady_state_error < channel_error_threshold:
        print(f"✓ PASS: Channel volume steady-state error is acceptable (< {channel_error_threshold:,.0f} m³)")
        passed_tests += 1
    else:
        print(f"✗ FAIL: Channel volume steady-state error is too large (>= {channel_error_threshold:,.0f} m³)")
    
    # Stability validation
    if reservoir_variation < reservoir_stability_threshold:
        print(f"✓ PASS: Reservoir level is stable in final 10 steps (< {reservoir_stability_threshold} m variation)")
        passed_tests += 1
    else:
        print(f"✗ FAIL: Reservoir level is still oscillating (>= {reservoir_stability_threshold} m variation)")
    
    if channel_variation < channel_stability_threshold:
        print(f"✓ PASS: Channel volume is stable in final 10 steps (< {channel_stability_threshold:,.0f} m³ variation)")
        passed_tests += 1
    else:
        print(f"✗ FAIL: Channel volume is still oscillating (>= {channel_stability_threshold:,.0f} m³ variation)")
    
    print(f"\n=== Overall Performance: {passed_tests}/{total_tests} tests passed ===")
    
    return {
        'reservoir_steady_state_error': reservoir_steady_state_error,
        'channel_steady_state_error': channel_steady_state_error,
        'reservoir_rmse': reservoir_rmse,
        'channel_rmse': channel_rmse,
        'reservoir_variation': reservoir_variation,
        'channel_variation': channel_variation,
        'tests_passed': passed_tests,
        'total_tests': total_tests
    }

def create_visualization(times, reservoir_levels, channel_volumes, gate1_openings, gate2_openings,
                        reservoir_setpoint, channel_setpoint, viz_config):
    """Create visualization plots."""
    try:
        import matplotlib.pyplot as plt
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot reservoir water level
        ax1.plot(times, reservoir_levels, 'b-', linewidth=2, label='Water Level')
        ax1.axhline(y=reservoir_setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Water Level (m)')
        ax1.set_title('Reservoir Water Level Control')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot channel volume
        ax2.plot(times, channel_volumes, 'g-', linewidth=2, label='Volume')
        ax2.axhline(y=channel_setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Volume (m³)')
        ax2.set_title('Channel Volume Control')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot gate 1 opening (controls reservoir level)
        ax3.plot(times, gate1_openings, 'orange', linewidth=2, label='Gate 1 Opening')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Opening (0-1)')
        ax3.set_title('Gate 1 Opening (Reservoir Control)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot gate 2 opening (controls channel volume)
        ax4.plot(times, gate2_openings, 'purple', linewidth=2, label='Gate 2 Opening')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Opening (0-1)')
        ax4.set_title('Gate 2 Opening (Channel Control)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_file = viz_config.get('output_file', '02_multi_component_results.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nResults plot saved as '{output_file}'")
        
    except ImportError:
        print("\nMatplotlib not available, skipping visualization")

def run_simulation(config_file):
    """Run the simulation using configuration file."""
    print(f"--- Loading Configuration from {config_file} ---")
    config = load_config(config_file)
    
    print("--- Setting up Multi-Component Simulation (Config-driven) ---")
    
    # Create simulation harness
    sim_config = config['simulation']
    harness = SimulationHarness(config=sim_config)
    
    # Create and add components
    components = {}
    for comp_name, comp_config in config['components'].items():
        component = create_component(comp_name, comp_config)
        components[comp_name] = component
        harness.add_component(comp_name, component)
        print(f"Added component: {comp_name} ({comp_config['type']})")
    
    # Add connections
    for connection in config['connections']:
        harness.add_connection(connection['from'], connection['to'])
        print(f"Connected: {connection['from']} -> {connection['to']}")
    
    # Create and add controllers
    for ctrl_name, ctrl_config in config['controllers'].items():
        controller = create_controller(ctrl_name, ctrl_config)
        harness.add_controller(
            controller_id=ctrl_name,
            controller=controller,
            controlled_id=ctrl_config['controlled_component'],
            observed_id=ctrl_config['observed_component'],
            observation_key=ctrl_config['observation_key']
        )
        description = ctrl_config.get('description', '')
        print(f"Added controller: {ctrl_name} ({ctrl_config['type']}) - {description}")
    
    # Finalize setup
    harness.build()
    
    # Run simulation
    print("\n--- Running Simulation ---")
    harness.run_simulation()
    print("\n--- Simulation Complete ---")
    
    # Analyze results
    results = analyze_results(harness, config)
    
    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Run Multi-Component Systems Example with configuration file'
    )
    parser.add_argument(
        '--config',
        default='config.yml',
        help='Configuration file path (default: config.yml)'
    )
    
    args = parser.parse_args()
    
    # Resolve config file path
    config_file = Path(args.config)
    if not config_file.is_absolute():
        config_file = Path(__file__).parent / config_file
    
    if not config_file.exists():
        print(f"Error: Configuration file '{config_file}' not found")
        sys.exit(1)
    
    try:
        results = run_simulation(config_file)
        print(f"\n=== Multi-Component Systems Example Complete ===")
        print(f"Configuration: {config_file}")
        print(f"Performance: {results['tests_passed']}/{results['total_tests']} tests passed")
        
    except Exception as e:
        print(f"Error running simulation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()