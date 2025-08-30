# -*- coding: utf-8 -*-
import sys
import os
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
from base_agent import BaseAgent

class ReservoirAgent(BaseAgent):
    """
    “真实”水库的仿真智能体。
    其行为由一组固定的、真实的物理参数决定。
    """
    def __init__(self, agent_id, config):
        super().__init__(agent_id, config)
        self.area = self.config['area']
        self.water_level = self.config['initial_level']
        self.outlet_coeff = self.config['outlet_coeff']
        self.outflow = 0

    def step(self, observation):
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
        return {
            "water_level": self.water_level,
            "outflow": self.outflow
        }
