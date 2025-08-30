# -*- coding: utf-8 -*-
import time

class PIDController:
    """
    一个基础的 PID 控制器。
    """
    def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(None, None)):
        """
        初始化 PID 控制器。

        :param Kp: 比例增益 (Proportional gain)。
        :param Ki: 积分增益 (Integral gain)。
        :param Kd: 微分增益 (Derivative gain)。
        :param setpoint: 目标设定点。
        :param output_limits: 控制器输出的最小值和最大值 (min, max)。
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.output_min, self.output_max = output_limits

        self._proportional = 0
        self._integral = 0
        self._derivative = 0

        self._last_error = 0
        self._last_time = time.time()

    def step(self, process_variable, current_time=None):
        """
        计算 PID 控制器的输出。

        :param process_variable: 当前过程变量的测量值。
        :param current_time: 当前时间（秒）。如果为 None，则使用 time.time()。
        :return: 控制器的输出信号。
        """
        if current_time is None:
            current_time = time.time()

        dt = current_time - self._last_time
        if dt <= 0:
            # 如果时间间隔为0或负数，则不进行计算，返回上一次的输出值
            return self._proportional + self._integral + self._derivative

        error = self.setpoint - process_variable

        # 比例项
        self._proportional = self.Kp * error

        # 积分项 (带抗饱和)
        self._integral += self.Ki * error * dt
        if self.output_max is not None and self._integral > self.output_max:
            self._integral = self.output_max
        elif self.output_min is not None and self._integral < self.output_min:
            self._integral = self.output_min

        # 微分项
        self._derivative = self.Kd * (error - self._last_error) / dt

        # 计算总输出
        output = self._proportional + self._integral + self._derivative

        # 应用输出限制
        if self.output_max is not None and output > self.output_max:
            output = self.output_max
        elif self.output_min is not None and output < self.output_min:
            output = self.output_min

        # 更新状态
        self._last_error = error
        self._last_time = current_time

        return output

    def reset(self, setpoint=None):
        """
        重置 PID 控制器状态。
        """
        self._proportional = 0
        self._integral = 0
        self._derivative = 0
        self._last_error = 0
        self._last_time = time.time()
        if setpoint is not None:
            self.setpoint = setpoint
