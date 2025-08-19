"""
A testing and simulation harness for running the Smart Water Platform.
"""
from collections import deque
from swp.core.interfaces import Simulatable, Agent, Controller
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.reservoir import Reservoir
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
        # Find the component's ID attribute (e.g., 'reservoir_id', 'pipe_id')
        id_attr = next((attr for attr in dir(component) if attr.endswith('_id')), None)
        if id_attr is None:
            raise ValueError("Component does not have a valid ID attribute (e.g., 'pipe_id').")

        component_id = getattr(component, id_attr)
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

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        new_states = {}

        for component_id in self.sorted_components:
            component = self.components[component_id]
            step_action = {}

            # 1. Aggregate inflows from upstream components (using their state from the *previous* timestep)
            total_inflow = 0
            for upstream_id in self.inverse_topology[component_id]:
                # To maintain consistency within a time step, all calculations should be based on the state at time T.
                # So we use the state before this step began.
                upstream_state = self.components[upstream_id].get_state()
                total_inflow += upstream_state.get('outflow', upstream_state.get('discharge', 0))
            step_action['inflow'] = total_inflow

            # 2. Add controller signals
            if component_id in controller_actions:
                step_action['control_signal'] = controller_actions[component_id]

            # 3. Provide head/level information from neighbors (based on state at time T)
            if self.inverse_topology[component_id]:
                upstream_id = self.inverse_topology[component_id][0]
                upstream_state = self.components[upstream_id].get_state()
                step_action['upstream_head'] = upstream_state.get('water_level', upstream_state.get('head', 0))
                step_action['upstream_level'] = step_action['upstream_head']

            if self.topology[component_id]:
                downstream_id = self.topology[component_id][0]
                downstream_state = self.components[downstream_id].get_state()
                step_action['downstream_head'] = downstream_state.get('water_level', downstream_state.get('head', 0))

            # 4. SPECIAL HANDLING for stateful components that need to know their outflow (e.g., Reservoir).
            # We calculate the outflow by "pre-stepping" the immediate downstream components
            # to determine how much water they will draw in this timestep.
            if isinstance(component, Reservoir):
                total_outflow = 0
                for downstream_id in self.topology[component_id]:
                    downstream_comp = self.components[downstream_id]

                    # Create a *specific* action for this downstream component to calculate its prospective flow.
                    downstream_action = {}

                    # Its upstream head is the current component's water level.
                    downstream_action['upstream_head'] = component.get_state().get('water_level', 0)
                    downstream_action['upstream_level'] = downstream_action['upstream_head']

                    # Its downstream head needs to be found from its own downstream neighbor.
                    if self.topology.get(downstream_id):
                        dds_id = self.topology[downstream_id][0]
                        dds_state = self.components[dds_id].get_state()
                        downstream_action['downstream_head'] = dds_state.get('water_level', dds_state.get('head', 0))

                    # Pre-calculate the flow of the downstream component with the correct action.
                    # The returned state contains the calculated flow/discharge for this step.
                    # This does not get applied yet; it's just to get the value.
                    temp_next_state = downstream_comp.step(downstream_action, dt)
                    total_outflow += temp_next_state.get('outflow', temp_next_state.get('discharge', 0))

                # Add the calculated outflow to the action for the current component (the reservoir).
                step_action['outflow'] = total_outflow

            # 5. Step the component with the fully constructed action and store its new state.
            new_states[component_id] = component.step(step_action, dt)

        # 6. After calculating all new states based on the state at time T, apply them all at once.
        for component_id, state in new_states.items():
            self.components[component_id].set_state(state)

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
