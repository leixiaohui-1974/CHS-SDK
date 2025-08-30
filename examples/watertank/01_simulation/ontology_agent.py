# -*- coding: utf-8 -*-
import math
import sys
import os

# 将 'base' 目录添加到系统路径中，以便导入基础模块
# 这是一种常见的处理项目内部模块引用的方式
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent

class OntologySimulationAgent(BaseAgent):
    """
    水箱本体仿真智能体。
    该智能体封装了水箱的物理模型。
    """
    def __init__(self, agent_id, config):
        """
        初始化水箱模型。

        :param agent_id: 智能体ID。
        :param config: 包含 'tank_params' 的配置字典。
        """
        super().__init__(agent_id, config)
        self.area = self.config['area']  # 水箱横截面积 (m^2)
        self.water_level = self.config['initial_level']  # 当前水位 (m)
        self.outlet_coeff = self.config['outlet_coeff']  # 出口流量系数
        self.outflow = 0 # 当前出水流量

    def step(self, observation):
        """
        根据输入流量，更新水箱状态。

        :param observation: 一个字典，包含 'inflow' (m^3/s) 和 'dt' (s)。
        :return: 当前的出水流量 (m^3/s)。
        """
        inflow = observation['inflow']
        dt = observation['dt']

        # 根据当前水位计算出水流量 (Torricelli's law)
        # Q_out = C * sqrt(h)
        # 为避免h为负数导致计算错误，我们取max(0, h)
        if self.water_level > 0:
            self.outflow = self.outlet_coeff * math.sqrt(self.water_level)
        else:
            self.outflow = 0

        # 计算水位的变化
        # dh = (Qin - Qout) * dt / A
        delta_h = (inflow - self.outflow) * dt / self.area

        # 更新水位
        self.water_level += delta_h

        # 确保水位不为负
        if self.water_level < 0:
            self.water_level = 0

        return self.outflow

    def get_state(self):
        """
        获取水箱的当前状态。

        :return: 包含当前水位和出水流量的字典。
        """
        return {
            "water_level": self.water_level,
            "outflow": self.outflow
        }
