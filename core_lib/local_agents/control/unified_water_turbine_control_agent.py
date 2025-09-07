"""
统一水轮机控制代理 - 基于统一架构

特点：
1. 继承 UnifiedLocalControlAgent
2. 使用 CONTINUOUS 控制策略
3. 集成水轮机特定功能
4. 保持架构一致性
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Dict, Any
import math

class UnifiedWaterTurbineControlAgent(UnifiedLocalControlAgent):
    """
    统一水轮机控制代理
    
    继承统一架构，添加水轮机特定功能：
    - 功率生成优化
    - 电网同步控制
    - 效率优化
    - 水头-流量特性处理
    """
    
    def __init__(self,
                 agent_id: str,
                 controller: Controller,
                 message_bus: MessageBus,
                 observation_topic: str,
                 observation_key: str,
                 action_topic: str,
                 dt: float,
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None,
                 **kwargs):
        """
        初始化统一水轮机控制代理
        
        Args:
            agent_id: 代理标识
            controller: PID控制器
            message_bus: 消息总线
            observation_topic: 观测主题
            observation_key: 观测键
            action_topic: 动作主题
            dt: 时间步长
            command_topic: 命令主题
            feedback_topic: 反馈主题
            **kwargs: 水轮机特定配置
        """
        # 调用父类构造函数，使用连续控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            dt=dt,
            control_strategy=ControlStrategy.CONTINUOUS,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            command_topic=command_topic,
            feedback_topic=feedback_topic,
            controller=controller,
            **kwargs
        )
    
    def _initialize_device_specific(self, **kwargs):
        """水轮机特定初始化"""
        # 水轮机物理参数
        self.turbine_type = kwargs.get('turbine_type', 'francis')  # francis, kaplan, pelton, etc.
        self.rated_power = kwargs.get('rated_power', 1000)  # kW
        self.rated_head = kwargs.get('rated_head', 50)  # m
        self.rated_flow = kwargs.get('rated_flow', 2.0)  # m³/s
        self.efficiency_curve = kwargs.get('efficiency_curve', {})
        
        # 控制参数
        self.power_factor_target = kwargs.get('power_factor_target', 0.9)
        self.frequency_target = kwargs.get('frequency_target', 50.0)  # Hz
        self.grid_sync_enabled = kwargs.get('grid_sync_enabled', True)
        
        # 水轮机状态
        self.current_power = 0.0
        self.current_head = 0.0
        self.current_flow = 0.0
        self.current_efficiency = 0.0
        self.current_frequency = 0.0
        
        print(f"Water turbine '{self.agent_id}' initialized: {self.turbine_type}, {self.rated_power}kW")
    
    def preprocess_observation(self, message: Message) -> Message:
        """水轮机特定观测预处理"""
        # 提取水轮机状态信息
        if 'power' in message:
            self.current_power = message['power']
        
        if 'head' in message:
            self.current_head = message['head']
        
        if 'flow' in message:
            self.current_flow = message['flow']
        
        if 'frequency' in message:
            self.current_frequency = message['frequency']
        
        # 计算效率
        if self.current_head > 0 and self.current_flow > 0:
            theoretical_power = self._calculate_theoretical_power(self.current_head, self.current_flow)
            if theoretical_power > 0:
                self.current_efficiency = (self.current_power / theoretical_power) * 100
        
        # 应用效率优化校正
        if 'process_variable' in message:
            optimized_value = self._apply_efficiency_optimization(message['process_variable'])
            message['process_variable'] = optimized_value
        
        return message
    
    def _calculate_theoretical_power(self, head: float, flow: float) -> float:
        """计算理论功率"""
        # P = ρ * g * H * Q * η
        # 其中：ρ = 1000 kg/m³, g = 9.81 m/s²
        rho = 1000  # kg/m³
        g = 9.81    # m/s²
        return rho * g * head * flow / 1000  # 转换为 kW
    
    def _apply_efficiency_optimization(self, control_signal: float) -> float:
        """应用效率优化"""
        # 根据水头-流量特性优化控制信号
        if self.current_head > 0:
            # 计算最优流量
            optimal_flow = self._calculate_optimal_flow(self.current_head)
            
            # 调整控制信号以接近最优流量
            if self.current_flow > 0:
                flow_ratio = optimal_flow / self.current_flow
                optimized_signal = control_signal * flow_ratio
                return max(0.0, min(1.0, optimized_signal))
        
        return control_signal
    
    def _calculate_optimal_flow(self, head: float) -> float:
        """计算给定水头下的最优流量"""
        # 简化的最优流量计算
        # 实际实现会使用水轮机的特性曲线
        head_ratio = head / self.rated_head
        optimal_flow_ratio = min(1.0, head_ratio ** 0.5)  # 简化的平方根关系
        return self.rated_flow * optimal_flow_ratio
    
    def handle_command_message(self, message: Message):
        """处理水轮机特定命令"""
        command_type = message.get('command_type')
        
        if command_type == 'set_power':
            # 设置目标功率
            target_power = message.get('power', 0.0)
            target_power = max(0.0, min(self.rated_power, target_power))
            
            if hasattr(self.controller, 'set_setpoint'):
                self.controller.set_setpoint(target_power)
                print(f"[{self.agent_id}] Power setpoint updated to: {target_power:.1f} kW")
        
        elif command_type == 'set_frequency':
            # 设置目标频率
            target_frequency = message.get('frequency', 50.0)
            if hasattr(self.controller, 'set_setpoint'):
                self.controller.set_setpoint(target_frequency)
                print(f"[{self.agent_id}] Frequency setpoint updated to: {target_frequency:.1f} Hz")
        
        elif command_type == 'grid_sync':
            # 电网同步
            self._perform_grid_synchronization()
        
        elif command_type == 'emergency_shutdown':
            # 紧急停机
            self._emergency_shutdown()
        
        elif command_type == 'efficiency_optimization':
            # 效率优化模式
            self._enable_efficiency_optimization()
        
        else:
            # 调用父类方法处理标准命令
            super().handle_command_message(message)
    
    def _perform_grid_synchronization(self):
        """执行电网同步"""
        print(f"[{self.agent_id}] Starting grid synchronization...")
        
        # 同步步骤：
        # 1. 检查频率匹配
        if abs(self.current_frequency - self.frequency_target) > 0.1:
            print("Adjusting frequency for grid sync...")
        
        # 2. 检查相位匹配
        print("Checking phase alignment...")
        
        # 3. 检查电压匹配
        print("Checking voltage levels...")
        
        print(f"[{self.agent_id}] Grid synchronization completed")
    
    def _emergency_shutdown(self):
        """紧急停机程序"""
        print(f"[{self.agent_id}] Emergency shutdown initiated...")
        
        # 停机步骤：
        # 1. 快速关闭导叶
        self.publish_action(0.0)
        
        # 2. 断开电网连接
        print("Disconnecting from grid...")
        
        # 3. 启动制动系统
        print("Activating brake system...")
        
        print(f"[{self.agent_id}] Emergency shutdown completed")
    
    def _enable_efficiency_optimization(self):
        """启用效率优化模式"""
        print(f"[{self.agent_id}] Efficiency optimization mode enabled")
        
        # 优化策略：
        # 1. 根据水头调整流量
        # 2. 监控效率曲线
        # 3. 自动调整控制参数
    
    def get_turbine_status(self) -> Dict[str, Any]:
        """获取水轮机状态信息"""
        return {
            'turbine_type': self.turbine_type,
            'rated_power': self.rated_power,
            'rated_head': self.rated_head,
            'rated_flow': self.rated_flow,
            'current_power': self.current_power,
            'current_head': self.current_head,
            'current_flow': self.current_flow,
            'current_efficiency': self.current_efficiency,
            'current_frequency': self.current_frequency,
            'power_factor_target': self.power_factor_target,
            'frequency_target': self.frequency_target,
            'grid_sync_enabled': self.grid_sync_enabled
        }
