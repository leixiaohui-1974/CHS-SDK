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
from noisy_digital_twin_agent import NoisyDigitalTwinAgent

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent

def run_sensor_disturbance():
    """运行传感器扰动下的PID控制仿真。"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(os.path.join(current_dir, 'config.json'))

    # 1. 加载配置
    tank_conf = config['tank_params']
    pid_conf = config['pid_params']
    noise_conf = config['noise_params']
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

    # 3. 创建物理对象和带噪声的感知智能体
    reservoir = Reservoir(
        message_bus=message_bus,
        inflow_topic=msg_conf['command_topic'],
        **tank_conf
    )
    noisy_twin_agent = NoisyDigitalTwinAgent(
        agent_id="noisy_twin_01",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=msg_conf['state_topic'],
        noise_params=noise_conf
    )

    # 4. 创建控制器
    pid_controller = PIDController(**pid_conf)
    pump_controller = LocalControlAgent(
        agent_id="pump_control_06",
        dt=sim_conf['time_step'],
        target_component="tank_noisy_sensor",
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

    # 5. 运行仿真循环
    total_time = sim_conf['total_time']
    dt = sim_conf['time_step']
    setpoint = pid_conf['setpoint']
    outflow_pattern = disturbance_conf['outflow_pattern']

    current_time = 0
    disturbance_idx = 0

    print("开始传感器扰动仿真...")
    print(f"目标水位 (Setpoint): {setpoint}")

    for t_step in np.arange(0, total_time, dt):
        # a. 更新外部扰动
        if disturbance_idx < len(outflow_pattern):
            if current_time >= sum(p['duration'] for p in outflow_pattern[:disturbance_idx+1]):
                disturbance_idx += 1
        current_disturbance = outflow_pattern[disturbance_idx]['outflow'] if disturbance_idx < len(outflow_pattern) else outflow_pattern[-1]['outflow']

        # b. 仿真物理世界一步
        action = {'outflow': current_disturbance}
        reservoir.step(action, dt)

        # c. 感知智能体发布带噪声的新状态
        noisy_twin_agent.publish_state()

        # d. 记录数据
        true_water_level = reservoir.get_state()['water_level']
        noisy_water_level = noisy_twin_agent.last_noisy_level
        inflow_control = pid_controller._previous_output if hasattr(pid_controller, '_previous_output') else 0

        logger.log_step([
            round(current_time + dt, 2), setpoint, round(true_water_level, 4),
            round(noisy_water_level, 4), round(inflow_control, 4), round(current_disturbance, 4)
        ])
        current_time += dt

    logger.save()
    print("传感器扰动仿真结束。")

if __name__ == "__main__":
    run_sensor_disturbance()
