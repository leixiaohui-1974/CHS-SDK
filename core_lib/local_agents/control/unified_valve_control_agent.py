"""
统一阀门控制代理 - 基于统一架构

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

class UnifiedValveControlAgent(UnifiedLocalControlAgent):
    """
    统一阀门控制代理
    
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
        初始化统一阀门控制代理
        
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
        # 阀门物理参数
        self.valve_type = kwargs.get('valve_type', 'butterfly')  # butterfly, gate, globe, etc.
        self.valve_size = kwargs.get('valve_size', 100)  # mm
        self.max_flow_rate = kwargs.get('max_flow_rate', 10.0)  # m³/s
        self.min_flow_rate = kwargs.get('min_flow_rate', 0.0)  # m³/s
        
        # 控制参数
        self.position_feedback_enabled = kwargs.get('position_feedback_enabled', True)
        self.flow_characteristic = kwargs.get('flow_characteristic', 'linear')  # linear, equal_percentage, etc.
        
        # 阀门状态
        self.current_position = 0.0  # 0-100%
        self.current_flow_rate = 0.0
        
        print(f"Valve '{self.agent_id}' initialized: {self.valve_type}, size {self.valve_size}mm")
    
    def preprocess_observation(self, message: Message) -> Message:
        """阀门特定观测预处理"""
        # 提取流量信息
        if 'flow_rate' in message:
            self.current_flow_rate = message['flow_rate']
        
        # 提取位置反馈
        if self.position_feedback_enabled and 'position' in message:
            self.current_position = message['position']
        
        # 应用流量特性校正
        if 'process_variable' in message:
            corrected_value = self._apply_flow_characteristic(message['process_variable'])
            message['process_variable'] = corrected_value
        
        return message
    
    def _apply_flow_characteristic(self, flow_rate: float) -> float:
        """应用流量特性校正"""
        if self.flow_characteristic == 'linear':
            return flow_rate
        elif self.flow_characteristic == 'equal_percentage':
            # 等百分比特性：Cv = Cv_max * R^(x-1)
            # 其中 R 是范围度，x 是阀门开度
            rangeability = 50  # 典型值
            normalized_flow = flow_rate / self.max_flow_rate
            if normalized_flow > 0:
                corrected_flow = self.max_flow_rate * (rangeability ** (normalized_flow - 1))
                return corrected_flow
            else:
                return 0.0
        else:
            return flow_rate
    
    def handle_command_message(self, message: Message):
        """处理阀门特定命令"""
        command_type = message.get('command_type')
        
        if command_type == 'set_position':
            # 直接设置阀门位置
            target_position = message.get('position', 0.0)
            target_position = max(0.0, min(100.0, target_position))
            
            # 计算对应的控制信号
            control_signal = target_position / 100.0  # 转换为 0-1 范围
            
            self.publish_action(control_signal)
            print(f"[{self.agent_id}] Position set to: {target_position:.1f}%")
        
        elif command_type == 'set_flow_rate':
            # 设置目标流量
            target_flow = message.get('flow_rate', 0.0)
            target_flow = max(self.min_flow_rate, min(self.max_flow_rate, target_flow))
            
            # 更新控制器设定值
            if hasattr(self.controller, 'set_setpoint'):
                self.controller.set_setpoint(target_flow)
                print(f"[{self.agent_id}] Flow rate setpoint updated to: {target_flow:.2f} m³/s")
        
        elif command_type == 'emergency_close':
            # 紧急关闭阀门
            self.publish_action(0.0)  # 完全关闭
            print(f"[{self.agent_id}] Emergency close activated")
        
        elif command_type == 'calibrate':
            # 阀门校准
            self._calibrate_valve()
        
        else:
            # 调用父类方法处理标准命令
            super().handle_command_message(message)
    
    def _calibrate_valve(self):
        """阀门校准程序"""
        print(f"[{self.agent_id}] Starting valve calibration...")
        
        # 校准步骤：
        # 1. 完全关闭
        self.publish_action(0.0)
        print("Step 1: Valve closed")
        
        # 2. 完全打开
        self.publish_action(1.0)
        print("Step 2: Valve opened")
        
        # 3. 回到中间位置
        self.publish_action(0.5)
        print("Step 3: Valve at 50% position")
        
        print(f"[{self.agent_id}] Calibration completed")
    
    def get_valve_status(self) -> Dict[str, Any]:
        """获取阀门状态信息"""
        return {
            'valve_type': self.valve_type,
            'valve_size': self.valve_size,
            'current_position': self.current_position,
            'current_flow_rate': self.current_flow_rate,
            'max_flow_rate': self.max_flow_rate,
            'min_flow_rate': self.min_flow_rate,
            'position_feedback_enabled': self.position_feedback_enabled,
            'flow_characteristic': self.flow_characteristic
        }
