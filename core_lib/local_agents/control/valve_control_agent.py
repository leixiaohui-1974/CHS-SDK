"""
阀门控制代理 - 基于统一架构

特点：
1. 继承 UnifiedLocalControlAgent
2. 使用 CONTINUOUS 控制策略
3. 集成阀门特定功能
4. 保持架构一致性
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Dict, Any
import math

class ValveControlAgent(UnifiedLocalControlAgent):
    """
    阀门控制代理
    
    继承统一架构，添加阀门特定功能：
    - 连续比例控制
    - 流量特性处理
    - 阀门位置反馈
    - 控制模式切换
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
        初始化阀门控制代理
        
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
            **kwargs: 阀门特定配置
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
        """阀门特定初始化"""
        # 阀门类型配置
        self.valve_type = kwargs.get('valve_type', 'butterfly')
        self.flow_characteristic = kwargs.get('flow_characteristic', 'linear')
        
        # 阀门操作参数
        self.min_opening = kwargs.get('min_opening', 0.0)
        self.max_opening = kwargs.get('max_opening', 100.0)
        self.max_opening_rate = kwargs.get('max_opening_rate', 10.0)  # %/s
        
        # 控制模式
        self.control_mode = kwargs.get('control_mode', 'automatic')  # automatic, manual, maintenance
        
        # 阀门状态
        self.current_opening = kwargs.get('initial_opening', 0.0)
        self.target_opening = self.current_opening
        self.valve_status = 'normal'  # normal, fault, maintenance
        
        print(f"[{self.agent_id}] Valve initialized: type={self.valve_type}, "
              f"characteristic={self.flow_characteristic}, opening={self.current_opening:.1f}%")
    
    def _handle_continuous_control(self, message: Message):
        """处理连续控制（重写父类方法）"""
        if self.control_mode != 'automatic':
            print(f"[{self.agent_id}] Control disabled: mode={self.control_mode}")
            return
        
        if not self.controller:
            print(f"[{self.agent_id}] Warning: No controller available")
            return
        
        # 提取过程变量
        process_variable = message.get(self.observation_key)
        if process_variable is None:
            print(f"[{self.agent_id}] Warning: Process variable '{self.observation_key}' not found")
            return
        
        # 计算控制动作
        observation_for_controller = {'process_variable': process_variable}
        raw_control_signal = self.controller.compute_control_action(observation_for_controller, self.time_step)
        
        # 应用阀门特性转换
        valve_opening = self._apply_valve_characteristics(raw_control_signal)
        
        # 应用操作约束
        constrained_opening = self._apply_opening_constraints(valve_opening)
        
        # 更新阀门状态
        self.target_opening = constrained_opening
        
        # 发布控制动作
        self.publish_action(constrained_opening)
        
        print(f"[{self.agent_id}] Valve control: {process_variable:.4f} -> "
              f"raw={raw_control_signal:.2f}, opening={constrained_opening:.1f}%")
    
    def _apply_valve_characteristics(self, control_signal: float) -> float:
        """应用阀门流量特性"""
        # 将控制信号转换为阀门开度百分比
        if self.flow_characteristic == 'linear':
            # 线性特性：流量与开度成正比
            opening_percent = control_signal * 100.0
        elif self.flow_characteristic == 'equal_percentage':
            # 等百分比特性：对数关系
            if control_signal > 0:
                opening_percent = 100.0 * (math.exp(control_signal) - 1) / (math.e - 1)
            else:
                opening_percent = 0.0
        elif self.flow_characteristic == 'quick_opening':
            # 快开特性：平方根关系
            opening_percent = 100.0 * math.sqrt(max(0, control_signal))
        else:
            # 默认线性特性
            opening_percent = control_signal * 100.0
        
        return opening_percent
    
    def _apply_opening_constraints(self, target_opening: float) -> float:
        """应用开度约束"""
        # 限制开度范围
        constrained_opening = max(self.min_opening, min(self.max_opening, target_opening))
        
        # 限制开度变化速率
        if hasattr(self, 'current_opening'):
            max_change = self.max_opening_rate * self.time_step
            opening_change = constrained_opening - self.current_opening
            
            if abs(opening_change) > max_change:
                if opening_change > 0:
                    constrained_opening = self.current_opening + max_change
                else:
                    constrained_opening = self.current_opening - max_change
        
        # 更新当前开度
        self.current_opening = constrained_opening
        
        return constrained_opening
    
    def handle_command_message(self, message: Message):
        """处理命令消息（重写父类方法）"""
        # 处理控制器设定值更新
        super().handle_command_message(message)
        
        # 处理阀门特定命令
        command_type = message.get('command_type')
        
        if command_type == 'set_control_mode':
            new_mode = message.get('control_mode', 'automatic')
            self.control_mode = new_mode
            print(f"[{self.agent_id}] Control mode changed to: {new_mode}")
        
        elif command_type == 'set_manual_opening':
            if self.control_mode == 'manual':
                manual_opening = message.get('opening', self.current_opening)
                constrained_opening = self._apply_opening_constraints(manual_opening)
                self.publish_action(constrained_opening)
                print(f"[{self.agent_id}] Manual opening set to: {constrained_opening:.1f}%")
        
        elif command_type == 'emergency_close':
            self.control_mode = 'manual'
            self.publish_action(self.min_opening)
            self.valve_status = 'emergency'
            print(f"[{self.agent_id}] Emergency close activated")
        
        elif command_type == 'reset_valve':
            self.valve_status = 'normal'
            self.control_mode = 'automatic'
            print(f"[{self.agent_id}] Valve reset to normal operation")
    
    def publish_action(self, opening_percent: float):
        """发布阀门开度控制动作"""
        action_message = {
            'control_signal': opening_percent,
            'agent_id': self.agent_id,
            'valve_type': self.valve_type,
            'control_mode': self.control_mode,
            'valve_status': self.valve_status,
            'timestamp': self.bus.get_current_time() if hasattr(self.bus, 'get_current_time') else 0
        }
        
        self.bus.publish(self.action_topic, action_message)
        print(f"[{self.agent_id}] Published valve opening: {opening_percent:.1f}%")
    
    def get_valve_status(self) -> Dict[str, Any]:
        """获取阀门状态信息"""
        return {
            'agent_id': self.agent_id,
            'valve_type': self.valve_type,
            'flow_characteristic': self.flow_characteristic,
            'control_mode': self.control_mode,
            'valve_status': self.valve_status,
            'current_opening': self.current_opening,
            'target_opening': self.target_opening,
            'min_opening': self.min_opening,
            'max_opening': self.max_opening,
            'max_opening_rate': self.max_opening_rate
        }