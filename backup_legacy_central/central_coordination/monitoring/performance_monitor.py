"""
性能监控器
为中央智能体系统提供性能监控功能
"""
import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics


@dataclass
class PerformanceMetrics:
    """性能指标"""
    agent_id: str
    message_count: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    max_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    error_count: int = 0
    last_activity: Optional[float] = None
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._lock = threading.RLock()
        self._start_time = time.time()
    
    def record_message_processing(self, agent_id: str, processing_time: float, success: bool = True):
        """
        记录消息处理性能
        
        Args:
            agent_id: 智能体ID
            processing_time: 处理时间
            success: 是否成功
        """
        with self._lock:
            if agent_id not in self._metrics:
                self._metrics[agent_id] = PerformanceMetrics(agent_id=agent_id)
            
            metrics = self._metrics[agent_id]
            metrics.message_count += 1
            metrics.total_processing_time += processing_time
            metrics.last_activity = time.time()
            metrics.recent_times.append(processing_time)
            
            if success:
                metrics.average_processing_time = metrics.total_processing_time / metrics.message_count
                metrics.max_processing_time = max(metrics.max_processing_time, processing_time)
                metrics.min_processing_time = min(metrics.min_processing_time, processing_time)
            else:
                metrics.error_count += 1
    
    def get_agent_metrics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体性能指标"""
        with self._lock:
            if agent_id not in self._metrics:
                return None
            
            metrics = self._metrics[agent_id]
            recent_avg = statistics.mean(metrics.recent_times) if metrics.recent_times else 0.0
            
            return {
                'agent_id': agent_id,
                'message_count': metrics.message_count,
                'total_processing_time': metrics.total_processing_time,
                'average_processing_time': metrics.average_processing_time,
                'recent_average_time': recent_avg,
                'max_processing_time': metrics.max_processing_time,
                'min_processing_time': metrics.min_processing_time if metrics.min_processing_time != float('inf') else 0.0,
                'error_count': metrics.error_count,
                'error_rate': metrics.error_count / metrics.message_count if metrics.message_count > 0 else 0.0,
                'last_activity': metrics.last_activity,
                'uptime': time.time() - self._start_time
            }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """获取系统性能概览"""
        with self._lock:
            total_messages = sum(m.message_count for m in self._metrics.values())
            total_errors = sum(m.error_count for m in self._metrics.values())
            active_agents = len([m for m in self._metrics.values() if m.last_activity and (time.time() - m.last_activity) < 300])
            
            return {
                'total_agents': len(self._metrics),
                'active_agents': active_agents,
                'total_messages': total_messages,
                'total_errors': total_errors,
                'system_error_rate': total_errors / total_messages if total_messages > 0 else 0.0,
                'uptime': time.time() - self._start_time
            }
    
    def reset_metrics(self, agent_id: Optional[str] = None):
        """重置性能指标"""
        with self._lock:
            if agent_id:
                if agent_id in self._metrics:
                    del self._metrics[agent_id]
            else:
                self._metrics.clear()
                self._start_time = time.time()


# 全局性能监控实例
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    return _global_monitor
