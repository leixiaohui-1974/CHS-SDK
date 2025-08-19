"""
End-to-End Example: A Data-Driven Simulation

This script demonstrates how to drive a simulation using external data from a CSV file.
"""
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.data_access.csv_data_source import CsvDataSourceAgent

def run_data_driven_example():
    """
    Sets up and runs the data-driven simulation.
    """
    print("--- Setting up the Data-Driven Simulation Example ---")

    # 1. Simulation and Communication Setup
    # Run for 2 days to match the data in the CSV
    simulation_config = {'duration': 172800, 'dt': 3600.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. Define the topic for our external data
    DATA_TOPIC = "data.inflow.observed"

    # 3. Create the Data Source Agent
    # This agent will read the CSV and publish inflow values to the DATA_TOPIC
    csv_agent = CsvDataSourceAgent(
        agent_id="csv_inflow_agent",
        message_bus=message_bus,
        csv_filepath="data/observed_inflow.csv",
        publish_topic=DATA_TOPIC
    )

    # 4. Create the Physical Components
    # The reservoir is subscribed to the DATA_TOPIC to receive its inflow
    reservoir = Reservoir(
        name="data_driven_reservoir",
        initial_state={'volume': 5e6, 'water_level': 10.0},
        parameters={'surface_area': 5e5},
        message_bus=message_bus,
        inflow_topic=DATA_TOPIC
    )

    # A simple gate downstream to allow for some outflow
    gate = Gate(
        name="outflow_gate",
        initial_state={'opening': 0.5}, # Fixed opening
        parameters={'width': 10, 'discharge_coefficient': 0.6}
    )

    # 5. Add components and agents to the harness
    harness.add_component(reservoir)
    harness.add_component(gate)
    harness.add_agent(csv_agent)

    # 6. Define topology and build
    harness.add_connection("data_driven_reservoir", "outflow_gate")
    harness.build()

    # 7. Run the MAS simulation
    harness.run_mas_simulation()

    print("\n--- FINAL SIMULATION STATE ---")
    final_states = {cid: comp.get_state() for cid, comp in harness.components.items()}
    for cid, state in final_states.items():
        state_str = ", ".join(f"{k}={v:.2f}" for k, v in state.items())
        print(f"  {cid}: {state_str}")

if __name__ == "__main__":
    run_data_driven_example()
