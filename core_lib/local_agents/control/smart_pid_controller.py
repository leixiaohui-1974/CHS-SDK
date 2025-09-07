"""
智能PID控制器，专门为水位控制设计。
"""
from core_lib.core.interfaces import Controller, State
import numpy as np

class SmartPIDController(Controller):
    """
    智能PID控制器，具有以下特性：
    1. 根据误差大小动态调整控制策略
    2. 大误差时使用bang-bang控制，小误差时使用PID控制
    3. 考虑系统响应时间，避免过度控制
    4. 自适应增益调整
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float,
                 min_output: float, max_output: float):
        """
        初始化智能PID控制器。
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
        
        # 智能控制参数
        self.integral_windup_limit = 0.01
        self.filter_time_constant = 0.5
        
        # 控制策略切换阈值
        self.bang_bang_threshold = 1.0  # 误差大于此值时使用bang-bang控制
        self.pid_threshold = 0.1        # 误差小于此值时使用精细PID控制
        
        # 自适应参数
        self.error_history = []
        self.max_history_length = 5
        self.control_cycle_count = 0
        
        print(f"SmartPIDController created with Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}")

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
                self.Kp = min(self.base_Kp * 1.5, self.base_Kp * 3.0)
                self.Ki = min(self.base_Ki * 1.2, self.base_Ki * 2.0)
            elif error_trend < -0.05:  # 误差快速减小
                self.Kp = max(self.base_Kp * 0.8, self.base_Kp * 0.5)
                self.Ki = max(self.base_Ki * 0.9, self.base_Ki * 0.7)
            else:  # 误差稳定
                self.Kp = self.base_Kp
                self.Ki = self.base_Ki

    def _bang_bang_control(self, error: float) -> float:
        """
        Bang-bang控制：大误差时使用开关控制。
        """
        if error < -self.bang_bang_threshold:  # 水位过高
            return self.max_output  # 全开闸门
        elif error > self.bang_bang_threshold:  # 水位过低
            return self.min_output  # 关闭闸门
        else:
            return (self.min_output + self.max_output) / 2  # 中等开度

    def _pid_control(self, error: float, dt: float) -> float:
        """
        标准PID控制。
        """
        # 比例项
        p_term = self.Kp * error

        # 积分项（带积分分离）
        integral_increment = error * dt
        if abs(integral_increment) > self.integral_windup_limit:
            integral_increment = self.integral_windup_limit * (1 if integral_increment > 0 else -1)
        
        # 积分分离：大误差时关闭积分
        if abs(error) > self.bang_bang_threshold:
            pass  # 大误差时，积分项不更新
        else:
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
        
        return control_signal

    def compute_control_action(self, observation: State, dt: float) -> float:
        """
        计算智能控制动作。
        """
        if dt <= 0:
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        process_variable = observation.get('process_variable')
        if process_variable is None:
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        error = self.setpoint - process_variable
        self.control_cycle_count += 1
        
        # 自适应增益调整
        self._adaptive_gain_adjustment(error, dt)

        # 根据误差大小选择控制策略
        if abs(error) > self.bang_bang_threshold:
            # 大误差：使用bang-bang控制
            control_signal = self._bang_bang_control(error)
            control_type = "Bang-Bang"
        elif abs(error) > self.pid_threshold:
            # 中等误差：使用PID控制
            control_signal = self._pid_control(error, dt)
            control_type = "PID"
        else:
            # 小误差：使用精细PID控制
            control_signal = self._pid_control(error, dt)
            control_type = "Fine PID"

        # 限制控制信号
        if control_signal > self.max_output:
            clamped_output = self.max_output
        elif control_signal < self.min_output:
            clamped_output = self.min_output
        else:
            clamped_output = control_signal
            
        # 调试输出（每10步输出一次）
        if self.control_cycle_count % 10 == 0 and abs(error) > 0.01:
            print(f"Smart PID [{control_type}]: error={error:.3f}, Kp={self.Kp:.2f}, "
                  f"output={clamped_output:.3f}, cycle={self.control_cycle_count}")

        # 更新状态
        self._previous_error = error
        self._previous_output = clamped_output

        return clamped_output

    def set_setpoint(self, new_setpoint: float):
        """
        更新设定值并重置内部状态。
        """
        if self.setpoint != new_setpoint:
            print(f"SmartPIDController setpoint updated from {self.setpoint} to {new_setpoint}")
            self.setpoint = new_setpoint
            # 重置积分项，避免设定值变化时的冲击
            self._integral = 0
            self._previous_error = 0
            self.error_history = []
            self.control_cycle_count = 0
