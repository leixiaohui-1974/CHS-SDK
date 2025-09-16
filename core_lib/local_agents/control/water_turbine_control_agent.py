"""
水轮机控制代理 - 基于统一架构

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

class WaterTurbineControlAgent(UnifiedLocalControlAgent):
    """
    水轮机控制代理
    
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
                 time_step: float,
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None,
                 **kwargs):
        """
        初始化水轮机控制代理
        
        Args:
            agent_id: 代理标识
            controller: PID控制器
            message_bus: 消息总线
            observation_topic: 观测主题
            observation_key: 观测键
            action_topic: 动作主题
            time_step: 时间步长
            command_topic: 命令主题
            feedback_topic: 反馈主题
            **kwargs: 水轮机特定配置
        """
        # 调用父类构造函数，使用连续控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
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
        # 水轮机类型和参数
        self.turbine_type = kwargs.get('turbine_type', 'francis')
        self.rated_power = kwargs.get('rated_power', 1000.0)  # kW
        self.rated_head = kwargs.get('rated_head', 100.0)     # m
        self.rated_flow = kwargs.get('rated_flow', 10.0)      # m³/s
        self.efficiency = kwargs.get('efficiency', 0.90)
        
        # 电网同步参数
        self.grid_sync_enabled = kwargs.get('grid_sync_enabled', True)
        self.grid_frequency = kwargs.get('grid_frequency', 50.0)  # Hz
        self.frequency_tolerance = kwargs.get('frequency_tolerance', 0.1)  # Hz
        
        # 操作约束
        self.min_flow_rate = kwargs.get('min_flow_rate', 0.1 * self.rated_flow)
        self.max_flow_rate = kwargs.get('max_flow_rate', 1.2 * self.rated_flow)
        self.max_flow_rate_change = kwargs.get('max_flow_rate_change', 0.1 * self.rated_flow)  # m³/s per second
        
        # 水轮机状态
        self.current_flow_rate = kwargs.get('initial_flow_rate', 0.0)
        self.current_power = 0.0
        self.current_efficiency = self.efficiency
        self.turbine_status = 'normal'  # normal, starting, stopping, fault
        self.grid_connected = False
        
        # 性能优化参数
        self.enable_efficiency_optimization = kwargs.get('enable_efficiency_optimization', True)
        self.head_flow_curve = kwargs.get('head_flow_curve')  # 可选的水头-流量曲线数据
        
        print(f"[{self.agent_id}] Water turbine initialized: type={self.turbine_type}, "
              f"rated_power={self.rated_power:.0f}kW, efficiency={self.efficiency:.2f}")
    
    def _handle_continuous_control(self, message: Message):
        """处理连续控制（重写父类方法）"""
        if self.turbine_status not in ['normal', 'starting']:
            print(f"[{self.agent_id}] Control disabled: status={self.turbine_status}")
            return
        
        if not self.controller:
            print(f"[{self.agent_id}] Warning: No controller available")
            return
        
        # 提取过程变量（通常是功率需求或水位）
        process_variable = message.get(self.observation_key)
        if process_variable is None:
            print(f"[{self.agent_id}] Warning: Process variable '{self.observation_key}' not found")
            return
        
        # 计算控制动作
        observation_for_controller = {'process_variable': process_variable}
        raw_control_signal = self.controller.compute_control_action(observation_for_controller, self.time_step)
        
        # 转换为流量控制信号
        target_flow_rate = self._convert_to_flow_rate(raw_control_signal, message)
        
        # 应用操作约束
        constrained_flow_rate = self._apply_flow_constraints(target_flow_rate)
        
        # 效率优化
        if self.enable_efficiency_optimization:
            optimized_flow_rate = self._optimize_efficiency(constrained_flow_rate, message)
        else:
            optimized_flow_rate = constrained_flow_rate
        
        # 电网同步检查
        if self.grid_sync_enabled and not self._check_grid_synchronization():
            print(f"[{self.agent_id}] Grid synchronization issue, reducing flow rate")
            optimized_flow_rate *= 0.9
        
        # 更新水轮机状态
        self.current_flow_rate = optimized_flow_rate
        self.current_power = self._calculate_power_output(optimized_flow_rate, message)
        
        # 发布控制动作
        self.publish_action(optimized_flow_rate)
        
        print(f"[{self.agent_id}] Turbine control: {process_variable:.4f} -> "
              f"flow={optimized_flow_rate:.2f}m³/s, power={self.current_power:.1f}kW")
    
    def _convert_to_flow_rate(self, control_signal: float, message: Message) -> float:
        """将控制信号转换为流量"""
        if self.observation_key in ['power_demand', 'power_setpoint']:
            # 功率控制模式：根据功率需求计算所需流量
            power_demand = control_signal
            available_head = message.get('head', self.rated_head)
            
            # P = ρ * g * Q * H * η
            # Q = P / (ρ * g * H * η)
            rho = 1000  # kg/m³
            g = 9.81    # m/s²
            
            if available_head > 0 and self.current_efficiency > 0:
                required_flow = power_demand * 1000 / (rho * g * available_head * self.current_efficiency)
            else:
                required_flow = 0.0
            
            return required_flow
        
        elif self.observation_key in ['water_level', 'head']:
            # 水位控制模式：根据水位偏差调整流量
            return self.current_flow_rate + control_signal * self.rated_flow * 0.1
        
        else:
            # 直接流量控制
            return control_signal * self.rated_flow
    
    def _apply_flow_constraints(self, target_flow_rate: float) -> float:
        """应用流量约束"""
        # 限制流量范围
        constrained_flow = max(self.min_flow_rate, min(self.max_flow_rate, target_flow_rate))
        
        # 限制流量变化速率
        if hasattr(self, 'current_flow_rate'):
            max_change = self.max_flow_rate_change * self.time_step
            flow_change = constrained_flow - self.current_flow_rate
            
            if abs(flow_change) > max_change:
                if flow_change > 0:
                    constrained_flow = self.current_flow_rate + max_change
                else:
                    constrained_flow = self.current_flow_rate - max_change
        
        return constrained_flow
    
    def _optimize_efficiency(self, flow_rate: float, message: Message) -> float:
        """效率优化"""
        available_head = message.get('head', self.rated_head)
        
        # 计算当前工况下的效率
        head_ratio = available_head / self.rated_head
        flow_ratio = flow_rate / self.rated_flow
        
        # 简化的效率曲线模型
        if 0.2 <= flow_ratio <= 1.0 and 0.5 <= head_ratio <= 1.5:
            # 在高效区间内
            efficiency_factor = 1.0 - 0.1 * abs(flow_ratio - 0.8)**2 - 0.05 * abs(head_ratio - 1.0)**2
            self.current_efficiency = self.efficiency * efficiency_factor
        else:
            # 在低效区间
            self.current_efficiency = self.efficiency * 0.7
        
        return flow_rate  # 简化：不调整流量，仅更新效率
    
    def _calculate_power_output(self, flow_rate: float, message: Message) -> float:
        """计算功率输出"""
        available_head = message.get('head', self.rated_head)
        
        # P = ρ * g * Q * H * η / 1000 (kW)
        rho = 1000  # kg/m³
        g = 9.81    # m/s²
        
        power = rho * g * flow_rate * available_head * self.current_efficiency / 1000
        return min(power, self.rated_power)  # 限制在额定功率内
    
    def _check_grid_synchronization(self) -> bool:
        """检查电网同步状态"""
        if not self.grid_sync_enabled:
            return True
        
        # 简化的电网同步检查
        # 在实际应用中，这里会检查频率、相位、电压等参数
        return self.grid_connected
    
    def handle_command_message(self, message: Message):
        """处理命令消息（重写父类方法）"""
        # 处理控制器设定值更新
        super().handle_command_message(message)
        
        # 处理水轮机特定命令
        command_type = message.get('command_type')
        
        if command_type == 'start_turbine':
            self.turbine_status = 'starting'
            print(f"[{self.agent_id}] Turbine starting sequence initiated")
        
        elif command_type == 'stop_turbine':
            self.turbine_status = 'stopping'
            self.current_flow_rate = 0.0
            self.publish_action(0.0)
            print(f"[{self.agent_id}] Turbine stopping sequence initiated")
        
        elif command_type == 'connect_grid':
            self.grid_connected = True
            print(f"[{self.agent_id}] Connected to grid")
        
        elif command_type == 'disconnect_grid':
            self.grid_connected = False
            print(f"[{self.agent_id}] Disconnected from grid")
        
        elif command_type == 'set_efficiency_mode':
            self.enable_efficiency_optimization = message.get('enabled', True)
            print(f"[{self.agent_id}] Efficiency optimization: {self.enable_efficiency_optimization}")
    
    def publish_action(self, flow_rate: float):
        """发布水轮机流量控制动作"""
        action_message = {
            'control_signal': flow_rate,
            'agent_id': self.agent_id,
            'turbine_type': self.turbine_type,
            'current_power': self.current_power,
            'current_efficiency': self.current_efficiency,
            'turbine_status': self.turbine_status,
            'grid_connected': self.grid_connected,
            'timestamp': self.bus.get_current_time() if hasattr(self.bus, 'get_current_time') else 0
        }
        
        self.bus.publish(self.action_topic, action_message)
        print(f"[{self.agent_id}] Published turbine flow: {flow_rate:.2f} m³/s, "
              f"power: {self.current_power:.1f} kW")
    
    def get_turbine_status(self) -> Dict[str, Any]:
        """获取水轮机状态信息"""
        return {
            'agent_id': self.agent_id,
            'turbine_type': self.turbine_type,
            'turbine_status': self.turbine_status,
            'grid_connected': self.grid_connected,
            'current_flow_rate': self.current_flow_rate,
            'current_power': self.current_power,
            'current_efficiency': self.current_efficiency,
            'rated_power': self.rated_power,
            'rated_head': self.rated_head,
            'rated_flow': self.rated_flow,
            'efficiency_optimization': self.enable_efficiency_optimization
        }