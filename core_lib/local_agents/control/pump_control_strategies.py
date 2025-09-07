"""
水泵控制策略模块 - 统一管理各种控制策略

遵循单一职责原则，每个策略类只负责一种控制算法
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import math

class ControlStrategyType(Enum):
    """控制策略类型"""
    OPTIMAL = "optimal"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    EFFICIENCY_BASED = "efficiency_based"

class PumpControlStrategy:
    """水泵控制策略基类 - 单一职责：计算控制动作"""
    
    @abstractmethod
    def compute_control_action(self, demand: float, pumps_info: List[Dict], 
                              current_status: Dict) -> Dict[str, Any]:
        """计算控制动作"""
        pass

class OptimalControlStrategy(PumpControlStrategy):
    """最优控制策略 - 基于效率优化"""
    
    def compute_control_action(self, demand: float, pumps_info: List[Dict], 
                              current_status: Dict) -> Dict[str, Any]:
        """计算最优控制动作"""
        n_pumps = len(pumps_info)
        best_combination = {}
        best_efficiency = 0.0
        best_flow_error = float('inf')
        
        # 尝试所有可能的泵组合
        for i in range(1, 2**n_pumps):
            combination = {}
            total_max_flow = 0
            
            for j in range(n_pumps):
                if i & (1 << j):
                    combination[j] = 1.0
                    total_max_flow += pumps_info[j]['max_flow']
            
            # 只考虑能够满足需求的组合
            if total_max_flow >= demand:
                # 计算流量误差
                flow_error = abs(total_max_flow - demand)
                
                # 优先选择流量误差小的组合
                if flow_error <= best_flow_error:
                    efficiency = self._calculate_combination_efficiency(combination, demand, pumps_info)
                    
                    # 如果流量误差相同，选择效率更高的
                    if flow_error < best_flow_error or (flow_error == best_flow_error and efficiency > best_efficiency):
                        best_efficiency = efficiency
                        best_combination = combination
                        best_flow_error = flow_error
        return {
            'strategy': 'optimal',
            'pump_commands': best_combination,
            'expected_efficiency': best_efficiency,
            'flow_error': best_flow_error
        }
    
    def _calculate_combination_efficiency(self, combination: Dict[int, float], 
                                         demand: float, pumps_info: List[Dict]) -> float:
        """计算组合效率"""
        total_power = 0
        total_flow = 0
        
        for pump_idx, speed in combination.items():
            pump_info = pumps_info[pump_idx]
            flow = pump_info['max_flow'] * speed
            power = pump_info['rated_power'] * speed**3
            total_power += power
            total_flow += flow
            
        if total_power > 0:
            return (demand * 9.81 * 20) / (total_power * 1000)
        return 0.0

class SequentialControlStrategy(PumpControlStrategy):
    """顺序控制策略 - 按顺序启停泵"""
    
    def compute_control_action(self, demand: float, pumps_info: List[Dict], 
                              current_status: Dict) -> Dict[str, Any]:
        """计算顺序控制动作"""
        current_flow = current_status.get('total_flow', 0)
        running_pumps = current_status.get('running_pumps', [])
        
        combination = {}
        
        if current_flow < demand * 0.9:  # 需要更多流量
            # 启动更多泵
            needed_pumps = min(len(pumps_info), 
                             math.ceil(demand / pumps_info[0]['max_flow']) if pumps_info else 0)
            for i in range(needed_pumps):
                combination[i] = 1.0
        elif current_flow > demand * 1.1:  # 流量过多
            # 停止部分泵
            needed_pumps = max(0, math.floor(demand / pumps_info[0]['max_flow']) if pumps_info else 0)
            for i in range(needed_pumps):
                combination[i] = 1.0
        else:
            # 保持当前状态
            for i in running_pumps:
                combination[i] = 1.0
                
        return {
            'strategy': 'sequential',
            'pump_commands': combination,
            'expected_efficiency': 0.0
        }

class ParallelControlStrategy(PumpControlStrategy):
    """并联控制策略 - 所有泵以相同速度运行"""
    
    def compute_control_action(self, demand: float, pumps_info: List[Dict], 
                              current_status: Dict) -> Dict[str, Any]:
        """计算并联控制动作"""
        total_max_flow = sum(pump['max_flow'] for pump in pumps_info)
        target_speed = min(1.0, demand / total_max_flow) if total_max_flow > 0 else 0
        
        combination = {}
        for i in range(len(pumps_info)):
            combination[i] = target_speed
            
        return {
            'strategy': 'parallel',
            'pump_commands': combination,
            'expected_efficiency': 0.0
        }

class EfficiencyBasedControlStrategy(PumpControlStrategy):
    """基于效率的控制策略"""
    
    def compute_control_action(self, demand: float, pumps_info: List[Dict], 
                              current_status: Dict) -> Dict[str, Any]:
        """计算基于效率的控制动作"""
        # 选择效率最高的泵组合
        best_combination = self._find_most_efficient_combination(demand, pumps_info)
        
        return {
            'strategy': 'efficiency_based',
            'pump_commands': best_combination,
            'expected_efficiency': 0.0
        }
    
    def _find_most_efficient_combination(self, demand: float, pumps_info: List[Dict]) -> Dict[int, float]:
        """寻找最高效的泵组合"""
        # 简化实现：选择前几个效率最高的泵
        sorted_pumps = sorted(enumerate(pumps_info), 
                            key=lambda x: x[1].get('efficiency', 0.8), reverse=True)
        
        combination = {}
        total_flow = 0
        
        for pump_idx, pump_info in sorted_pumps:
            if total_flow < demand:
                combination[pump_idx] = 1.0
                total_flow += pump_info['max_flow']
            else:
                break
                
        return combination
