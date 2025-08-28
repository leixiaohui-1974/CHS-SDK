"""
End-to-End Example: Branched Network Simulation from a Configuration File.
"""
import json
import numpy as np
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach
from swp.simulation_identification.hydro_nodes.gate_node import GateNode
from swp.core_engine.solver.network_solver import NetworkSolver

# Map component type strings from JSON to actual Python classes
COMPONENT_CLASS_MAP = {
    "StVenantReach": StVenantReach,
    "GateNode": GateNode,
}

def run_hydrodynamic_network_from_config(config_path: str):
    """
    Sets up and runs a network simulation based on a JSON configuration file.
    """
    print(f"--- Loading simulation from config file: {config_path} ---")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # --- 1. Define Simulation Parameters from Config ---
    settings = config['simulation_settings']
    sim_dt = settings['dt']
    sim_theta = settings['theta']
    num_steps = settings['num_steps']

    # --- 2. Instantiate Components Dynamically ---
    print("\n--- Instantiating Components ---")
    components = {}
    for comp_conf in config['components']:
        comp_id = comp_conf['id']
        comp_type = comp_conf['type']
        params = comp_conf['params']

        if comp_type not in COMPONENT_CLASS_MAP:
            raise ValueError(f"Unknown component type '{comp_type}' in config.")

        CompClass = COMPONENT_CLASS_MAP[comp_type]

        # Special handling for component parameters before instantiation
        initial_opening = None
        if comp_type == "StVenantReach":
            num_points = params['num_points']
            # Create numpy arrays for initial H and Q
            params['initial_H'] = np.full(num_points, params.pop('initial_H'))
            params['initial_Q'] = np.full(num_points, params.pop('initial_Q'))
        elif comp_type == "GateNode":
            # Pop 'initial_opening' as it's not a constructor argument.
            # It will be handled by a separate set_opening() call later.
            if 'initial_opening' in params:
                initial_opening = params.pop('initial_opening')

        instance = CompClass(name=comp_id, **params)
        components[comp_id] = instance
        print(f"  - Created {comp_type}: {comp_id}")

    # --- 3. Create and Configure the Solver ---
    solver = NetworkSolver(dt=sim_dt, theta=sim_theta)
    for comp in components.values():
        solver.add_component(comp)

    # --- 4. Link Components Dynamically ---
    print("\n--- Linking Components ---")
    for conn in config['connections']:
        from_id = conn['from']
        to_id = conn['to']

        from_obj = components[from_id]
        to_obj = components[to_id]

        # This logic assumes a simple chain: Reach -> Node -> Reach
        # More complex logic would be needed for Junctions etc.
        if isinstance(from_obj, StVenantReach) and isinstance(to_obj, GateNode):
            to_obj.link_to_reaches(up_obj=from_obj, down_obj=None)
            to_obj.upstream_idx = -1
            print(f"  - Linked {from_id} (upstream) to {to_id}")
        elif isinstance(from_obj, GateNode) and isinstance(to_obj, StVenantReach):
            from_obj.link_to_reaches(up_obj=from_obj.upstream_obj, down_obj=to_obj)
            from_obj.downstream_idx = 0
            print(f"  - Linked {from_id} (downstream) to {to_id}")
        else:
            print(f"  - WARNING: Don't know how to connect {from_id} to {to_id}. Skipping.")

    # --- 5. Set Boundary Conditions from Config ---
    print("\n--- Setting Boundary Conditions ---")
    for bc in config.get('boundary_conditions', []):
        comp_id = bc['component_id']
        variable = bc['variable']
        index = bc['index']
        value = bc['value'] # For now, we only support constant values

        if comp_id in components:
            component = components[comp_id]
            # The lambda captures the 'value' from this loop iteration
            solver.add_boundary_condition(component, variable, index, lambda t, v=value: v)
            print(f"  - Set BC for {comp_id}: {variable}[{index}] = {value}")
        else:
            print(f"  - WARNING: Component '{comp_id}' for BC not found.")

    # Set initial gate opening if specified
    gate_conf = next((c for c in config['components'] if c['type'] == 'GateNode'), None)
    if gate_conf and 'initial_opening' in gate_conf['params']:
        gate_id = gate_conf['id']
        opening = gate_conf['params']['initial_opening']
        components[gate_id].set_opening(opening)
        print(f"  - Set initial opening for {gate_id} to {opening}")


    # --- 6. Run the Simulation ---
    print("\n--- Starting Hydrodynamic Simulation ---")
    for i in range(num_steps):
        current_time = i * solver.dt
        print(f"\n--- Time Step {i+1}/{num_steps} (t={current_time:.1f}s) ---")

        # Example of a manual intervention during the run (can be moved to config later)
        if i == 5:
            gate_id = 'gate1'
            if gate_id in components:
                print("\n!!! CLOSING GATE FURTHER !!!\n")
                components[gate_id].set_opening(0.2)

        solver.step(current_time)

        # Print state of the reaches for monitoring
        reach1 = components.get('reach1')
        reach2 = components.get('reach2')
        if reach1:
            print(f"  Reach 1: H_start={reach1.H[0]:.3f}, H_end={reach1.H[-1]:.3f} | Q_end={reach1.Q[-1]:.3f}")
        if reach2:
            print(f"  Reach 2: H_start={reach2.H[0]:.3f}, H_end={reach2.H[-1]:.3f} | Q_start={reach2.Q[0]:.3f}")

    print("\n--- Simulation Finished ---")


if __name__ == "__main__":
    # The script now requires a path to a config file to run.
    # This makes it reusable for any compatible simulation scenario.
    config_file_path = "data/simulation_cases/branched_canal_network.json"
    run_hydrodynamic_network_from_config(config_file_path)
