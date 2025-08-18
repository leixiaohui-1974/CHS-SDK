"""
End-to-End Example: Multi-Component River System Simulation

This script demonstrates the platform's capability to handle more complex,
multi-component topologies.

The scenario consists of:
- A Reservoir with a constant inflow.
- A Gate (gate_1) controlling the outflow from the reservoir.
- A RiverChannel that receives the outflow from gate_1.
- A second Gate (gate_2) that controls the outflow from the RiverChannel.
- Two PID Controllers:
  - controller_1 adjusts gate_1 to maintain a water level in the Reservoir.
  - controller_2 adjusts gate_2 to maintain a water volume in the RiverChannel.
- A Simulation Harness that orchestrates the entire simulation.
"""
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from swp.local_agents.control.pid_controller import PIDController
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_multi_gate_river_example():
    """
    Sets up and runs the multi-component river simulation example.
    """
    print("--- Setting up the Multi-Gate River Example ---")

    # 1. Define the components
    reservoir = Reservoir(
        reservoir_id="reservoir_1",
        initial_state={'volume': 25e6, 'water_level': 15.0},
        params={'surface_area': 1.5e6}
    )
    gate1 = Gate(
        gate_id="gate_1",
        initial_state={'opening': 0.2},
        params={'max_rate_of_change': 0.05, 'discharge_coefficient': 0.6, 'width': 10}
    )
    channel = RiverChannel(
        channel_id="channel_1",
        initial_state={'volume': 5e5, 'outflow': 50},
        params={'k': 0.0001, 'length': 5000}
    )
    gate2 = Gate(
        gate_id="gate_2",
        initial_state={'opening': 0.5},
        params={'max_rate_of_change': 0.05, 'discharge_coefficient': 0.6, 'width': 10}
    )

    # 2. Define the controllers
    # Controller 1 targets a water level of 18m in the main reservoir.
    controller1 = PIDController(Kp=0.1, Ki=0.005, Kd=0.05, setpoint=18.0)
    # Controller 2 targets a volume of 400,000 m^3 in the river channel.
    controller2 = PIDController(Kp=1e-5, Ki=1e-7, Kd=1e-6, setpoint=4e5)


    # 3. Set up the Simulation Harness
    simulation_config = {'duration': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    # 4. Add components and controllers to the harness
    harness.add_component(reservoir)
    harness.add_component(gate1)
    harness.add_component(channel)
    harness.add_component(gate2)

    harness.add_controller(controlled_object_id="gate_1", controller=controller1)
    harness.add_controller(controlled_object_id="gate_2", controller=controller2)

    # 5. Run the simulation
    harness.run_simulation()

if __name__ == "__main__":
    run_multi_gate_river_example()
