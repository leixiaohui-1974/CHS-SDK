"""
控制策略模块 - 统一管理各种控制策略

将分散的控制逻辑集中管理，提供统一的接口
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import math

class ControlStrategyType(Enum):
    """控制策略类型"""
    PID_CONTROL = "pid_control"
    ON_OFF_CONTROL = "on_off_control"
    OPTIMAL_CONTROL = "optimal_control"
    ADAPTIVE_CONTROL = "adaptive_control"

class ControlStrategy:
    """控制策略基类"""
    
    @abstractmethod
    def compute_control_action(self, observation: Dict[str, Any], 
                              target: float, **kwargs) -> Any:
        """计算控制动作"""
        pass

class PumpControlStrategy(ControlStrategy):
    """水泵控制策略"""
    
    def __init__(self, strategy_type: ControlStrategyType, **params):
        self.strategy_type = strategy_type
        self.params = params
        
    def compute_control_action(self, observation: Dict[str, Any], 
                              target: float, **kwargs) -> Dict[str, Any]:
        """计算水泵控制动作"""
        if self.strategy_type == ControlStrategyType.ON_OFF_CONTROL:
            return self._on_off_control(observation, target, **kwargs)
        elif self.strategy_type == ControlStrategyType.OPTIMAL_CONTROL:
            return self._optimal_control(observation, target, **kwargs)
        else:
            return self._default_control(observation, target, **kwargs)
    
    def _on_off_control(self, observation: Dict[str, Any], 
                       target: float, **kwargs) -> Dict[str, Any]:
        """开关控制策略"""
        current_flow = observation.get('current_flow', 0)
        pumps = kwargs.get('pumps', [])
        
        if current_flow < target * 0.9:  # 10%死区
            # 需要启动更多水泵
            num_pumps_needed = math.ceil(target / self.params.get('pump_capacity', 10))
            num_pumps_needed = min(num_pumps_needed, len(pumps))
        elif current_flow > target * 1.1:
            # 需要停止水泵
            num_pumps_needed = max(0, math.floor(target / self.params.get('pump_capacity', 10)))
        else:
            # 保持当前状态
            num_pumps_needed = kwargs.get('current_active_pumps', 0)
        
        # 生成控制信号
        control_signals = {}
        for i, pump in enumerate(pumps):
            control_signals[f"action.pump.{pump.name}"] = 1 if i < num_pumps_needed else 0
            
        return control_signals
    
    def _optimal_control(self, observation: Dict[str, Any], 
                         target: float, **kwargs) -> Dict[str, Any]:
        """最优控制策略"""
        # 实现最优控制逻辑
        pumps = kwargs.get('pumps', [])
        efficiency_data = kwargs.get('efficiency_data', {})
        
        # 简化的最优控制：选择效率最高的泵组合
        best_combination = self._find_best_pump_combination(target, pumps, efficiency_data)
        
        control_signals = {}
        for i, pump in enumerate(pumps):
            control_signals[f"action.pump.{pump.name}"] = 1 if i in best_combination else 0
            
        return control_signals
    
    def _find_best_pump_combination(self, target: float, pumps: List, 
                                   efficiency_data: Dict) -> List[int]:
        """寻找最佳泵组合"""
        # 简化实现：选择前几个泵
        num_pumps_needed = math.ceil(target / self.params.get('pump_capacity', 10))
        return list(range(min(num_pumps_needed, len(pumps))))
    
    def _default_control(self, observation: Dict[str, Any], 
                        target: float, **kwargs) -> Dict[str, Any]:
        """默认控制策略"""
        return self._on_off_control(observation, target, **kwargs)
