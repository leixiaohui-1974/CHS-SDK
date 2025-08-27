"""
端到端案例研究：一个用于渠道网络的分层MPC-PID控制系统。

该脚本构建并运行一个包含两个闸门和三个渠道的串联仿真系统，
完全按照详细的设计规范。它展示了一个分层分布式控制架构，
其中一个中央MPC智能体为两个本地PID控制器设定目标。

系统的核心目标是在应对上游入流扰动时，将每个闸门前的水位
维持在动态调整的最优设定点。

工作流程：
1. 预测：一个“全知”的预测智能体发布对未来入流的完美预测。
2. 正常运行（0-100秒）：MPC将设定点维持在正常水平。PID控制器跟踪这些设定点。
3. 扰动（100-200秒）：一个扰动智能体注入额外入流。
4. MPC响应：中央MPC智能体接收到预测，并计算出更低的“应急”设定点以预先释放库容。
5. PID响应：本地PID控制器接收到新的设定点，并调整闸门开度以达到这些新目标。
6. 恢复（200秒后）：扰动结束，MPC逐渐将设定点恢复到正常水平。
"""
import numpy as np
import matplotlib.pyplot as plt

from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.io.physical_io_agent import PhysicalIOAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.simulation_identification.disturbances.rainfall_agent import RainfallAgent
from swp.local_agents.prediction.inflow_forecaster_agent import InflowForecasterAgent
from swp.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent
from swp.core.interfaces import Agent

class DataLoggerAgent(Agent):
    """一个简单的智能体，用于记录来自特定主题的数据以供绘图。"""
    def __init__(self, agent_id, bus, topics_to_log):
        super().__init__(agent_id)
        self.bus = bus
        self.topics_to_log = topics_to_log
        self.latest_values = {name: None for name in topics_to_log.values()}
        self.log = []
        for topic, name in self.topics_to_log.items():
            self.bus.subscribe(topic, lambda msg, t=name: self._update_latest(msg, t))

    def _update_latest(self, message, topic_name):
        """仅更新最新值，不在回调中记录。"""
        self.latest_values[topic_name] = message.get('new_setpoint')

    def run(self, current_time: float):
        """在每个时间步，用正确的时间戳记录最新值。"""
        for topic_name, value in self.latest_values.items():
            if value is not None:
                self.log.append({
                    'time': current_time,
                    'topic': topic_name,
                    'value': value
                })

def setup_system(bus: MessageBus, sim_dt: float, user_params: dict):
    """设置仿真所需的所有物理组件和智能体。"""

    # 定义通信主题
    UPSTREAM_STATE_TOPIC = "state/canal/upstream"
    DOWNSTREAM_STATE_TOPIC = "state/canal/downstream"
    UPSTREAM_CMD_TOPIC = "command/pid1/setpoint"
    DOWNSTREAM_CMD_TOPIC = "command/pid2/setpoint"
    GATE1_ACTION_TOPIC = "action/gate1/opening"
    GATE2_ACTION_TOPIC = "action/gate2/opening"
    INFLOW_FORECAST_TOPIC = "forecast/inflow"
    DISTURBANCE_TOPIC = "disturbance/upstream/inflow"

    # 1. 物理组件
    # Note: Using the now-fixed Canal class instead of Reservoir
    canal_params = {
        'bottom_width': 20, 'length': 5000, 'slope': 0.0001,
        'side_slope_z': 2, 'manning_n': 0.03
    }
    normal_water_level = 5.0
    surface_area = canal_params['length'] * (canal_params['bottom_width'] + canal_params['side_slope_z'] * normal_water_level)
    # V = L * (b*y + z*y^2) - Or more simply, Area * Level
    initial_volume = surface_area * normal_water_level

    gate_params = {'discharge_coefficient': 0.8, 'width': 5, 'max_opening': 3.0, 'max_rate_of_change': 0.1}

    # sink_canal 仍然是一个渠道，因为它的出流是自由的
    sink_canal_params = {'bottom_width': 20, 'length': 1000, 'slope': 0.001, 'side_slope_z': 2, 'manning_n': 0.025}

    upstream_pool = Canal("upstream_canal", {'volume': initial_volume, 'water_level': normal_water_level}, canal_params, message_bus=bus, inflow_topic=DISTURBANCE_TOPIC)
    control_gate_1 = Gate("control_gate_1", {'opening': 1.0}, gate_params) # Decoupled from bus
    downstream_pool = Canal("downstream_canal", {'volume': initial_volume, 'water_level': normal_water_level}, canal_params)
    final_gate_2 = Gate("final_gate_2", {'opening': 1.0}, gate_params) # Decoupled from bus
    sink_canal = Canal("sink_canal", {'volume': 0, 'water_level': 0}, sink_canal_params)

    components = [upstream_pool, control_gate_1, downstream_pool, final_gate_2, sink_canal]

    # 2. 智能体组件
    # IO Agent - a single agent now handles all hardware abstraction
    io_agent = PhysicalIOAgent("io_agent_main", bus,
        sensors_config={}, # DigitalTwinAgents are reading directly for this example
        actuators_config={
            'gate1_actuator': {'obj': control_gate_1, 'target_attr': 'target_opening', 'topic': GATE1_ACTION_TOPIC, 'control_key': 'control_signal'},
            'gate2_actuator': {'obj': final_gate_2, 'target_attr': 'target_opening', 'topic': GATE2_ACTION_TOPIC, 'control_key': 'control_signal'}
        }
    )

    # 数字孪生
    twin_upstream = DigitalTwinAgent("twin_agent_upstream", upstream_pool, bus, UPSTREAM_STATE_TOPIC)
    twin_downstream = DigitalTwinAgent("twin_agent_downstream", downstream_pool, bus, DOWNSTREAM_STATE_TOPIC)

    # 本地PID控制器
    pid1 = PIDController(Kp=-0.5, Ki=-0.1, Kd=-0.05, setpoint=user_params['mpc']['normal_setpoint_upstream'], min_output=0, max_output=gate_params['max_opening'])
    pid2 = PIDController(Kp=-0.5, Ki=-0.1, Kd=-0.05, setpoint=user_params['mpc']['normal_setpoint_downstream'], min_output=0, max_output=gate_params['max_opening'])

    lca1 = LocalControlAgent("gate_control_agent_1", pid1, bus, UPSTREAM_STATE_TOPIC, 'water_level', GATE1_ACTION_TOPIC, sim_dt, command_topic=UPSTREAM_CMD_TOPIC)
    lca2 = LocalControlAgent("gate_control_agent_2", pid2, bus, DOWNSTREAM_STATE_TOPIC, 'water_level', GATE2_ACTION_TOPIC, sim_dt, command_topic=DOWNSTREAM_CMD_TOPIC)

    # 扰动和预测智能体
    rainfall_agent = RainfallAgent("rainfall_agent", bus, user_params['disturbance'])
    forecaster_config = user_params['forecaster']
    forecaster_config.update({"forecast_topic": INFLOW_FORECAST_TOPIC, "dt": sim_dt, "prediction_horizon": user_params['mpc']['prediction_horizon']})
    forecaster = InflowForecasterAgent("rainfall_forecaster", bus, forecaster_config)

    # 中央MPC调度器
    mpc_config = {
        "prediction_horizon": user_params['mpc']['prediction_horizon'],
        "dt": sim_dt,
        "q_weight": user_params['mpc']['q_weight'],
        "r_weight": user_params['mpc']['r_weight'],
        "state_keys": ['upstream_level', 'downstream_level'],
        "state_subscriptions": {'upstream_level': UPSTREAM_STATE_TOPIC, 'downstream_level': DOWNSTREAM_STATE_TOPIC},
        "forecast_subscription": INFLOW_FORECAST_TOPIC,
        "command_topics": {'upstream_cmd': UPSTREAM_CMD_TOPIC, 'downstream_cmd': DOWNSTREAM_CMD_TOPIC},
        "normal_setpoints": [user_params['mpc']['normal_setpoint_upstream'], user_params['mpc']['normal_setpoint_downstream']],
        "emergency_setpoint": user_params['mpc']['emergency_setpoint'],
        "flood_thresholds": [user_params['mpc']['upstream_flood_threshold'], user_params['mpc']['downstream_flood_threshold']],
        "canal_surface_areas": [surface_area] * 2,
        "outflow_coefficient": 25.0 # 需要调整的简化参数
    }
    central_dispatcher = CentralMPCAgent("central_dispatcher", bus, mpc_config)

    # 数据记录器
    logger = DataLoggerAgent("logger", bus, {
        UPSTREAM_CMD_TOPIC: "upstream_setpoint",
        DOWNSTREAM_CMD_TOPIC: "downstream_setpoint"
    })

    agents = [io_agent, twin_upstream, twin_downstream, lca1, lca2, rainfall_agent, forecaster, central_dispatcher, logger]

    return components, agents, logger

def plot_results(harness: SimulationHarness, logger: DataLoggerAgent, user_params: dict):
    """绘制仿真结果图表。"""
    import pandas as pd

    history = harness.history
    if not history:
        print("No history to plot.")
        return

    # 1. 将物理组件的历史记录转换为DataFrame
    flat_history = []
    for step in history:
        row = {'time': step['time']}
        for component_name, states in step.items():
            if component_name == 'time' or not isinstance(states, dict): continue
            for state_key, value in states.items():
                row[f"{component_name}.{state_key}"] = value
        flat_history.append(row)
    results = pd.DataFrame(flat_history).set_index('time')

    # 2. 将记录器的数据转换为DataFrame
    if logger.log:
        log_df = pd.DataFrame(logger.log).set_index('time')
        # 将长格式的日志数据透视为宽格式
        setpoint_df = log_df.pivot(columns='topic', values='value')
        # 合并两个DataFrame
        results = results.join(setpoint_df, how='outer').ffill()

    fig, axes = plt.subplots(3, 1, figsize=(15, 12), sharex=True)

    # 图1: 水位
    axes[0].plot(results.index, results['upstream_canal.water_level'], label='Upstream Canal Level')
    axes[0].plot(results.index, results['downstream_canal.water_level'], label='Downstream Canal Level')
    if 'upstream_setpoint' in results.columns:
        axes[0].plot(results.index, results['upstream_setpoint'], '--', label='Upstream Setpoint (from MPC)')
    if 'downstream_setpoint' in results.columns:
        axes[0].plot(results.index, results['downstream_setpoint'], '--', label='Downstream Setpoint (from MPC)')
    axes[0].axhline(y=5.0, color='grey', linestyle=':', label='Normal Setpoint')
    axes[0].axhline(y=4.0, color='red', linestyle=':', label='Emergency Setpoint')
    axes[0].axvline(x=100, color='k', linestyle='--', label='Disturbance Start')
    axes[0].axvline(x=200, color='k', linestyle='--')
    axes[0].set_title('Canal Water Levels and MPC Setpoints')
    axes[0].set_ylabel('Water Level (m)')
    axes[0].legend()
    axes[0].grid(True)

    # 图2: 闸门开度
    axes[1].plot(results.index, results['control_gate_1.opening'], label='Gate 1 Opening')
    axes[1].plot(results.index, results['final_gate_2.opening'], label='Gate 2 Opening')
    axes[1].set_title('Gate Openings')
    axes[1].set_ylabel('Opening (m)')
    axes[1].legend()
    axes[1].grid(True)

    # 图3: 流量
    axes[2].plot(results.index, results['upstream_canal.outflow'], label='Upstream Canal Outflow')
    axes[2].plot(results.index, results['downstream_canal.outflow'], label='Downstream Canal Outflow')
    # 手动添加扰动数据以便绘图
    disturbance_inflow = [user_params['disturbance']['inflow_rate'] if 100 <= t < 200 else 0 for t in results.index]
    axes[2].plot(results.index, disturbance_inflow, label='Disturbance Inflow', color='red', linestyle='-.')
    axes[2].set_title('Flow Rates')
    axes[2].set_ylabel('Flow (m^3/s)')
    axes[2].set_xlabel('Time (s)')
    axes[2].legend()
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig("hierarchical_mpc_control_results.png")
    print("\nResults plot saved to hierarchical_mpc_control_results.png")

def run_case_study():
    """设置并运行分层MPC控制案例研究。"""
    print("--- Setting up the Hierarchical MPC Control Case Study ---")

    # 从用户请求中获取参数
    user_params = {
        "pid": {"Kp": -0.5, "Ki": -0.1, "Kd": -0.05},
        "mpc": {
            "upstream_flood_threshold": 6.0, "downstream_flood_threshold": 6.0,
            "normal_setpoint_upstream": 5.0, "normal_setpoint_downstream": 5.0,
            "emergency_setpoint": 4.0, "prediction_horizon": 10,
            "q_weight": 1.0, "r_weight": 0.1
        },
        "disturbance": {
            "topic": "disturbance/upstream/inflow", "start_time": 100,
            "duration": 100, "inflow_rate": 50.0
        },
        "forecaster": {
            "disturbance_start_time": 100, "disturbance_duration": 100,
            "disturbance_inflow_rate": 50.0
        }
    }

    # 1. 创建消息总线
    message_bus = MessageBus()

    # 2. 设置仿真环境
    simulation_dt = 1.0
    components, agents, logger = setup_system(message_bus, simulation_dt, user_params)

    # 3. 设置并运行仿真
    harness = SimulationHarness(config={'duration': 400, 'dt': simulation_dt})
    for component in components: harness.add_component(component)
    for agent in agents: harness.add_agent(agent)

    # 4. 定义拓扑并构建
    harness.add_connection("upstream_canal", "control_gate_1")
    harness.add_connection("control_gate_1", "downstream_canal")
    harness.add_connection("downstream_canal", "final_gate_2")
    harness.add_connection("final_gate_2", "sink_canal")
    harness.build()

    # 5. 运行仿真
    print("\n--- Running Simulation ---")
    harness.run_mas_simulation()
    print("\n--- Simulation Complete ---")

    # 6. 绘制结果
    plot_results(harness, logger, user_params)

if __name__ == "__main__":
    run_case_study()
