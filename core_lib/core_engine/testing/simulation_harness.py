"""
A testing and simulation harness for running the Smart Water Platform.
"""
import threading
import copy
import math
import numbers
from collections import deque
from core_lib.core.interfaces import Simulatable, Agent, Controller
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.disturbances.disturbance_framework import DisturbanceManager, BaseDisturbance
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

        # 兼容旧版本示例中使用的 "duration" 字段，并确保与显式 "end_time"
        # 设置保持一致。如果同时提供，则以 end_time 为准；否则根据
        # duration 推导得到终止时间。
        if 'end_time' in config:
            self.end_time = config['end_time']
        elif 'duration' in config:
            self.end_time = self.start_time + config['duration']
        else:
            self.end_time = self.start_time + 100

        # Support both legacy 'dt' and more descriptive 'time_step' keys.
        if 'dt' in config:
            self.dt = config['dt']
        else:
            self.dt = config.get('time_step', 1.0)
        if not isinstance(self.dt, numbers.Real):
            raise ValueError("Simulation time step must be a real number.")
        self.dt = float(self.dt)
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
        
        # 扰动管理器
        self.disturbance_manager = DisturbanceManager()

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
    
    def add_disturbance(self, disturbance: BaseDisturbance):
        """添加扰动到仿真中"""
        self.disturbance_manager.register_disturbance(disturbance)
        print(f"扰动 {disturbance.config.disturbance_id} 已添加到仿真中")
    
    def remove_disturbance(self, disturbance_id: str):
        """从仿真中移除扰动"""
        self.disturbance_manager.remove_disturbance(disturbance_id)
        print(f"扰动 {disturbance_id} 已从仿真中移除")
    
    def get_active_disturbances(self) -> List[str]:
        """获取当前活跃的扰动列表"""
        return self.disturbance_manager.get_active_disturbances()
    
    def get_disturbance_history(self) -> List[Dict[str, Any]]:
        """获取扰动历史"""
        return self.disturbance_manager.get_disturbance_history()

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
            component_state = self.components[cid].get_state()
            step_history[cid] = component_state if component_state is not None else {}
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
        
        # 返回仿真结果
        return {
            'history': self.history,
            'final_time': self.t,
            'simulation_steps': len(self.history)
        }

    def run_simulation(self):
        """运行简单仿真（非智能体模式）"""
        # Ensure previous state does not leak between independent runs
        self.history = []
        self.t = self.start_time

        # Automatically build the topology if the caller forgot to do so
        if not self.sorted_components:
            self.build()
        else:
            self.is_running = True

        # Capture the initial state snapshot before stepping the system so we
        # obtain a time-aligned history (t = start_time represents the initial
        # condition, subsequent entries correspond to the end of each interval).
        initial_snapshot = {"time": float(self.t)}
        for component_id in self.sorted_components:
            state = self.components[component_id].get_state()
            initial_snapshot[component_id] = copy.deepcopy(state) if isinstance(state, dict) else {}
        self.history.append(initial_snapshot)

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

            # 更新时间至区间末端后记录状态
            self.t += self.dt

            # Phase 3: 记录历史
            step_history = {'time': float(self.t)}
            for cid in self.sorted_components:
                state = self.components[cid].get_state()
                step_history[cid] = copy.deepcopy(state) if isinstance(state, dict) else {}
            self.history.append(step_history)

        print(f"Simple simulation completed at time {self.t:.2f}s")
        print(f"Generated {len(self.history)} steps of history data.")

        # Mark the harness as stopped so follow-up runs can restart cleanly
        self.is_running = False

        # Convert the recorded history into columnar time series for downstream
        # validation utilities. Each component state dictionary is flattened
        # into "component.variable" keys.
        results: Dict[str, List[float]] = {"time": []}
        series_cache: Dict[str, List[float]] = {}

        for entry in self.history:
            results["time"].append(float(entry.get("time", 0.0)))
            current_index = len(results["time"]) - 1

            for component_id, state in entry.items():
                if component_id == "time" or not isinstance(state, dict):
                    continue

                for key, value in state.items():
                    if not isinstance(value, numbers.Real):
                        continue

                    numeric_value = float(value)
                    if not math.isfinite(numeric_value):
                        continue

                    series_key = f"{component_id}.{key}"
                    if series_key not in series_cache:
                        # Pad the new series so it aligns with previously recorded timestamps
                        series_cache[series_key] = [0.0] * current_index

                    series_cache[series_key].append(numeric_value)

            # 对于本次时间步未更新的序列，重复上一时刻的值以保持长度一致
            for series_key, values in series_cache.items():
                if len(values) < len(results["time"]):
                    fill_value = values[-1] if values else 0.0
                    values.append(fill_value)

        # 追加整理后的序列
        for key, values in series_cache.items():
            results[key] = values

        return results

    def _step_physical_models(self, dt: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        # 更新扰动状态
        disturbance_effects = self.disturbance_manager.update(self.t, dt, self.components)
        
        new_states = {}
        current_step_outflows = {}
        
        # 记录哪些组件受到扰动影响，避免自动入流覆盖
        disturbed_components = set()
        for disturbance_id, effect in disturbance_effects.items():
            if 'applied_inflow' in effect:
                # 找到对应的扰动配置
                for dist_id, disturbance in self.disturbance_manager.active_disturbances.items():
                    if dist_id == disturbance_id:
                        disturbed_components.add(disturbance.config.target_component_id)
                        break

        for component_id in self.sorted_components:
            component = self.components[component_id]
            action = {'control_signal': controller_actions.get(component_id)}

            upstream_inflow = 0
            for upstream_id in self.inverse_topology.get(component_id, []):
                upstream_inflow += current_step_outflows.get(upstream_id, 0)

            # 只有在组件没有受到入流扰动影响时才设置自动计算的入流
            if component_id not in disturbed_components:
                base_inflow = 0.0
                if hasattr(component, 'base_inflow'):
                    base_inflow = getattr(component, 'base_inflow')
                elif hasattr(component, '_base_inflow'):
                    base_inflow = getattr(component, '_base_inflow', 0.0)

                combined_inflow = base_inflow + upstream_inflow
                component.set_inflow(combined_inflow, preserve_base=True)

            if hasattr(component, 'is_stateful') and component.is_stateful:
                total_outflow = 0
                for downstream_id in self.topology.get(component_id, []):
                    downstream_comp = self.components[downstream_id]
                    downstream_action = {}
                    component_state = component.get_state()
                    downstream_action['upstream_head'] = component_state.get('water_level', 0) if component_state else 0

                    if self.topology.get(downstream_id):
                        dds_id = self.topology[downstream_id][0]
                        dds_state = self.components[dds_id].get_state()
                        downstream_action['downstream_head'] = dds_state.get('water_level', 0) if dds_state else 0

                    import copy
                    temp_downstream_comp = copy.deepcopy(downstream_comp)

                    temp_next_state = temp_downstream_comp.step(downstream_action, dt)
                    total_outflow += temp_next_state.get('outflow', 0)

                action['outflow'] = total_outflow

            else:
                if self.inverse_topology.get(component_id):
                    up_id = self.inverse_topology[component_id][0]
                    up_state = self.components[up_id].get_state()
                    action['upstream_head'] = up_state.get('water_level', 0) if up_state else 0
                if self.topology.get(component_id):
                    down_id = self.topology[component_id][0]
                    down_state = self.components[down_id].get_state()
                    action['downstream_head'] = down_state.get('water_level', 0) if down_state else 0

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
