"""
Runs a pipe simulation example from a configuration file.
"""
import json
import os
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.core_engine.testing.simulation_harness import SimulationHarness

# Map component type strings from JSON to actual Python classes
COMPONENT_CLASS_MAP = {
    "Reservoir": Reservoir,
    "Pipe": Pipe,
    "Gate": Gate,
}

def run_pipe_simulation_from_config(config_path: str):
    """
    Sets up and runs a simulation using SimulationHarness based on a JSON config.
    """
    print(f"--- Loading simulation from config file: {config_path} ---")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # 1. Set up the Simulation Harness
    harness = SimulationHarness(config=config['simulation_settings'])

    # 2. Instantiate and add components dynamically
    print("\n--- Instantiating Components ---")
    for comp_conf in config['components']:
        comp_id = comp_conf['id']
        comp_type = comp_conf['type']

        if comp_type not in COMPONENT_CLASS_MAP:
            raise ValueError(f"Unknown component type '{comp_type}' in config.")

        CompClass = COMPONENT_CLASS_MAP[comp_type]

        instance = CompClass(
            name=comp_id,
            initial_state=comp_conf.get('initial_state', {}),
            parameters=comp_conf.get('params', {})
        )
        harness.add_component(instance)

    # 3. Add connections
    print("\n--- Linking Components ---")
    for conn in config['connections']:
        harness.add_connection(conn['from'], conn['to'])

    # 4. Build and run the simulation
    harness.build()
    harness.run_simulation()

    # 5. Save results to JSON
    output_path = os.path.join(os.path.dirname(config_path), "output.json")
    # The harness stores results in its `history` attribute
    with open(output_path, 'w') as f:
        # Use a custom serializer to handle non-serializable objects if necessary
        # For now, assuming states are dicts of primitives
        json.dump(harness.history, f, indent=4)
    print(f"\n--- Results saved to {output_path} ---")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(script_dir, "config.json")
    run_pipe_simulation_from_config(config_file_path)
