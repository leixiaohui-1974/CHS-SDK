import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swp.core_engine.solver.network_solver import NetworkSolver
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach
from swp.simulation_identification.hydro_nodes.turbine_node import TurbineNode
from swp.simulation_identification.hydro_nodes.gate_node import GateNode

# Component Mapping for Network Solver
NET_COMPONENT_MAP = {
    "StVenantReach": StVenantReach,
    "TurbineNode": TurbineNode,
    "GateNode": GateNode
}

def run_network_simulation(config_path):
    """
    Builds and runs a NetworkSolver-based simulation from a JSON config file.
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Network Solver Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {config.get('description', 'No description provided.')} ---")

    all_results = {}

    # Iterate through each simulation defined in the config
    for sim_config in config.get('simulations', []):
        sim_name = sim_config['name']
        print(f"\n--- Setting up Simulation: {sim_name} ---")

        # 1. Initialize Solver
        sim_settings = sim_config['simulation_settings']
        solver = NetworkSolver(dt=sim_settings['dt'], theta=0.8)
        num_steps = sim_settings['num_steps']

        # 2. Instantiate Components
        components = {}
        for comp_config in sim_config.get('components', []):
            comp_type = comp_config.pop('type')
            comp_name = comp_config['name']

            # Handle special initial conditions for StVenantReach
            if comp_type == "StVenantReach":
                num_points = comp_config['params']['num_points']
                initial_H = np.full(num_points, comp_config.pop('initial_H'))
                initial_Q = np.full(num_points, comp_config.pop('initial_Q'))
                comp_config['initial_H'] = initial_H
                comp_config['initial_Q'] = initial_Q

            cls = NET_COMPONENT_MAP.get(comp_type)
            if cls:
                components[comp_name] = cls(name=comp_name, **comp_config['params'])
                if 'initial_H' in comp_config: # For reaches
                    components[comp_name].H = comp_config['initial_H']
                    components[comp_name].Q = comp_config['initial_Q']
                solver.add_component(components[comp_name])
            else:
                print(f"Warning: Component type '{comp_type}' not found in NET_COMPONENT_MAP.")

        # 3. Add Connections
        for conn in sim_config.get('connections', []):
            node = components[conn['node']]
            up_obj = components[conn['upstream']]
            down_obj = components[conn['downstream']]
            node.link_to_reaches(up_obj=up_obj, down_obj=down_obj)

        # 4. Add Boundary Conditions
        for bc in sim_config.get('boundary_conditions', []):
            comp = components[bc['component']]
            var = bc['variable']
            idx = bc['index']
            bc_type = bc['type']

            # Map bc_type string to a lambda function
            if bc_type == 'constant':
                func = lambda t, v=bc['value']: v
            elif bc_type == 'linearly_rising':
                total_time = num_steps * solver.dt
                func = lambda t, s=bc['start_value'], e=bc['end_value'], tt=total_time: s + (e - s) * (t / tt)
            else:
                print(f"Warning: Unknown boundary condition type '{bc_type}'. Skipping.")
                continue
            solver.add_boundary_condition(comp, var, idx, func)

        # 5. Simulation Loop
        results = {'time': [], 'H_up': [], 'H_down': [], 'Q': []}
        events = sorted(sim_config.get('scenario_events', []), key=lambda e: e['time'])
        event_idx = 0

        print(f"--- Starting {sim_name} ---")
        for i in range(num_steps):
            current_time = i * solver.dt

            # Handle events
            if event_idx < len(events) and current_time >= events[event_idx]['time']:
                event = events[event_idx]
                if event['type'] == 'set_opening':
                    print(f"!!! Event at t={current_time}s: Setting opening for {event['target']} to {event['value']} !!!")
                    components[event['target']].set_opening(event['value'])
                event_idx += 1

            solver.step(current_time)

            # Record results (assuming a simple forebay -> node -> tailrace structure)
            forebay = next(c for c in components.values() if "forebay" in c.name)
            tailrace = next(c for c in components.values() if "tailrace" in c.name)
            results['time'].append(current_time)
            results['H_up'].append(forebay.H[-1])
            results['H_down'].append(tailrace.H[0])
            results['Q'].append(forebay.Q[-1])

        all_results[sim_name] = results
        print(f"--- {sim_name} Finished ---")

    # 6. Plotting
    output_settings = config.get('output_settings', {})
    if 'plot_file' in output_settings:
        plot_file = output_settings['plot_file']
        fig, axes = plt.subplots(len(all_results), 1, figsize=(12, 6 * len(all_results)), sharex=True)
        if len(all_results) == 1: axes = [axes] # Ensure axes is always a list

        fig.suptitle(config.get('description', 'Simulation Results'), fontsize=16)

        for ax, (sim_name, results) in zip(axes, all_results.items()):
            ax.plot(results['time'], results['H_up'], 'b-', label='Upstream Head')
            ax.plot(results['time'], results['H_down'], 'b--', label='Downstream Head')
            ax_twin = ax.twinx()
            ax_twin.plot(results['time'], results['Q'], 'c-', label='Flow (Q)', alpha=0.7)
            ax.set_ylabel('Water Level (m)')
            ax_twin.set_ylabel('Flow (m^3/s)')
            ax.set_title(sim_name.replace('_', ' ').title())
            ax.grid(True)
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax_twin.get_legend_handles_labels()
            ax_twin.legend(lines + lines2, labels + labels2, loc='upper right')

        plt.xlabel('Time (s)')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(plot_file)
        print(f"\nSaved combined plot to {plot_file}")
        # plt.show() # Disabled for non-interactive environments

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_file_path = sys.argv[1]
    else:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>")
        sys.exit(1)

    run_network_simulation(config_file_path)
