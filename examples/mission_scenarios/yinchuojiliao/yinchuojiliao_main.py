# -*- coding: utf-8 -*-

"""
Main simulation script for the Yin Chuo Ji Liao Water Transfer Project.

This script sets up and runs a multi-agent simulation for the entire water transfer
system, based on the hierarchical control architecture described in the project
documentation.
"""

import logging
import pandas as pd
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# 添加项目根目录到Python路径，遵循项目结构约定
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Physical Components
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.pipe import Pipe
from core_lib.physical_objects.valve import Valve

# Core Simulation Infrastructure
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core.interfaces import Agent

# Agent Components
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
# TODO: 创建通用的emergency_agent和central_dispatcher_agent
# from mission.agents.emergency_agent import EmergencyAgent
# from mission.agents.central_dispatcher_agent import CentralDispatcherAgent
# from mission.agents.csv_inflow_agent import CsvInflowAgent

# 配置参数常量 - 避免魔数和硬编码
class SimulationConstants:
    """仿真系统常量配置类"""
    
    # 时间参数
    SIMULATION_DURATION_HOURS = 168.0  # 7天仿真时长
    TIME_STEP_HOURS = 1.0  # 1小时时间步长
    PIPE_BURST_TIME_HOURS = 100.0  # 管道爆裂测试时间点
    
    # 物理参数 - 压力阈值（单位：MPa）
    EMERGENCY_PRESSURE_THRESHOLD_MPA = 0.3
    
    # 物理参数 - 水位阈值（单位：m）
    TERMINAL_POOL_LOW_LEVEL_M = 212.0
    TERMINAL_POOL_HIGH_LEVEL_M = 213.0
    INTAKE_SETPOINT_LOW_M = 349.8
    INTAKE_SETPOINT_HIGH_M = 349.2
    
    # PID控制器参数
    class PIDControllerParams:
        # 渠道闸门控制参数
        TAORIVER_KP = -0.1
        TAORIVER_KI = -0.01
        TAORIVER_KD = -0.05
        TAORIVER_SETPOINT_M = 324.20
        
        GUILIU_KP = -0.1
        GUILIU_KI = -0.01
        GUILIU_KD = -0.05
        GUILIU_SETPOINT_M = 320.38
        
        # 阀门控制参数
        ONLINE_VALVE_KP = 0.2
        ONLINE_VALVE_KI = 0.02
        ONLINE_VALVE_KD = 0.1
        ONLINE_VALVE_SETPOINT = 0.65
        
        TERMINAL_VALVE_KP = -0.05
        TERMINAL_VALVE_KI = -0.005
        TERMINAL_VALVE_KD = -0.02
        TERMINAL_VALVE_SETPOINT_M = 212.5
        
        INTAKE_GATE_KP = -0.1
        INTAKE_GATE_KI = -0.01
        INTAKE_GATE_KD = -0.05
        INTAKE_GATE_SETPOINT_M = 349.5
        
        # 输出限制
        MIN_OUTPUT = 0.0
        MAX_OUTPUT = 1.0

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def run_simulation():
    """
    Initializes and runs the full project simulation.
    """
    logging.info("Initializing the Yin Chuo Ji Liao Project simulation...")

    # --- Core Infrastructure ---
    harness = SimulationHarness(config={
        'end_time': SimulationConstants.SIMULATION_DURATION_HOURS,
        'time_step': SimulationConstants.TIME_STEP_HOURS,
        'start_time': 0.0
    })
    message_bus = MessageBus()

    # --- 1. Define and Add Physical Components ---
    logging.info("Creating physical components...")
    components = [
        Reservoir(name="wendegen_reservoir", initial_state={'water_level': 350.0}, parameters={'surface_area': 5e7}),
        Gate(name="water_intake_gate", initial_state={'opening': 0.5}, parameters={'width': 15, 'discharge_coefficient': 0.6}),
        UnifiedCanal(model_type='integral', name="tunnel_1", initial_state={'water_level': 349.0, 'volume': 7e7}, parameters={'length': 70000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Gate(name="taoriver_gate", initial_state={'opening': 0.6}, parameters={}),
        UnifiedCanal(model_type='integral', name="tunnel_2", initial_state={'water_level': 325.0, 'volume': 8e6}, parameters={'length': 8000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Gate(name="guiliu_gate", initial_state={'opening': 0.6}, parameters={}),
        UnifiedCanal(model_type='integral', name="tunnel_3", initial_state={'water_level': 322.0, 'volume': 1e8}, parameters={'length': 100000, 'bottom_width': 20, 'slope': 0.0001, 'side_slope_z': 2, 'manning_n': 0.03}),
        Reservoir(name="connection_pool", initial_state={'water_level': 320.0}, parameters={'surface_area': 1e4}),
        Pipe(name="pipe_1", initial_state={'flow': 15.0, 'pressure': 0.8}, parameters={'length': 20000, 'diameter': 3.0, 'friction_factor': 0.015}),
        Valve(name="online_valve", initial_state={'setting': 0.7}, parameters={}),
        Pipe(name="pipe_2", initial_state={'flow': 15.0, 'pressure': 0.7}, parameters={'length': 80000, 'diameter': 3.0, 'friction_factor': 0.015}),
        Valve(name="terminal_valve", initial_state={'setting': 0.5}, parameters={}),
        Reservoir(name="terminal_pool", initial_state={'water_level': 212.0}, parameters={'surface_area': 1e5})
    ]
    for comp in components:
        harness.add_component(comp)
    comp_map = {c.name: c for c in components}

    # --- 2. Define and Add Agents ---
    agents = []
    logging.info("Creating agents...")

    # 2.1 Perception Layer
    for comp in components:
        agents.append(DigitalTwinAgent(f"twin_{comp.name}", comp, message_bus, f"state/{comp.name}"))

    # 2.2 Local Control Layer - 使用配置常量避免硬编码
    pid_taoriver = PIDController(
        Kp=SimulationConstants.PIDControllerParams.TAORIVER_KP,
        Ki=SimulationConstants.PIDControllerParams.TAORIVER_KI,
        Kd=SimulationConstants.PIDControllerParams.TAORIVER_KD,
        setpoint=SimulationConstants.PIDControllerParams.TAORIVER_SETPOINT_M,
        min_output=SimulationConstants.PIDControllerParams.MIN_OUTPUT,
        max_output=SimulationConstants.PIDControllerParams.MAX_OUTPUT
    )
    harness.add_controller('taoriver_ctrl', pid_taoriver, 'taoriver_gate', 'tunnel_1', 'water_level')
    
    pid_guiliu = PIDController(
        Kp=SimulationConstants.PIDControllerParams.GUILIU_KP,
        Ki=SimulationConstants.PIDControllerParams.GUILIU_KI,
        Kd=SimulationConstants.PIDControllerParams.GUILIU_KD,
        setpoint=SimulationConstants.PIDControllerParams.GUILIU_SETPOINT_M,
        min_output=SimulationConstants.PIDControllerParams.MIN_OUTPUT,
        max_output=SimulationConstants.PIDControllerParams.MAX_OUTPUT
    )
    harness.add_controller('guiliu_ctrl', pid_guiliu, 'guiliu_gate', 'tunnel_2', 'water_level')
    
    pid_online_valve = PIDController(
        Kp=SimulationConstants.PIDControllerParams.ONLINE_VALVE_KP,
        Ki=SimulationConstants.PIDControllerParams.ONLINE_VALVE_KI,
        Kd=SimulationConstants.PIDControllerParams.ONLINE_VALVE_KD,
        setpoint=SimulationConstants.PIDControllerParams.ONLINE_VALVE_SETPOINT,
        min_output=SimulationConstants.PIDControllerParams.MIN_OUTPUT,
        max_output=SimulationConstants.PIDControllerParams.MAX_OUTPUT
    )
    harness.add_controller('online_valve_ctrl', pid_online_valve, 'online_valve', 'pipe_2', 'pressure')
    
    pid_terminal_valve = PIDController(
        Kp=SimulationConstants.PIDControllerParams.TERMINAL_VALVE_KP,
        Ki=SimulationConstants.PIDControllerParams.TERMINAL_VALVE_KI,
        Kd=SimulationConstants.PIDControllerParams.TERMINAL_VALVE_KD,
        setpoint=SimulationConstants.PIDControllerParams.TERMINAL_VALVE_SETPOINT_M,
        min_output=SimulationConstants.PIDControllerParams.MIN_OUTPUT,
        max_output=SimulationConstants.PIDControllerParams.MAX_OUTPUT
    )
    harness.add_controller('terminal_valve_ctrl', pid_terminal_valve, 'terminal_valve', 'terminal_pool', 'water_level')
    
    pid_intake_gate = PIDController(
        Kp=SimulationConstants.PIDControllerParams.INTAKE_GATE_KP,
        Ki=SimulationConstants.PIDControllerParams.INTAKE_GATE_KI,
        Kd=SimulationConstants.PIDControllerParams.INTAKE_GATE_KD,
        setpoint=SimulationConstants.PIDControllerParams.INTAKE_GATE_SETPOINT_M,
        min_output=SimulationConstants.PIDControllerParams.MIN_OUTPUT,
        max_output=SimulationConstants.PIDControllerParams.MAX_OUTPUT
    )
    harness.add_controller('intake_gate_ctrl', pid_intake_gate, 'water_intake_gate', 'tunnel_1', 'water_level')

    # 2.3 Supervisory and Emergency Layer - 创建简化的应急处理智能体
    class SimpleEmergencyAgent(Agent):
        """简化的应急处理智能体"""
        def __init__(self, agent_id: str, message_bus: MessageBus, 
                     monitored_topics: list, pressure_threshold: float, action_topic: str):
            super().__init__(agent_id)
            self.bus = message_bus
            self.pressure_threshold = pressure_threshold
            self.action_topic = action_topic
            self.emergency_triggered = False
            
            for topic in monitored_topics:
                self.bus.subscribe(topic, self.handle_pressure_message)
        
        def handle_pressure_message(self, message):
            if 'pressure' not in message:
                return
            pressure = message['pressure']
            if pressure < self.pressure_threshold and not self.emergency_triggered:
                logging.warning(f"Emergency triggered! Pressure {pressure} below threshold {self.pressure_threshold}")
                self.bus.publish(self.action_topic, {'control_signal': 0.0})  # 关闭闸门
                self.emergency_triggered = True
        
        def run(self, current_time: float):
            pass  # 事件驱动，无需在run中处理
    
    # 2.3.1 应急处理智能体
    emergency_agent = SimpleEmergencyAgent(
        'emergency_agent', 
        message_bus, 
        ['state/pipe_1', 'state/pipe_2'], 
        SimulationConstants.EMERGENCY_PRESSURE_THRESHOLD_MPA, 
        'control/water_intake_gate'
    )
    agents.append(emergency_agent)
    
    # 2.3.2 中央调度智能体 - 简化实现
    class SimpleCentralDispatcherAgent(Agent):
        """简化的中央调度智能体"""
        def __init__(self, agent_id: str, message_bus: MessageBus, monitored_topic: str, 
                     observation_key: str, command_topic: str, dispatch_config: dict):
            super().__init__(agent_id)
            self.bus = message_bus
            self.command_topic = command_topic
            self.config = dispatch_config
            self.observation_key = observation_key
            
            self.bus.subscribe(monitored_topic, self.handle_water_level_message)
        
        def handle_water_level_message(self, message):
            if self.observation_key not in message:
                return
            
            water_level = message[self.observation_key]
            
            if water_level < self.config['low_level']:
                new_setpoint = self.config['low_setpoint']
                self.bus.publish(self.command_topic, {'new_setpoint': new_setpoint})
                logging.info(f"Low level detected: {water_level}m, setting intake to {new_setpoint}m")
            elif water_level > self.config['high_level']:
                new_setpoint = self.config['high_setpoint']
                self.bus.publish(self.command_topic, {'new_setpoint': new_setpoint})
                logging.info(f"High level detected: {water_level}m, setting intake to {new_setpoint}m")
        
        def run(self, current_time: float):
            pass  # 事件驱动，无需在run中处理
    
    dispatcher_config = {
        'low_level': SimulationConstants.TERMINAL_POOL_LOW_LEVEL_M,
        'high_level': SimulationConstants.TERMINAL_POOL_HIGH_LEVEL_M,
        'low_setpoint': SimulationConstants.INTAKE_SETPOINT_LOW_M,
        'high_setpoint': SimulationConstants.INTAKE_SETPOINT_HIGH_M
    }
    
    central_dispatcher = SimpleCentralDispatcherAgent(
        'central_dispatcher', 
        message_bus, 
        'state/terminal_pool', 
        'water_level', 
        'command/intake_gate_ctrl', 
        dispatcher_config
    )
    agents.append(central_dispatcher)
    
    def intake_setpoint_updater(message):
        if 'new_setpoint' not in message:
            raise KeyError("新设定点参数'new_setpoint'是必需的")
        pid_intake_gate.set_setpoint(message['new_setpoint'])
    
    message_bus.subscribe('command/intake_gate_ctrl', intake_setpoint_updater)

    # 2.4 Data Input Layer - 创建简化的CSV入流智能体
    class SimpleCsvInflowAgent(Agent):
        """简化的CSV入流智能体"""
        def __init__(self, agent_id: str, target_component, csv_file: str, time_column: str, data_column: str):
            super().__init__(agent_id)
            self.target_component = target_component
            self.csv_file = csv_file
            self.time_column = time_column
            self.data_column = data_column
            self.data = None
            self.current_index = 0
            self._load_data()
        
        def _load_data(self):
            """加载CSV数据"""
            try:
                import pandas as pd
                file_path = Path(__file__).parent / self.csv_file
                if file_path.exists():
                    self.data = pd.read_csv(file_path)
                    logging.info(f"Loaded {len(self.data)} inflow data points from {file_path}")
                else:
                    logging.warning(f"CSV file not found: {file_path}, using default inflow")
                    # 创建默认数据
                    self.data = pd.DataFrame({
                        self.time_column: list(range(0, int(SimulationConstants.SIMULATION_DURATION_HOURS) + 1)),
                        self.data_column: [50.0] * (int(SimulationConstants.SIMULATION_DURATION_HOURS) + 1)
                    })
            except Exception as e:
                logging.error(f"Failed to load CSV data: {e}, using default inflow")
                # 创建默认数据
                self.data = pd.DataFrame({
                    self.time_column: list(range(0, int(SimulationConstants.SIMULATION_DURATION_HOURS) + 1)),
                    self.data_column: [50.0] * (int(SimulationConstants.SIMULATION_DURATION_HOURS) + 1)
                })
        
        def run(self, current_time: float):
            """更新入流数据"""
            if self.data is None or len(self.data) == 0:
                return
            
            # 找到对应时间的入流数据
            time_mask = self.data[self.time_column] <= current_time
            if time_mask.any():
                latest_row = self.data[time_mask].iloc[-1]
                inflow_value = latest_row[self.data_column]
                if hasattr(self.target_component, 'set_inflow'):
                    self.target_component.set_inflow(inflow_value)
    
    csv_inflow_agent = SimpleCsvInflowAgent(
        'csv_inflow', 
        comp_map['wendegen_reservoir'], 
        'data/historical_inflow.csv', 
        'time', 
        'inflow'
    )
    agents.append(csv_inflow_agent)

    for agent in agents:
        harness.add_agent(agent)

    # --- 3. Define Physical Topology ---
    logging.info("Connecting physical components...")
    # (Connections are defined in the component list order for this linear system)
    for i in range(len(components) - 1):
        harness.add_connection(components[i].name, components[i+1].name)

    # --- 4. Build and Run Simulation ---
    logging.info("Building and running simulation...")
    harness.build()

    # 创建管道爆裂测试智能体 - 使用配置常量而非硬编码
    class PipeBurstTestAgent(Agent):
        """管道爆裂测试智能体，用于测试应急响应系统"""
        def __init__(self, agent_id: str, component_map: dict, burst_time: float, target_pipe: str):
            super().__init__(agent_id)
            self.comp_map = component_map
            self.burst_time = burst_time
            self.target_pipe = target_pipe
            self.burst_triggered = False
        
        def run(self, current_time: float):
            if not self.burst_triggered and abs(current_time - self.burst_time) < 0.5:
                logging.warning(f"!!! Simulating pipe burst at time {current_time} for testing emergency response !!!")
                if self.target_pipe in self.comp_map:
                    # 设置低压力触发应急响应
                    if hasattr(self.comp_map[self.target_pipe], 'pressure'):
                        self.comp_map[self.target_pipe].pressure = 0.1  # 0.1 MPa，低于阈值
                self.burst_triggered = True
    
    burst_agent = PipeBurstTestAgent(
        "pipe_burst_test_agent", 
        comp_map, 
        SimulationConstants.PIPE_BURST_TIME_HOURS, 
        'pipe_1'
    )
    harness.add_agent(burst_agent)

    harness.run_mas_simulation()
    logging.info("Simulation complete.")

    # --- 5. Plotting and Verification ---
    # Process history from harness
    history = harness.history
    log_data = []
    for step_data in history:
        time = step_data['time']
        entry = {'time': time}
        for comp_name, state in step_data.items():
            if comp_name == 'time': continue
            for key, value in state.items():
                entry[f"{comp_name}_{key}"] = value
        # also log the pid setpoint
        entry['intake_pid_setpoint'] = pid_intake_gate.setpoint
        log_data.append(entry)
    log_df = pd.DataFrame(log_data)
    log_df.set_index('time', inplace=True)

    fig, axes = plt.subplots(4, 1, figsize=(15, 20), sharex=True)
    fig.suptitle('Yin Chuo Ji Liao Project Simulation Results', fontsize=16)
    axes[0].plot(log_df.index, log_df['wendegen_reservoir_water_level'], label='Wendegen Reservoir')
    axes[0].plot(log_df.index, log_df['tunnel_1_water_level'], label='Tunnel 1')
    axes[0].plot(log_df.index, log_df['terminal_pool_water_level'], label='Terminal Pool')
    axes[0].set_ylabel('Water Level (m)'); axes[0].legend(); axes[0].grid(True); axes[0].set_title('Water Levels')
    axes[1].plot(log_df.index, log_df['water_intake_gate_opening'], label='Intake Gate')
    axes[1].plot(log_df.index, log_df['taoriver_gate_opening'], label='Taoriver Gate')
    axes[1].set_ylabel('Opening (0-1)'); axes[1].legend(); axes[1].grid(True); axes[1].set_title('Gate Openings')
    axes[1].axvline(x=100, color='k', linestyle=':', label='Pipe Burst')
    axes[2].plot(log_df.index, log_df.get('pipe_2_pressure', pd.Series(0, index=log_df.index)), label='Pipe 2 Pressure')
    axes[2].axhline(y=0.3, color='r', linestyle='--', label='Emergency Threshold')
    axes[2].set_ylabel('Pressure (MPa)'); axes[2].legend(); axes[2].grid(True); axes[2].set_title('Pipeline Pressure')
    axes[2].axvline(x=100, color='k', linestyle=':', label='Pipe Burst')
    axes[3].plot(log_df.index, log_df['intake_pid_setpoint'], label='Intake PID Setpoint', drawstyle='steps-post')
    axes[3].set_ylabel('Setpoint (m)'); axes[3].legend(); axes[3].grid(True); axes[3].set_title('Central Dispatcher Action')

    plt.xlabel('Time (hours)'); plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    output_filename = "yinchuojiliao_simulation_results.png"
    plt.savefig(output_filename)
    logging.info(f"Saved plot to {output_filename}")


# 已移至主函数内部，使用配置化的PipeBurstTestAgent

if __name__ == "__main__":
    run_simulation()
