"""
轻量级事件总线实现

设计特点：
1. 简单的发布订阅模式
2. 线程安全
3. 支持通配符订阅
4. 内置指标收集
"""
import threading
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
import fnmatch
import time
from dataclasses import dataclass
from core_lib.core.new_interfaces import EventBus, Message

@dataclass
class BusMetrics:
    """事件总线指标"""
    total_messages: int = 0
    total_subscriptions: int = 0
    active_topics: int = 0
    last_message_time: Optional[float] = None
    
class SimpleEventBus(EventBus):
    """简单事件总线实现"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = defaultdict(list)
        self._lock = threading.RLock()
        self._metrics = BusMetrics()
        
    def subscribe(self, topic: str, handler: Callable[[Message], None]):
        """订阅主题"""
        with self._lock:
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)
                self._metrics.total_subscriptions += 1
                self._metrics.active_topics = len(self._subscribers)
                print(f"[EventBus] Subscribed to topic '{topic}', total subscriptions: {self._metrics.total_subscriptions}")
    
    def unsubscribe(self, topic: str, handler: Callable[[Message], None]):
        """取消订阅"""
        with self._lock:
            if topic in self._subscribers and handler in self._subscribers[topic]:
                self._subscribers[topic].remove(handler)
                self._metrics.total_subscriptions -= 1
                if not self._subscribers[topic]:
                    del self._subscribers[topic]
                self._metrics.active_topics = len(self._subscribers)
                print(f"[EventBus] Unsubscribed from topic '{topic}', total subscriptions: {self._metrics.total_subscriptions}")
    
    def publish(self, topic: str, message: Message):
        """发布消息"""
        with self._lock:
            # 添加时间戳和主题到消息
            enhanced_message = {
                **message,
                '_timestamp': time.time(),
                '_topic': topic
            }
            
            # 直接匹配的订阅者
            handlers = self._subscribers.get(topic, []).copy()
            
            # 通配符匹配的订阅者
            for pattern, pattern_handlers in self._subscribers.items():
                if '*' in pattern or '?' in pattern:
                    if fnmatch.fnmatch(topic, pattern):
                        handlers.extend(pattern_handlers)
            
            # 去重
            unique_handlers = list(set(handlers))
            
            self._metrics.total_messages += 1
            self._metrics.last_message_time = time.time()
            
            if unique_handlers:
                print(f"[EventBus] Publishing to topic '{topic}', {len(unique_handlers)} handlers")
            
        # 在锁外执行处理器，避免死锁
        for handler in unique_handlers:
            try:
                handler(enhanced_message)
            except Exception as e:
                print(f"[EventBus] Error in handler for topic '{topic}': {e}")
    
    def get_topics(self) -> List[str]:
        """获取所有主题"""
        with self._lock:
            return list(self._subscribers.keys())
    
    def get_metrics(self) -> BusMetrics:
        """获取总线指标"""
        with self._lock:
            return self._metrics
    
    def clear_all(self):
        """清除所有订阅"""
        with self._lock:
            self._subscribers.clear()
            self._metrics = BusMetrics()
            print("[EventBus] All subscriptions cleared")

# 全局事件总线实例
_global_event_bus = None

def get_global_event_bus() -> SimpleEventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = SimpleEventBus()
    return _global_event_bus

def set_global_event_bus(bus: SimpleEventBus):
    """设置全局事件总线实例"""
    global _global_event_bus
    _global_event_bus = bus
