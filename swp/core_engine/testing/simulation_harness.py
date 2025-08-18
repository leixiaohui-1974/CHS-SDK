"""
Simulation Harness for running in-the-loop tests.
"""
from typing import List, Dict, Any
import time

# Import component types for robust checking
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate


class SimulationHarness:
    """
    The Simulation Harness orchestrates the execution of a simulation scenario.

    It manages the simulation loop, advances time, calls the `step` method on all
    simulatable objects, and facilitates the interaction between them (e.g., the
    outflow from one component becomes the inflow for another).

    This is the core of the Model-in-the-Loop (MIL) and Software-in-the-Loop (SIL)
    testing capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the harness with a simulation configuration.

        Args:
            config: A dictionary containing simulation settings like duration,
                    time step, and components involved.
        """
        self.sim_config = config
        # In a real implementation, the components would be passed in or built by a factory
        self.components = []
        self.controllers = {} # Maps controlled object id to a controller
        print("SimulationHarness created.")

    def add_component(self, component: Any):
        """Adds a simulatable component to the harness."""
        self.components.append(component)

    def add_controller(self, controlled_object_id: str, controller: Any):
        """Adds a controller and links it to a component."""
        self.controllers[controlled_object_id] = controller

    def run_simulation(self):
        """
        Executes the main simulation loop.
        """
        duration = self.sim_config.get('duration', 100) # seconds
        dt = self.sim_config.get('dt', 1) # second
        num_steps = int(duration / dt)

        print(f"Starting simulation: Duration={duration}s, TimeStep={dt}s")

        # This is a very simplified simulation loop.
        # A real harness would need to handle complex topologies and data flows.
        # We will simulate a simple reservoir-gate system.
        reservoir = next((c for c in self.components if isinstance(c, Reservoir)), None)
        gate = next((c for c in self.components if isinstance(c, Gate)), None)

        if not reservoir:
            print("Error: A Reservoir component was not found in the harness.")
            return

        controller = self.controllers.get(reservoir.reservoir_id, None)

        if not (reservoir and gate and controller):
            print("Error: Simulation requires a reservoir, a gate, and a controller.")
            return

        for i in range(num_steps):
            current_time = i * dt
            print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # 1. Observe the system state
            reservoir_state = reservoir.get_state()
            print(f"  Observation: Reservoir water level = {reservoir_state.get('water_level'):.3f}m")

            # 2. Controller computes action
            # The observation for the controller needs to be structured correctly.
            controller_obs = {'process_variable': reservoir_state.get('water_level')}
            control_signal = controller.compute_control_action(controller_obs)
            # Let's say the output is a target opening for the gate.
            gate_action = {'target_opening': max(0, min(1, control_signal))} # Clamp between 0 and 1
            print(f"  Controller Action: Target gate opening = {gate_action['target_opening']:.2f}")

            # 3. Step the physical models
            gate.step(gate_action, dt)
            gate_state = gate.get_state()
            print(f"  Gate State: Actual opening = {gate_state.get('opening'):.3f}")

            # 4. Calculate interactions
            # Outflow from gate depends on reservoir water level
            outflow = gate.calculate_discharge(
                upstream_level=reservoir.get_state().get('water_level'),
                downstream_level=0 # simplified assumption
            )
            print(f"  Interaction: Calculated discharge = {outflow:.3f} m^3/s")

            # Inflow to reservoir is constant for this simple example
            inflow = 10 # m^3/s
            reservoir_action = {'inflow': inflow, 'outflow': outflow}
            reservoir.step(reservoir_action, dt)

            time.sleep(0.01) # To make the output readable

        print("\nSimulation finished.")
