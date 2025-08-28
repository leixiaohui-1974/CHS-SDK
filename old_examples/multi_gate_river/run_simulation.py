"""
Runs a multi-gate river simulation from a configuration file.
"""
import json
import os
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from swp.local_agents.control.pid_controller import PIDController
from swp.core_engine.testing.simulation_harness import SimulationHarness

# Map component type strings from JSON to actual Python classes
COMPONENT_CLASS_MAP = {
    "Reservoir": Reservoir,
    "Gate": Gate,
    "RiverChannel": RiverChannel,
}

CONTROLLER_CLASS_MAP = {
    "PIDController": PIDController
}

def run_multi_gate_river_from_config(config_path: str):
    """
    Sets up and runs a simulation using SimulationHarness based on a JSON config,
    including controllers.
    """
    print(f"--- Loading simulation from config file: {config_path} ---")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # 1. Set up the Simulation Harness
    harness = SimulationHarness(config=config['simulation_settings'])

    # 2. Instantiate and add components
    print("\n--- Instantiating Components ---")
    for comp_conf in config['components']:
        CompClass = COMPONENT_CLASS_MAP[comp_conf['type']]
        instance = CompClass(
            name=comp_conf['id'],
            initial_state=comp_conf.get('initial_state', {}),
            parameters=comp_conf.get('params', {})
        )
        harness.add_component(instance)

    # 3. Add connections
    print("\n--- Linking Components ---")
    for conn in config['connections']:
        harness.add_connection(conn['from'], conn['to'])

    # 4. Instantiate and add controllers
    print("\n--- Instantiating Controllers ---")
    for ctrl_conf in config.get('controllers', []):
        CtrlClass = CONTROLLER_CLASS_MAP[ctrl_conf['type']]
        controller = CtrlClass(**ctrl_conf['params'])

        wiring = ctrl_conf['wiring']
        harness.add_controller(
            controller_id=ctrl_conf['id'],
            controller=controller,
            controlled_id=wiring['controlled_id'],
            observed_id=wiring['observed_id'],
            observation_key=wiring['observation_key']
        )

    # 5. Build and run the simulation
    harness.build()
    harness.run_simulation()

    # 6. Save results to JSON
    output_path = os.path.join(os.path.dirname(config_path), "output.json")
    with open(output_path, 'w') as f:
        json.dump(harness.history, f, indent=4)
    print(f"\n--- Results saved to {output_path} ---")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(script_dir, "config.json")
    run_multi_gate_river_from_config(config_file_path)
