import sys
from pathlib import Path
import yaml
import numpy as np

# Add project root to Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core.interfaces import Agent
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pipe import Pipe
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.identification.identification_agent import ParameterIdentificationAgent
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

def main():
    """
    Main function to run the pipe roughness identification scenario.
    """
    print("Starting pipe roughness (Manning's n) identification example...")

    scenario_path = Path(__file__).parent

    # --- 1. Load Configuration ---
    with open(scenario_path / 'config.yml', 'r') as f:
        config = yaml.safe_load(f)
    with open(scenario_path / 'components.yml', 'r') as f:
        components_config = yaml.safe_load(f)
    with open(scenario_path / 'agents.yml', 'r') as f:
        agents_config = yaml.safe_load(f)
    with open(scenario_path / 'topology.yml', 'r') as f:
        topology_config = yaml.safe_load(f)

    # --- 2. Manually Instantiate Objects ---
    bus = MessageBus()

    # Create components
    up_res_conf = components_config['upstream_reservoir']
    upstream_reservoir = Reservoir(name='upstream_reservoir',
                                   initial_state=up_res_conf['initial_state'],
                                   parameters=up_res_conf['parameters'])

    down_res_conf = components_config['downstream_reservoir']
    downstream_reservoir = Reservoir(name='downstream_reservoir',
                                     initial_state=down_res_conf['initial_state'],
                                     parameters=down_res_conf['parameters'])

    true_pipe_conf = components_config['true_pipe']
    true_pipe = Pipe(name='true_pipe',
                     initial_state=true_pipe_conf['initial_state'],
                     parameters=true_pipe_conf['parameters'])

    twin_pipe_conf = components_config['twin_pipe']
    twin_pipe = Pipe(name='twin_pipe',
                     initial_state=twin_pipe_conf['initial_state'],
                     parameters=twin_pipe_conf['parameters'])

    components = [upstream_reservoir, downstream_reservoir, true_pipe, twin_pipe]

    # Create agents
    agents = []
    all_models = {c.name: c for c in components}

    up_obs_conf = agents_config['upstream_observer']['parameters']
    agents.append(DigitalTwinAgent('upstream_observer', all_models[up_obs_conf['target_model']], bus, up_obs_conf['publish_topic']))

    down_obs_conf = agents_config['downstream_observer']['parameters']
    agents.append(DigitalTwinAgent('downstream_observer', all_models[down_obs_conf['target_model']], bus, down_obs_conf['publish_topic']))

    pipe_obs_conf = agents_config['pipe_observer']['parameters']
    agents.append(DigitalTwinAgent('pipe_observer', all_models[pipe_obs_conf['target_model']], bus, pipe_obs_conf['publish_topic']))

    id_agent_conf = agents_config['identification_agent']['parameters']
    agents.append(ParameterIdentificationAgent('identification_agent', twin_pipe, bus, id_agent_conf))

    updater_conf = agents_config['model_updater']['parameters']
    agents.append(ModelUpdaterAgent('model_updater', bus, f"identified_parameters/{updater_conf['target_model_name']}", all_models))

    # --- 3. Store Initial Parameters for Comparison ---
    true_n = true_pipe.get_parameters()['manning_n']
    initial_twin_n = twin_pipe.get_parameters()['manning_n']

    # --- 4. Initialize and Run Simulation Harness ---
    print("\nInitializing simulation harness...")
    harness = SimulationHarness(config=config['simulation'])
    harness.message_bus = bus

    for comp in components:
        harness.add_component(comp)
    for link in topology_config.get('links', []):
        harness.add_connection(link['upstream'], link['downstream'])
    for agent in agents:
        harness.add_agent(agent)

    harness.build()

    print("Running MAS simulation...")
    harness.run_mas_simulation()
    print("Simulation finished.")

    # --- 5. Get Final Parameters and Show Results ---
    final_twin_n = twin_pipe.get_parameters()['manning_n']

    print("\nIdentification process complete. Comparing results...")
    print("-" * 50)
    print("Pipe Roughness (Manning's n) Identification")
    print("-" * 50)
    print(f"True Value:      {true_n:.6f}")
    print(f"Initial Guess:   {initial_twin_n:.6f}")
    print(f"Final Identified:{final_twin_n:.6f}")
    print("-" * 50)

if __name__ == "__main__":
    main()
