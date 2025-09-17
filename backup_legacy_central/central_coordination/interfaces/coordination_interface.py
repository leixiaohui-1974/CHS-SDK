"""
协调接口定义

定义中央协调相关的标准接口，包括状态聚合、决策分发等。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class CoordinationMode(Enum):
    """协调模式枚举"""
    CENTRALIZED = "centralized"    # 中心化
    DISTRIBUTED = "distributed"   # 分布式
    HIERARCHICAL = "hierarchical" # 分层式
    HYBRID = "hybrid"             # 混合式


class StateAggregatorInterface(ABC):
    """状态聚合器接口"""
    
    @abstractmethod
    def register_component(self, component_id: str, topic: str) -> bool:
        """
        注册组件状态监听
        
        Args:
            component_id: 组件ID
            topic: 状态主题
            
        Returns:
            bool: 注册是否成功
        """
        pass
        
    @abstractmethod
    def unregister_component(self, component_id: str) -> bool:
        """
        取消注册组件
        
        Args:
            component_id: 组件ID
            
        Returns:
            bool: 取消注册是否成功
        """
        pass
        
    @abstractmethod
    def get_global_state(self) -> Dict[str, Any]:
        """
        获取全局状态
        
        Returns:
            Dict[str, Any]: 全局状态字典
        """
        pass
        
    @abstractmethod
    def get_component_state(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定组件状态
        
        Args:
            component_id: 组件ID
            
        Returns:
            Optional[Dict[str, Any]]: 组件状态，如果不存在返回None
        """
        pass


class DecisionDispatcherInterface(ABC):
    """决策分发器接口"""
    
    @abstractmethod
    def register_target(self, target_id: str, topic: str) -> bool:
        """
        注册决策目标
        
        Args:
            target_id: 目标ID
            topic: 决策主题
            
        Returns:
            bool: 注册是否成功
        """
        pass
        
    @abstractmethod
    def dispatch_decision(self, decision: Dict[str, Any]) -> bool:
        """
        分发决策
        
        Args:
            decision: 决策内容
            
        Returns:
            bool: 分发是否成功
        """
        pass
        
    @abstractmethod
    def dispatch_to_target(self, target_id: str, decision: Dict[str, Any]) -> bool:
        """
        向特定目标分发决策
        
        Args:
            target_id: 目标ID
            decision: 决策内容
            
        Returns:
            bool: 分发是否成功
        """
        pass


class CoordinatorInterface(ABC):
    """协调器接口"""
    
    @abstractmethod
    def set_coordination_mode(self, mode: CoordinationMode) -> bool:
        """
        设置协调模式
        
        Args:
            mode: 协调模式
            
        Returns:
            bool: 设置是否成功
        """
        pass
        
    @abstractmethod
    def coordinate_agents(self, agent_list: List[str]) -> Dict[str, Any]:
        """
        协调智能体
        
        Args:
            agent_list: 智能体ID列表
            
        Returns:
            Dict[str, Any]: 协调结果
        """
        pass
        
    @abstractmethod
    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解决冲突
        
        Args:
            conflicts: 冲突列表
            
        Returns:
            List[Dict[str, Any]]: 解决方案列表
        """
        pass
        
    @abstractmethod
    def get_coordination_status(self) -> Dict[str, Any]:
        """
        获取协调状态
        
        Returns:
            Dict[str, Any]: 协调状态信息
        """
        pass