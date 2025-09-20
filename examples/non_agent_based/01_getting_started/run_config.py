#!/usr/bin/env python3
"""
Configuration-driven version of Getting Started Example.

This script demonstrates how to run the reservoir-gate PID control simulation
using a YAML configuration file, providing a more flexible and maintainable approach.

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
    water_levels = [step['reservoir_1']['water_level'] for step in harness.history]
    gate_openings = [step['gate_1']['opening'] for step in harness.history]
    
    # Get analysis configuration
    analysis_config = config.get('analysis', {})
    sim_config = config.get('simulation', {})
    metrics_config = analysis_config.get('performance_metrics', {})
    
    # Extract thresholds
    setpoint = config['controllers']['pid_controller_1']['parameters']['setpoint']
    steady_state_threshold = metrics_config.get('steady_state_error_threshold', 0.1)
    overshoot_threshold = metrics_config.get('overshoot_threshold', 20)
    settling_time_threshold = metrics_config.get('settling_time_threshold', 50)
    settling_tolerance = metrics_config.get('settling_tolerance', 0.02)
    rmse_threshold = metrics_config.get('rmse_threshold', 0.1)
    max_deviation_threshold = metrics_config.get('max_deviation_threshold', 0.1)
    
    # Calculate performance metrics
    final_water_level = water_levels[-1]
    steady_state_error = abs(final_water_level - setpoint)
    
    # Calculate settling time
    tolerance = settling_tolerance * setpoint
    settling_time = None
    for i, level in enumerate(water_levels):
        if abs(level - setpoint) <= tolerance:
            settling_time = times[i]
            break
    
    # Calculate overshoot
    max_level = max(water_levels)
    reference_level = max(setpoint, water_levels[0])
    overshoot = max(0, max_level - reference_level)
    overshoot_percent = (overshoot / reference_level) * 100 if reference_level != 0 else 0

    # Calculate RMSE and maximum deviation on a settled window
    total_time = times[-1] if times else sim_config.get('duration', sim_config.get('end_time', 0))
    horizon = total_time - times[0] if times else 0

    evaluation_start_time = times[0] + 0.6 * horizon
    if settling_time is not None:
        evaluation_start_time = max(evaluation_start_time, settling_time + 0.1 * horizon)

    start_index = next((i for i, t in enumerate(times) if t >= evaluation_start_time), len(times) - 1)
    settled_levels = water_levels[start_index:] or [water_levels[-1]]

    rmse = math.sqrt(sum((level - setpoint)**2 for level in settled_levels) / len(settled_levels))
    max_deviation = max(abs(level - setpoint) for level in settled_levels)
    
    # Print performance analysis
    print(f"\n=== PID Control Performance Analysis ===")
    print(f"Target water level (setpoint): {setpoint:.2f} m")
    print(f"Initial water level: {water_levels[0]:.2f} m")
    print(f"Final water level: {final_water_level:.2f} m")
    print(f"Steady-state error: {steady_state_error:.4f} m")
    print(f"Maximum overshoot: {overshoot:.4f} m ({overshoot_percent:.2f}%)")
    if settling_time is not None:
        print(f"Settling time ({settling_tolerance*100:.0f}% tolerance): {settling_time:.1f} s")
    else:
        print("System did not settle within simulation time")
    print(f"Root Mean Square Error (RMSE, settled window): {rmse:.4f} m")
    print(f"Maximum absolute deviation (settled window): {max_deviation:.4f} m")
    
    # Create visualization if enabled
    viz_config = analysis_config.get('visualization', {})
    if viz_config.get('enabled', True):
        create_visualization(times, water_levels, gate_openings, setpoint, viz_config)
    
    # Validate control performance
    print("\n=== Control Performance Validation ===")
    
    evaluations = {
        'steady_state_error': (steady_state_error, steady_state_threshold),
        'overshoot_percent': (overshoot_percent, overshoot_threshold),
        'settling_time': (settling_time if settling_time is not None else float('inf'), settling_time_threshold),
        'rmse': (rmse, rmse_threshold),
        'max_deviation': (max_deviation, max_deviation_threshold)
    }

    passed_tests = 0
    for metric, (value, threshold) in evaluations.items():
        label = metric.replace('_', ' ').title()
        if value <= threshold:
            print(f"✓ PASS: {label} = {value:.4f} ≤ {threshold}")
            passed_tests += 1
        else:
            print(f"✗ FAIL: {label} = {value:.4f} > {threshold}")

    total_tests = len(evaluations)
    print(f"\n=== Overall Performance: {passed_tests}/{total_tests} tests passed ===")

    if passed_tests != total_tests:
        raise RuntimeError("Control performance targets were not met")

    return {
        'steady_state_error': steady_state_error,
        'overshoot_percent': overshoot_percent,
        'settling_time': settling_time,
        'rmse': rmse,
        'max_deviation': max_deviation,
        'tests_passed': passed_tests,
        'total_tests': total_tests
    }

def create_visualization(times, water_levels, gate_openings, setpoint, viz_config):
    """Create visualization plots."""
    try:
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot water level
        ax1.plot(times, water_levels, 'b-', linewidth=2, label='Water Level')
        ax1.axhline(y=setpoint, color='r', linestyle='--', linewidth=2, label='Setpoint')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Water Level (m)')
        ax1.set_title('PID Control of Reservoir Water Level')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot gate opening
        ax2.plot(times, gate_openings, 'g-', linewidth=2, label='Gate Opening')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Gate Opening (0-1)')
        ax2.set_title('PID Controller Output (Gate Opening)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_file = viz_config.get('output_file', '01_getting_started_results.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nResults plot saved as '{output_file}'")
        
    except ImportError:
        print("\nMatplotlib not available, skipping visualization")

def run_simulation(config_file):
    """Run the simulation using configuration file."""
    print(f"--- Loading Configuration from {config_file} ---")
    config = load_config(config_file)
    
    print("--- Setting up Getting Started Simulation (Config-driven) ---")
    
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
        print(f"Added controller: {ctrl_name} ({ctrl_config['type']})")
    
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
        description='Run Getting Started Example with configuration file'
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
        print(f"\n=== Getting Started Example Complete ===")
        print(f"Configuration: {config_file}")
        print(f"Performance: {results['tests_passed']}/{results['total_tests']} tests passed")
        
    except Exception as e:
        print(f"Error running simulation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()