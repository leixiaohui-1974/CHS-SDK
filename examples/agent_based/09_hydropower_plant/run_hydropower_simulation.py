import sys
import os
from pathlib import Path

# Add the project root to the Python path
# This is not best practice, but it's a simple way to make the example runnable
# without having to install the project as a package.
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from core_lib.core.interfaces import State
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def run_hydropower_simulation():
    """
    This function sets up and runs a simulation of a simple hydropower plant.
    """
    print("--- Setting up Hydropower Plant Simulation ---")

    # 1. Create the simulation harness
    simulation_config = {'duration': 10, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. Create the physical components
    # An upstream reservoir with a high water level
    source_res = Reservoir(
        name="source_res",
        initial_state={'water_level': 100.0, 'volume': 1e7, 'outflow': 0},
        parameters={'surface_area': 1e5}
    )

    # A downstream reservoir with a lower water level
    downstream_res = Reservoir(
        name="downstream_res",
        initial_state={'water_level': 20.0, 'volume': 2e6, 'outflow': 0},
        parameters={'surface_area': 1e5}
    )

    # A water turbine connecting the two reservoirs
    # We will set a constant target outflow for simplicity in this example.
    turbine = WaterTurbine(
        name="turbine1",
        initial_state={'power': 0, 'outflow': 0},
        parameters={'efficiency': 0.9, 'max_flow_rate': 50}
    )
    # Manually set the target outflow for the turbine
    turbine.target_outflow = 30.0

    # 3. Add components to the harness
    harness.add_component("source_res", source_res)
    harness.add_component("downstream_res", downstream_res)
    harness.add_component("turbine_1", turbine)

    # 4. Connect the components
    harness.add_connection("source_res", "turbine_1")
    harness.add_connection("turbine_1", "downstream_res")

    # 5. Build the simulation
    harness.build()
    print("Simulation harness build complete and ready to run.")

    # 6. Run the simulation using a manual loop
    print("\n--- Running Simulation ---")
    num_steps = int(simulation_config['duration'] / simulation_config['dt'])
    dt = simulation_config['dt']

    for i in range(num_steps):
        current_time = i * dt
        print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

        # Get head levels from reservoirs
        source_head = source_res.get_state()['water_level']
        downstream_head = downstream_res.get_state()['water_level']

        # Step 1: Update the Turbine
        # The turbine's outflow is determined by its target and the available head.
        turbine.set_inflow(float('inf')) # Assume source has infinite water for this simple case
        turbine_action = {'upstream_head': source_head, 'downstream_head': downstream_head}
        turbine_state = turbine.step(turbine_action, dt)
        turbine_outflow = turbine_state['outflow']
        turbine_power = turbine_state['power']
        print(f"  [Turbine] Power Generated: {turbine_power/1e6:.2f} MW, Outflow: {turbine_outflow:.2f} m^3/s")

        # Step 2: Update the Source Reservoir
        # Outflow is determined by the turbine's demand
        source_action = {'outflow': turbine_outflow}
        source_res.set_inflow(0) # No external inflow to the source
        source_res.step(source_action, dt)

        # Step 3: Update the Downstream Reservoir
        # Inflow is the outflow from the turbine
        downstream_action = {'outflow': 0} # No outflow from the downstream reservoir
        downstream_res.set_inflow(turbine_outflow)
        downstream_res.step(downstream_action, dt)

        # Print current states
        print(f"  [Source Res] Water Level: {source_res.get_state()['water_level']:.2f} m")
        print(f"  [Downstream Res] Water Level: {downstream_res.get_state()['water_level']:.2f} m")


    # 7. Print final states
    print("\n--- Simulation Complete ---")
    print(f"Final state of {source_res.name}: {source_res.get_state()}")
    print(f"Final state of {turbine.name}: {turbine.get_state()}")
    print(f"Final state of {downstream_res.name}: {downstream_res.get_state()}")

if __name__ == "__main__":
    run_hydropower_simulation()
