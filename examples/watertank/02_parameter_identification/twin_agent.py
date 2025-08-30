# -*- coding: utf-8 -*-
import math
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent

class TwinAgent(BaseAgent):
    """
    水箱的孪生智能体，用于参数辨识。
    它包含一个与水库智能体结构相同的模型，但其出口系数是可调的。
    """
    def __init__(self, agent_id, config, identification_config):
        """
        初始化孪生模型。

        :param agent_id: 智能体ID。
        :param config: 包含 'twin_params' 的配置字典。
        :param identification_config: 包含辨识算法参数的字典。
        """
        super().__init__(agent_id, config)
        self.area = self.config['area']
        self.water_level = self.config['initial_level']
        # 出口系数是可变的，从初始猜测值开始
        self.outlet_coeff = self.config['initial_outlet_coeff']
        self.learning_rate = identification_config['learning_rate']
        self.outflow = 0

    def step(self, observation):
        """
        孪生智能体执行一步，包括仿真和参数调整。

        :param observation: 一个字典，应包含：
                          'inflow': 进水流量 (m^3/s)
                          'dt': 时间步长 (s)
                          'real_water_level': 真实水库的水位 (m)
        :return: None
        """
        inflow = observation['inflow']
        dt = observation['dt']
        real_water_level = observation['real_water_level']

        # 1. 使用当前参数进行仿真，预测自己的水位
        if self.water_level > 0:
            self.outflow = self.outlet_coeff * math.sqrt(self.water_level)
        else:
            self.outflow = 0

        delta_h = (inflow - self.outflow) * dt / self.area
        self.water_level += delta_h

        if self.water_level < 0:
            self.water_level = 0

        # 2. 与真实水位进行比较，计算误差
        error = self.water_level - real_water_level

        # 3. 根据误差调整出口系数 (简化的梯度下降思想)
        # 如果孪生水位偏高 (error > 0)，说明模型出流偏小，应增大系数。
        # 如果孪生水位偏低 (error < 0)，说明模型出流偏大，应减小系数。
        # 调整量与误差成正比。
        # 注意：这里的梯度方向是简化的，真实梯度计算更复杂。
        # 我们用 error 本身作为调整方向的指示。
        adjustment = self.learning_rate * error

        # 更新系数，确保其不为负
        self.outlet_coeff += adjustment
        if self.outlet_coeff < 0:
            self.outlet_coeff = 0

    def get_state(self):
        """
        获取孪生智能体的当前状态。

        :return: 包含当前水位和估计的出口系数的字典。
        """
        return {
            "water_level": self.water_level,
            "estimated_coeff": self.outlet_coeff
        }
