"""
End-to-End Example: Multi-Component River System Simulation

This script demonstrates the platform's capability to handle more complex,
multi-component topologies in a centrally orchestrated manner.

The scenario consists of:
- A Reservoir.
- A Gate (gate_1) controlling the outflow from the reservoir.
- A RiverChannel that receives the outflow from gate_1.
- A second Gate (gate_2) that controls the outflow from the RiverChannel.
- Two independent PID Controllers, wired to their respective components by the harness.
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
        params={'max_rate_of_change': 0.05, 'discharge_coefficient': 0.6, 'width': 10, 'max_opening': 1.0}
    )
    channel = RiverChannel(
        channel_id="channel_1",
        initial_state={'volume': 5e5, 'water_level': 5.0, 'outflow': 50},
        params={'k': 0.0001, 'length': 5000, 'inflow': 0}
    )
    gate2 = Gate(
        gate_id="gate_2",
        initial_state={'opening': 0.5},
        params={'max_rate_of_change': 0.05, 'discharge_coefficient': 0.6, 'width': 10, 'max_opening': 1.0}
    )

    # 2. Define the controllers
    # Controller 1 tries to raise the water level to 18m in the reservoir.
    # Closing the gate raises the level, so this is a direct-acting process (positive gains).
    controller1 = PIDController(
        Kp=0.2, Ki=0.01, Kd=0.05, setpoint=18.0,
        min_output=0.0, max_output=1.0
    )
    # Controller 2 tries to lower the volume to 400,000 m^3 in the river channel.
    # Opening the gate lowers the volume, so this is a reverse-acting process (negative gains).
    controller2 = PIDController(
        Kp=-1e-5, Ki=-1e-7, Kd=-1e-6, setpoint=4e5,
        min_output=0.0, max_output=1.0
    )

    # 3. Set up the Simulation Harness
    simulation_config = {'duration': 1000, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    # 4. Add components and controllers to the harness
    harness.add_component(reservoir)
    harness.add_component(gate1)
    harness.add_component(channel)
    harness.add_component(gate2)

    harness.add_controller(
        controller_id="res_level_ctrl",
        controller=controller1,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )
    harness.add_controller(
        controller_id="chan_vol_ctrl",
        controller=controller2,
        controlled_id="gate_2",
        observed_id="channel_1",
        observation_key="volume"
    )

    # 5. Run the simulation
    harness.run_simulation()

if __name__ == "__main__":
    run_multi_gate_river_example()
