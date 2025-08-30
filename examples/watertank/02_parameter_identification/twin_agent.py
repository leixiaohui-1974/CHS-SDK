# -*- coding: utf-8 -*-
import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
from base_agent import BaseAgent

class TwinAgent(BaseAgent):
    """
    数字孪生智能体，用于辨识“真实”水库的出口系数。
    """
    def __init__(self, agent_id, config, identification_config):
        super().__init__(agent_id, config)
        self.area = self.config['area']
        self.water_level = self.config['initial_level']
        # The parameter to be identified, with an initial guess
        self.outlet_coeff = self.config['initial_outlet_coeff']
        self.learning_rate = identification_config['learning_rate']
        self.outflow = 0

    def step(self, observation):
        """
        运行一步仿真，并根据与真实世界的误差来更新参数。
        """
        inflow = observation['inflow']
        dt = observation['dt']
        real_water_level = observation['real_water_level']

        # 1. 使用当前的参数进行仿真
        if self.water_level > 0:
            self.outflow = self.outlet_coeff * math.sqrt(self.water_level)
        else:
            self.outflow = 0

        delta_h = (inflow - self.outflow) * dt / self.area
        self.water_level += delta_h

        if self.water_level < 0:
            self.water_level = 0

        # 2. 计算与真实水位的误差
        error = real_water_level - self.water_level

        # 3. 根据误差更新出口系数 (简单的梯度下降法)
        # 如果真实水位更高，说明我们的模型出流太大了（或进流太小），
        # 意味着 outlet_coeff 可能偏大，所以要减小它。
        # 这里用一个简化的更新规则，error > 0 意味着 real > twin,
        # 即 twin 的水位偏低，可能是coeff太大导致出流过多，所以要减小coeff。
        # 更新量与误差成正比。
        update = -self.learning_rate * error
        self.outlet_coeff += update

        # 确保系数不为负
        if self.outlet_coeff < 0:
            self.outlet_coeff = 0

    def get_state(self):
        return {
            "water_level": self.water_level,
            "estimated_coeff": self.outlet_coeff
        }
