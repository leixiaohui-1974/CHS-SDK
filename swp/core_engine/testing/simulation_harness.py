"""
A testing and simulation harness for running the Smart Water Platform.
"""
from swp.core.interfaces import Simulatable, Agent
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from typing import List, Dict, Any

class SimulationHarness:
    """
    Manages the setup and execution of a simulation scenario.

    This class is responsible for:
    - Holding the simulation configuration (e.g., duration, time step).
    - Storing all the components (simulatable objects) and agents.
    - Running the main simulation loop, including modeling physical interactions.
    - Providing a central message bus for agent communication.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.duration = config.get('duration', 100)
        self.dt = config.get('dt', 1.0)

        self.components: List[Simulatable] = []
        self.agents: List[Agent] = []

        # The harness owns the message bus
        self.message_bus = MessageBus()
        print("SimulationHarness created.")

    def add_component(self, component: Simulatable):
        """Adds a physical or logical component to the simulation."""
        self.components.append(component)

    def add_agent(self, agent: Agent):
        """Adds an agent to the simulation."""
        self.agents.append(agent)

    def run_mas_simulation(self):
        """
        Runs a full Multi-Agent System (MAS) simulation.

        This loop orchestrates the interaction between agents and the environment.
        It models both the information flow (via the message bus) and the
        physical flow (interactions between components).
        """
        num_steps = int(self.duration / self.dt)
        print(f"Starting MAS simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # --- Phase 1: Perception and Control Logic ---
            # Digital Twin agents perceive the state of the world and publish it.
            # This triggers a synchronous cascade of agent logic.
            print("  Phase 1: Triggering agent perception and action cascade.")
            for agent in self.agents:
                if isinstance(agent, DigitalTwinAgent):
                    agent.run()

            # --- Phase 2: Environment Update ---
            # The physical models are stepped forward in time, accounting for
            # their physical interactions.
            print("  Phase 2: Stepping physical models with interactions.")

            # This is a hardcoded interaction for the specific hierarchical example.
            # A more advanced harness would use a system topology graph.
            reservoir = next((c for c in self.components if isinstance(c, Reservoir)), None)
            gate = next((c for c in self.components if isinstance(c, Gate)), None)

            if reservoir and gate:
                # 1. Calculate the discharge from the gate based on the reservoir's current water level.
                upstream_level = reservoir.get_state()['water_level']
                discharge = gate.calculate_discharge(upstream_level=upstream_level, downstream_level=0)

                # 2. Step the reservoir, applying the gate's discharge as its outflow.
                reservoir_action = {'outflow': discharge}
                reservoir.step(reservoir_action, self.dt)

                # 3. Step the gate (to update its opening based on its target).
                gate.step({}, self.dt)
            else:
                # Fallback for other simulation types
                for component in self.components:
                    component.step({}, self.dt)

            # --- Logging ---
            reservoir_level = reservoir.get_state()['water_level'] if reservoir else 'N/A'
            gate_opening = gate.get_state()['opening'] if gate else 'N/A'
            print(f"  State Update: Reservoir level = {reservoir_level:.3f}m, "
                  f"Gate opening = {gate_opening:.3f}m\n")

        print("MAS Simulation finished.")
