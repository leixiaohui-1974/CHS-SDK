"""
A testing and simulation harness for running the Smart Water Platform.
"""
import threading
from collections import deque
from core_lib.core.interfaces import Simulatable, Agent, Controller
from core_lib.central_coordination.collaboration.message_bus import MessageBus
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
        self.start_time = config.get('start_time', 0)
        self.end_time = config.get('end_time', 100)
        self.dt = config.get('dt', 1.0)
        self.t = self.start_time

        self.history = []

        self.components: Dict[str, Simulatable] = {}
        self.agents: List[Agent] = []
        self.controllers: Dict[str, ControllerSpec] = {}

        # Graph representation: adjacency lists for downstream and upstream connections
        self.topology: Dict[str, List[str]] = {}
        self.inverse_topology: Dict[str, List[str]] = {}
        self.sorted_components: List[str] = []

        self.message_bus = MessageBus()
        self._is_paused = threading.Event()
        self.is_running = False

        print("SimulationHarness created.")

    def add_component(self, component_id: str, component: Simulatable):
        """Adds a physical or logical component to the simulation."""
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
        self.is_running = True
        print("Simulation harness build complete and ready to run.")

    def pause(self):
        """Pauses the simulation."""
        self._is_paused.set()
        print("Simulation paused.")

    def resume(self):
        """Resumes the simulation."""
        self._is_paused.clear()
        print("Simulation resumed.")

    def step(self):
        """
        Advances the simulation by a single time step.
        This includes running agents and updating physical models.
        """
        if self.t >= self.end_time:
            self.is_running = False
            return

        # This logic is adapted from the original run_mas_simulation
        # print(f"--- MAS Simulation Step, Time: {self.t:.2f}s ---")

        # Phase 1: Trigger agents
        for agent in self.agents:
            agent.run(self.t)

        # Phase 2: Step physical models
        self._step_physical_models(self.dt)

        # Phase 3: Store history (optional, can be disabled for performance)
        step_history = {'time': self.t}
        for cid in self.sorted_components:
            step_history[cid] = self.components[cid].get_state()
        for agent in self.agents:
            if hasattr(agent, 'get_state'):
                # A bit of safety here in case agent doesn't have a state method
                try:
                    step_history[agent.agent_id] = agent.get_state()
                except Exception as e:
                    print(f"Could not get state from agent {agent.agent_id}: {e}")
        self.history.append(step_history)

        # Update time
        self.t += self.dt

    def run_mas_simulation(self):
        """运行多智能体系统仿真"""
        print(f"Starting MAS simulation from {self.start_time} to {self.end_time} with dt={self.dt}")
        
        while self.t < self.end_time and self.is_running:
            # 检查是否暂停
            if self._is_paused.is_set():
                self._is_paused.wait()
                continue
            
            # 执行一个仿真步骤
            self.step()
        
        print(f"MAS simulation completed at time {self.t:.2f}s")
        print(f"Generated {len(self.history)} steps of history data.")

    def run_simulation(self):
        """运行简单仿真（非智能体模式）"""
        print(f"Starting simple simulation from {self.start_time} to {self.end_time} with dt={self.dt}")
        
        while self.t < self.end_time and self.is_running:
            # 检查是否暂停
            if self._is_paused.is_set():
                self._is_paused.wait()
                continue
            
            # Phase 1: 计算控制器动作
            controller_actions = {}
            for controller_id, spec in self.controllers.items():
                try:
                    # 获取观测值
                    observed_component = self.components[spec.observed_id]
                    observation = observed_component.get_state().get(spec.observation_key, 0)
                    
                    # 计算控制动作
                    action = spec.controller.compute_control_action({'process_variable': observation}, self.dt)
                    controller_actions[spec.controlled_id] = action
                    
                except Exception as e:
                    print(f"Error in controller {controller_id}: {e}")
            
            # Phase 2: 步进物理模型
            self._step_physical_models(self.dt, controller_actions)
            
            # Phase 3: 记录历史
            step_history = {'time': self.t}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            self.history.append(step_history)
            
            # 更新时间
            self.t += self.dt
        
        print(f"Simple simulation completed at time {self.t:.2f}s")
        print(f"Generated {len(self.history)} steps of history data.")

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        new_states = {}
        current_step_outflows = {}

        for component_id in self.sorted_components:
            component = self.components[component_id]
            action = {'control_signal': controller_actions.get(component_id)}

            total_inflow = 0
            for upstream_id in self.inverse_topology.get(component_id, []):
                total_inflow += current_step_outflows.get(upstream_id, 0)

            component.set_inflow(total_inflow)

            if hasattr(component, 'is_stateful') and component.is_stateful:
                total_outflow = 0
                for downstream_id in self.topology.get(component_id, []):
                    downstream_comp = self.components[downstream_id]
                    downstream_action = {}
                    downstream_action['upstream_head'] = component.get_state().get('water_level', 0)

                    if self.topology.get(downstream_id):
                        dds_id = self.topology[downstream_id][0]
                        downstream_action['downstream_head'] = self.components[dds_id].get_state().get('water_level', 0)

                    import copy
                    temp_downstream_comp = copy.deepcopy(downstream_comp)

                    temp_next_state = temp_downstream_comp.step(downstream_action, dt)
                    total_outflow += temp_next_state.get('outflow', 0)

                action['outflow'] = total_outflow

            else:
                if self.inverse_topology.get(component_id):
                    up_id = self.inverse_topology[component_id][0]
                    action['upstream_head'] = self.components[up_id].get_state().get('water_level', 0)
                if self.topology.get(component_id):
                    down_id = self.topology[component_id][0]
                    action['downstream_head'] = self.components[down_id].get_state().get('water_level', 0)

            new_states[component_id] = component.step(action, dt)
            current_step_outflows[component_id] = new_states[component_id].get('outflow', 0)

        for component_id, state in new_states.items():
            self.components[component_id].set_state(state)
    
    def export_output_data(self, output_dir: str = "output"):
        """Export logged data from TopicLoggerAgents to CSV files."""
        import os
        import pandas as pd
        from pathlib import Path
        
        if not hasattr(self, '_output_configs'):
            print("No output configurations found for CSV export.")
            return
            
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"Exporting {len(self._output_configs)} output files to '{output_dir}'...")
        
        for output_config in self._output_configs:
            topic = output_config['topic']
            file_name = output_config['file']
            agent_id = output_config['agent_id']
            
            # Find the TopicLoggerAgent
            logger_agent = None
            for agent in self.agents:
                if hasattr(agent, 'agent_id') and agent.agent_id == agent_id:
                    logger_agent = agent
                    break
                    
            if not logger_agent:
                print(f"Warning: TopicLoggerAgent '{agent_id}' not found, skipping '{file_name}'")
                continue
                
            # Extract data from the TopicLoggerAgent's message history
            data_rows = []
            
            # Get message history from the TopicLoggerAgent
            if hasattr(logger_agent, 'get_message_history'):
                message_history = logger_agent.get_message_history()
                
                for entry in message_history:
                    time_val = entry.get('time', 0)
                    message = entry.get('message', {})
                    
                    # Create a row with time and all message data
                    row = {'time': time_val}
                    
                    # Add all message fields to the row
                    if isinstance(message, dict):
                        for key, value in message.items():
                            # Convert values to appropriate types for CSV
                            if isinstance(value, (int, float, str, bool)):
                                row[key] = value
                            else:
                                row[key] = str(value)
                    
                    data_rows.append(row)
            else:
                print(f"Warning: TopicLoggerAgent '{agent_id}' does not have message history method")
            
            if data_rows:
                # Create DataFrame and save to CSV
                df = pd.DataFrame(data_rows)
                file_path = output_path / file_name
                df.to_csv(file_path, index=False)
                print(f"Exported '{file_name}' with {len(data_rows)} rows")
            else:
                print(f"Warning: No data found for topic '{topic}', creating empty file '{file_name}'")
                # Create empty CSV with just headers
                df = pd.DataFrame(columns=['time'])
                file_path = output_path / file_name
                df.to_csv(file_path, index=False)
                
        print("CSV export completed.")
