"""
统一本地控制代理基类 - 重构版本

设计原则：
1. 所有控制代理（闸门、泵、阀、水轮机）都继承此基类
2. 提供灵活但统一的接口
3. 支持不同控制策略（连续、离散、多执行器）
4. 保持架构一致性
"""
from abc import abstractmethod
from core_lib.core.interfaces import Agent, Controller, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Dict, Any, Union, List
from enum import Enum

class ControlStrategy(Enum):
    """控制策略枚举"""
    CONTINUOUS = "continuous"      # 连续控制（PID等）
    DISCRETE = "discrete"          # 离散控制（开关）
    MULTI_ACTUATOR = "multi_actuator"  # 多执行器协调

class UnifiedLocalControlAgent(Agent):
    """
    统一的本地控制代理基类
    
    设计特点：
    1. 支持多种控制策略
    2. 灵活的配置系统
    3. 统一的接口规范
    4. 可扩展的架构
    """
    
    def enable_control_logging(self, enabled: bool, state_topic: str, interval: int = 5):
        """
        启用控制状态日志记录
        
        Args:
            enabled: 启用/禁用日志功能
            state_topic: 发布调试状态的主题
            interval: 日志记录间隔（秒）
        """
        self.debug_enabled = enabled
        self.state_topic = state_topic
        self.log_interval = interval
        
        if enabled:
            # 初始化状态发布定时器
            self._last_log_time = 0
            print(f"Control logging enabled @ {interval}s intervals to {state_topic}")
    
    def __init__(self,
                 agent_id: str,
                 message_bus: MessageBus,
                 time_step: float,
                 control_strategy: ControlStrategy,
                 # 基础配置
                 observation_topic: Optional[str] = None,
                 observation_key: Optional[str] = 'value',
                 action_topic: Optional[str] = None,
                 command_topic: Optional[str] = None,
                 feedback_topic: Optional[str] = None,
                 # 控制器配置
                 controller: Optional[Controller] = None,
                 controller_config: Optional[Dict[str, Any]] = None,
                 # 设备特定配置
                 device_config: Optional[Dict[str, Any]] = None,
                 # 扩展配置
                 **kwargs):
        """
        初始化统一控制代理
        
        Args:
            agent_id: 代理唯一标识
            message_bus: 消息总线
            time_step: 仿真时间步长
            control_strategy: 控制策略类型
            observation_topic: 观测主题
            observation_key: 观测数据键
            action_topic: 动作主题
            command_topic: 命令主题
            feedback_topic: 反馈主题
            controller: 控制器实例
            controller_config: 控制器配置
            device_config: 设备特定配置
            **kwargs: 其他配置参数
        """
        super().__init__(agent_id)
        
        # 基础属性
        self.bus = message_bus
        self.time_step = time_step
        self.control_strategy = control_strategy
        
        # 主题配置
        self.observation_topic = observation_topic
        self.observation_key = observation_key
        self.action_topic = action_topic or f'control.{agent_id}.action'
        self.command_topic = command_topic
        self.feedback_topic = feedback_topic
        
        # 控制器配置
        self.controller = controller
        self.controller_config = controller_config or {}
        self.device_config = device_config or {}
        
        # 状态管理
        self.latest_feedback: State = {}
        self.current_observation: State = {}
        
        # 订阅主题
        self._setup_subscriptions()
        
        # 设备特定初始化
        self._initialize_device_specific(**kwargs)
        
        print(f"UnifiedLocalControlAgent '{self.agent_id}' initialized with {control_strategy.value} strategy")
    
    def _setup_subscriptions(self):
        """设置消息订阅"""
        if self.observation_topic:
            self.bus.subscribe(self.observation_topic, self.handle_observation)
            print(f"Subscribed to observation topic: {self.observation_topic}")
        
        if self.command_topic:
            self.bus.subscribe(self.command_topic, self.handle_command_message)
            print(f"Subscribed to command topic: {self.command_topic}")
        
        if self.feedback_topic:
            self.bus.subscribe(self.feedback_topic, self.handle_feedback_message)
            print(f"Subscribed to feedback topic: {self.feedback_topic}")
    
    @abstractmethod
    def _initialize_device_specific(self, **kwargs):
        """设备特定初始化 - 子类必须实现"""
        pass
    
    def handle_observation(self, message: Message):
        """处理观测消息"""
        # 预处理观测数据
        processed_message = self.preprocess_observation(message)
        self.current_observation = processed_message
        
        # 根据控制策略执行控制逻辑
        if self.control_strategy == ControlStrategy.CONTINUOUS:
            self._handle_continuous_control(processed_message)
        elif self.control_strategy == ControlStrategy.DISCRETE:
            self._handle_discrete_control(processed_message)
        elif self.control_strategy == ControlStrategy.MULTI_ACTUATOR:
            self._handle_multi_actuator_control(processed_message)
    
    def _handle_continuous_control(self, message: Message):
        """处理连续控制"""
        if not self.controller:
            print(f"[{self.agent_id}] Warning: No controller available for continuous control")
            return
        
        # 提取过程变量
        process_variable = message.get(self.observation_key)
        if process_variable is None:
            print(f"[{self.agent_id}] Warning: Process variable '{self.observation_key}' not found")
            return
        
        # 计算控制动作
        observation_for_controller = {'process_variable': process_variable}
        control_signal = self.controller.compute_control_action(observation_for_controller, self.time_step)
        
        # 发布控制动作
        self.publish_action(control_signal)
        print(f"[{self.agent_id}] Continuous control: {process_variable:.4f} -> {control_signal:.4f}")
    
    def _handle_discrete_control(self, message: Message):
        """处理离散控制"""
        # 子类可以重写此方法实现特定的离散控制逻辑
        control_signal = self.compute_discrete_control_action(message)
        if control_signal is not None:
            self.publish_action(control_signal)
            print(f"[{self.agent_id}] Discrete control: {control_signal}")
    
    def _handle_multi_actuator_control(self, message: Message):
        """处理多执行器控制"""
        # 子类可以重写此方法实现多执行器协调逻辑
        control_signals = self.compute_multi_actuator_control_action(message)
        if control_signals:
            self.publish_action(control_signals)
            print(f"[{self.agent_id}] Multi-actuator control: {len(control_signals)} signals")
    
    def preprocess_observation(self, message: Message) -> Message:
        """预处理观测消息 - 子类可重写"""
        return message
    
    def compute_discrete_control_action(self, message: Message) -> Optional[Union[int, float, bool]]:
        """计算离散控制动作 - 子类可重写"""
        return None
    
    def compute_multi_actuator_control_action(self, message: Message) -> Optional[Dict[str, Any]]:
        """计算多执行器控制动作 - 子类可重写"""
        return None
    
    def handle_command_message(self, message: Message):
        """处理命令消息"""
        if hasattr(self.controller, 'update_setpoint'):
            self.controller.update_setpoint(message)
        elif hasattr(self.controller, 'set_setpoint'):
            new_setpoint = message.get('new_setpoint')
            if new_setpoint is not None:
                self.controller.set_setpoint(new_setpoint)
    
    def handle_feedback_message(self, message: Message):
        """处理反馈消息"""
        self.latest_feedback = message
    
    def publish_action(self, control_signal: Union[float, int, bool, Dict[str, Any]]):
        """发布控制动作"""
        if isinstance(control_signal, dict):
            # 多执行器模式
            print(f"[{self.agent_id}] Multi-actuator control: {len(control_signal)} signals")
            for topic, signal_value in control_signal.items():
                if topic and signal_value is not None:
                    action_message = {'control_signal': signal_value, 'agent_id': self.agent_id}
                    print(f"[{self.agent_id}] Publishing to {topic}: {signal_value:.4f}")
                    self.bus.publish(topic, action_message)
        else:
            # 单执行器模式
            action_message = {'control_signal': control_signal, 'agent_id': self.agent_id}
            print(f"[{self.agent_id}] Publishing single signal: {control_signal:.4f}")
            self.bus.publish(self.action_topic, action_message)
    
    def run(self, current_time: float):
        """主执行循环 - 事件驱动代理通常为空实现"""
        pass
