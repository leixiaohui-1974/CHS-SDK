"""
End-to-End Example: Simulation with a Pipe

This script demonstrates how to use the new `Pipe` model to connect a reservoir
to a downstream gate.
"""
import math
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_pipe_example():
    """
    Sets up and runs a simulation including a pipe.
    """
    print("--- Setting up the Pipe Simulation Example ---")

    # 1. Define the components
    reservoir = Reservoir(
        name="res1",
        initial_state={'volume': 25e6, 'water_level': 15.0},
        parameters={'surface_area': 1.5e6}
    )

    pipe = Pipe(
        name="pipe1",
        initial_state={'outflow': 0},
        parameters={
            'length': 1000, # 1 km
            'diameter': 1.5, # m
            'friction_factor': 0.02
        }
    )

    # This gate is uncontrolled and just provides a downstream boundary condition
    gate = Gate(
        name="g1",
        initial_state={'opening': 0.3}, # 30% open
        parameters={'width': 10, 'max_opening': 1.0, 'discharge_coefficient': 0.6}
    )

    # 2. Set up the Simulation Harness
    simulation_config = {'duration': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    # 3. Add components and define topology
    harness.add_component(reservoir)
    harness.add_component(pipe)
    harness.add_component(gate)

    harness.add_connection("res1", "pipe1")
    harness.add_connection("pipe1", "g1")

    # 4. Build and run the simulation
    harness.build()
    harness.run_simulation()

if __name__ == "__main__":
    run_pipe_example()
