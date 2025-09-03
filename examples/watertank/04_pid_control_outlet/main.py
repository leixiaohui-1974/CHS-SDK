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

def run_correctly_refactored_pid_control_outlet():
    """
    运行基于出水阀的PID水位控制仿真（正确重构版）。
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
    # 在这个场景中，Reservoir 不通过消息总线接收指令
    reservoir = Reservoir(**tank_conf)

    # 4. 创建感知智能体 (DigitalTwinAgent)
    twin_agent = DigitalTwinAgent(
        agent_id="tank_twin_02",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=msg_conf['state_topic']
    )

    # 5. 创建控制器和控制智能体
    pid_controller = PIDController(
        Kp=pid_conf['Kp'], Ki=pid_conf['Ki'], Kd=pid_conf['Kd'],
        setpoint=pid_conf['setpoint'],
        min_output=pid_conf['min_output'], max_output=pid_conf['max_output']
    )
    # LocalControlAgent 在这里仅用于封装PID逻辑，其发布的动作在主循环中直接读取
    valve_controller = LocalControlAgent(
        agent_id="valve_control_01",
        message_bus=message_bus,
        dt=sim_conf['time_step'],
        target_component="valve",
        control_type="valve_control",
        data_sources={"primary_data": msg_conf['state_topic']},
        control_targets={"primary_target": msg_conf['command_topic']},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic=msg_conf['state_topic'],
        observation_key='water_level',
        action_topic=msg_conf['command_topic'] # 可以是虚拟主题
    )

    # 6. 运行仿真循环
    total_time = sim_conf['total_time']
    dt = sim_conf['time_step']
    setpoint = pid_conf['setpoint']
    inflow_pattern = disturbance_conf['inflow_pattern']

    current_time = 0
    disturbance_idx = 0

    print("开始正确重构后的PID水位控制仿真（控制出水）...")
    print(f"目标水位 (Setpoint): {setpoint}")

    for t_step in np.arange(0, total_time, dt):
        # a. 更新外部扰动 (inflow)
        if disturbance_idx < len(inflow_pattern):
            if current_time >= sum(p['duration'] for p in inflow_pattern[:disturbance_idx+1]):
                disturbance_idx += 1
        current_inflow_disturbance = inflow_pattern[disturbance_idx]['inflow'] if disturbance_idx < len(inflow_pattern) else inflow_pattern[-1]['inflow']

        # b. 仿真物理世界一步
        # 从PID控制器获取最新的控制指令（outflow）
        outflow_control = pid_controller._previous_output if hasattr(pid_controller, '_previous_output') else 0

        # 设置物理对象的入流
        reservoir.set_inflow(current_inflow_disturbance)
        # 在action中设置出流并步进
        action = {'outflow': outflow_control}
        reservoir.step(action, dt)

        # c. 感知智能体发布新状态，这将触发下一次的PID计算
        twin_agent.run(current_time)

        # d. 记录数据
        water_level = reservoir.get_state()['water_level']

        logger.log_step([
            round(current_time + dt, 2), setpoint, round(water_level, 4),
            round(outflow_control, 4), round(current_inflow_disturbance, 4)
        ])
        current_time += dt

    logger.save()
    print("PID控制仿真结束。")

if __name__ == "__main__":
    run_correctly_refactored_pid_control_outlet()
