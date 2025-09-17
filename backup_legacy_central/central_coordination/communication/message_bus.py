"""
增强的消息总线实现

解决原有设计中的topic信息传递问题，提供更灵活的消息处理机制。
"""
from typing import Callable, Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import threading
import time
import logging


# Type aliases
Message = Dict[str, Any]


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class MessageEnvelope:
    """消息封装类，包含完整的消息信息"""
    topic: str
    message: Message
    timestamp: float
    sender_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None


class MessageHandler:
    """消息处理器包装类"""
    
    def __init__(self, handler_func: Callable, handler_id: Optional[str] = None, 
                 include_envelope: bool = False):
        """
        初始化消息处理器
        
        Args:
            handler_func: 处理函数
            handler_id: 处理器ID（可选）
            include_envelope: 是否包含完整的消息封装
        """
        self.handler_func = handler_func
        self.handler_id = handler_id or f"handler_{id(handler_func)}"
        self.include_envelope = include_envelope
        self.call_count = 0
        self.last_call_time = None
        
    def __call__(self, envelope: MessageEnvelope):
        """调用处理函数"""
        self.call_count += 1
        self.last_call_time = time.time()
        
        if self.include_envelope:
            # 传递完整的消息封装
            return self.handler_func(envelope)
        else:
            # 只传递消息内容（向后兼容）
            return self.handler_func(envelope.message)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "handler_id": self.handler_id,
            "call_count": self.call_count,
            "last_call_time": self.last_call_time
        }


class MessageBus:
    """
    增强的消息总线
    
    提供发布/订阅机制，支持：
    1. 主题路由
    2. 消息优先级
    3. 统计信息
    4. 线程安全
    5. 向后兼容
    """

    def __init__(self, enable_stats: bool = True):
        """
        初始化消息总线
        
        Args:
            enable_stats: 是否启用统计功能
        """
        self._subscriptions: Dict[str, List[MessageHandler]] = {}
        self._component_topology: Dict[str, Dict[str, str]] = {}
        self._stats_enabled = enable_stats
        self._message_stats: Dict[str, int] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        if enable_stats:
            self._logger.info("MessageBus created with statistics enabled.")
        else:
            self._logger.info("MessageBus created.")

    def set_component_topology(self, topology: Dict[str, Dict[str, str]]):
        """
        设置组件拓扑关系
        
        Args:
            topology: 拓扑关系字典
        """
        with self._lock:
            self._component_topology = topology.copy()
            self._logger.info("Component topology updated.")

    def get_component_topology(self) -> Dict[str, Dict[str, str]]:
        """获取组件拓扑关系"""
        with self._lock:
            return self._component_topology.copy()

    def subscribe(self, topic: str, handler: Union[Callable, MessageHandler], 
                  handler_id: Optional[str] = None, include_envelope: bool = False) -> bool:
        """
        订阅主题
        
        Args:
            topic: 主题名称
            handler: 处理函数或MessageHandler实例
            handler_id: 处理器ID（可选）
            include_envelope: 是否向处理器传递完整的消息封装
            
        Returns:
            bool: 订阅是否成功
        """
        with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            
            # 如果是普通函数，包装成MessageHandler
            if not isinstance(handler, MessageHandler):
                handler = MessageHandler(handler, handler_id, include_envelope)
            
            # 检查是否已存在相同的处理器
            for existing_handler in self._subscriptions[topic]:
                if existing_handler.handler_id == handler.handler_id:
                    self._logger.warning(
                        f"Handler '{handler.handler_id}' already subscribed to topic '{topic}'."
                    )
                    return False
            
            self._subscriptions[topic].append(handler)
            self._logger.info(
                f"Handler '{handler.handler_id}' subscribed to topic '{topic}'."
            )
            return True

    def unsubscribe(self, topic: str, handler_id: str) -> bool:
        """
        取消订阅
        
        Args:
            topic: 主题名称
            handler_id: 处理器ID
            
        Returns:
            bool: 取消订阅是否成功
        """
        with self._lock:
            if topic not in self._subscriptions:
                return False
            
            for i, handler in enumerate(self._subscriptions[topic]):
                if handler.handler_id == handler_id:
                    self._subscriptions[topic].pop(i)
                    self._logger.info(
                        f"Handler '{handler_id}' unsubscribed from topic '{topic}'."
                    )
                    
                    # 如果主题没有订阅者了，删除主题
                    if not self._subscriptions[topic]:
                        del self._subscriptions[topic]
                    
                    return True
            
            return False

    def publish(self, topic: str, message: Message, sender_id: Optional[str] = None,
                priority: MessagePriority = MessagePriority.NORMAL,
                correlation_id: Optional[str] = None) -> int:
        """
        发布消息
        
        Args:
            topic: 主题名称
            message: 消息内容
            sender_id: 发送者ID
            priority: 消息优先级
            correlation_id: 关联ID
            
        Returns:
            int: 成功处理的订阅者数量
        """
        with self._lock:
            # 更新统计信息
            if self._stats_enabled:
                self._message_stats[topic] = self._message_stats.get(topic, 0) + 1
            
            # 如果没有订阅者，直接返回
            if topic not in self._subscriptions:
                return 0
            
            # 创建消息封装
            envelope = MessageEnvelope(
                topic=topic,
                message=message,
                timestamp=time.time(),
                sender_id=sender_id,
                priority=priority,
                correlation_id=correlation_id
            )
            
            # 发送给所有订阅者
            successful_deliveries = 0
            for handler in self._subscriptions[topic]:
                try:
                    handler(envelope)
                    successful_deliveries += 1
                except Exception as e:
                    self._logger.error(
                        f"Error delivering message to handler '{handler.handler_id}' "
                        f"on topic '{topic}': {e}"
                    )
            
            return successful_deliveries

    def get_subscriptions(self) -> Dict[str, List[str]]:
        """
        获取订阅信息
        
        Returns:
            Dict[str, List[str]]: 主题和处理器ID的映射
        """
        with self._lock:
            result = {}
            for topic, handlers in self._subscriptions.items():
                result[topic] = [h.handler_id for h in handlers]
            return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self._stats_enabled:
            return {"stats_enabled": False}
        
        with self._lock:
            handler_stats = {}
            for topic, handlers in self._subscriptions.items():
                handler_stats[topic] = [h.get_stats() for h in handlers]
            
            return {
                "stats_enabled": True,
                "message_counts": self._message_stats.copy(),
                "subscription_counts": {
                    topic: len(handlers) 
                    for topic, handlers in self._subscriptions.items()
                },
                "handler_stats": handler_stats,
                "total_topics": len(self._subscriptions),
                "total_handlers": sum(len(handlers) for handlers in self._subscriptions.values())
            }

    def clear_statistics(self):
        """清除统计信息"""
        if self._stats_enabled:
            with self._lock:
                self._message_stats.clear()
                for handlers in self._subscriptions.values():
                    for handler in handlers:
                        handler.call_count = 0
                        handler.last_call_time = None
                self._logger.info("Statistics cleared.")

    def shutdown(self):
        """关闭消息总线"""
        with self._lock:
            self._subscriptions.clear()
            self._component_topology.clear()
            if self._stats_enabled:
                self._message_stats.clear()
            self._logger.info("MessageBus shutdown completed.")


# 向后兼容的类型别名
Listener = Callable[[Message], None]