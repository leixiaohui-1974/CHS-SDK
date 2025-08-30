# -*- coding: utf-8 -*-
import sys
import os
import numpy as np

# 添加路径以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.dirname(__file__))

from config_loader import load_config
from data_logger import DataLogger
from watertank_twin_agent import WaterTankTwinAgent
from valve_agent import ValveAgent

def run_pid_control():
    """
    运行基于出水阀门的PID水位控制仿真。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 加载配置
    config_path = os.path.join(current_dir, 'config.json')
    config = load_config(config_path)

    tank_params = config['tank_params']
    pid_params = config['pid_params']
    sim_params = config['simulation_params']
    disturbance_params = config['disturbance_params']
    log_params = config['logging_params']

    # 2. 初始化数据记录器
    log_dir_path = os.path.join(current_dir, '..', log_params['log_dir'])
    logger = DataLogger(
        log_dir=log_dir_path,
        file_name=log_params['log_file'],
        headers=log_params['log_headers']
    )

    # 3. 初始化智能体
    tank = WaterTankTwinAgent(agent_id="tank_02", config=tank_params)
    valve = ValveAgent(agent_id="valve_01", config=pid_params)

    # 4. 运行仿真循环
    total_time = sim_params['total_time']
    dt = sim_params['time_step']
    setpoint = pid_params['setpoint']
    inflow_pattern = disturbance_params['inflow_pattern']

    current_time = 0
    inflow_idx = 0

    print("开始PID水位控制仿真（控制出水）...")
    print(f"目标水位 (Setpoint): {setpoint}")

    while current_time < total_time:
        # 获取当前的进水扰动流量
        if inflow_idx < len(inflow_pattern):
            current_inflow = inflow_pattern[inflow_idx]['inflow']
            if current_time >= np.sum([p['duration'] for p in inflow_pattern[:inflow_idx+1]]):
                inflow_idx += 1
        else:
            current_inflow = inflow_pattern[-1]['inflow']

        # a. ValveAgent (控制器) 观察水位并决策
        tank_state = tank.get_state()
        valve_obs = {
            "current_level": tank_state['water_level'],
            "dt": dt
        }
        outflow_control = valve.step(valve_obs)

        # b. WaterTankAgent (被控对象) 根据控制和扰动更新状态
        tank_obs = {
            "inflow_disturbance": current_inflow,
            "outflow": outflow_control,
            "dt": dt
        }
        tank.step(tank_obs)

        # c. 记录数据
        final_tank_state = tank.get_state()
        log_data = [
            round(current_time + dt, 2),
            setpoint,
            round(final_tank_state['water_level'], 4),
            round(outflow_control, 4),
            round(current_inflow, 4)
        ]
        logger.log_step(log_data)

        current_time += dt

    # 5. 保存日志
    logger.save()
    print("PID控制仿真结束。")

if __name__ == "__main__":
    run_pid_control()
