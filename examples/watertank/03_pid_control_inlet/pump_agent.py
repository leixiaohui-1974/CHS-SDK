# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent
from pid_controller import PIDController

class PumpAgent(BaseAgent):
    """
    水泵智能体，内置一个PID控制器来调节进水流量。
    """
    def __init__(self, agent_id, config):
        """
        初始化水泵智能体。

        :param agent_id: 智能体ID。
        :param config: 包含 'pid_params' 的配置字典。
        """
        super().__init__(agent_id, config)

        pid_conf = self.config
        self.pid_controller = PIDController(
            Kp=pid_conf['kp'],
            Ki=pid_conf['ki'],
            Kd=pid_conf['kd'],
            setpoint=pid_conf['setpoint'],
            output_limits=tuple(pid_conf['output_limits'])
        )
        self.control_signal = 0

    def step(self, observation):
        """
        根据当前水位，计算并返回所需的进水流量。

        :param observation: 一个字典，包含:
                          'current_level': 当前水箱的水位。
                          'dt': 时间步长 (s)。
        :return: 计算出的进水流量 (m^3/s)。
        """
        current_level = observation['current_level']
        # PID控制器根据当前值和设定值的误差，计算输出
        self.control_signal = self.pid_controller.step(current_level)
        return self.control_signal

    def get_state(self):
        """
        获取水泵智能体的当前状态。

        :return: 包含当前控制信号（即进水流量）的字典。
        """
        return {
            "inflow_control": self.control_signal
        }
