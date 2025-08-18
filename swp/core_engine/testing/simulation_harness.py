"""
A testing and simulation harness for running the Smart Water Platform.
"""
from collections import deque
from swp.core.interfaces import Simulatable, Agent, Controller
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.simulation_identification.physical_objects.gate import Gate
from typing import List, Dict, Any, NamedTuple

class ControllerSpec(NamedTuple):
    """Defines the wiring for a controller in a simple simulation."""
    controller: Controller
    controlled_id: str
    observed_id: str
    observation_key: str

class SimulationHarness:
    """
    Manages the setup and execution of a simulation scenario using a graph-based topology.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.duration = config.get('duration', 100)
        self.dt = config.get('dt', 1.0)

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}

        # Graph representation: adjacency lists for downstream and upstream connections
        self.topology: Dict[str, List[str]] = {}
        self.inverse_topology: Dict[str, List[str]] = {}
        self.sorted_components: List[str] = []

        self.message_bus = MessageBus()
        print("SimulationHarness created.")

    def add_component(self, component: Simulatable):
        """Adds a physical or logical component to the simulation."""
        component_id = getattr(component, 'reservoir_id', getattr(component, 'gate_id', getattr(component, 'channel_id', "un-id-ed_component")))
        if component_id in self.components:
            raise ValueError(f"Component with ID '{component_id}' already exists.")
        self.components[component_id] = component
        self.topology[component_id] = []
        self.inverse_topology[component_id] = []
        print(f"Component '{component_id}' added.")

    def add_connection(self, upstream_id: str, downstream_id: str):
        """Adds a directional connection between two components."""
        if upstream_id not in self.components:
            raise ValueError(f"Upstream component '{upstream_id}' not found.")
        if downstream_id not in self.components:
            raise ValueError(f"Downstream component '{downstream_id}' not found.")

        self.topology[upstream_id].append(downstream_id)
        self.inverse_topology[downstream_id].append(upstream_id)
        print(f"Connection added: {upstream_id} -> {downstream_id}")

    def add_agent(self, agent: Agent):
        """Adds an agent to the simulation."""
        self.agents.append(agent)

    def add_controller(self, controller_id: str, controller: Controller, controlled_id: str, observed_id: str, observation_key: str):
        """Associates a controller with a specific component and its observation source."""
        spec = ControllerSpec(controller, controlled_id, observed_id, observation_key)
        self.controllers[controller_id] = spec
        print(f"Controller '{controller_id}' associated with component '{controlled_id}'.")

    def _topological_sort(self):
        """
        Performs a topological sort of the components graph.
        This determines the correct order for stepping through the physical models.
        """
        in_degree = {u: 0 for u in self.topology}
        for u in self.topology:
            for v in self.topology[u]:
                in_degree[v] += 1

        queue = deque([u for u in self.topology if in_degree[u] == 0])

        self.sorted_components = []
        while queue:
            u = queue.popleft()
            self.sorted_components.append(u)

            for v in self.topology[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(self.sorted_components) != len(self.components):
            raise Exception("Graph has at least one cycle, which is not allowed in a water system topology.")

        print("Topological sort complete. Update order determined.")

    def build(self):
        """Finalizes the harness setup by sorting the component graph."""
        self._topological_sort()
        print("Simulation harness build complete and ready to run.")

    def _step_physical_models(self, dt: float, actions: Dict[str, Any] = None):
        """
        Private helper to step through all physical models using a two-phase update.
        This correctly handles the inter-dependencies between components like reservoirs and gates.
        """
        if actions is None:
            actions = {}

        # Phase 1: Update all gate openings and then calculate their new discharge.
        # This is based on the system's state from the *previous* time step (t),
        # to determine the flows for the current time step (t+dt).
        for component_id, component in self.components.items():
            if isinstance(component, Gate):
                gate_action = {}
                # Pass controller signal if it exists for this gate
                if component_id in actions:
                    gate_action['control_signal'] = actions[component_id]

                # Provide the upstream water level needed for discharge calculation
                if self.inverse_topology[component_id]:
                    # Assuming a gate has one primary upstream component for its level reading
                    upstream_id = self.inverse_topology[component_id][0]
                    upstream_component = self.components[upstream_id]

                    gate_action['upstream_level'] = upstream_component.get_state().get('water_level', 0)

                # Step the gate to update its opening and calculate its discharge
                component.step(gate_action, dt)

        # Phase 2: Update the state of non-gate components (reservoirs, channels)
        # in topological order.
        for component_id in self.sorted_components:
            if isinstance(self.components[component_id], Gate):
                continue  # Gates have already been updated in Phase 1

            component = self.components[component_id]

            # Aggregate total inflow from the states of all upstream components
            total_inflow = 0
            for upstream_id in self.inverse_topology[component_id]:
                upstream_state = self.components[upstream_id].get_state()
                inflow = upstream_state.get('outflow', upstream_state.get('discharge', 0))
                total_inflow += inflow

            # For reservoirs and channels, their effective outflow is the sum of the
            # discharges of all gates directly downstream from them.
            total_outflow = 0
            for downstream_id in self.topology[component_id]:
                if isinstance(self.components[downstream_id], Gate):
                    downstream_gate_state = self.components[downstream_id].get_state()
                    total_outflow += downstream_gate_state.get('discharge', 0)

            # Step the component with the calculated total in/outflows
            step_action = {'inflow': total_inflow, 'outflow': total_outflow}
            component.step(step_action, dt)

    def run_simulation(self):
        """
        Runs a simple, centralized control simulation loop using the graph topology.
        """
        if not self.sorted_components:
            raise Exception("Harness has not been built. Call harness.build() before running.")

        num_steps = int(self.duration / self.dt)
        print(f"Starting simple simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # 1. Compute control actions
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

            # 2. Step the physical models in order
            self._step_physical_models(self.dt, actions)

            # 3. Print state summary (optional)
            # You can customize this to print states of interest
            print("  State Update:")
            for cid in self.sorted_components:
                state = self.components[cid].get_state()
                print(f"    {cid}: {state}")
            print("")

    def run_mas_simulation(self):
        """
        Runs a full Multi-Agent System (MAS) simulation using the graph topology.
        """
        if not self.sorted_components:
            raise Exception("Harness has not been built. Call harness.build() before running.")

        num_steps = int(self.duration / self.dt)
        print(f"Starting MAS simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            print("  Phase 1: Triggering agent perception and action cascade.")
            for agent in self.agents:
                agent.run(current_time)

            print("  Phase 2: Stepping physical models with interactions.")
            self._step_physical_models(self.dt)

            # Print state summary (optional)
            print("  State Update:")
            for cid in self.sorted_components:
                state_str = ", ".join(f"{k}={v:.2f}" for k, v in self.components[cid].get_state().items())
                print(f"    {cid}: {state_str}")
            print("")

        print("MAS Simulation finished.")
