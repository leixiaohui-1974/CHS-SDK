"""
End-to-End Example: Branched Network Simulation from a Configuration File.
"""
import json
import os
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
    disturbances = {d['time_step']: d for d in config.get('disturbances', [])}

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
            params['initial_H'] = np.full(num_points, params.pop('initial_H'))
            params['initial_Q'] = np.full(num_points, params.pop('initial_Q'))
        elif comp_type == "GateNode":
            if 'initial_opening' in params:
                initial_opening = params.pop('initial_opening')

        instance = CompClass(name=comp_id, **params)
        if initial_opening is not None:
            instance.set_opening(initial_opening)

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

        if isinstance(from_obj, StVenantReach) and isinstance(to_obj, GateNode):
            to_obj.link_to_reaches(up_obj=from_obj, down_obj=None)
            to_obj.upstream_idx = -1
        elif isinstance(from_obj, GateNode) and isinstance(to_obj, StVenantReach):
            from_obj.link_to_reaches(up_obj=from_obj.upstream_obj, down_obj=to_obj)
            from_obj.downstream_idx = 0
    print("  - Connections established.")

    # --- 5. Set Boundary Conditions from Config ---
    print("\n--- Setting Boundary Conditions ---")
    for bc in config.get('boundary_conditions', []):
        component = components[bc['component_id']]
        solver.add_boundary_condition(component, bc['variable'], bc['index'], lambda t, v=bc['value']: v)
        print(f"  - Set BC for {bc['component_id']}")

    # --- 6. Prepare for Simulation and Data Logging ---
    results = {
        "time": [],
        "components": {comp_id: {"H": [], "Q": []} for comp_id, comp in components.items() if isinstance(comp, StVenantReach)}
    }
    # Add other component types to results if needed

    # --- 7. Run the Simulation ---
    print("\n--- Starting Hydrodynamic Simulation ---")
    for i in range(num_steps):
        current_time = i * solver.dt

        # Apply disturbances from config
        if i in disturbances:
            event = disturbances[i]
            comp_id = event['component_id']
            action = event['action']
            value = event['value']
            if comp_id in components:
                component = components[comp_id]
                if hasattr(component, action):
                    print(f"\n!!! Applying Disturbance at t={current_time:.1f}s: {comp_id}.{action}({value}) !!!\n")
                    getattr(component, action)(value)
                else:
                    print(f"Warning: Action '{action}' not found on component '{comp_id}'")

        solver.step(current_time)

        # Log results
        results["time"].append(current_time)
        for comp_id, comp_data in results["components"].items():
            reach = components[comp_id]
            # Log H and Q at the start, middle, and end of the reach
            num_pts = len(reach.H)
            mid_pt = num_pts // 2
            comp_data["H"].append([float(reach.H[0]), float(reach.H[mid_pt]), float(reach.H[-1])])
            comp_data["Q"].append([float(reach.Q[0]), float(reach.Q[mid_pt]), float(reach.Q[-1])])

    print("\n--- Simulation Finished ---")

    # --- 8. Save Results to JSON ---
    output_path = os.path.join(os.path.dirname(config_path), "output.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"\n--- Results saved to {output_path} ---")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(script_dir, "config.json")
    run_hydrodynamic_network_from_config(config_file_path)
