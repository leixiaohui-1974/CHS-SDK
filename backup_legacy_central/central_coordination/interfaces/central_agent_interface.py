"""
中央智能体接口定义

定义所有中央智能体必须实现的标准接口，确保一致性和可扩展性。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core_lib.core.interfaces import Agent


class CentralAgentInterface(Agent, ABC):
    """
    中央智能体基础接口
    
    所有中央智能体都应该继承此接口，确保：
    1. 统一的初始化方式
    2. 标准的配置管理
    3. 一致的生命周期管理
    4. 规范的状态报告
    """
    
    def __init__(self, agent_id: str, message_bus, **config):
        """
        初始化中央智能体
        
        Args:
            agent_id: 智能体唯一标识
            message_bus: 消息总线实例
            **config: 配置参数
        """
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.config = config
        self.is_active = False
        self.status = "initialized"
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化智能体
        
        Returns:
            bool: 初始化是否成功
        """
        pass
        
    @abstractmethod
    def start(self) -> bool:
        """
        启动智能体
        
        Returns:
            bool: 启动是否成功
        """
        pass
        
    @abstractmethod
    def stop(self) -> bool:
        """
        停止智能体
        
        Returns:
            bool: 停止是否成功
        """
        pass
        
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Returns:
            Dict[str, Any]: 包含状态信息的字典
        """
        pass
        
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """
        获取性能指标
        
        Returns:
            Dict[str, float]: 性能指标字典
        """
        pass
        
    @abstractmethod
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            new_config: 新的配置参数
            
        Returns:
            bool: 更新是否成功
        """
        pass
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置参数
        
        Args:
            config: 待验证的配置
            
        Returns:
            bool: 配置是否有效
        """
        # 基础验证，子类可以重写
        return isinstance(config, dict)


class ControlAgentInterface(CentralAgentInterface):
    """控制类中央智能体接口"""
    
    @abstractmethod
    def compute_control_actions(self, current_time: float) -> Dict[str, Any]:
        """
        计算控制动作
        
        Args:
            current_time: 当前时间
            
        Returns:
            Dict[str, Any]: 控制动作字典
        """
        pass
        
    @abstractmethod
    def get_control_targets(self) -> List[str]:
        """
        获取控制目标列表
        
        Returns:
            List[str]: 控制目标组件ID列表
        """
        pass


class PerceptionAgentInterface(CentralAgentInterface):
    """感知类中央智能体接口"""
    
    @abstractmethod
    def aggregate_states(self) -> Dict[str, Any]:
        """
        聚合状态信息
        
        Returns:
            Dict[str, Any]: 聚合后的状态信息
        """
        pass
        
    @abstractmethod
    def get_monitored_components(self) -> List[str]:
        """
        获取监控组件列表
        
        Returns:
            List[str]: 监控组件ID列表
        """
        pass


class DecisionAgentInterface(CentralAgentInterface):
    """决策类中央智能体接口"""
    
    @abstractmethod
    def make_decision(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        做出决策
        
        Args:
            input_data: 输入数据
            
        Returns:
            Dict[str, Any]: 决策结果
        """
        pass
        
    @abstractmethod
    def get_decision_criteria(self) -> Dict[str, Any]:
        """
        获取决策标准
        
        Returns:
            Dict[str, Any]: 决策标准
        """
        pass


class ForecastingAgentInterface(CentralAgentInterface):
    """预测类中央智能体接口"""
    
    @abstractmethod
    def generate_forecast(self, horizon: int) -> Dict[str, List[float]]:
        """
        生成预测
        
        Args:
            horizon: 预测时域
            
        Returns:
            Dict[str, List[float]]: 预测结果
        """
        pass
        
    @abstractmethod
    def get_forecast_accuracy(self) -> Dict[str, float]:
        """
        获取预测精度
        
        Returns:
            Dict[str, float]: 各项预测的精度指标
        """
        pass