"""
A testing and simulation harness for running the Smart Water Platform.
"""
import threading
import copy
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
        self.start_time = config["start_time"]
        self.end_time = config['end_time']
        self.time_step = config['time_step']
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
        
        # 常量定义，避免魔数
        self.DEFAULT_OBSERVATION_VALUE = 0.0  # 默认观测值
        self.DEFAULT_INFLOW_VALUE = 0.0       # 默认入流值
        self.DEFAULT_WATER_LEVEL = 0.0        # 默认水位
        self.DEFAULT_OUTFLOW_VALUE = 0.0      # 默认出流值
        self.DEFAULT_TIME_VALUE = 0.0         # 默认时间值
        self.FIRST_COMPONENT_INDEX = 0        # 第一个组件索引

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
        self._step_physical_models(self.time_step)

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
        self.t += self.time_step

    def run_mas_simulation(self):
        """运行多智能体系统仿真"""
        print(f"Starting MAS simulation from {self.start_time} to {self.end_time} with time_step={self.time_step}")
        
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
        print(f"Starting simple simulation from {self.start_time} to {self.end_time} with time_step={self.time_step}")
        
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
                    observation = observed_component.get_state().get(spec.observation_key, self.DEFAULT_OBSERVATION_VALUE)
                    
                    # 计算控制动作
                    action = spec.controller.compute_control_action({'process_variable': observation}, self.time_step)
                    controller_actions[spec.controlled_id] = action
                    
                except Exception as e:
                    print(f"Error in controller {controller_id}: {e}")
            
            # Phase 2: 步进物理模型
            self._step_physical_models(self.time_step, controller_actions)
            
            # Phase 3: 记录历史
            step_history = {'time': self.t}
            for cid in self.sorted_components:
                step_history[cid] = self.components[cid].get_state()
            self.history.append(step_history)
            
            # 更新时间
            self.t += self.time_step
        
        print(f"Simple simulation completed at time {self.t:.2f}s")
        print(f"Generated {len(self.history)} steps of history data.")

    def _step_physical_models(self, time_step: float, controller_actions: Dict[str, Any] = None):
        if controller_actions is None:
            controller_actions = {}

        # 更新扰动状态
        disturbance_effects = self.disturbance_manager.update(self.t, time_step, self.components)
        
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

            # 处理入流设置：只有非边界组件才自动计算入流
            upstream_components = self.inverse_topology.get(component_id, [])
            if upstream_components:  # 有上游组件，自动计算入流
                total_inflow = self.DEFAULT_INFLOW_VALUE
                for upstream_id in upstream_components:
                    upstream_outflow = current_step_outflows.get(upstream_id, self.DEFAULT_INFLOW_VALUE)
                    total_inflow += upstream_outflow
                    print(f"[DEBUG] 组件 {component_id} 的上游组件 {upstream_id} 出流: {upstream_outflow}")
                
                print(f"[DEBUG] 组件 {component_id} 计算的总入流: {total_inflow}")
                
                # 只有在组件没有受到入流扰动影响时才设置自动计算的入流
                if component_id not in disturbed_components:
                    if hasattr(component, '_inflow') and component._inflow != total_inflow:
                        print(f"[DEBUG] 组件 {component_id} 当前入流 {component._inflow} != 计算入流 {total_inflow}，调用 set_inflow")
                        component.set_inflow(total_inflow)
                    elif not hasattr(component, '_inflow'):
                        print(f"[DEBUG] 组件 {component_id} 没有 _inflow 属性，调用 set_inflow")
                        component.set_inflow(total_inflow)
                    else:
                        print(f"[DEBUG] 组件 {component_id} 当前入流 {component._inflow} == 计算入流 {total_inflow}，跳过 set_inflow")
            # 否则，边界组件（如上游水库）保持其原有入流设置

            # 为所有组件设置water head信息（无论是否stateful）
            if self.inverse_topology.get(component_id):
                up_id = self.inverse_topology[component_id][self.FIRST_COMPONENT_INDEX]
                up_state = self.components[up_id].get_state()
                action['upstream_head'] = up_state.get('water_level', self.DEFAULT_WATER_LEVEL) if up_state else self.DEFAULT_WATER_LEVEL
            if self.topology.get(component_id):
                down_id = self.topology[component_id][self.FIRST_COMPONENT_INDEX]
                down_state = self.components[down_id].get_state()
                action['downstream_head'] = down_state.get('water_level', self.DEFAULT_WATER_LEVEL) if down_state else self.DEFAULT_WATER_LEVEL

            if hasattr(component, 'is_stateful') and component.is_stateful:
                # Stateful组件：根据下游需求计算出流
                total_outflow = self.DEFAULT_OUTFLOW_VALUE
                for downstream_id in self.topology.get(component_id, []):  # 遍历下游
                    downstream_comp = self.components[downstream_id]
                    downstream_action = {}
                    component_state = component.get_state()
                    downstream_action['upstream_head'] = component_state.get('water_level', self.DEFAULT_WATER_LEVEL) if component_state else self.DEFAULT_WATER_LEVEL

                    if self.topology.get(downstream_id):
                        dds_id = self.topology[downstream_id][self.FIRST_COMPONENT_INDEX]
                        dds_state = self.components[dds_id].get_state()
                        downstream_action['downstream_head'] = dds_state.get('water_level', self.DEFAULT_WATER_LEVEL) if dds_state else self.DEFAULT_WATER_LEVEL

                    import copy
                    temp_downstream_comp = copy.deepcopy(downstream_comp)

                    temp_next_state = temp_downstream_comp.step(downstream_action, time_step)
                    total_outflow += temp_next_state.get('outflow', self.DEFAULT_OUTFLOW_VALUE)  # 计算下游的出流

                # 如果计算出的出流为0，为上游水库设置一个合理的初始出流值
                if total_outflow == 0 and component_id == 'upstream_reservoir':
                    total_outflow = 10.0  # 设置初始出流为10 m³/s
                    print(f"[DEBUG] 为上游水库设置初始出流: {total_outflow} m³/s")

                action['outflow'] = total_outflow  # 计算当前步骤的出流

            new_states[component_id] = component.step(action, time_step)
            current_step_outflows[component_id] = new_states[component_id].get('outflow', self.DEFAULT_OUTFLOW_VALUE)

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
                    time_val = entry.get('time', self.DEFAULT_TIME_VALUE)
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
