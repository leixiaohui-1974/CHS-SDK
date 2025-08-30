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
from pump_agent import PumpAgent

def run_pid_control():
    """
    运行基于进水泵的PID水位控制仿真。
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
    tank = WaterTankTwinAgent(agent_id="tank_01", config=tank_params)
    pump = PumpAgent(agent_id="pump_01", config=pid_params)

    # 4. 运行仿真循环
    total_time = sim_params['total_time']
    dt = sim_params['time_step']
    setpoint = pid_params['setpoint']
    outflow_pattern = disturbance_params['outflow_pattern']

    current_time = 0
    outflow_idx = 0

    print("开始PID水位控制仿真（控制进水）...")
    print(f"目标水位 (Setpoint): {setpoint}")

    while current_time < total_time:
        # 获取当前的出水扰动流量
        if outflow_idx < len(outflow_pattern):
            current_outflow = outflow_pattern[outflow_idx]['outflow']
            if current_time >= np.sum([p['duration'] for p in outflow_pattern[:outflow_idx+1]]):
                outflow_idx += 1
        else:
            current_outflow = outflow_pattern[-1]['outflow']

        # a. PumpAgent (控制器) 观察水位并决策
        tank_state = tank.get_state()
        pump_obs = {
            "current_level": tank_state['water_level'],
            "dt": dt
        }
        inflow_control = pump.step(pump_obs)

        # b. WaterTankAgent (被控对象) 根据控制和扰动更新状态
        tank_obs = {
            "inflow": inflow_control,
            "outflow_disturbance": current_outflow,
            "dt": dt
        }
        tank.step(tank_obs)

        # c. 记录数据
        final_tank_state = tank.get_state()
        log_data = [
            round(current_time + dt, 2),
            setpoint,
            round(final_tank_state['water_level'], 4),
            round(inflow_control, 4),
            round(current_outflow, 4)
        ]
        logger.log_step(log_data)

        current_time += dt

    # 5. 保存日志
    logger.save()
    print("PID控制仿真结束。")

if __name__ == "__main__":
    run_pid_control()
