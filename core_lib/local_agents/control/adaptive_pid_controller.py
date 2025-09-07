"""
自适应PID控制器，能够根据系统响应自动调整参数。
"""
from core_lib.core.interfaces import Controller, State
import numpy as np

class AdaptivePIDController(Controller):
    """
    自适应PID控制器，具有以下特性：
    1. 根据误差大小自动调整PID参数
    2. 积分分离：大误差时关闭积分项
    3. 微分先行：减少设定值变化时的冲击
    4. 自适应增益调整
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float,
                 min_output: float, max_output: float):
        """
        初始化自适应PID控制器。

        Args:
            Kp: 基础比例增益
            Ki: 基础积分增益
            Kd: 基础微分增益
            setpoint: 目标值
            min_output: 最小输出
            max_output: 最大输出
        """
        # 基础PID参数
        self.base_Kp = Kp
        self.base_Ki = Ki
        self.base_Kd = Kd
        
        # 当前PID参数（会自适应调整）
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        
        self.setpoint = setpoint
        self.min_output = min_output
        self.max_output = max_output

        # 内部状态
        self._integral = 0
        self._previous_error = 0
        self._previous_output = 0
        self._filtered_derivative = 0
        
        # 自适应参数
        self.integral_windup_limit = 0.05
        self.filter_time_constant = 0.1
        
        # 积分分离参数
        self.integral_separation_threshold = 1.0  # 误差大于此值时关闭积分
        
        # 自适应增益参数
        self.adaptive_gain_factor = 0.1
        self.error_history = []
        self.max_history_length = 10
        
        print(f"AdaptivePIDController created with base Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}")

    def _adaptive_gain_adjustment(self, error: float, dt: float):
        """
        根据误差历史自适应调整增益。
        """
        # 记录误差历史
        self.error_history.append(abs(error))
        if len(self.error_history) > self.max_history_length:
            self.error_history.pop(0)
        
        # 计算误差变化趋势
        if len(self.error_history) >= 3:
            recent_errors = self.error_history[-3:]
            error_trend = np.mean(np.diff(recent_errors))
            
            # 如果误差在减小，保持当前参数
            # 如果误差在增大，增加增益
            if error_trend > 0:  # 误差增大
                self.Kp = min(self.base_Kp * 1.2, self.base_Kp * 2.0)
                self.Ki = min(self.base_Ki * 1.1, self.base_Ki * 1.5)
            elif error_trend < -0.1:  # 误差快速减小
                self.Kp = max(self.base_Kp * 0.9, self.base_Kp * 0.5)
                self.Ki = max(self.base_Ki * 0.95, self.base_Ki * 0.7)
            else:  # 误差稳定
                self.Kp = self.base_Kp
                self.Ki = self.base_Ki

    def compute_control_action(self, observation: State, dt: float) -> float:
        """
        计算自适应PID控制动作。
        """
        if dt <= 0:
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        process_variable = observation.get('process_variable')
        if process_variable is None:
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        error = self.setpoint - process_variable
        
        # 自适应增益调整
        self._adaptive_gain_adjustment(error, dt)

        # 比例项
        p_term = self.Kp * error

        # 积分项（带积分分离）
        integral_increment = error * dt
        if abs(integral_increment) > self.integral_windup_limit:
            integral_increment = self.integral_windup_limit * (1 if integral_increment > 0 else -1)
        
        # 积分分离：大误差时关闭积分
        if abs(error) > self.integral_separation_threshold:
            # 大误差时，积分项不更新，避免积分饱和
            pass
        else:
            # 小误差时，正常更新积分项
            self._integral += integral_increment
        
        i_term = self.Ki * self._integral

        # 微分项（带滤波）
        raw_derivative = (error - self._previous_error) / dt
        alpha = dt / (self.filter_time_constant + dt)
        self._filtered_derivative = alpha * raw_derivative + (1 - alpha) * self._filtered_derivative
        d_term = self.Kd * self._filtered_derivative

        # 计算原始输出
        output = p_term + i_term + d_term

        # 水位控制逻辑：当水位高于目标时，需要增加闸门开度
        if error < 0:  # 水位高于目标，需要增加闸门开度
            control_signal = -output  # 反转符号
        else:  # 水位低于目标，需要减少闸门开度
            control_signal = 0  # 直接设为0
        
        # 限制控制信号
        if control_signal > self.max_output:
            clamped_output = self.max_output
            if error < 0:
                self._integral -= integral_increment
        elif control_signal < self.min_output:
            clamped_output = self.min_output
            if error > 0:
                self._integral -= integral_increment
        else:
            clamped_output = control_signal
            
        # 调试输出（只在误差较大时）
        if abs(error) > 0.1:
            print(f"Adaptive PID: error={error:.3f}, Kp={self.Kp:.2f}, Ki={self.Ki:.3f}, "
                  f"P={p_term:.3f}, I={i_term:.3f}, D={d_term:.3f}, output={clamped_output:.3f}")

        # 更新状态
        self._previous_error = error
        self._previous_output = clamped_output

        return clamped_output

    def set_setpoint(self, new_setpoint: float):
        """
        更新设定值并重置内部状态。
        """
        if self.setpoint != new_setpoint:
            print(f"AdaptivePIDController setpoint updated from {self.setpoint} to {new_setpoint}")
            self.setpoint = new_setpoint
            # 重置积分项，避免设定值变化时的冲击
            self._integral = 0
            self._previous_error = 0
            self.error_history = []  # 清空误差历史
