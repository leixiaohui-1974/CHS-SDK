# -*- coding: utf-8 -*-
import sys
import os
import numpy as np

# 添加路径以便导入模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.dirname(__file__))

from config_loader import load_config
from data_logger import DataLogger
from reservoir_agent import ReservoirAgent
from twin_agent import TwinAgent

def run_identification():
    """
    运行参数辨识过程。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 加载配置
    config_path = os.path.join(current_dir, 'config.json')
    config = load_config(config_path)

    sim_params = config['simulation_params']
    reservoir_params = config['reservoir_params']
    twin_params = config['twin_params']
    identification_params = config['identification_params']
    log_params = config['logging_params']

    # 2. 初始化数据记录器
    log_dir_path = os.path.join(current_dir, '..', log_params['log_dir'])
    logger = DataLogger(
        log_dir=log_dir_path,
        file_name=log_params['log_file'],
        headers=log_params['log_headers']
    )

    # 3. 初始化智能体
    # “真实”水库
    reservoir = ReservoirAgent(
        agent_id="reservoir_01",
        config=reservoir_params
    )
    # 数字孪生
    twin = TwinAgent(
        agent_id="twin_01",
        config=twin_params,
        identification_config=identification_params
    )

    # 4. 运行仿真和辨识循环
    total_time = sim_params['total_time']
    dt = sim_params['time_step']
    inflow_pattern = sim_params['inflow_pattern']

    current_time = 0
    inflow_idx = 0

    print("开始参数辨识...")
    print(f"真实出口系数: {reservoir.outlet_coeff}")
    print(f"孪生模型初始出口系数: {twin.outlet_coeff}")

    while current_time < total_time:
        # 获取当前阶段的进水流量
        if inflow_idx < len(inflow_pattern):
            current_inflow = inflow_pattern[inflow_idx]['inflow']
            duration = inflow_pattern[inflow_idx]['duration']
            if current_time >= np.sum([p['duration'] for p in inflow_pattern[:inflow_idx+1]]):
                inflow_idx += 1
        else:
            # 如果模式结束，使用最后一个模式的流量
            current_inflow = inflow_pattern[-1]['inflow']

        # 准备给智能体的观察值
        reservoir_obs = {"inflow": current_inflow, "dt": dt}

        # “真实”水库运行一步
        reservoir.step(reservoir_obs)
        real_state = reservoir.get_state()
        real_water_level = real_state['water_level']

        # 孪生智能体运行一步（包含辨识）
        twin_obs = {
            "inflow": current_inflow,
            "dt": dt,
            "real_water_level": real_water_level
        }
        twin.step(twin_obs)
        twin_state = twin.get_state()
        twin_water_level = twin_state['water_level']
        estimated_coeff = twin_state['estimated_coeff']

        # 计算误差
        error = twin_water_level - real_water_level

        # 记录数据
        log_data = [
            round(current_time + dt, 2),
            round(real_water_level, 4),
            round(twin_water_level, 4),
            round(estimated_coeff, 4),
            round(error, 4)
        ]
        logger.log_step(log_data)

        current_time += dt

    # 5. 保存日志文件
    logger.save()
    print("参数辨识结束。")
    print(f"最终辨识出的出口系数: {twin.get_state()['estimated_coeff']:.4f}")


if __name__ == "__main__":
    run_identification()
