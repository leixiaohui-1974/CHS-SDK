"""
A testing and simulation harness for running the Smart Water Platform.
"""
from swp.core.interfaces import Simulatable, Agent, Controller
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from typing import List, Dict, Any, NamedTuple

class ControllerSpec(NamedTuple):
    """Defines the wiring for a controller in a simple simulation."""
    controller: Controller
    controlled_id: str
    observed_id: str
    observation_key: str

class SimulationHarness:
    """
    Manages the setup and execution of a simulation scenario.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.duration = config.get('duration', 100)
        self.dt = config.get('dt', 1.0)

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}

        self.message_bus = MessageBus()
        print("SimulationHarness created.")

    def add_component(self, component: Simulatable):
        """Adds a physical or logical component to the simulation."""
        component_id = getattr(component, 'reservoir_id', getattr(component, 'gate_id', getattr(component, 'channel_id', None)))
        if component_id:
            self.components[component_id] = component
        else:
            self.components[f"component_{len(self.components)}"] = component

    def add_agent(self, agent: Agent):
        """Adds an agent to the simulation."""
        self.agents.append(agent)

    def add_controller(self, controller_id: str, controller: Controller, controlled_id: str, observed_id: str, observation_key: str):
        """Associates a controller with a specific component and its observation source."""
        spec = ControllerSpec(controller, controlled_id, observed_id, observation_key)
        self.controllers[controller_id] = spec
        print(f"Controller '{controller_id}' associated with component '{controlled_id}'.")

    def run_simulation(self):
        """
        Runs a simple, centralized control simulation loop.
        """
        num_steps = int(self.duration / self.dt)
        print(f"Starting simple simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            actions = {}
            for cid, spec in self.controllers.items():
                observed_component = self.components.get(spec.observed_id)
                if not observed_component: continue

                observation_state = observed_component.get_state()
                process_variable = observation_state.get(spec.observation_key)

                if process_variable is not None:
                    control_signal = spec.controller.compute_control_action({'process_variable': process_variable}, self.dt)
                    actions[spec.controlled_id] = control_signal
                    print(f"  Controller '{cid}': Target for '{spec.controlled_id}' = {control_signal:.2f}")

            for component_id, action_signal in actions.items():
                if component_id in self.components and hasattr(self.components[component_id], 'handle_action_message'):
                    self.components[component_id].handle_action_message({'control_signal': action_signal})

            # Hardcoded physics for different topologies
            reservoir = self.components.get("reservoir_1")
            gate1 = self.components.get("gate_1")
            channel = self.components.get("channel_1")
            gate2 = self.components.get("gate_2")

            if reservoir and gate1 and channel and gate2:
                g1_discharge = gate1.calculate_discharge(reservoir.get_state()['water_level'], 0)
                reservoir.step({'inflow': 50, 'outflow': g1_discharge}, self.dt)
                gate1.step({}, self.dt)
                channel.step({'inflow': g1_discharge, 'outflow_gate_opening': actions.get('gate_2', 0)}, self.dt)
                gate2.step({}, self.dt)
                print(f"  State Update: Res Level={reservoir.get_state()['water_level']:.2f}m, "
                      f"Chan Vol={channel.get_state()['volume']:.2f}m^3, "
                      f"G1 Open={gate1.get_state()['opening']:.2f}, G2 Open={gate2.get_state()['opening']:.2f}\n")
            elif reservoir and gate1:
                discharge = gate1.calculate_discharge(reservoir.get_state()['water_level'], 0)
                reservoir.step({'inflow': 0, 'outflow': discharge}, self.dt)
                gate1.step({}, self.dt)
                print(f"  State Update: Reservoir water level = {reservoir.get_state()['water_level']:.3f}m\n")

    def run_mas_simulation(self):
        """
        Runs a full Multi-Agent System (MAS) simulation.
        """
        num_steps = int(self.duration / self.dt)
        print(f"Starting MAS simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            print("  Phase 1: Triggering agent perception and action cascade.")
            for agent in self.agents:
                # The harness passes the current time to each agent
                agent.run(current_time)

            print("  Phase 2: Stepping physical models with interactions.")
            reservoir = self.components.get("reservoir_1")
            gate = self.components.get("gate_1")

            if reservoir and gate:
                upstream_level = reservoir.get_state()['water_level']
                discharge = gate.calculate_discharge(upstream_level=upstream_level, downstream_level=0)
                reservoir.step({'inflow': 0, 'outflow': discharge}, self.dt)
                gate.step({}, self.dt)
            else:
                for component in self.components.values():
                    component.step({}, self.dt)

            reservoir_level = reservoir.get_state()['water_level'] if reservoir else 'N/A'
            gate_opening = gate.get_state()['opening'] if gate else 'N/A'
            print(f"  State Update: Reservoir level = {reservoir_level:.3f}m, "
                  f"Gate opening = {gate_opening:.3f}m\n")

        print("MAS Simulation finished.")
