"""
A Proportional-Integral-Derivative (PID) Controller with anti-windup.
"""
from core_lib.core.interfaces import Controller, State

class PIDController(Controller):
    """
    A standard PID controller with clamping and anti-windup.

    This controller computes an action based on the error between a setpoint and a
    process variable. It includes an anti-windup mechanism to prevent integral
    term saturation when the actuator is at its limit.
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float,
                 min_output: float, max_output: float):
        """
        Initializes the PID controller.

        Args:
            Kp: Proportional gain.
            Ki: Integral gain.
            Kd: Derivative gain.
            setpoint: The desired value for the system state.
            min_output: The minimum value for the control action.
            max_output: The maximum value for the control action.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.min_output = min_output
        self.max_output = max_output

        self._integral = 0
        self._previous_error = 0
        self._previous_output = 0
        
        # 增强控制参数
        self.integral_windup_limit = 0.5  # 积分抗饱和限制
        self.filter_time_constant = 0.1   # 微分滤波时间常数
        self._filtered_derivative = 0     # 滤波后的微分项
        
        print(f"PIDController created with Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}, "
              f"OutputRange=[{min_output}, {max_output}].")

    def compute_control_action(self, observation: State, dt: float) -> float:
        """
        Computes the PID control action with enhanced anti-windup and filtering.

        Args:
            observation: The current state, must contain the key 'process_variable'.
            dt: The time step duration in seconds.

        Returns:
            The computed and clamped control action.
        """
        if dt <= 0:
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        process_variable = observation.get('process_variable')
        if process_variable is None:
            # Handle cases where the observation is not as expected
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        # 对于水位控制，当水位高于目标时，需要增加闸门开度（正值）
        # 当水位低于目标时，需要减少闸门开度（负值，但限制在0）
        error = self.setpoint - process_variable

        # Proportional term
        p_term = self.Kp * error

        # Integral term with improved anti-windup
        # 限制积分项的增长速度
        integral_increment = error * dt
        if abs(integral_increment) > self.integral_windup_limit:
            integral_increment = self.integral_windup_limit * (1 if integral_increment > 0 else -1)
        
        self._integral += integral_increment
        i_term = self.Ki * self._integral

        # Derivative term with filtering
        raw_derivative = (error - self._previous_error) / dt
        # 应用一阶低通滤波器
        alpha = dt / (self.filter_time_constant + dt)
        self._filtered_derivative = alpha * raw_derivative + (1 - alpha) * self._filtered_derivative
        d_term = self.Kd * self._filtered_derivative

        # Compute raw, unclamped output
        output = p_term + i_term + d_term

        # 对于水位控制，我们需要特殊处理：
        # 当水位高于目标时（error < 0），需要增加闸门开度，输出应该是正值
        # 当水位低于目标时（error > 0），需要减少闸门开度，输出应该是负值但限制在0
        
        # 重新计算控制信号：当水位高于目标时，输出正值
        if error < 0:  # 水位高于目标，需要增加闸门开度
            # 将负误差转换为正控制信号
            control_signal = -output  # 反转符号
        else:  # 水位低于目标，需要减少闸门开度
            control_signal = 0  # 直接设为0，不减少闸门开度
        
        # 限制控制信号在合理范围内
        if control_signal > self.max_output:
            clamped_output = self.max_output
            # 反向计算积分项，防止积分饱和
            if error < 0:  # 当需要增加开度但被限制时
                self._integral -= integral_increment
        elif control_signal < self.min_output:
            clamped_output = self.min_output
            # 反向计算积分项，防止积分饱和
            if error > 0:  # 当需要减少开度但被限制时
                self._integral -= integral_increment
        else:
            clamped_output = control_signal
            
        # 调试输出
        if abs(error) > 0.1:  # 只在误差较大时输出调试信息
            print(f"PID Debug: error={error:.3f}, P={p_term:.3f}, I={i_term:.3f}, D={d_term:.3f}, "
                  f"raw_output={output:.3f}, clamped={clamped_output:.3f}")

        # Update state for next iteration
        self._previous_error = error
        self._previous_output = clamped_output

        return clamped_output

    def set_setpoint(self, new_setpoint: float):
        """
        Updates the controller's setpoint and resets internal states.
        """
        if self.setpoint != new_setpoint:
            print(f"PIDController setpoint updated from {self.setpoint} to {new_setpoint}.")
            self.setpoint = new_setpoint
            # Reset integral and derivative error to prevent output jumps
            self._integral = 0
            self._previous_error = 0 # Or set to current error if smooth transition is needed
