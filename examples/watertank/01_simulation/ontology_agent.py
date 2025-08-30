# -*- coding: utf-8 -*-
import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent

class OntologySimulationAgent(BaseAgent):
    """
    一个简单的水箱本体仿真智能体。
    它根据物理公式模拟水箱的水位变化。
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
        self.outlet_coeff = self.config['outlet_coeff']
        self.outflow = 0

    def step(self, observation):
        """
        根据输入流量，更新水箱状态并计算出水流量。

        :param observation: 一个字典，包含:
                          'inflow': 进水流量 (m^3/s)。
                          'dt': 时间步长 (s)。
        :return: 计算出的出水流量 (m^3/s)。
        """
        inflow = observation['inflow']
        dt = observation['dt']

        # 根据当前水位计算出水流量 (托里拆利定律)
        if self.water_level > 0:
            self.outflow = self.outlet_coeff * math.sqrt(self.water_level)
        else:
            self.outflow = 0

        # 计算水位变化
        delta_h = (inflow - self.outflow) * dt / self.area
        self.water_level += delta_h

        # 确保水位不为负
        if self.water_level < 0:
            self.water_level = 0

        return self.outflow

    def get_state(self):
        """
        获取水箱的当前状态。
        :return: 包含当前水位的字典。
        """
        return {
            "water_level": self.water_level,
            "outflow": self.outflow
        }
