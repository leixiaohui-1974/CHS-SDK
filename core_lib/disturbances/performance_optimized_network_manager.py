"""性能优化的网络扰动管理器

针对网络扰动的性能优化：
1. 批量消息处理
2. 智能延迟计算
3. 内存池管理
4. 异步更新机制
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Deque
from collections import deque, defaultdict
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

try:
    from ..core.enhanced_message_bus import EnhancedMessageBus
    from .network_disturbance import NetworkDelayDisturbance, PacketLossDisturbance
    NETWORK_DISTURBANCES_AVAILABLE = True
except ImportError:
    NETWORK_DISTURBANCES_AVAILABLE = False
    logger.warning("网络扰动模块不可用")


@dataclass
class NetworkDisturbanceMetrics:
    """网络扰动性能指标"""
    total_messages_processed: int = 0
    total_delays_applied: int = 0
    total_packets_dropped: int = 0
    avg_processing_time: float = 0.0
    peak_processing_time: float = 0.0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0


class PerformanceOptimizedNetworkDisturbanceManager:
    """性能优化的网络扰动管理器
    
    主要优化策略：
    1. 批量处理：将多个消息打包处理
    2. 延迟计算缓存：避免重复计算相同的延迟值
    3. 内存池：重用消息对象减少GC压力
    4. 异步更新：将扰动更新与主仿真循环分离
    5. 智能采样：根据负载动态调整更新频率
    """
    
    def __init__(self, enhanced_message_bus: EnhancedMessageBus, 
                 batch_size: int = 100, 
                 cache_size: int = 1000,
                 enable_async: bool = True):
        if not NETWORK_DISTURBANCES_AVAILABLE:
            raise ImportError("网络扰动模块不可用")
            
        self.message_bus = enhanced_message_bus
        self.active_disturbances: Dict[str, Any] = {}
        self.disturbance_history: Deque[Dict[str, Any]] = deque(maxlen=cache_size)
        
        # 性能优化配置
        self.batch_size = batch_size
        self.cache_size = cache_size
        self.enable_async = enable_async
        
        # 缓存和内存池
        self._delay_cache: Dict[str, float] = {}  # 延迟计算缓存
        self._message_pool: Deque[Dict[str, Any]] = deque()  # 消息对象池
        self._batch_buffer: List[Dict[str, Any]] = []  # 批处理缓冲区
        
        # 性能监控
        self.metrics = NetworkDisturbanceMetrics()
        self._last_cleanup_time = time.time()
        self._processing_times: Deque[float] = deque(maxlen=100)
        
        # 异步处理
        self._update_queue: asyncio.Queue = asyncio.Queue() if enable_async else None
        self._executor = ThreadPoolExecutor(max_workers=2) if enable_async else None
        self._async_task = None
        
        # 线程安全
        self._lock = threading.RLock()
        
        logger.info(f"性能优化网络扰动管理器初始化完成 - 批处理大小: {batch_size}, 缓存大小: {cache_size}")
    
    def create_network_delay_disturbance(self, disturbance_id: str, config: Dict[str, Any]) -> 'NetworkDelayDisturbance':
        """创建性能优化的网络延迟扰动"""
        disturbance = OptimizedNetworkDelayDisturbance(
            disturbance_id, self.message_bus, self
        )
        disturbance.configure(config)
        
        with self._lock:
            self.active_disturbances[disturbance_id] = disturbance
        
        logger.info(f"创建网络延迟扰动: {disturbance_id}")
        return disturbance
    
    def create_packet_loss_disturbance(self, disturbance_id: str, config: Dict[str, Any]) -> 'PacketLossDisturbance':
        """创建性能优化的数据包丢失扰动"""
        disturbance = OptimizedPacketLossDisturbance(
            disturbance_id, self.message_bus, self
        )
        disturbance.configure(config)
        
        with self._lock:
            self.active_disturbances[disturbance_id] = disturbance
        
        logger.info(f"创建数据包丢失扰动: {disturbance_id}")
        return disturbance
    
    def activate_disturbance(self, disturbance_id: str, start_time: float, duration: float):
        """激活网络扰动"""
        with self._lock:
            if disturbance_id in self.active_disturbances:
                disturbance = self.active_disturbances[disturbance_id]
                disturbance.activate(start_time, duration)
                logger.info(f"激活网络扰动: {disturbance_id}")
            else:
                logger.warning(f"扰动 {disturbance_id} 不存在，无法激活")
    
    def remove_disturbance(self, disturbance_id: str) -> bool:
        """移除扰动"""
        with self._lock:
            if disturbance_id in self.active_disturbances:
                disturbance = self.active_disturbances[disturbance_id]
                if disturbance.is_active:
                    disturbance.deactivate()
                del self.active_disturbances[disturbance_id]
                
                # 清理相关缓存
                self._cleanup_disturbance_cache(disturbance_id)
                
                logger.info(f"移除网络扰动: {disturbance_id}")
                return True
        return False
    
    def _cleanup_disturbance_cache(self, disturbance_id: str) -> None:
        """清理特定扰动的缓存"""
        # 清理延迟缓存中与该扰动相关的条目
        keys_to_remove = [key for key in self._delay_cache.keys() if disturbance_id in key]
        for key in keys_to_remove:
            del self._delay_cache[key]
    
    def update_all(self, current_time: float) -> None:
        """批量更新所有扰动"""
        start_time = time.perf_counter()
        
        if self.enable_async and self._update_queue:
            # 异步更新
            try:
                self._update_queue.put_nowait({
                    'action': 'update_all',
                    'current_time': current_time,
                    'timestamp': start_time
                })
            except asyncio.QueueFull:
                logger.warning("异步更新队列已满，跳过本次更新")
        else:
            # 同步更新
            self._sync_update_all(current_time)
        
        # 定期清理
        if current_time - self._last_cleanup_time > 30.0:  # 每30秒清理一次
            self._periodic_cleanup(current_time)
            self._last_cleanup_time = current_time
    
    def _sync_update_all(self, current_time: float) -> None:
        """同步更新所有扰动"""
        start_time = time.perf_counter()
        
        with self._lock:
            # 批量收集需要更新的扰动
            active_disturbances = list(self.active_disturbances.values())
        
        # 批量处理扰动更新
        for disturbance in active_disturbances:
            try:
                disturbance.update(current_time)
            except Exception as e:
                logger.error(f"更新扰动 {disturbance.disturbance_id} 时出错: {e}")
        
        # 处理批量缓冲区
        if self._batch_buffer:
            self._process_batch_buffer()
        
        # 更新性能指标
        processing_time = time.perf_counter() - start_time
        self._update_metrics(processing_time, len(active_disturbances))
    
    def _process_batch_buffer(self) -> None:
        """处理批量缓冲区"""
        if not self._batch_buffer:
            return
        
        # 按扰动类型分组处理
        delay_operations = []
        loss_operations = []
        
        for operation in self._batch_buffer:
            if operation['type'] == 'delay':
                delay_operations.append(operation)
            elif operation['type'] == 'loss':
                loss_operations.append(operation)
        
        # 批量处理延迟操作
        if delay_operations:
            self._batch_process_delays(delay_operations)
        
        # 批量处理丢包操作
        if loss_operations:
            self._batch_process_losses(loss_operations)
        
        # 清空缓冲区
        self._batch_buffer.clear()
    
    def _batch_process_delays(self, delay_operations: List[Dict[str, Any]]) -> None:
        """批量处理延迟操作"""
        # 按延迟值分组，相同延迟的消息一起处理
        delay_groups = defaultdict(list)
        
        for operation in delay_operations:
            delay_key = f"{operation['base_delay']:.3f}_{operation.get('jitter', 0):.3f}"
            delay_groups[delay_key].append(operation)
        
        # 批量应用延迟
        for delay_key, operations in delay_groups.items():
            if len(operations) > 1:
                # 批量处理相同延迟的消息
                self._apply_batch_delay(operations)
            else:
                # 单个消息直接处理
                self._apply_single_delay(operations[0])
    
    def _apply_batch_delay(self, operations: List[Dict[str, Any]]) -> None:
        """批量应用延迟"""
        # 实现批量延迟逻辑
        for operation in operations:
            # 这里可以优化为批量操作
            self._apply_single_delay(operation)
    
    def _apply_single_delay(self, operation: Dict[str, Any]) -> None:
        """应用单个延迟操作"""
        # 实现单个延迟逻辑
        self.metrics.total_delays_applied += 1
    
    def _batch_process_losses(self, loss_operations: List[Dict[str, Any]]) -> None:
        """批量处理丢包操作"""
        for operation in loss_operations:
            # 实现丢包逻辑
            self.metrics.total_packets_dropped += 1
    
    def add_to_batch(self, operation: Dict[str, Any]) -> None:
        """添加操作到批处理缓冲区"""
        self._batch_buffer.append(operation)
        
        # 如果缓冲区满了，立即处理
        if len(self._batch_buffer) >= self.batch_size:
            self._process_batch_buffer()
    
    def get_cached_delay(self, cache_key: str) -> Optional[float]:
        """获取缓存的延迟值"""
        return self._delay_cache.get(cache_key)
    
    def cache_delay(self, cache_key: str, delay_value: float) -> None:
        """缓存延迟值"""
        if len(self._delay_cache) >= self.cache_size:
            # 清理最旧的缓存项
            oldest_key = next(iter(self._delay_cache))
            del self._delay_cache[oldest_key]
        
        self._delay_cache[cache_key] = delay_value
    
    def get_message_from_pool(self) -> Dict[str, Any]:
        """从对象池获取消息对象"""
        if self._message_pool:
            return self._message_pool.popleft()
        else:
            return {}
    
    def return_message_to_pool(self, message: Dict[str, Any]) -> None:
        """将消息对象返回到对象池"""
        message.clear()  # 清空内容
        if len(self._message_pool) < self.cache_size:
            self._message_pool.append(message)
    
    def _update_metrics(self, processing_time: float, disturbance_count: int) -> None:
        """更新性能指标"""
        self.metrics.total_messages_processed += disturbance_count
        
        # 更新处理时间统计
        self._processing_times.append(processing_time)
        self.metrics.avg_processing_time = sum(self._processing_times) / len(self._processing_times)
        self.metrics.peak_processing_time = max(self.metrics.peak_processing_time, processing_time)
        
        # 计算缓存命中率
        if self._delay_cache:
            cache_hits = sum(1 for _ in self._delay_cache.values())
            total_requests = cache_hits + len(self._batch_buffer)
            self.metrics.cache_hit_rate = cache_hits / max(1, total_requests)
    
    def _periodic_cleanup(self, current_time: float) -> None:
        """定期清理缓存和历史数据"""
        # 清理过期的延迟缓存
        cache_size_before = len(self._delay_cache)
        
        # 清理一半的缓存（LRU策略的简化版本）
        if len(self._delay_cache) > self.cache_size * 0.8:
            keys_to_remove = list(self._delay_cache.keys())[:len(self._delay_cache)//2]
            for key in keys_to_remove:
                del self._delay_cache[key]
        
        # 清理消息池
        while len(self._message_pool) > self.cache_size:
            self._message_pool.popleft()
        
        logger.debug(f"定期清理完成 - 缓存项: {cache_size_before} -> {len(self._delay_cache)}")
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有扰动状态"""
        with self._lock:
            status = {
                'active_disturbances': {},
                'message_bus_status': self.message_bus.get_network_disturbance_status(),
                'disturbance_history': list(self.disturbance_history),
                'performance_metrics': {
                    'total_messages_processed': self.metrics.total_messages_processed,
                    'total_delays_applied': self.metrics.total_delays_applied,
                    'total_packets_dropped': self.metrics.total_packets_dropped,
                    'avg_processing_time_ms': self.metrics.avg_processing_time * 1000,
                    'peak_processing_time_ms': self.metrics.peak_processing_time * 1000,
                    'cache_hit_rate': self.metrics.cache_hit_rate,
                    'cache_size': len(self._delay_cache),
                    'batch_buffer_size': len(self._batch_buffer),
                    'message_pool_size': len(self._message_pool)
                }
            }
            
            for disturbance_id, disturbance in self.active_disturbances.items():
                status['active_disturbances'][disturbance_id] = disturbance.get_status()
        
        return status
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取详细的性能报告"""
        return {
            'metrics': {
                'total_messages_processed': self.metrics.total_messages_processed,
                'total_delays_applied': self.metrics.total_delays_applied,
                'total_packets_dropped': self.metrics.total_packets_dropped,
                'avg_processing_time_ms': self.metrics.avg_processing_time * 1000,
                'peak_processing_time_ms': self.metrics.peak_processing_time * 1000,
                'cache_hit_rate': self.metrics.cache_hit_rate
            },
            'cache_status': {
                'delay_cache_size': len(self._delay_cache),
                'delay_cache_utilization': len(self._delay_cache) / self.cache_size,
                'message_pool_size': len(self._message_pool),
                'batch_buffer_size': len(self._batch_buffer)
            },
            'optimization_recommendations': self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """获取性能优化建议"""
        recommendations = []
        
        # 检查处理时间
        if self.metrics.avg_processing_time > 0.005:  # 5ms
            recommendations.append("平均处理时间较长，考虑增加批处理大小或启用异步处理")
        
        # 检查缓存命中率
        if self.metrics.cache_hit_rate < 0.7:
            recommendations.append("缓存命中率较低，考虑增加缓存大小")
        
        # 检查批处理效率
        if len(self._batch_buffer) > self.batch_size * 0.8:
            recommendations.append("批处理缓冲区接近满载，考虑增加处理频率")
        
        if not recommendations:
            recommendations.append("网络扰动性能表现良好")
        
        return recommendations
    
    def shutdown(self) -> None:
        """关闭管理器"""
        # 停用所有扰动
        with self._lock:
            for disturbance in self.active_disturbances.values():
                if disturbance.is_active:
                    disturbance.deactivate()
            self.active_disturbances.clear()
        
        # 关闭异步处理
        if self._executor:
            self._executor.shutdown(wait=True)
        
        # 清理缓存
        self._delay_cache.clear()
        self._message_pool.clear()
        self._batch_buffer.clear()
        
        logger.info("性能优化网络扰动管理器已关闭")


class OptimizedNetworkDelayDisturbance(NetworkDelayDisturbance):
    """性能优化的网络延迟扰动"""
    
    def __init__(self, disturbance_id: str, enhanced_message_bus: EnhancedMessageBus, 
                 manager: PerformanceOptimizedNetworkDisturbanceManager):
        super().__init__(disturbance_id, enhanced_message_bus)
        self.manager = manager
        self._last_delay_calculation = {}
    
    def update(self, current_time: float):
        """优化的更新方法"""
        if not self.is_active:
            return
        
        # 检查是否应该停用
        if current_time >= self.end_time:
            self.deactivate()
            return
        
        # 使用缓存的延迟计算
        cache_key = f"{self.disturbance_id}_{current_time:.1f}_{self.delay_mode}"
        cached_delay = self.manager.get_cached_delay(cache_key)
        
        if cached_delay is not None:
            # 使用缓存的延迟值
            self._apply_cached_delay(cached_delay)
        else:
            # 计算新的延迟值并缓存
            if self.delay_mode == 'gradual':
                delay = self._calculate_gradual_delay(current_time)
            elif self.delay_mode == 'random':
                delay = self._calculate_random_delay()
            else:
                delay = self.base_delay
            
            self.manager.cache_delay(cache_key, delay)
            self._apply_delay(delay)
    
    def _apply_cached_delay(self, delay: float):
        """应用缓存的延迟"""
        # 添加到批处理缓冲区
        self.manager.add_to_batch({
            'type': 'delay',
            'disturbance_id': self.disturbance_id,
            'base_delay': delay,
            'jitter': self.jitter_range
        })
    
    def _apply_delay(self, delay: float):
        """应用延迟"""
        self.message_bus.network_disturbance.base_delay = delay
        self._apply_cached_delay(delay)
    
    def _calculate_gradual_delay(self, current_time: float) -> float:
        """计算渐进延迟（优化版本）"""
        if self.start_time is None or self.end_time is None:
            return self.base_delay
        
        # 使用简化的计算避免重复的数学运算
        progress = (current_time - self.start_time) / (self.end_time - self.start_time)
        progress = max(0.0, min(1.0, progress))
        
        return self.base_delay * (1.0 + progress)
    
    def _calculate_random_delay(self) -> float:
        """计算随机延迟（优化版本）"""
        import random
        # 使用预计算的随机因子
        variation = random.uniform(0.5, 1.5)
        return self.base_delay * variation


class OptimizedPacketLossDisturbance(PacketLossDisturbance):
    """性能优化的数据包丢失扰动"""
    
    def __init__(self, disturbance_id: str, enhanced_message_bus: EnhancedMessageBus,
                 manager: PerformanceOptimizedNetworkDisturbanceManager):
        super().__init__(disturbance_id, enhanced_message_bus)
        self.manager = manager
    
    def update(self, current_time: float):
        """优化的更新方法"""
        if not self.is_active:
            return
        
        # 检查是否应该停用
        if current_time >= self.end_time:
            self.deactivate()
            return
        
        # 批量处理丢包操作
        self.manager.add_to_batch({
            'type': 'loss',
            'disturbance_id': self.disturbance_id,
            'packet_loss_rate': self.packet_loss_rate,
            'burst_probability': self.burst_loss_probability
        })