"""性能优化的扰动管理器

针对扰动框架的性能瓶颈进行优化：
1. 减少不必要的组件查找和状态检查
2. 使用缓存机制避免重复计算
3. 批量处理扰动更新
4. 优化内存使用
"""

import abc
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# 导入原有的扰动类型和配置
from .disturbance_framework import (
    DisturbanceType, DisturbanceConfig, BaseDisturbance,
    InflowDisturbance, SensorNoiseDisturbance, ActuatorFailureDisturbance
)

try:
    from .network_disturbance import NetworkDelayDisturbance, PacketLossDisturbance
    NETWORK_DISTURBANCES_AVAILABLE = True
except ImportError:
    NETWORK_DISTURBANCES_AVAILABLE = False
    logger.warning("网络扰动模块不可用，网络扰动功能将被禁用")


class PerformanceOptimizedDisturbanceManager:
    """性能优化的扰动管理器
    
    主要优化策略：
    1. 活跃扰动缓存：只处理当前时间窗口内的扰动
    2. 组件映射缓存：避免重复的组件查找
    3. 批量状态更新：减少单独的状态检查
    4. 延迟清理：避免频繁的内存分配/释放
    """
    
    def __init__(self, cache_size: int = 500, cleanup_interval: int = 50):
        # 基础存储
        self.disturbances: Dict[str, BaseDisturbance] = {}
        self.active_disturbances: Dict[str, BaseDisturbance] = {}
        
        # 性能优化缓存
        self._component_cache: Dict[str, Any] = {}  # 组件缓存
        self._time_window_cache: Dict[float, Set[str]] = {}  # 时间窗口缓存
        self._last_update_time: float = 0.0
        self._update_counter: int = 0
        self._last_cleanup_time: float = 0.0
        
        # 配置参数
        self.cache_size = cache_size
        self.cleanup_interval = cleanup_interval
        self.max_history_size = cache_size // 2  # 历史记录最大大小
        
        # 性能统计
        self.performance_stats = {
            'total_updates': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_update_time': 0.0,
            'active_disturbance_count': 0
        }
        
        self.disturbance_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.PerformanceOptimizedDisturbanceManager")
    
    def add_disturbance(self, disturbance: BaseDisturbance) -> None:
        """添加扰动"""
        disturbance_id = disturbance.config.disturbance_id
        self.disturbances[disturbance_id] = disturbance
        
        # 预计算时间窗口
        self._precompute_time_window(disturbance)
        
        self.logger.info(f"添加扰动: {disturbance_id}")
    
    def register_disturbance(self, disturbance: BaseDisturbance) -> None:
        """注册扰动到管理器（兼容性方法）"""
        self.add_disturbance(disturbance)
    
    def _precompute_time_window(self, disturbance: BaseDisturbance) -> None:
        """预计算扰动的时间窗口"""
        start_time = disturbance.config.start_time
        end_time = disturbance.config.end_time
        disturbance_id = disturbance.config.disturbance_id
        
        # 将扰动ID添加到相应的时间窗口
        if start_time not in self._time_window_cache:
            self._time_window_cache[start_time] = set()
        self._time_window_cache[start_time].add(disturbance_id)
    
    def remove_disturbance(self, disturbance_id: str) -> bool:
        """移除扰动"""
        if disturbance_id in self.disturbances:
            disturbance = self.disturbances[disturbance_id]
            
            # 如果扰动正在活跃，先停用它
            if disturbance_id in self.active_disturbances:
                component = self._get_cached_component(disturbance.config.target_component_id)
                if component:
                    disturbance.remove(component)
                del self.active_disturbances[disturbance_id]
            
            del self.disturbances[disturbance_id]
            
            # 清理时间窗口缓存
            self._cleanup_time_window_cache(disturbance_id)
            
            self.logger.info(f"移除扰动: {disturbance_id}")
            return True
        return False
    
    def _cleanup_time_window_cache(self, disturbance_id: str) -> None:
        """清理时间窗口缓存中的扰动ID"""
        for time_window in self._time_window_cache.values():
            time_window.discard(disturbance_id)
    
    def _get_cached_component(self, component_id: str) -> Optional[Any]:
        """获取缓存的组件"""
        if component_id in self._component_cache:
            self.performance_stats['cache_hits'] += 1
            return self._component_cache[component_id]
        
        self.performance_stats['cache_misses'] += 1
        return None
    
    def _update_component_cache(self, components: Dict[str, Any]) -> None:
        """更新组件缓存"""
        # 只缓存当前需要的组件
        needed_components = set()
        for disturbance in self.disturbances.values():
            needed_components.add(disturbance.config.target_component_id)
        
        # 清理不需要的缓存
        self._component_cache = {
            comp_id: comp for comp_id, comp in components.items() 
            if comp_id in needed_components
        }
    
    def update(self, current_time: float, time_step: float, components: Dict[str, Any]) -> Dict[str, Any]:
        """性能优化的扰动更新方法"""
        start_time = time.perf_counter()
        
        # 定期内存清理
        if current_time - self._last_cleanup_time > 10.0:  # 每10秒清理一次
            self._cleanup_memory()
            self._last_cleanup_time = current_time
        
        # 更新组件缓存（仅在需要时）
        if abs(current_time - self._last_update_time) > dt or not self._component_cache:
            self._update_component_cache(components)
        
        disturbance_effects = {}
        
        # 批量处理：获取当前时间窗口内需要检查的扰动
        candidate_disturbances = self._get_candidate_disturbances(current_time)
        
        # 批量状态检查和更新
        for disturbance_id in candidate_disturbances:
            if disturbance_id not in self.disturbances:
                continue
                
            disturbance = self.disturbances[disturbance_id]
            target_component_id = disturbance.config.target_component_id
            
            # 使用缓存获取组件
            component = self._get_cached_component(target_component_id)
            if not component:
                # 如果缓存中没有，从原始字典获取
                component = components.get(target_component_id)
                if component:
                    self._component_cache[target_component_id] = component
            
            if not component:
                continue
            
            # 检查是否应该激活扰动
            should_be_active = disturbance.should_be_active(current_time)
            is_currently_active = disturbance_id in self.active_disturbances
            
            if should_be_active and not is_currently_active:
                self.activate_disturbance(disturbance_id, component)
            elif not should_be_active and is_currently_active:
                self.deactivate_disturbance(disturbance_id, component)
            
            # 应用活跃的扰动
            if disturbance_id in self.active_disturbances:
                effect = disturbance.apply(component, current_time, dt)
                if effect:
                    disturbance_effects[disturbance_id] = effect
        
        # 记录扰动历史（采样记录以减少内存使用）
        if disturbance_effects and self._update_counter % 10 == 0:
            self.disturbance_history.append({
                'time': current_time,
                'effects': disturbance_effects.copy()
            })
            
            # 限制历史记录大小
            if len(self.disturbance_history) > self.cache_size:
                self.disturbance_history = self.disturbance_history[-self.cache_size//2:]
        
        # 定期清理缓存
        self._update_counter += 1
        if self._update_counter % self.cleanup_interval == 0:
            self._periodic_cleanup(current_time)
        
        # 更新性能统计
        update_time = time.perf_counter() - start_time
        self._update_performance_stats(update_time, len(disturbance_effects))
        
        self._last_update_time = current_time
        return disturbance_effects
    
    def _get_candidate_disturbances(self, current_time: float) -> Set[str]:
        """获取当前时间窗口内的候选扰动"""
        candidates = set()
        
        # 检查时间窗口缓存
        for time_point, disturbance_ids in self._time_window_cache.items():
            # 检查时间窗口（考虑扰动的持续时间）
            for disturbance_id in disturbance_ids:
                if disturbance_id in self.disturbances:
                    disturbance = self.disturbances[disturbance_id]
                    if (disturbance.config.start_time <= current_time <= 
                        disturbance.config.end_time + 1.0):  # 添加1秒缓冲
                        candidates.add(disturbance_id)
        
        # 总是包含当前活跃的扰动
        candidates.update(self.active_disturbances.keys())
        
        return candidates
    
    def _periodic_cleanup(self, current_time: float) -> None:
        """定期清理过期的缓存数据"""
        # 清理过期的时间窗口缓存
        expired_times = [
            time_point for time_point in self._time_window_cache.keys()
            if time_point < current_time - 100.0  # 保留最近100秒的缓存
        ]
        
        for expired_time in expired_times:
            del self._time_window_cache[expired_time]
        
        self.logger.debug(f"清理了 {len(expired_times)} 个过期时间窗口缓存")
    
    def _cleanup_memory(self) -> None:
        """内存清理方法"""
        # 清理过期的缓存
        if len(self._component_cache) > self.cache_size:
            # 保留最近使用的缓存项
            cache_items = list(self._component_cache.items())
            self._component_cache = dict(cache_items[-self.cache_size//2:])
        
        if len(self._time_window_cache) > self.cache_size:
            cache_items = list(self._time_window_cache.items())
            self._time_window_cache = dict(cache_items[-self.cache_size//2:])
        
        # 清理历史记录
        if len(self.disturbance_history) > self.max_history_size:
            self.disturbance_history = self.disturbance_history[-self.max_history_size//2:]
        
        # 更新性能统计中的内存优化计数
        if 'memory_optimizations' not in self.performance_stats:
            self.performance_stats['memory_optimizations'] = 0
        self.performance_stats['memory_optimizations'] += 1
    
    def _update_performance_stats(self, update_time: float, active_count: int) -> None:
        """更新性能统计"""
        self.performance_stats['total_updates'] += 1
        self.performance_stats['active_disturbance_count'] = active_count
        
        # 计算平均更新时间（指数移动平均）
        alpha = 0.1
        if self.performance_stats['avg_update_time'] == 0:
            self.performance_stats['avg_update_time'] = update_time
        else:
            self.performance_stats['avg_update_time'] = (
                alpha * update_time + 
                (1 - alpha) * self.performance_stats['avg_update_time']
            )
    
    def activate_disturbance(self, disturbance_id: str, component: Any) -> bool:
        """激活扰动"""
        if disturbance_id in self.disturbances and disturbance_id not in self.active_disturbances:
            disturbance = self.disturbances[disturbance_id]
            self.active_disturbances[disturbance_id] = disturbance
            
            self.logger.info(f"激活扰动: {disturbance_id} -> {disturbance.config.target_component_id}")
            return True
        return False
    
    def deactivate_disturbance(self, disturbance_id: str, component: Any) -> bool:
        """停用扰动"""
        if disturbance_id in self.active_disturbances:
            disturbance = self.active_disturbances[disturbance_id]
            disturbance.remove(component)
            del self.active_disturbances[disturbance_id]
            
            self.logger.info(f"停用扰动: {disturbance_id}")
            return True
        return False
    
    def get_active_disturbances(self) -> Dict[str, List[str]]:
        """获取活跃扰动列表"""
        physical_disturbances = list(self.active_disturbances.keys())
        return {
            'physical': physical_disturbances,
            'network': []  # 网络扰动由单独的管理器处理
        }
    
    def get_disturbance_status(self) -> Dict[str, Any]:
        """获取扰动状态"""
        return {
            'total_disturbances': len(self.disturbances),
            'active_disturbances': len(self.active_disturbances),
            'performance_stats': self.performance_stats.copy(),
            'cache_efficiency': (
                self.performance_stats['cache_hits'] / 
                max(1, self.performance_stats['cache_hits'] + self.performance_stats['cache_misses'])
            )
        }
    
    def get_disturbance_history(self) -> List[Dict[str, Any]]:
        """获取扰动历史记录"""
        return self.disturbance_history.copy()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'performance_stats': self.performance_stats.copy(),
            'cache_status': {
                'component_cache_size': len(self._component_cache),
                'time_window_cache_size': len(self._time_window_cache),
                'history_size': len(self.disturbance_history)
            },
            'optimization_recommendations': self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        # 检查缓存效率
        cache_efficiency = (
            self.performance_stats['cache_hits'] / 
            max(1, self.performance_stats['cache_hits'] + self.performance_stats['cache_misses'])
        )
        
        if cache_efficiency < 0.8:
            recommendations.append("考虑增加缓存大小以提高缓存命中率")
        
        # 检查更新时间
        if self.performance_stats['avg_update_time'] > 0.01:  # 10ms
            recommendations.append("扰动更新时间较长，考虑减少扰动数量或优化扰动逻辑")
        
        # 检查活跃扰动数量
        if self.performance_stats['active_disturbance_count'] > 50:
            recommendations.append("活跃扰动数量较多，考虑分批处理或使用更高效的数据结构")
        
        if not recommendations:
            recommendations.append("性能表现良好，无需特别优化")
        
        return recommendations