"""
统一闸门控制代理 - 基于统一架构

特点：
1. 继承 UnifiedLocalControlAgent
2. 使用 MULTI_ACTUATOR 控制策略
3. 集成闸门特定功能
4. 保持架构一致性
"""
from core_lib.core.interfaces import Controller
from core_lib.local_agents.control.unified_local_control_agent import UnifiedLocalControlAgent, ControlStrategy
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.identification.rls_estimator import RLSEstimator
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
import pandas as pd
from typing import Optional, Dict, Any

class UnifiedGateControlAgent(UnifiedLocalControlAgent):
    """
    统一闸门控制代理
    
    继承统一架构，添加闸门特定功能：
    - 实时参数识别
    - 多闸门流量分配
    - 数据清洗和预处理
    - RLS参数估计
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
        初始化统一闸门控制代理
        
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
            **kwargs: 闸门特定配置
        """
        # 调用父类构造函数，使用多执行器控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=dt,
            control_strategy=ControlStrategy.MULTI_ACTUATOR,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            command_topic=command_topic,
            feedback_topic=feedback_topic,
            controller=controller,
            **kwargs
        )
    
    def _initialize_device_specific(self, **kwargs):
        """闸门特定初始化"""
        # 闸门物理参数
        self.physical_object_name = kwargs.get('target_component', 'gate')
        self.control_variable = kwargs.get('control_variable', 'water_level')
        self.target_location = kwargs.get('target_location', 'upstream')
        
        # 增强功能初始化
        self._initialize_enhanced_features(**kwargs)
        
        # 闸门状态变量
        self.us_water_level = None
        self.ds_water_level = None
        self.gate_opening = None
        
        print(f"UnifiedGateControlAgent '{self.agent_id}' initialized with enhanced features")
    
    def _initialize_enhanced_features(self, **kwargs):
        """初始化增强功能"""
        # 1. 数据清洗器（预留）
        self.cleaner = None
        
        # 2. 实时识别（RLS估计器）
        identification_config = kwargs.get('identification_config')
        if identification_config:
            self.identifier = RLSEstimator(
                dim=1,
                forgetting_factor=identification_config.get('forgetting_factor', 0.98)
            )
            self.identified_discharge_coeff = kwargs.get('initial_discharge_coefficient', 0.6)
            self.bus.publish(
                f'agent.{self.agent_id}.identified_discharge_coefficient',
                self.identified_discharge_coefficient
            )
        else:
            self.identifier = None
        
        # 3. 多闸门流量分配策略
        allocation_table_path = kwargs.get('allocation_table_path')
        if allocation_table_path:
            self.allocation_table = pd.read_csv(allocation_table_path)
            self.number_of_gates = kwargs.get('number_of_gates', 1)
        else:
            self.allocation_table = None
    
    def preprocess_observation(self, message: Message) -> Message:
        """闸门特定观测预处理"""
        # 应用数据清洗
        if self.cleaner:
            # 未来实现数据清洗
            pass
        
        # 提取闸门特定数据
        if 'water_level' in message:
            if self.target_location == 'upstream':
                self.us_water_level = message['water_level']
            else:
                self.ds_water_level = message['water_level']
        
        if 'opening' in message:
            self.gate_opening = message['opening']
        
        return message
    
    def compute_multi_actuator_control_action(self, message: Message) -> Optional[Dict[str, Any]]:
        """计算多执行器控制动作"""
        # 获取过程变量 - 优先使用water_level，如果没有则使用process_variable
        process_variable = message.get('water_level') or message.get('process_variable')
        if process_variable is None:
            return None
        
        # 实时参数识别
        if self.identifier and self.us_water_level is not None and self.ds_water_level is not None:
            self._update_discharge_coefficient()
        
        # 计算基础PID控制动作
        if self.controller:
            observation_for_controller = {'process_variable': process_variable}
            base_control_signal = self.controller.compute_control_action(observation_for_controller, self.dt)
            print(f"[{self.agent_id}] PID input: {observation_for_controller}, output: {base_control_signal:.4f}")
        else:
            base_control_signal = 0.0
            print(f"[{self.agent_id}] No controller available, using 0.0")
        
        # 应用多闸门流量分配
        if self.allocation_table is not None:
            allocated_signals = self._apply_flow_allocation(base_control_signal)
            return allocated_signals
        else:
            # 单闸门控制
            return {self.action_topic: base_control_signal}
    
    def _update_discharge_coefficient(self):
        """使用RLS估计更新流量系数"""
        if self.identifier and self.gate_opening is not None:
            try:
                # 实际实现需要使用真实的流量测量数据
                # 这里只是示例框架
                pass
            except Exception as e:
                print(f"[{self.agent_id}] RLS estimation error: {e}")
    
    def _apply_flow_allocation(self, base_control_signal: float) -> Dict[str, float]:
        """应用多闸门流量分配策略"""
        if self.allocation_table is None:
            return {self.action_topic: base_control_signal}
        
        try:
            # 简化的流量分配逻辑
            # 实际实现会使用分配表
            allocated_signals = {}
            for i in range(self.number_of_gates):
                gate_topic = f"{self.action_topic}_gate_{i+1}"
                # 简单的平均分配
                allocated_signals[gate_topic] = base_control_signal / self.number_of_gates
            
            return allocated_signals
        except Exception as e:
            print(f"[{self.agent_id}] Flow allocation error: {e}")
            return {self.action_topic: base_control_signal}
