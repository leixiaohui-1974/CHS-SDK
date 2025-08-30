# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))

from base_agent import BaseAgent
from pid_controller import PIDController

class ValveAgent(BaseAgent):
    """
    阀门智能体，内置一个PID控制器来调节出水流量。
    """
    def __init__(self, agent_id, config):
        """
        初始化阀门智能体。

        :param agent_id: 智能体ID。
        :param config: 包含 'pid_params' 的配置字典。
        """
        super().__init__(agent_id, config)

        pid_conf = self.config
        # 注意：这里的设定点在PID控制器内部仍然存在，但我们在计算误差时会使用
        # 一个“反向”的误差，所以PID的目标可以理解为让 (current_level - setpoint) -> 0
        self.pid_controller = PIDController(
            Kp=pid_conf['kp'],
            Ki=pid_conf['ki'],
            Kd=pid_conf['kd'],
            setpoint=0, # 我们希望 (current_level - setpoint) 这个差值趋近于0
            output_limits=tuple(pid_conf['output_limits'])
        )
        self.control_signal = 0
        self.setpoint = pid_conf['setpoint']

    def step(self, observation):
        """
        根据当前水位，计算并返回所需的出水流量。

        :param observation: 一个字典，包含:
                          'current_level': 当前水箱的水位。
                          'dt': 时间步长 (s)。
        :return: 计算出的出水流量 (m^3/s)。
        """
        current_level = observation['current_level']

        # 计算“反向”误差
        # 如果水位高于设定点，误差为正，需要增 大出水
        # 如果水位低于设定点，误差为负，需要减 小出水
        error = current_level - self.setpoint

        # PID控制器根据此误差计算输出
        self.control_signal = self.pid_controller.step(error)

        return self.control_signal

    def get_state(self):
        """
        获取阀门智能体的当前状态。

        :return: 包含当前控制信号（即出水流量）的字典。
        """
        return {
            "outflow_control": self.control_signal
        }
