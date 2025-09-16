"""
统一本地控制Agent实现

收敛所有本地控制类型：闸门、泵、阀门、水轮机等
替代：GateControlAgent、PumpControlAgent、ValveControlAgent等
"""
from typing import Dict, Any, Optional, Union
import time
import threading

from core_lib.core.new_interfaces import (
    LocalControlAgent, DeviceType, ControlStrategy, Config, Message, State
)
from core_lib.core.event_bus import get_global_event_bus
from core_lib.core.factories import get_global_controller_factory
from core_lib.core.config_schema import LocalControlAgentConfig

class UnifiedLocalControlAgent(LocalControlAgent):
    """
    统一本地控制Agent
    
    支持的设备类型：
    - GATE (闸门) - 替代 GateControlAgent
    - PUMP (泵) - 替代 PumpControlAgent  
    - VALVE (阀门) - 替代 ValveControlAgent
    - TURBINE (水轮机) - 替代 WaterTurbineControlAgent
    - RESERVOIR (水库) - 用于水库控制
    - CHANNEL (渠道) - 用于渠道控制
    
    支持的控制策略：
    - PID - 连续控制
    - MPC - 模型预测控制
    - RULE_BASED - 基于规则
    - DISCRETE - 离散控制
    - NEURAL_NETWORK - 神经网络控制
    - FUZZY - 模糊控制
    """
    
    def __init__(self, agent_id: str, device_type: DeviceType, 
                 control_strategy: ControlStrategy, config: Optional[Config] = None):
        super().__init__(agent_id, device_type, control_strategy, config)
        
        # 基础配置
        self.target_component = config.get('target_component') if config else None
        self.observation_topic = config.get('observation_topic') if config else None
        self.action_topic = config.get('action_topic', f'control.{agent_id}.action') if config else f'control.{agent_id}.action'
        self.command_topic = config.get('command_topic') if config else None
        self.feedback_topic = config.get('feedback_topic') if config else None
        self.observation_key = config.get('observation_key', 'value') if config else 'value'
        
        # 控制配置
        self.controller_config = config.get('controller_config', {}) if config else {}
        self.control_limits = config.get('control_limits', {}) if config else {}
        
        # 设备特定配置
        self.device_config = config.get('device_config', {}) if config else {}
        
        # 状态管理
        self.current_observation: Optional[State] = None
        self.last_control_action: Optional[Any] = None
        self.control_history: List[Dict[str, Any]] = []
        self.max_history_length = config.get('max_history_length', 100) if config else 100
        
        # 性能监控
        self.control_metrics = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'average_response_time': 0.0,
            'last_action_time': None
        }
        
        # 初始化控制器
        self._initialize_controller()
        
        # 设备特定初始化
        self._initialize_device_specific()
        
        print(f"[UnifiedLocalControl] Initialized {device_type.value} controller: {agent_id} with {control_strategy.value} strategy")
    
    def configure(self, config: Config) -> bool:
        """配置Agent"""
        try:
            self.config.update(config)
            
            # 更新控制器配置
            if 'controller_config' in config:
                self.controller_config.update(config['controller_config'])
                self._initialize_controller()
            
            # 更新设备配置
            if 'device_config' in config:
                self.device_config.update(config['device_config'])
                self._initialize_device_specific()
            
            self._log("info", "Configuration updated successfully")
            return True
        except Exception as e:
            self._log("error", f"Configuration failed: {e}")
            return False
    
    def start(self) -> bool:
        """启动Agent"""
        try:
            # 设置事件总线
            if not self.event_bus:
                self.event_bus = get_global_event_bus()
            
            # 订阅主题
            self._setup_subscriptions()
            
            self.status = self.status.__class__.RUNNING
            self._log("info", "Agent started successfully")
            return True
        except Exception as e:
            self._log("error", f"Start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """停止Agent"""
        try:
            # 取消订阅
            self._cleanup_subscriptions()
            
            self.status = self.status.__class__.STOPPED
            self._log("info", "Agent stopped")
            return True
        except Exception as e:
            self._log("error", f"Stop failed: {e}")
            return False
    
    def step(self, current_time: float) -> bool:
        """执行一个时间步"""
        try:
            # 更新指标
            self.metrics.last_execution_time = time.time()
            
            # 如果有观测数据，执行控制逻辑
            if self.current_observation:
                action = self.compute_control_action(self.current_observation, current_time)
                if action is not None:
                    return self.apply_control_action(action)
            
            return True
        except Exception as e:
            self._log("error", f"Step execution failed: {e}")
            return False
    
    def get_device_state(self) -> State:
        """获取设备状态"""
        return {
            'agent_id': self.agent_id,
            'device_type': self.device_type.value,
            'control_strategy': self.control_strategy.value,
            'status': self.status.value,
            'current_observation': self.current_observation,
            'last_control_action': self.last_control_action,
            'metrics': self.control_metrics,
            'target_component': self.target_component
        }
    
    def compute_control_action(self, observation: State, current_time: float) -> Any:
        """计算控制动作"""
        start_time = time.time()
        
        try:
            # 预处理观测数据
            processed_observation = self._preprocess_observation(observation)
            
            # 根据控制策略计算动作
            if self.control_strategy == ControlStrategy.PID:
                action = self._compute_pid_action(processed_observation, current_time)
            elif self.control_strategy == ControlStrategy.MPC:
                action = self._compute_mpc_action(processed_observation, current_time)
            elif self.control_strategy == ControlStrategy.RULE_BASED:
                action = self._compute_rule_based_action(processed_observation, current_time)
            elif self.control_strategy == ControlStrategy.DISCRETE:
                action = self._compute_discrete_action(processed_observation, current_time)
            else:
                action = self._compute_generic_action(processed_observation, current_time)
            
            # 应用控制限制
            action = self._apply_control_limits(action)
            
            # 更新性能指标
            response_time = time.time() - start_time
            self._update_control_metrics(response_time, True)
            
            return action
            
        except Exception as e:
            self._log("error", f"Control action computation failed: {e}")
            self._update_control_metrics(time.time() - start_time, False)
            return None
    
    def apply_control_action(self, action: Any) -> bool:
        """应用控制动作"""
        try:
            # 记录动作历史
            self._record_action(action)
            
            # 根据设备类型应用不同的动作
            if self.device_type == DeviceType.GATE:
                return self._apply_gate_action(action)
            elif self.device_type == DeviceType.PUMP:
                return self._apply_pump_action(action)
            elif self.device_type == DeviceType.VALVE:
                return self._apply_valve_action(action)
            elif self.device_type == DeviceType.TURBINE:
                return self._apply_turbine_action(action)
            else:
                return self._apply_generic_action(action)
                
        except Exception as e:
            self._log("error", f"Control action application failed: {e}")
            return False
    
    def _initialize_controller(self):
        """初始化控制器"""
        try:
            if self.control_strategy in [ControlStrategy.PID, ControlStrategy.MPC]:
                factory = get_global_controller_factory()
                self.controller = factory.create_controller(self.control_strategy, self.controller_config)
                self._log("info", f"Controller initialized: {self.control_strategy.value}")
            else:
                self.controller = None
                self._log("info", f"Using built-in logic for {self.control_strategy.value}")
        except Exception as e:
            self._log("error", f"Controller initialization failed: {e}")
            self.controller = None
    
    def _initialize_device_specific(self):
        """设备特定初始化"""
        if self.device_type == DeviceType.GATE:
            self._initialize_gate_specific()
        elif self.device_type == DeviceType.PUMP:
            self._initialize_pump_specific()
        elif self.device_type == DeviceType.VALVE:
            self._initialize_valve_specific()
        elif self.device_type == DeviceType.TURBINE:
            self._initialize_turbine_specific()
    
    def _initialize_gate_specific(self):
        """闸门特定初始化"""
        self.gate_config = {
            'min_opening': self.device_config.get('min_opening', 0.0),
            'max_opening': self.device_config.get('max_opening', 1.0),
            'opening_rate': self.device_config.get('opening_rate', 0.1),  # 开启速率
            'closing_rate': self.device_config.get('closing_rate', 0.1)   # 关闭速率
        }
        self._log("info", f"Gate configuration: {self.gate_config}")
    
    def _initialize_pump_specific(self):
        """泵特定初始化"""
        self.pump_config = {
            'min_speed': self.device_config.get('min_speed', 0.0),
            'max_speed': self.device_config.get('max_speed', 100.0),
            'acceleration': self.device_config.get('acceleration', 10.0),
            'efficiency_curve': self.device_config.get('efficiency_curve', None)
        }
        self._log("info", f"Pump configuration: {self.pump_config}")
    
    def _initialize_valve_specific(self):
        """阀门特定初始化"""
        self.valve_config = {
            'valve_type': self.device_config.get('valve_type', 'linear'),  # linear, equal_percentage
            'cv': self.device_config.get('cv', 1.0),  # 流量系数
            'min_position': self.device_config.get('min_position', 0.0),
            'max_position': self.device_config.get('max_position', 100.0)
        }
        self._log("info", f"Valve configuration: {self.valve_config}")
    
    def _initialize_turbine_specific(self):
        """水轮机特定初始化"""
        self.turbine_config = {
            'rated_power': self.device_config.get('rated_power', 1000.0),
            'min_head': self.device_config.get('min_head', 5.0),
            'max_head': self.device_config.get('max_head', 100.0),
            'efficiency': self.device_config.get('efficiency', 0.85)
        }
        self._log("info", f"Turbine configuration: {self.turbine_config}")
    
    def _setup_subscriptions(self):
        """设置订阅"""
        if self.observation_topic:
            self.subscribe_topic(self.observation_topic, self._handle_observation)
        if self.command_topic:
            self.subscribe_topic(self.command_topic, self._handle_command)
        if self.feedback_topic:
            self.subscribe_topic(self.feedback_topic, self._handle_feedback)
    
    def _cleanup_subscriptions(self):
        """清理订阅"""
        # EventBus会自动处理清理
        pass
    
    def _handle_observation(self, message: Message):
        """处理观测消息"""
        try:
            self.current_observation = message
            
            # 提取过程变量
            process_variable = message.get(self.observation_key)
            if process_variable is not None:
                # 立即计算并应用控制动作
                current_time = message.get('_timestamp', time.time())
                action = self.compute_control_action(message, current_time)
                if action is not None:
                    self.apply_control_action(action)
            else:
                self._log("warning", f"Process variable '{self.observation_key}' not found in observation")
                
        except Exception as e:
            self._log("error", f"Observation handling failed: {e}")
    
    def _handle_command(self, message: Message):
        """处理命令消息"""
        try:
            command_type = message.get('command_type')
            
            if command_type == 'setpoint':
                new_setpoint = message.get('setpoint')
                if new_setpoint is not None and self.controller:
                    if hasattr(self.controller, 'set_setpoint'):
                        self.controller.set_setpoint(new_setpoint)
                        self._log("info", f"Setpoint updated to {new_setpoint}")
            
            elif command_type == 'enable':
                self.status = self.status.__class__.RUNNING
                self._log("info", "Controller enabled")
            
            elif command_type == 'disable':
                self.status = self.status.__class__.PAUSED
                self._log("info", "Controller disabled")
            
            else:
                self._log("warning", f"Unknown command type: {command_type}")
                
        except Exception as e:
            self._log("error", f"Command handling failed: {e}")
    
    def _handle_feedback(self, message: Message):
        """处理反馈消息"""
        try:
            # 反馈信息可用于控制器调整
            if self.controller and hasattr(self.controller, 'update_feedback'):
                self.controller.update_feedback(message)
            
            self._log("debug", f"Feedback received: {message}")
        except Exception as e:
            self._log("error", f"Feedback handling failed: {e}")
    
    def _preprocess_observation(self, observation: State) -> State:
        """预处理观测数据"""
        # 提取关键数据
        processed = {
            'process_variable': observation.get(self.observation_key, 0.0),
            'timestamp': observation.get('_timestamp', time.time())
        }
        
        # 设备特定预处理
        if self.device_type == DeviceType.GATE:
            processed['water_level'] = observation.get('water_level', 0.0)
            processed['flow_rate'] = observation.get('flow_rate', 0.0)
        elif self.device_type == DeviceType.PUMP:
            processed['pressure'] = observation.get('pressure', 0.0)
            processed['flow_rate'] = observation.get('flow_rate', 0.0)
        
        return processed
    
    def _compute_pid_action(self, observation: State, current_time: float) -> float:
        """计算PID控制动作"""
        if not self.controller:
            return 0.0
        
        return self.controller.compute_control_action(observation, current_time)
    
    def _compute_mpc_action(self, observation: State, current_time: float) -> float:
        """计算MPC控制动作"""
        if not self.controller:
            return 0.0
        
        return self.controller.compute_control_action(observation, current_time)
    
    def _compute_rule_based_action(self, observation: State, current_time: float) -> Any:
        """计算基于规则的控制动作"""
        process_variable = observation.get('process_variable', 0.0)
        
        # 简单的规则示例
        if self.device_type == DeviceType.GATE:
            if process_variable > 0.8:
                return 1.0  # 完全打开
            elif process_variable < 0.2:
                return 0.0  # 完全关闭
            else:
                return 0.5  # 半开
        
        return 0.0
    
    def _compute_discrete_action(self, observation: State, current_time: float) -> int:
        """计算离散控制动作"""
        process_variable = observation.get('process_variable', 0.0)
        
        # 简单的开关控制
        if process_variable > 0.5:
            return 1  # 开
        else:
            return 0  # 关
    
    def _compute_generic_action(self, observation: State, current_time: float) -> float:
        """计算通用控制动作"""
        # 默认比例控制
        process_variable = observation.get('process_variable', 0.0)
        setpoint = self.controller_config.get('setpoint', 0.5)
        gain = self.controller_config.get('gain', 1.0)
        
        error = setpoint - process_variable
        return gain * error
    
    def _apply_control_limits(self, action: Any) -> Any:
        """应用控制限制"""
        if isinstance(action, (int, float)):
            min_limit = self.control_limits.get('min', float('-inf'))
            max_limit = self.control_limits.get('max', float('inf'))
            return max(min_limit, min(max_limit, action))
        
        return action
    
    def _apply_gate_action(self, action: float) -> bool:
        """应用闸门动作"""
        try:
            # 限制开度范围
            opening = max(self.gate_config['min_opening'], 
                         min(self.gate_config['max_opening'], action))
            
            # 发布控制信号
            control_message = {
                'agent_id': self.agent_id,
                'device_type': 'gate',
                'action_type': 'set_opening',
                'opening': opening,
                'timestamp': time.time()
            }
            
            self.publish_message(self.action_topic, control_message)
            self.last_control_action = opening
            
            self._log("debug", f"Gate opening set to {opening:.3f}")
            return True
        except Exception as e:
            self._log("error", f"Gate action failed: {e}")
            return False
    
    def _apply_pump_action(self, action: float) -> bool:
        """应用泵动作"""
        try:
            # 限制速度范围
            speed = max(self.pump_config['min_speed'], 
                       min(self.pump_config['max_speed'], action))
            
            # 发布控制信号
            control_message = {
                'agent_id': self.agent_id,
                'device_type': 'pump',
                'action_type': 'set_speed',
                'speed': speed,
                'timestamp': time.time()
            }
            
            self.publish_message(self.action_topic, control_message)
            self.last_control_action = speed
            
            self._log("debug", f"Pump speed set to {speed:.3f}")
            return True
        except Exception as e:
            self._log("error", f"Pump action failed: {e}")
            return False
    
    def _apply_valve_action(self, action: float) -> bool:
        """应用阀门动作"""
        try:
            # 限制位置范围
            position = max(self.valve_config['min_position'], 
                          min(self.valve_config['max_position'], action))
            
            # 发布控制信号
            control_message = {
                'agent_id': self.agent_id,
                'device_type': 'valve',
                'action_type': 'set_position',
                'position': position,
                'timestamp': time.time()
            }
            
            self.publish_message(self.action_topic, control_message)
            self.last_control_action = position
            
            self._log("debug", f"Valve position set to {position:.3f}")
            return True
        except Exception as e:
            self._log("error", f"Valve action failed: {e}")
            return False
    
    def _apply_turbine_action(self, action: float) -> bool:
        """应用水轮机动作"""
        try:
            # 发布控制信号
            control_message = {
                'agent_id': self.agent_id,
                'device_type': 'turbine',
                'action_type': 'set_guide_vane',
                'guide_vane_opening': action,
                'timestamp': time.time()
            }
            
            self.publish_message(self.action_topic, control_message)
            self.last_control_action = action
            
            self._log("debug", f"Turbine guide vane set to {action:.3f}")
            return True
        except Exception as e:
            self._log("error", f"Turbine action failed: {e}")
            return False
    
    def _apply_generic_action(self, action: Any) -> bool:
        """应用通用动作"""
        try:
            control_message = {
                'agent_id': self.agent_id,
                'device_type': self.device_type.value,
                'action_type': 'generic',
                'action': action,
                'timestamp': time.time()
            }
            
            self.publish_message(self.action_topic, control_message)
            self.last_control_action = action
            
            self._log("debug", f"Generic action: {action}")
            return True
        except Exception as e:
            self._log("error", f"Generic action failed: {e}")
            return False
    
    def _record_action(self, action: Any):
        """记录动作历史"""
        record = {
            'timestamp': time.time(),
            'action': action,
            'observation': self.current_observation
        }
        
        self.control_history.append(record)
        
        # 限制历史长度
        if len(self.control_history) > self.max_history_length:
            self.control_history.pop(0)
    
    def _update_control_metrics(self, response_time: float, success: bool):
        """更新控制指标"""
        self.control_metrics['total_actions'] += 1
        
        if success:
            self.control_metrics['successful_actions'] += 1
        else:
            self.control_metrics['failed_actions'] += 1
        
        # 更新平均响应时间
        total_time = self.control_metrics['average_response_time'] * (self.control_metrics['total_actions'] - 1)
        self.control_metrics['average_response_time'] = (total_time + response_time) / self.control_metrics['total_actions']
        
        self.control_metrics['last_action_time'] = time.time()

# 适配器：为旧类提供兼容性

class GateControlAgentAdapter(UnifiedLocalControlAgent):
    """GateControlAgent适配器"""
    
    def __init__(self, agent_id: str, message_bus, time_step: float, 
                 controller=None, observation_topic=None, observation_key='value',
                 action_topic=None, command_topic=None, feedback_topic=None, **kwargs):
        
        config = {
            'observation_topic': observation_topic,
            'observation_key': observation_key,
            'action_topic': action_topic,
            'command_topic': command_topic,
            'feedback_topic': feedback_topic,
            'controller_config': kwargs.get('controller_config', {}),
            **kwargs
        }
        
        # 推断控制策略
        if controller:
            if hasattr(controller, 'kp'):  # PID控制器
                strategy = ControlStrategy.PID
                config['controller_config'] = {
                    'kp': getattr(controller, 'kp', 1.0),
                    'ki': getattr(controller, 'ki', 0.0),
                    'kd': getattr(controller, 'kd', 0.0),
                    'setpoint': getattr(controller, 'setpoint', 0.0)
                }
            else:
                strategy = ControlStrategy.RULE_BASED
        else:
            strategy = ControlStrategy.RULE_BASED
        
        super().__init__(agent_id, DeviceType.GATE, strategy, config)
        
        import warnings
        warnings.warn(
            "GateControlAgent is deprecated. Use UnifiedLocalControlAgent with DeviceType.GATE instead.",
            DeprecationWarning,
            stacklevel=2
        )

class PumpControlAgentAdapter(UnifiedLocalControlAgent):
    """PumpControlAgent适配器"""
    
    def __init__(self, agent_id: str, **kwargs):
        config = kwargs
        strategy = ControlStrategy.PID if 'controller_config' in kwargs else ControlStrategy.RULE_BASED
        
        super().__init__(agent_id, DeviceType.PUMP, strategy, config)
        
        import warnings
        warnings.warn(
            "PumpControlAgent is deprecated. Use UnifiedLocalControlAgent with DeviceType.PUMP instead.",
            DeprecationWarning,
            stacklevel=2
        )

class ValveControlAgentAdapter(UnifiedLocalControlAgent):
    """ValveControlAgent适配器"""
    
    def __init__(self, agent_id: str, **kwargs):
        config = kwargs
        strategy = ControlStrategy.PID if 'controller_config' in kwargs else ControlStrategy.RULE_BASED
        
        super().__init__(agent_id, DeviceType.VALVE, strategy, config)
        
        import warnings
        warnings.warn(
            "ValveControlAgent is deprecated. Use UnifiedLocalControlAgent with DeviceType.VALVE instead.",
            DeprecationWarning,
            stacklevel=2
        )
