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
from joint_control_agent import JointControlCoordinatorAgent

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class CommandHandler:
    """一个简单的类，用于订阅主题并存储收到的最新消息。"""
    def __init__(self, message_bus: MessageBus, topic: str):
        self.latest_command = 0.0
        message_bus.subscribe(topic, self.handle_message)

    def handle_message(self, message):
        self.latest_command = message.get('control_signal', 0.0)

def run_joint_control():
    """运行联合控制仿真。"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(os.path.join(current_dir, 'config.json'))

    # 1. 加载配置
    tank_conf = config['tank_params']
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

    # 3. 创建物理对象和感知智能体
    reservoir = Reservoir(**tank_conf)
    twin_agent = DigitalTwinAgent(
        agent_id="tank_twin_05",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=msg_conf['state_topic']
    )

    # 4. 创建协调控制器智能体
    coordinator_agent = JointControlCoordinatorAgent(
        agent_id="coordinator_01",
        message_bus=message_bus,
        config=config # Pass the whole config
    )

    # 5. 创建命令处理器来监听最终的执行器指令
    pump_handler = CommandHandler(message_bus, msg_conf['pump_command_topic'])
    valve_handler = CommandHandler(message_bus, msg_conf['valve_command_topic'])

    # 6. 运行仿真循环
    total_time = sim_conf['total_time']
    dt = sim_conf['time_step']
    setpoint = config['pid_params']['setpoint']
    disturbance_pattern = disturbance_conf['pattern']

    current_time = 0
    disturbance_idx = 0

    print("开始联合控制仿真...")
    print(f"目标水位 (Setpoint): {setpoint}")

    for t_step in np.arange(0, total_time, dt):
        # a. 更新外部扰动
        if disturbance_idx < len(disturbance_pattern):
            if current_time >= sum(p['duration'] for p in disturbance_pattern[:disturbance_idx+1]):
                disturbance_idx += 1
        current_disturbance = disturbance_pattern[disturbance_idx]['flow'] if disturbance_idx < len(disturbance_pattern) else disturbance_pattern[-1]['flow']

        # b. 仿真物理世界一步
        # 从处理器获取最新的控制指令
        pump_inflow = pump_handler.latest_command
        valve_outflow = valve_handler.latest_command

        # 总出流量 = 阀门控制的出流量 + 不可控的扰动出流量
        total_outflow = valve_outflow + current_disturbance

        reservoir.set_inflow(pump_inflow)
        action = {'outflow': total_outflow}
        reservoir.step(action, dt)

        # c. 感知智能体发布新状态，这将触发协调器的PID计算
        twin_agent.run(current_time)

        # d. 记录数据
        water_level = reservoir.get_state()['water_level']

        logger.log_step([
            round(current_time + dt, 2), setpoint, round(water_level, 4),
            round(pump_inflow, 4), round(valve_outflow, 4), round(current_disturbance, 4)
        ])
        current_time += dt

    logger.save()
    print("联合控制仿真结束。")

if __name__ == "__main__":
    run_joint_control()
