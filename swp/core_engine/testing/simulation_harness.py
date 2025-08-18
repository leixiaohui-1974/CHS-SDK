"""
Simulation Harness for running in-the-loop tests.
"""
from typing import List, Dict, Any
import time

# Import component types for robust checking
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel


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

        This version is enhanced to handle a simple, linear topology of components.
        It identifies components by class and processes them in a logical order.
        A more advanced implementation would use a formal topology graph from the config.
        """
        duration = self.sim_config.get('duration', 100)
        dt = self.sim_config.get('dt', 1)
        num_steps = int(duration / dt)

        print(f"Starting simulation: Duration={duration}s, TimeStep={dt}s")

        # --- Component Identification ---
        # Instead of hard-coding, we find components by their type.
        # This is more flexible than the previous version.
        components_by_class = {
            Reservoir: [c for c in self.components if isinstance(c, Reservoir)],
            Gate: [c for c in self.components if isinstance(c, Gate)],
            RiverChannel: [c for c in self.components if isinstance(c, RiverChannel)],
        }

        # --- Simplified Topology Assumption ---
        reservoir = components_by_class[Reservoir][0] if components_by_class[Reservoir] else None
        gates = sorted(components_by_class[Gate], key=lambda g: g.gate_id) # Sort for consistent order
        channel = components_by_class[RiverChannel][0] if components_by_class[RiverChannel] else None

        if not reservoir or not gates:
            print("Error: Simulation requires at least one Reservoir and at least one Gate.")
            return

        # --- Main Simulation Loop ---
        for i in range(num_steps):
            current_time = i * dt
            print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # Determine upstream and downstream water levels for calculations
            reservoir_level = reservoir.get_state().get('water_level', 0)

            # If there's a channel, its water level is important
            # This is a simplification; a real model would have varying levels.
            channel_volume = channel.get_state().get('volume', 0) if channel else 0
            # Rough estimation of channel water level for discharge calculation
            channel_level = channel_volume / 5e5 if channel else 0

            # --- Component Processing based on Topology ---

            # 1. Process the first gate (controlled by reservoir level)
            gate1 = gates[0]
            controller1 = self.controllers.get(gate1.gate_id)
            if controller1:
                obs1 = {'process_variable': reservoir_level}
                control_signal1 = controller1.compute_control_action(obs1)
                action1 = {'target_opening': max(0, min(1, control_signal1))}
                print(f"  Controller for '{gate1.gate_id}': Target opening = {action1['target_opening']:.2f} (based on reservoir level {reservoir_level:.2f}m)")
                gate1.step(action1, dt)

            outflow_gate1 = gate1.calculate_discharge(
                upstream_level=reservoir_level,
                downstream_level=channel_level # Gate outflow depends on downstream channel level
            )
            print(f"  Interaction: Discharge from '{gate1.gate_id}' = {outflow_gate1:.3f} m^3/s")

            # 2. Process the River Channel if it exists
            if channel:
                channel_action = {'inflow': outflow_gate1}
                channel.step(channel_action, dt)
                outflow_channel = channel.get_state().get('outflow', 0)
                print(f"  State Update: Channel volume = {channel.get_state().get('volume'):.2f} m^3, Outflow = {outflow_channel:.3f} m^3/s")

                # 3. Process the second gate if it exists (controlled by channel state)
                if len(gates) > 1:
                    gate2 = gates[1]
                    controller2 = self.controllers.get(gate2.gate_id)
                    if controller2:
                        # Controller for gate2 could be based on channel volume or level
                        obs2 = {'process_variable': channel.get_state().get('volume')}
                        control_signal2 = controller2.compute_control_action(obs2)
                        action2 = {'target_opening': max(0, min(1, control_signal2))}
                        print(f"  Controller for '{gate2.gate_id}': Target opening = {action2['target_opening']:.2f} (based on channel volume)")
                        gate2.step(action2, dt)

                    outflow_gate2 = gate2.calculate_discharge(
                        upstream_level=channel_level, # Upstream is now the channel
                        downstream_level=0 # Assumed free discharge
                    )
                    print(f"  Interaction: Discharge from '{gate2.gate_id}' = {outflow_gate2:.3f} m^3/s")
                    # In this topology, the river channel's outflow is actually determined by gate2
                    channel.get_state()['outflow'] = outflow_gate2

            # 4. Update the reservoir
            inflow_reservoir = 50  # m^3/s, a larger constant inflow for a more dynamic scenario
            reservoir_action = {'inflow': inflow_reservoir, 'outflow': outflow_gate1}
            reservoir.step(reservoir_action, dt)
            print(f"  State Update: Reservoir water level = {reservoir.get_state().get('water_level'):.3f}m")

            time.sleep(0.01)

        print("\nSimulation finished.")
