"""
End-to-End Example: Simple Reservoir-Gate Control Simulation

This script demonstrates how to use the Smart Water Platform framework to set up
and run a simple simulation scenario.

The scenario consists of:
- A Reservoir with a constant inflow.
- A Gate that controls the outflow from the reservoir.
- A PID Controller that adjusts the gate opening to maintain a specific water level
  in the reservoir.
- A Simulation Harness that orchestrates the entire simulation.

This script showcases the modularity and interoperability of the platform's components.
"""
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_reservoir_control_example():
    """
    Sets up and runs the reservoir control simulation example.
    """
    print("--- Setting up the Reservoir Control Example ---")

    # 1. Define the components and their parameters

    # Reservoir Model
    reservoir_params = {
        'surface_area': 1.5e6, # m^2
    }
    reservoir_initial_state = {
        'volume': 21e6, # m^3, equivalent to 14m * 1.5e6 m^2
        'water_level': 14.0 # m, start above the setpoint
    }
    reservoir = Reservoir(
        reservoir_id="reservoir_1",
        initial_state=reservoir_initial_state,
        params=reservoir_params
    )

    # Gate Model
    gate_params = {
        'max_rate_of_change': 0.1, # 10% per second
        'discharge_coefficient': 0.6,
        'width': 10 # m
    }
    gate_initial_state = {
        'opening': 0.5 # 50% open
    }
    gate = Gate(
        gate_id="gate_1",
        initial_state=gate_initial_state,
        params=gate_params
    )

    # 2. Define the controller

    # PID Controller to maintain the reservoir water level at 12 meters
    # The gains are negative because it's a reverse-acting process
    # (opening the gate lowers the water level).
    pid_controller = PIDController(
        Kp=-0.5, # Proportional gain
        Ki=-0.01, # Integral gain
        Kd=-0.1,  # Derivative gain
        setpoint=12.0, # Target water level in meters
        min_output=0.0,
        max_output=1.0 # Gate opening is a percentage
    )

    # 3. Set up the Simulation Harness

    simulation_config = {
        'duration': 300, # Simulate for 300 seconds
        'dt': 1.0 # Time step of 1 second
    }
    harness = SimulationHarness(config=simulation_config)

    # 4. Add components and controllers to the harness
    # This demonstrates the "pluggable" nature of the architecture.
    harness.add_component(reservoir)
    harness.add_component(gate)
    # Add the controller and define its wiring
    harness.add_controller(
        controller_id="pid_for_gate1",
        controller=pid_controller,
        controlled_id="gate_1",
        observed_id="reservoir_1",
        observation_key="water_level"
    )

    # 5. Run the simulation
    harness.run_simulation()

if __name__ == "__main__":
    run_reservoir_control_example()
