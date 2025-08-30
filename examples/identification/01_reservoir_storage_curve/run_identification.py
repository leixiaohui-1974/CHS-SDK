import sys
from pathlib import Path
import yaml
import numpy as np

# Add the project root to the Python path to allow imports from core_lib
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.data_access.csv_inflow_agent import CsvInflowAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.identification.identification_agent import ParameterIdentificationAgent
from core_lib.identification.model_updater_agent import ModelUpdaterAgent

def print_curve_comparison(title, true_curve, initial_curve, final_curve):
    """Helper function to print a comparison of the storage curves."""
    print("-" * 65)
    print(title)
    print("-" * 65)
    print(f"{'Volume (m^3)':<15} | {'True Level (m)':<15} | {'Initial Level (m)':<18} | {'Final Level (m)':<15}")
    print("-" * 65)
    for i in range(len(true_curve)):
        vol = true_curve[i][0]
        true_level = true_curve[i][1]
        initial_level = initial_curve[i][1]
        final_level = final_curve[i][1]
        print(f"{vol:<15.1e} | {true_level:<15.2f} | {initial_level:<18.2f} | {final_level:<15.2f}")
    print("-" * 65)

def plot_curves(true_curve, initial_curve, final_curve):
    """Plots the storage curves for visual comparison."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nMatplotlib not found. Skipping plot.")
        return

    true_vols = true_curve[:, 0]
    true_levels = true_curve[:, 1]
    initial_levels = initial_curve[:, 1]
    final_levels = final_curve[:, 1]

    plt.figure(figsize=(10, 6))
    plt.plot(true_vols, true_levels, 'g-o', label='True Curve', linewidth=3, markersize=8)
    plt.plot(true_vols, initial_levels, 'r--x', label='Initial Guess', markersize=8)
    plt.plot(true_vols, final_levels, 'b-^', label='Identified Curve')

    plt.title('Storage Curve Identification Results')
    plt.xlabel('Volume (m^3)')
    plt.ylabel('Water Level (m)')
    plt.legend()
    plt.grid(True)

    output_path = "identification_results.png"
    plt.savefig(output_path)
    print(f"\nPlot saved to {output_path}")

def main():
    """
    Main function to run the reservoir identification scenario.
    """
    print("Starting reservoir storage curve identification example...")

    scenario_path = Path(__file__).parent

    # --- 1. Load Configuration from YAML Files ---
    with open(scenario_path / 'config.yml', 'r') as f:
        config = yaml.safe_load(f)
    with open(scenario_path / 'components.yml', 'r') as f:
        components_config = yaml.safe_load(f)
    with open(scenario_path / 'agents.yml', 'r') as f:
        agents_config = yaml.safe_load(f)

    # --- 2. Manually Instantiate Objects ---
    bus = MessageBus()

    # Create components
    true_res_conf = components_config['true_reservoir']
    true_reservoir = Reservoir(
        name='true_reservoir',
        initial_state=true_res_conf['initial_state'],
        parameters=true_res_conf['parameters'],
        message_bus=bus
    )

    twin_res_conf = components_config['twin_reservoir']
    twin_reservoir = Reservoir(
        name='twin_reservoir',
        initial_state=twin_res_conf['initial_state'],
        parameters=twin_res_conf['parameters'],
        message_bus=bus
    )

    components = [true_reservoir, twin_reservoir]

    # Create agents
    inflow_agent_conf = agents_config['inflow_agent']['parameters']
    inflow_agent = CsvInflowAgent(
        agent_id='inflow_agent',
        message_bus=bus,
        target_component=true_reservoir,
        inflow_topic=inflow_agent_conf['topic'],
        csv_file_path=str(scenario_path / inflow_agent_conf['filepath']),
        time_column=inflow_agent_conf['time_column'],
        data_column=inflow_agent_conf['data_column']
    )

    obs_agent_conf = agents_config['observation_agent']['parameters']
    observation_agent = DigitalTwinAgent(
        agent_id='observation_agent',
        message_bus=bus,
        simulated_object=true_reservoir,
        state_topic=obs_agent_conf['publish_topic']
    )

    twin_perc_agent_conf = agents_config['twin_perception_agent']['parameters']
    twin_perception_agent = DigitalTwinAgent(
        agent_id='twin_perception_agent',
        message_bus=bus,
        simulated_object=twin_reservoir,
        state_topic=twin_perc_agent_conf['publish_topic']
    )

    id_agent_conf = agents_config['identification_agent']['parameters']
    identification_agent = ParameterIdentificationAgent(
        agent_id='identification_agent',
        target_model=twin_reservoir,
        message_bus=bus,
        config=id_agent_conf
    )

    all_models_dict = {comp.name: comp for comp in components}
    model_updater = ModelUpdaterAgent(
        agent_id='model_updater',
        message_bus=bus,
        parameter_topic=f"identified_parameters/{id_agent_conf['target_model']}",
        models=all_models_dict
    )

    agents = [inflow_agent, observation_agent, twin_perception_agent, identification_agent, model_updater]

    # --- 3. Store Initial Parameters for Comparison ---
    true_curve = np.array(true_reservoir.get_parameters()['storage_curve'])
    initial_twin_curve = np.array(twin_reservoir.get_parameters()['storage_curve'])

    # --- 4. Initialize and Run Simulation Harness ---
    print("\nInitializing simulation harness...")
    # Correctly initialize the harness
    harness = SimulationHarness(config=config['simulation'])
    harness.message_bus = bus # Share the same message bus

    # Add components and agents to the harness
    for comp in components:
        harness.add_component(comp)
    for agent in agents:
        harness.add_agent(agent)

    # Build the harness (for topological sort, etc.)
    harness.build()

    print("Running MAS simulation...")
    harness.run_mas_simulation()
    print("Simulation finished.")

    # --- 5. Get Final Parameters and Show Results ---
    final_twin_curve = np.array(twin_reservoir.get_parameters()['storage_curve'])

    print("\nIdentification process complete. Comparing results...")
    print_curve_comparison(
        "Reservoir Storage Curve Identification",
        true_curve,
        initial_twin_curve,
        final_twin_curve
    )

    # --- 6. Plot Results for Visual Inspection ---
    plot_curves(true_curve, initial_twin_curve, final_twin_curve)


if __name__ == "__main__":
    main()
