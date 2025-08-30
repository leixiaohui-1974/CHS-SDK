# -*- coding: utf-8 -*-
import sys
import os
import numpy as np

# 将 'base' 目录和当前目录添加到系统路径中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.dirname(__file__))

from config_loader import load_config
from data_logger import DataLogger
from ontology_agent import OntologySimulationAgent

def run_simulation():
    """
    运行水箱仿真。
    """
    # 获取当前脚本所在目录的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 加载配置
    config_path = os.path.join(current_dir, 'config.json')
    config = load_config(config_path)

    sim_params = config['simulation_params']
    tank_params = config['tank_params']
    log_params = config['logging_params']

    # 2. 初始化数据记录器
    # 日志目录相对于项目根目录（examples/watertank）
    log_dir_path = os.path.join(current_dir, '..', log_params['log_dir'])
    logger = DataLogger(
        log_dir=log_dir_path,
        file_name=log_params['log_file'],
        headers=log_params['log_headers']
    )

    # 3. 初始化水箱本体仿真智能体
    tank_agent = OntologySimulationAgent(
        agent_id="tank_ontology_01",
        config=tank_params
    )

    # 4. 运行仿真循环
    total_time = sim_params['total_time']
    dt = sim_params['time_step']
    inflow_rate = sim_params['inflow_rate']

    print("开始水箱仿真...")
    for t in np.arange(0, total_time, dt):
        # 准备给智能体的观察值
        observation = {
            "inflow": inflow_rate,
            "dt": dt
        }

        # 智能体执行一步
        outflow = tank_agent.step(observation)

        # 获取智能体状态
        state = tank_agent.get_state()
        water_level = state['water_level']

        # 记录数据
        # 表头: ["time", "water_level", "inflow", "outflow"]
        log_data = [round(t + dt, 2), round(water_level, 4), inflow_rate, round(outflow, 4)]
        logger.log_step(log_data)

    # 5. 保存日志文件
    logger.save()
    print("仿真结束。")

if __name__ == "__main__":
    run_simulation()
