from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.simulation_identification.physical_objects.lake import Lake
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine
from swp.simulation_identification.physical_objects.canal import Canal
from swp.examples.helpers import (
    print_simulation_results,
    setup_logging,
)

def main():
    """
    This example demonstrates a simple hydropower generation scenario involving a
    lake, a water turbine, and a canal.
    """
    setup_logging()
    print("--- Setting up the Hydropower Generation Example ---")

    # 1. Create the simulation harness
    # Simulate for 3 days in hourly steps
    harness = SimulationHarness(config={'dt': 3600, 'duration': 86400 * 3})

    # 2. Create physical components
    # Evaporation rate: 2mm/day -> 0.002m / (24 * 3600s) = 2.31e-8 m/s
    initial_lake_volume = 40e6
    lake_surface_area = 2e6
    upper_lake = Lake(
        name="upper_lake",
        initial_state={'volume': initial_lake_volume, 'water_level': initial_lake_volume / lake_surface_area, 'outflow': 0},
        parameters={'surface_area': lake_surface_area, 'max_volume': 50e6, 'evaporation_rate_m_per_s': 2.31e-8}
    )

    turbine = WaterTurbine(
        name="turbine_1",
        initial_state={'power': 0, 'outflow': 0},
        parameters={'efficiency': 0.85, 'max_flow_rate': 150}
    )

    tailrace_canal = Canal(
        name="tailrace_canal",
        initial_state={'volume': 100000, 'water_level': 2.1, 'outflow': 0}, # Initial level approx for some flow
        parameters={
            'bottom_width': 20,
            'length': 5000,
            'slope': 0.0002,
            'side_slope_z': 2,
            'manning_n': 0.025
        }
    )

    # 3. Add components to the harness
    harness.add_component(upper_lake)
    harness.add_component(turbine)
    harness.add_component(tailrace_canal)

    # 4. Define the connections between components
    harness.add_connection("upper_lake", "turbine_1")
    harness.add_connection("turbine_1", "tailrace_canal")

    # 5. Build the simulation
    harness.build()

    # 6. Run the simulation
    harness.run_simulation()

    # 7. Print final results
    print("\n--- FINAL SIMULATION STATE ---")
    final_states = {cid: comp.get_state() for cid, comp in harness.components.items()}
    print_simulation_results(final_states)


if __name__ == "__main__":
    main()
