import unittest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.valve import Valve
from core_lib.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent
from core_lib.local_agents.control.valve_control_agent import ValveControlAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class TestSimpleScenario(unittest.TestCase):
    """
    An integration test for a simple scenario involving a reservoir, a valve,
    and their corresponding perception and control agents.
    """

    def test_reservoir_valve_control_scenario(self):
        """
        Tests a closed-loop system where a valve controls the outflow of a
        reservoir to maintain a specific water level setpoint.
        """
        # 1. Setup: Create the message bus, components, and agents
        bus = MessageBus()

        # Physical components
        reservoir = Reservoir(
            name="source_reservoir",
            initial_state={'water_level': 10.0, 'volume': 10000.0},
            parameters={'surface_area': 1000.0}
        )
        # The valve's outflow is controlled by the reservoir's water level
        valve = Valve(
            name="outlet_valve",
            initial_state={'opening': 50.0},
            parameters={'diameter': 0.5, 'discharge_coefficient': 0.8},
            message_bus=bus,
            action_topic="action/valve/command"
        )

        # Agents and Controllers
        perception_agent = ReservoirPerceptionAgent(
            agent_id="reservoir_twin",
            reservoir_model=reservoir,
            message_bus=bus,
            state_topic="perception/reservoir/state"
        )
        # For this setup, where a higher output (valve opening) is needed when the
        # water level is too high (process_variable > setpoint), we need a
        # reverse-acting controller. This is achieved with negative gains.
        pid_controller = PIDController(
            Kp=-2.0, Ki=-0.1, Kd=-0.01, # Negative gains for reverse action
            setpoint=8.0,  # Target water level: 8.0 meters
            min_output=0, max_output=100  # Valve opening percentage
        )
        control_agent = ValveControlAgent(
            agent_id="valve_controller",
            controller=pid_controller,
            message_bus=bus,
            observation_topic="perception/reservoir/state",
            observation_key="water_level", # Control based on water level
            action_topic="action/valve/command",
            dt=1.0 # Simulation time step
        )

        # 2. Simulation Harness
        config = {'duration': 100, 'dt': 1.0}
        harness = SimulationHarness(config)
        harness.add_component(reservoir)
        harness.add_component(valve)
        harness.add_agent(perception_agent)
        harness.add_agent(control_agent)

        # Define the physical connections
        harness.add_connection("source_reservoir", "outlet_valve")
        harness.build()

        # 3. Run the simulation
        # Reservoir starts at 10m, setpoint is 8m.
        # The PID controller should close the valve to lower the water level.
        # We give it an inflow to make the problem non-trivial.
        reservoir.set_inflow(10.0) # Constant inflow of 10 m^3/s

        # The harness now runs the full loop
        harness.run_mas_simulation()

        # 4. Assertions
        # After the simulation, the water level should be closer to the setpoint of 8.0m
        # than it was at the start (10.0m).
        final_state = harness.history[-1]['source_reservoir']
        final_water_level = final_state['water_level']

        # It's hard to assert an exact value, so we check for convergence.
        self.assertLess(final_water_level, 10.0)
        self.assertGreater(final_water_level, 7.0) # Should not overshoot too much

        # Check if the final level is closer to the setpoint than the initial level
        initial_error = abs(10.0 - 8.0)
        final_error = abs(final_water_level - 8.0)
        self.assertLess(final_error, initial_error)


if __name__ == '__main__':
    unittest.main()
