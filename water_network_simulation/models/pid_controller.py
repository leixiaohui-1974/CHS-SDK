class PIDController:
    """一个简单的 PID 控制器实现。"""
    def __init__(self, Kp, Ki, Kd, setpoint=0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint

        self._previous_error = 0
        self._integral = 0

        print(f"PIDController: Initialized with Kp={Kp}, Ki={Ki}, Kd={Kd}")

    def update(self, current_value, dt=1):
        """
        计算 PID 控制输出。

        :param current_value: 当前测量值
        :param dt: 时间步长
        :return: 控制变量的输出
        """
        error = self.setpoint - current_value

        # 比例项
        P_out = self.Kp * error

        # 积分项
        self._integral += error * dt
        I_out = self.Ki * self._integral

        # 微分项
        derivative = (error - self._previous_error) / dt
        D_out = self.Kd * derivative

        # 总输出
        output = P_out + I_out + D_out

        # 更新状态
        self._previous_error = error

        return output

    def set_setpoint(self, setpoint):
        """更新设定点并重置积分器。"""
        self.setpoint = setpoint
        self._integral = 0
        self._previous_error = 0
        print(f"PIDController: New setpoint set to {setpoint}. Integrator reset.")
