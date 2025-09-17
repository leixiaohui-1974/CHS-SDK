"""
闸门控制代理 - 基于统一架构

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
from scipy.interpolate import griddata
from typing import Optional, Dict, Any
import numpy as np

class GateControlAgent(UnifiedLocalControlAgent):
    """
    闸门控制代理
    
    继承统一架构，添加闸门特定功能：
    - PID控制与实时参数识别
    - 多闸门流量分配
    - 数据清洗和预处理
    - RLS实时参数估计
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
                 identification_config: Optional[Dict[str, Any]] = None,
                 allocation_table_path: Optional[str] = None,
                 **kwargs):
        """
        初始化闸门控制代理
        
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
            identification_config: 参数识别配置
            allocation_table_path: 分配表路径
            **kwargs: 闸门特定配置
        """
        # 调用父类构造函数，使用多执行器控制策略
        super().__init__(
            agent_id=agent_id,
            message_bus=message_bus,
            time_step=time_step,
            control_strategy=ControlStrategy.MULTI_ACTUATOR,
            observation_topic=observation_topic,
            observation_key=observation_key,
            action_topic=action_topic,
            command_topic=command_topic,
            feedback_topic=feedback_topic,
            controller=controller,
            identification_config=identification_config,
            allocation_table_path=allocation_table_path,
            **kwargs
        )
    
    def _initialize_device_specific(self, **kwargs):
        """闸门特定初始化"""
        # 参数识别配置
        identification_config = kwargs.get('identification_config') or {}
        if identification_config.get('enable_identification', False):
            forgetting_factor = identification_config.get('forgetting_factor', 0.98)
            self.identifier = RLSEstimator(forgetting_factor=forgetting_factor)
            self.identification_enabled = True
            print(f"[{self.agent_id}] RLS parameter identification enabled (λ={forgetting_factor})")
        else:
            self.identifier = None
            self.identification_enabled = False
        
        # 流量分配表
        allocation_table_path = kwargs.get('allocation_table_path')
        if allocation_table_path:
            try:
                self.allocation_table = pd.read_csv(allocation_table_path)
                print(f"[{self.agent_id}] Loaded allocation table from {allocation_table_path}")
            except Exception as e:
                print(f"[{self.agent_id}] Warning: Could not load allocation table: {e}")
                self.allocation_table = None
        else:
            self.allocation_table = None
        
        # 数据清洗配置
        self.data_cleaning_enabled = kwargs.get('enable_data_cleaning', True)
        self.outlier_threshold = kwargs.get('outlier_threshold', 3.0)  # 3-sigma规则
        
        # 历史数据缓存
        self.observation_history = []
        self.control_history = []
        self.max_history_length = kwargs.get('max_history_length', 100)
        
        print(f"[{self.agent_id}] Gate control agent initialized with advanced features")
    
    def preprocess_observation(self, message: Message) -> Message:
        """预处理观测消息"""
        if not self.data_cleaning_enabled:
            return message
        
        # 数据清洗
        cleaned_message = self._clean_observation_data(message)
        
        # 缓存历史数据
        self.observation_history.append(cleaned_message.get(self.observation_key, 0))
        if len(self.observation_history) > self.max_history_length:
            self.observation_history.pop(0)
        
        return cleaned_message
    
    def _clean_observation_data(self, message: Message) -> Message:
        """清洗观测数据"""
        observation_value = message.get(self.observation_key)
        if observation_value is None:
            return message
        
        # 异常值检测（3-sigma规则）
        if len(self.observation_history) >= 10:
            history_array = np.array(self.observation_history[-10:])
            mean_val = np.mean(history_array)
            std_val = np.std(history_array)
            
            if abs(observation_value - mean_val) > self.outlier_threshold * std_val:
                # 使用历史平均值替代异常值
                cleaned_value = mean_val
                print(f"[{self.agent_id}] Outlier detected: {observation_value:.4f} -> {cleaned_value:.4f}")
                message = dict(message)
                message[self.observation_key] = cleaned_value
        
        return message
    
    def compute_multi_actuator_control_action(self, message: Message) -> Optional[Dict[str, Any]]:
        """计算多执行器控制动作"""
        if not self.controller:
            return None
        
        # 提取过程变量
        process_variable = message.get(self.observation_key)
        if process_variable is None:
            return None
        
        # 计算基础控制信号
        observation_for_controller = {'process_variable': process_variable}
        base_control_signal = self.controller.compute_control_action(observation_for_controller, self.time_step)
        
        # 参数识别
        if self.identification_enabled and self.identifier:
            self._update_parameter_identification(process_variable, base_control_signal)
        
        # 流量分配
        control_signals = self._allocate_flow_to_gates(base_control_signal)
        
        # 缓存控制历史
        self.control_history.append(base_control_signal)
        if len(self.control_history) > self.max_history_length:
            self.control_history.pop(0)
        
        return control_signals
    
    def _update_parameter_identification(self, process_variable: float, control_signal: float):
        """更新参数识别"""
        try:
            # 构造回归向量（简化示例）
            regressor = np.array([control_signal, process_variable])
            output = process_variable  # 简化：使用当前过程变量作为输出
            
            # RLS更新
            self.identifier.update(regressor, output)
            
            # 获取识别参数
            if hasattr(self.identifier, 'get_parameters'):
                identified_params = self.identifier.get_parameters()
                print(f"[{self.agent_id}] Identified parameters: {identified_params}")
        except Exception as e:
            print(f"[{self.agent_id}] Parameter identification error: {e}")
    
    def _allocate_flow_to_gates(self, total_control_signal: float) -> Dict[str, Any]:
        """将总控制信号分配到多个闸门"""
        if not self.allocation_table is not None:
            # 使用分配表进行插值分配
            return self._interpolate_allocation(total_control_signal)
        else:
            # 默认均匀分配
            return self._uniform_allocation(total_control_signal)
    
    def _interpolate_allocation(self, total_signal: float) -> Dict[str, Any]:
        """基于分配表的插值分配"""
        try:
            # 假设分配表有列：total_flow, gate_1, gate_2, ...
            total_flows = self.allocation_table['total_flow'].values
            gate_columns = [col for col in self.allocation_table.columns if col.startswith('gate_')]
            
            control_signals = {}
            for gate_col in gate_columns:
                gate_values = self.allocation_table[gate_col].values
                interpolated_value = np.interp(total_signal, total_flows, gate_values)
                control_signals[f"gate_control.{gate_col}"] = float(interpolated_value)
            
            return control_signals
        except Exception as e:
            print(f"[{self.agent_id}] Interpolation allocation error: {e}")
            return self._uniform_allocation(total_signal)
    
    def _uniform_allocation(self, total_signal: float) -> Dict[str, Any]:
        """均匀分配控制信号"""
        # 默认分配到主动作主题
        return {self.action_topic: total_signal}
    
    def get_identification_status(self) -> Dict[str, Any]:
        """获取参数识别状态"""
        if not self.identification_enabled or not self.identifier:
            return {'enabled': False}
        
        status = {
            'enabled': True,
            'parameters': self.identifier.get_parameters() if hasattr(self.identifier, 'get_parameters') else None,
            'covariance': self.identifier.get_covariance() if hasattr(self.identifier, 'get_covariance') else None
        }
        return status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if len(self.observation_history) < 2 or len(self.control_history) < 2:
            return {}
        
        # 计算基础统计指标
        obs_array = np.array(self.observation_history)
        ctrl_array = np.array(self.control_history)
        
        metrics = {
            'observation_mean': float(np.mean(obs_array)),
            'observation_std': float(np.std(obs_array)),
            'control_mean': float(np.mean(ctrl_array)),
            'control_std': float(np.std(ctrl_array)),
            'history_length': len(self.observation_history)
        }
        
        return metrics