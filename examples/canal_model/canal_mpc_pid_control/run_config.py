#!/usr/bin/env python3
"""
Canal MPC+PID Control Example Runner

This script demonstrates a MIMO MPC controller with PID cascade control for canal systems.
The system uses a centralized MPC controller to coordinate multiple PID controllers
that manage individual gates, providing optimal water level control under disturbances.

Usage:
    python run_config.py [--config CONFIG_FILE] [--agents AGENTS_FILE] [--output OUTPUT_FILE]
    
Examples:
    # Run with default configuration (MPC controls flow setpoints)
    python run_config.py
    
    # Run with level control configuration (MPC controls water levels directly)
    python run_config.py --agents agents_level_control.yml
    
    # Run with custom output file
    python run_config.py --output my_results.yml
"""

import sys
import os
import argparse
import yaml
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.io.yaml_writer import save_history_to_yaml

def load_configuration(config_file: str, agents_file: str = "agents.yml") -> tuple:
    """Load configuration files for the simulation."""
    config_path = Path(config_file)
    agents_path = Path(agents_file)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    if not agents_path.exists():
        raise FileNotFoundError(f"Agents file not found: {agents_file}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    with open(agents_path, 'r', encoding='utf-8') as f:
        agents_config = yaml.safe_load(f)
    
    return config, agents_config

def run_simulation(scenario_path: str, agents_file: str = "agents.yml") -> Any:
    """Run the MPC+PID control simulation."""
    print(f"--- Loading Canal MPC+PID Control Scenario ---")
    print(f"Scenario path: {scenario_path}")
    print(f"Agents file: {agents_file}")
    
    # Initialize the loader
    loader = YamlSimulationLoader(scenario_path=scenario_path, agents_file=agents_file)
    
    # Load the simulation harness
    harness = loader.load()
    
    print("--- Running Simulation ---")
    harness.run_mas_simulation()
    
    print("--- Simulation Complete ---")
    return harness

def analyze_mpc_pid_performance(harness: Any, config: Dict, agents_config: Dict) -> Dict[str, Any]:
    """Analyze the performance of the MPC+PID control system."""
    print("\n--- Analyzing MPC+PID Control Performance ---")
    
    if not harness.history:
        print("Warning: No simulation history available for analysis")
        return {}
    
    # Extract data from simulation history
    times = [step['time'] for step in harness.history]
    canal_levels = [step.get('canal_1', {}).get('water_level', 0) for step in harness.history]
    gate1_openings = [step.get('gate_1', {}).get('opening', 0) for step in harness.history]
    gate2_openings = [step.get('gate_2', {}).get('opening', 0) for step in harness.history]
    gate1_flows = [step.get('gate_1', {}).get('outflow', 0) for step in harness.history]
    gate2_flows = [step.get('gate_2', {}).get('outflow', 0) for step in harness.history]
    
    # Get target water level from MPC configuration
    target_level = 5.0  # Default target
    for agent in agents_config.get('agents', []):
        if agent.get('id') == 'central_mpc_agent':
            target_level = agent.get('config', {}).get('controller_config', {}).get('config', {}).get('objective_config', {}).get('target_level', 5.0)
            break
    
    # Calculate performance metrics
    final_level = canal_levels[-1] if canal_levels else 0
    steady_state_error = abs(final_level - target_level)
    
    # Calculate RMSE
    rmse = math.sqrt(sum((level - target_level)**2 for level in canal_levels) / len(canal_levels)) if canal_levels else 0
    
    # Calculate settling time (within 2% of target)
    tolerance = 0.02 * target_level
    settling_time = None
    for i, level in enumerate(canal_levels):
        if abs(level - target_level) <= tolerance:
            settling_time = times[i]
            break
    
    # Calculate overshoot
    max_level = max(canal_levels) if canal_levels else 0
    overshoot = max(0, max_level - target_level)
    overshoot_percent = (overshoot / target_level) * 100 if target_level != 0 else 0
    
    # Calculate control effort (sum of absolute gate opening changes)
    gate1_effort = sum(abs(gate1_openings[i] - gate1_openings[i-1]) for i in range(1, len(gate1_openings)))
    gate2_effort = sum(abs(gate2_openings[i] - gate2_openings[i-1]) for i in range(1, len(gate2_openings)))
    total_effort = gate1_effort + gate2_effort
    
    # Print performance analysis
    print(f"\n=== MPC+PID Control Performance Analysis ===")
    print(f"Target water level: {target_level:.2f} m")
    print(f"Initial water level: {canal_levels[0]:.2f} m" if canal_levels else "N/A")
    print(f"Final water level: {final_level:.2f} m")
    print(f"Steady-state error: {steady_state_error:.4f} m")
    print(f"Maximum overshoot: {overshoot:.4f} m ({overshoot_percent:.2f}%)")
    if settling_time is not None:
        print(f"Settling time (2% tolerance): {settling_time:.1f} s")
    else:
        print("System did not settle within simulation time")
    print(f"Root Mean Square Error (RMSE): {rmse:.4f} m")
    print(f"Total control effort: {total_effort:.4f}")
    print(f"Gate 1 control effort: {gate1_effort:.4f}")
    print(f"Gate 2 control effort: {gate2_effort:.4f}")
    
    # Validate control performance
    print("\n=== Control Performance Validation ===")
    
    passed_tests = 0
    total_tests = 4
    
    # Test 1: Steady-state error
    if steady_state_error < 0.1:
        print("✓ PASS: Steady-state error is acceptable (< 0.1 m)")
        passed_tests += 1
    else:
        print("✗ FAIL: Steady-state error is too large (>= 0.1 m)")
    
    # Test 2: Overshoot
    if overshoot_percent < 10:
        print("✓ PASS: Overshoot is acceptable (< 10%)")
        passed_tests += 1
    else:
        print("✗ FAIL: Overshoot is too large (>= 10%)")
    
    # Test 3: Settling time
    if settling_time is not None and settling_time < 1000:
        print("✓ PASS: Settling time is acceptable (< 1000 s)")
        passed_tests += 1
    else:
        print("✗ FAIL: Settling time is too long or system did not settle")
    
    # Test 4: Control stability (no excessive oscillations)
    if total_effort < 50:
        print("✓ PASS: Control effort is reasonable (< 50)")
        passed_tests += 1
    else:
        print("✗ FAIL: Control effort is excessive (>= 50)")
    
    print(f"\n=== Overall Performance: {passed_tests}/{total_tests} tests passed ===")
    
    return {
        'target_level': target_level,
        'final_level': final_level,
        'steady_state_error': steady_state_error,
        'overshoot_percent': overshoot_percent,
        'settling_time': settling_time,
        'rmse': rmse,
        'total_effort': total_effort,
        'gate1_effort': gate1_effort,
        'gate2_effort': gate2_effort,
        'tests_passed': passed_tests,
        'total_tests': total_tests
    }

def create_visualization(harness: Any, output_file: str = "canal_mpc_pid_results.png"):
    """Create visualization plots for the MPC+PID control results."""
    try:
        import matplotlib.pyplot as plt
        
        if not harness.history:
            print("No simulation history available for visualization")
            return
        
        # Extract data
        times = [step['time'] for step in harness.history]
        canal_levels = [step.get('canal_1', {}).get('water_level', 0) for step in harness.history]
        gate1_openings = [step.get('gate_1', {}).get('opening', 0) for step in harness.history]
        gate2_openings = [step.get('gate_2', {}).get('opening', 0) for step in harness.history]
        gate1_flows = [step.get('gate_1', {}).get('outflow', 0) for step in harness.history]
        gate2_flows = [step.get('gate_2', {}).get('outflow', 0) for step in harness.history]
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Plot 1: Canal water level
        ax1.plot(times, canal_levels, 'b-', linewidth=2, label='Canal Water Level')
        ax1.axhline(y=5.0, color='r', linestyle='--', linewidth=2, label='Target Level')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Water Level (m)')
        ax1.set_title('Canal Water Level Control')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Gate openings
        ax2.plot(times, gate1_openings, 'g-', linewidth=2, label='Gate 1 Opening')
        ax2.plot(times, gate2_openings, 'm-', linewidth=2, label='Gate 2 Opening')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Gate Opening (0-1)')
        ax2.set_title('Gate Control Actions')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Gate flows
        ax3.plot(times, gate1_flows, 'g-', linewidth=2, label='Gate 1 Flow')
        ax3.plot(times, gate2_flows, 'm-', linewidth=2, label='Gate 2 Flow')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Flow Rate (m³/s)')
        ax3.set_title('Gate Flow Rates')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Control error
        target_level = 5.0
        errors = [level - target_level for level in canal_levels]
        ax4.plot(times, errors, 'r-', linewidth=2, label='Control Error')
        ax4.axhline(y=0, color='k', linestyle='-', linewidth=1, alpha=0.5)
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Error (m)')
        ax4.set_title('Water Level Control Error')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nResults plot saved as '{output_file}'")
        
    except ImportError:
        print("\nMatplotlib not available, skipping visualization")
    except Exception as e:
        print(f"\nError creating visualization: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Run Canal MPC+PID Control Example',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration (MPC controls flow setpoints)
  python run_config.py
  
  # Run with level control configuration (MPC controls water levels directly)
  python run_config.py --agents agents_level_control.yml
  
  # Run with custom output file
  python run_config.py --output my_results.yml
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.yml',
        help='Configuration file path (default: config.yml)'
    )
    parser.add_argument(
        '--agents',
        default='agents.yml',
        help='Agents configuration file (default: agents.yml)'
    )
    parser.add_argument(
        '--output',
        default='output.yml',
        help='Output file for simulation results (default: output.yml)'
    )
    parser.add_argument(
        '--plot',
        default='canal_mpc_pid_results.png',
        help='Output file for visualization plot (default: canal_mpc_pid_results.png)'
    )
    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Skip creating visualization plot'
    )
    
    args = parser.parse_args()
    
    # Resolve file paths
    script_dir = Path(__file__).parent
    config_file = script_dir / args.config
    agents_file = script_dir / args.agents
    output_file = script_dir / args.output
    plot_file = script_dir / args.plot
    
    try:
        # Load configuration
        config, agents_config = load_configuration(str(config_file), str(agents_file))
        
        # Run simulation
        harness = run_simulation(str(script_dir), str(agents_file))
        
        # Save results
        save_history_to_yaml(harness.history, str(output_file))
        print(f"Simulation results saved to: {output_file}")
        
        # Analyze performance
        results = analyze_mpc_pid_performance(harness, config, agents_config)
        
        # Create visualization
        if not args.no_plot:
            create_visualization(harness, str(plot_file))
        
        print(f"\n=== Canal MPC+PID Control Example Complete ===")
        print(f"Configuration: {config_file}")
        print(f"Agents: {agents_file}")
        print(f"Output: {output_file}")
        if not args.no_plot:
            print(f"Plot: {plot_file}")
        print(f"Performance: {results.get('tests_passed', 0)}/{results.get('total_tests', 0)} tests passed")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
