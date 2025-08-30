# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent

class WaterTankTwinAgent(BaseAgent):
    """
    被控的水箱孪生智能体。
    它的出水流量是一个外部定义的扰动，而不是由水位决定的。
    """
    def __init__(self, agent_id, config):
        """
        初始化水箱模型。

        :param agent_id: 智能体ID。
        :param config: 包含 'tank_params' 的配置字典。
        """
        super().__init__(agent_id, config)
        self.area = self.config['area']
        self.water_level = self.config['initial_level']

    def step(self, observation):
        """
        根据输入流量和扰动流量，更新水箱状态。

        :param observation: 一个字典，包含:
                          'inflow': 进水流量 (m^3/s), 由PID控制器计算得出。
                          'outflow_disturbance': 出水扰动流量 (m^3/s)。
                          'dt': 时间步长 (s)。
        :return: None
        """
        inflow = observation['inflow']
        outflow_disturbance = observation['outflow_disturbance']
        dt = observation['dt']

        # 水位的变化仅由进水和出水扰动决定
        delta_h = (inflow - outflow_disturbance) * dt / self.area

        # 更新水位
        self.water_level += delta_h

        # 确保水位不为负
        if self.water_level < 0:
            self.water_level = 0

    def get_state(self):
        """
        获取水箱的当前状态。

        :return: 包含当前水位的字典。
        """
        return {
            "water_level": self.water_level
        }
