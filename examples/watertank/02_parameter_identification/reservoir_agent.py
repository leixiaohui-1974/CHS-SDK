# -*- coding: utf-8 -*-
import math
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent

class ReservoirAgent(BaseAgent):
    """
    水库智能体，代表“真实”的物理系统。
    其行为与 OntologySimulationAgent 相同，但在概念上代表了物理真实。
    """
    def __init__(self, agent_id, config):
        """
        初始化水库模型。

        :param agent_id: 智能体ID。
        :param config: 包含 'reservoir_params' 的配置字典。
        """
        super().__init__(agent_id, config)
        self.area = self.config['area']
        self.water_level = self.config['initial_level']
        self.outlet_coeff = self.config['outlet_coeff'] # 这是“真实”的、待辨识的系数
        self.outflow = 0

    def step(self, observation):
        """
        根据输入流量，更新水箱状态。

        :param observation: 一个字典，包含 'inflow' (m^3/s) 和 'dt' (s)。
        :return: 当前的出水流量 (m^3/s)。
        """
        inflow = observation['inflow']
        dt = observation['dt']

        if self.water_level > 0:
            self.outflow = self.outlet_coeff * math.sqrt(self.water_level)
        else:
            self.outflow = 0

        delta_h = (inflow - self.outflow) * dt / self.area
        self.water_level += delta_h

        if self.water_level < 0:
            self.water_level = 0

        return self.outflow

    def get_state(self):
        """
        获取水库的当前状态。

        :return: 包含当前水位的字典。
        """
        return {
            "water_level": self.water_level
        }
