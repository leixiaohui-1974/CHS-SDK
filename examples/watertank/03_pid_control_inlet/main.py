# -*- coding: utf-8 -*-
import sys
import os
import numpy as np

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# --- Imports ---
from config_loader import load_config
from data_logger import DataLogger

# Import standard library components
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

def run_correctly_refactored_pid_control():
    """
    运行基于进水泵的PID水位控制仿真（正确重构版）。
    使用标准的基础库智能体和消息总线架构。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(os.path.join(current_dir, 'config.json'))

    # 1. 加载配置
    tank_conf = config['tank_params']
    pid_conf = config['pid_params']
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

    # 3. 创建物理对象 (Reservoir)
    # Reservoir 将通过消息总线监听入流指令
    reservoir = Reservoir(
        message_bus=message_bus,
        inflow_topic=msg_conf['command_topic'],
        **tank_conf
    )

    # 4. 创建感知智能体 (DigitalTwinAgent)
    # 它将封装 Reservoir 并发布其状态
    twin_agent = DigitalTwinAgent(
        agent_id="tank_twin_01",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=msg_conf['state_topic']
    )

    # 5. 创建控制器和控制智能体 (PIDController, LocalControlAgent)
    pid_controller = PIDController(
        Kp=pid_conf['Kp'], Ki=pid_conf['Ki'], Kd=pid_conf['Kd'],
        setpoint=pid_conf['setpoint'],
        min_output=pid_conf['min_output'],
        max_output=pid_conf['max_output']
    )
    pump_controller = LocalControlAgent(
        agent_id="pump_control_01",
        message_bus=message_bus,
        dt=sim_conf['time_step'],
        target_component="pump",
        control_type="pump_control",
        data_sources={"primary_data": msg_conf['state_topic']},
        control_targets={"primary_target": msg_conf['command_topic']},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic=msg_conf['state_topic'],
        observation_key='water_level',
        action_topic=msg_conf['command_topic']
    )

    # 6. 运行仿真循环
    total_time = sim_conf['total_time']
    dt = sim_conf['time_step']
    setpoint = pid_conf['setpoint']
    outflow_pattern = disturbance_conf['outflow_pattern']

    current_time = 0
    disturbance_idx = 0
    current_disturbance = 0

    print("开始正确重构后的PID水位控制仿真（控制进水）...")
    print(f"目标水位 (Setpoint): {setpoint}")

    for t_step in np.arange(0, total_time, dt):
        # a. 更新外部扰动
        if disturbance_idx < len(outflow_pattern):
            if current_time >= sum(p['duration'] for p in outflow_pattern[:disturbance_idx+1]):
                disturbance_idx += 1
        current_disturbance = outflow_pattern[disturbance_idx]['outflow'] if disturbance_idx < len(outflow_pattern) else outflow_pattern[-1]['outflow']

        # b. 仿真物理世界一步
        # LocalControlAgent 会自动监听状态并发布指令，Reservoir 会自动监听指令
        # 我们只需要在主循环中调用 Reservoir.step() 和 twin_agent.run()
        action = {'outflow': current_disturbance}
        reservoir.step(action, dt)

        # c. 感知智能体发布新状态
        twin_agent.run(current_time) # 这会触发控制器的事件

        # d. 记录数据
        water_level = reservoir.get_state()['water_level']
        # Access the internal state of the PID controller for logging purposes
        inflow_control = pid_controller._previous_output if hasattr(pid_controller, '_previous_output') else 0

        logger.log_step([
            round(current_time + dt, 2), setpoint, round(water_level, 4),
            round(inflow_control, 4), round(current_disturbance, 4)
        ])
        current_time += dt

    logger.save()
    print("PID控制仿真结束。")

if __name__ == "__main__":
    run_correctly_refactored_pid_control()
