# -*- coding: utf-8 -*-
import sys
import os
import numpy as np

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
sys.path.append(os.path.dirname(__file__))

# --- Imports ---
from config_loader import load_config
from data_logger import DataLogger
from noisy_actuator_reservoir import NoisyActuatorReservoir

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

def run_actuator_disturbance():
    """运行执行器扰动下的PID控制仿真。"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(os.path.join(current_dir, 'config.json'))

    # 1. 加载配置
    tank_conf = config['tank_params']
    pid_conf = config['pid_params']
    actuator_noise_conf = config['actuator_noise_params']
    sim_conf = config['simulation_params']
    disturbance_conf = config['disturbance_params']
    msg_conf = config['messaging_params']
    log_conf = config['logging_params']

    # 2. 初始化核心组件
    message_bus = MessageBus()
    logger = DataLogger(
        log_dir=os.path.join(current_dir, '..', log_conf['log_dir']),
        file_name=log_conf['log_file'],
        headers=log_conf['log_headers']
    )

    # 3. 创建带噪声执行器的物理对象
    reservoir = NoisyActuatorReservoir(
        noise_params=actuator_noise_conf,
        **tank_conf
    )

    # 4. 创建感知智能体
    # 注意：这个例子中，感知是完美的，只有执行器有噪声
    twin_agent = DigitalTwinAgent(
        agent_id="perfect_twin_01",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=msg_conf['state_topic']
    )

    # 5. 创建控制器
    pid_controller = PIDController(**pid_conf)
    pump_controller = LocalControlAgent(
        agent_id="pump_control_07",
        dt=sim_conf['time_step'],
        target_component="tank_noisy_actuator",
        control_type="pid",
        data_sources={
            "observation_topic": msg_conf['state_topic'],
            "observation_key": 'water_level'
        },
        control_targets={
            "action_topic": msg_conf['command_topic']
        },
        allocation_config={
            "method": "direct"
        },
        controller_config={
            "controller": pid_controller
        },
        message_bus=message_bus
    )

    # 6. 创建一个命令处理器来监听水泵指令
    class CommandHandler:
        def __init__(self):
            self.latest_command = 0.0
            message_bus.subscribe(msg_conf['command_topic'], lambda msg: self.handle(msg))
        def handle(self, message):
            self.latest_command = message.get('control_signal', 0.0)

    pump_handler = CommandHandler()

    # 7. 运行仿真循环
    total_time = sim_conf['total_time']
    dt = sim_conf['time_step']
    setpoint = pid_conf['setpoint']
    outflow_pattern = disturbance_conf['outflow_pattern']

    current_time = 0
    disturbance_idx = 0

    print("开始执行器扰动仿真...")
    print(f"目标水位 (Setpoint): {setpoint}")

    for t_step in np.arange(0, total_time, dt):
        # a. 更新外部扰动
        if disturbance_idx < len(outflow_pattern):
            if current_time >= sum(p['duration'] for p in outflow_pattern[:disturbance_idx+1]):
                disturbance_idx += 1
        current_disturbance = outflow_pattern[disturbance_idx]['outflow'] if disturbance_idx < len(outflow_pattern) else outflow_pattern[-1]['outflow']

        # b. 仿真物理世界一步
        # 控制器发布的指令被处理器捕获
        commanded_inflow = pump_handler.latest_command
        # 我们将指令发送给带噪声的执行器
        reservoir.set_inflow(commanded_inflow)

        action = {'outflow': current_disturbance}
        reservoir.step(action, dt)

        # c. 感知智能体发布新状态
        twin_agent.run(current_time)

        # d. 记录数据
        state = reservoir.get_state()
        water_level = state['water_level']
        actual_inflow = state['actual_inflow']

        logger.log_step([
            round(current_time + dt, 2), setpoint, round(water_level, 4),
            round(commanded_inflow, 4), round(actual_inflow, 4), round(current_disturbance, 4)
        ])
        current_time += dt

    logger.save()
    print("执行器扰动仿真结束。")

if __name__ == "__main__":
    run_actuator_disturbance()
