"""
A testing and simulation harness for running the Smart Water Platform.
"""
from collections import deque
from functools import partial
from core_lib.core.interfaces import Simulatable, Agent, Controller
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
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
        # Use 'time_step' to be consistent with config.yml, but fall back to 'dt'
        self.dt = config.get('time_step', config.get('dt', 1.0))
        self.history = []

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}
        self.actions: Dict[str, Any] = {} # To store actions from agents

        self.topology: Dict[str, List[str]] = {}
        self.inverse_topology: Dict[str, List[str]] = {}
        self.sorted_components: List[str] = []

        self.message_bus = MessageBus()
        print("SimulationHarness created.")

    def add_component(self, component: Simulatable):
        component_id = component.name
        if component_id in self.components:
            raise ValueError(f"Component with ID '{component_id}' already exists.")
        self.components[component_id] = component
        self.topology[component_id] = []
        self.inverse_topology[component_id] = []
        print(f"Component '{component_id}' added.")

    def add_connection(self, upstream_id: str, downstream_id: str):
        if upstream_id not in self.components:
            raise ValueError(f"Upstream component '{upstream_id}' not found.")
        if downstream_id not in self.components:
            raise ValueError(f"Downstream component '{downstream_id}' not found.")

        self.topology[upstream_id].append(downstream_id)
        self.inverse_topology[downstream_id].append(upstream_id)
        print(f"Connection added: {upstream_id} -> {downstream_id}")

    def add_agent(self, agent: Agent):
        self.agents.append(agent)

    def subscribe_to_action(self, topic: str):
        """
        Subscribes the harness to an agent's action topic to collect control signals.
        A closure is used to pass the component_id to the handler.
        """
        component_id = topic.split('.')[-1]

        # Create a specific handler for this topic that knows the component_id
        def handle_specific_action(message: Message, comp_id: str):
            control_signal = message.get('control_signal')
            if control_signal is not None:
                self.actions[comp_id] = control_signal

        # Use a partial to "bake in" the component_id for the callback
        self.message_bus.subscribe(topic, partial(handle_specific_action, comp_id=component_id))
        print(f"Harness subscribed to action topic '{topic}' for component '{component_id}'.")

    def _topological_sort(self):
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
        self._topological_sort()
        print("Simulation harness build complete and ready to run.")

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        # First, calculate all inflows based on the previous step's outflows
        # This prevents the update order from affecting the result in a single step
        inflows = {}
        for cid in self.sorted_components:
            inflows[cid] = sum(
                self.components[up_id].get_state().get('outflow', 0)
                for up_id in self.inverse_topology.get(cid, [])
            )

        # Now, step through each component with the calculated inflows
        for component_id in self.sorted_components:
            component = self.components[component_id]
            component.set_inflow(inflows[component_id])

            # Prepare action dictionary for the component's step method
            action = {}
            if component_id in controller_actions:
                 action['control_signal'] = controller_actions.get(component_id)

            # For components that need head info (like Gates), find it from neighbors
            # Upstream Head
            upstream_ids = self.inverse_topology.get(component_id, [])
            if upstream_ids:
                # Assuming one primary upstream component for head calculation
                up_comp = self.components[upstream_ids[0]]
                action['upstream_head'] = up_comp.get_state().get('water_level', 0)

            # Downstream Head
            downstream_ids = self.topology.get(component_id, [])
            if downstream_ids:
                # Assuming one primary downstream component for head calculation
                down_comp = self.components[downstream_ids[0]]
                action['downstream_head'] = down_comp.get_state().get('water_level', 0)

            # Step the component
            component.step(action, dt)

    def _publish_states(self):
        """Publishes the current state of all components to the message bus."""
        for cid, component in self.components.items():
            state = component.get_state()
            # Publish to a standardized topic name that agents can subscribe to
            self.message_bus.publish(f"state.{cid}", state)

    def run_mas_simulation(self):
        if not self.sorted_components:
            raise Exception("Harness has not been built. Call harness.build() before running.")

        num_steps = int(self.duration / self.dt)
        print(f"Starting MAS simulation: Duration={self.duration}s, TimeStep={self.dt}s\n")

        self.history = []
        for i in range(num_steps):
            current_time = i * self.dt
            print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # Phase 1: Publish current states for agents to perceive
            print("  Phase 1: Publishing component states for agent perception.")
            self._publish_states()

            # The message bus is synchronous, so agents have already reacted and
            # published their actions. The actions are now in self.actions.

            # Phase 2: Step physical models using the collected actions
            print(f"  Phase 2: Stepping physical models with {len(self.actions)} collected action(s).")
            self._step_physical_models(self.dt, self.actions)

            # Clear actions for the next step
            self.actions.clear()

            # Store history
            step_history = {'time': current_time}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            self.history.append(step_history)

            # Print state summary
            print("  State Update:")
            for cid in self.sorted_components:
                state_str = ", ".join(f"{k}={v:.2f}" for k, v in self.components[cid].get_state().items())
                print(f"    {cid}: {state_str}")
            print("")

        print("MAS Simulation finished.")
