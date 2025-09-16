"""
主题管理器

提供主题的注册、发现和管理功能。
"""
from typing import Dict, List, Set, Optional, Pattern, Any
import re
import threading
from enum import Enum


class TopicType(Enum):
    """主题类型"""
    STATE = "state"           # 状态主题
    COMMAND = "command"       # 命令主题
    EVENT = "event"          # 事件主题
    DATA = "data"            # 数据主题
    CONTROL = "control"      # 控制主题
    SENSOR = "sensor"        # 传感器主题
    ACTUATOR = "actuator"    # 执行器主题


class TopicManager:
    """
    主题管理器
    
    提供主题的注册、分类、路由和发现功能。
    """
    
    def __init__(self):
        """初始化主题管理器"""
        self._topics: Dict[str, Dict[str, Any]] = {}
        self._topic_patterns: Dict[str, Pattern] = {}
        self._topic_categories: Dict[TopicType, Set[str]] = {
            topic_type: set() for topic_type in TopicType
        }
        self._lock = threading.RLock()
    
    def register_topic(self, topic: str, topic_type: TopicType,
                      description: str = "", metadata: Optional[Dict] = None) -> bool:
        """
        注册主题
        
        Args:
            topic: 主题名称
            topic_type: 主题类型
            description: 主题描述
            metadata: 元数据
            
        Returns:
            bool: 注册是否成功
        """
        with self._lock:
            if topic in self._topics:
                return False
            
            self._topics[topic] = {
                "type": topic_type,
                "description": description,
                "metadata": metadata or {},
                "subscribers": set(),
                "created_at": None,
                "last_published": None,
                "message_count": 0
            }
            
            self._topic_categories[topic_type].add(topic)
            return True
    
    def unregister_topic(self, topic: str) -> bool:
        """
        取消注册主题
        
        Args:
            topic: 主题名称
            
        Returns:
            bool: 取消注册是否成功
        """
        with self._lock:
            if topic not in self._topics:
                return False
            
            topic_info = self._topics[topic]
            topic_type = topic_info["type"]
            
            # 从分类中移除
            self._topic_categories[topic_type].discard(topic)
            
            # 删除主题
            del self._topics[topic]
            return True
    
    def get_topic_info(self, topic: str) -> Optional[Dict]:
        """
        获取主题信息
        
        Args:
            topic: 主题名称
            
        Returns:
            Optional[Dict]: 主题信息，如果不存在返回None
        """
        with self._lock:
            return self._topics.get(topic, {}).copy() if topic in self._topics else None
    
    def get_topics_by_type(self, topic_type: TopicType) -> List[str]:
        """
        根据类型获取主题列表
        
        Args:
            topic_type: 主题类型
            
        Returns:
            List[str]: 主题列表
        """
        with self._lock:
            return list(self._topic_categories[topic_type])
    
    def find_topics(self, pattern: str) -> List[str]:
        """
        根据模式查找主题
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            List[str]: 匹配的主题列表
        """
        try:
            regex = re.compile(pattern)
            with self._lock:
                return [topic for topic in self._topics.keys() if regex.match(topic)]
        except re.error:
            return []
    
    def add_subscriber(self, topic: str, subscriber_id: str) -> bool:
        """
        添加订阅者
        
        Args:
            topic: 主题名称
            subscriber_id: 订阅者ID
            
        Returns:
            bool: 添加是否成功
        """
        with self._lock:
            if topic not in self._topics:
                return False
            
            self._topics[topic]["subscribers"].add(subscriber_id)
            return True
    
    def remove_subscriber(self, topic: str, subscriber_id: str) -> bool:
        """
        移除订阅者
        
        Args:
            topic: 主题名称
            subscriber_id: 订阅者ID
            
        Returns:
            bool: 移除是否成功
        """
        with self._lock:
            if topic not in self._topics:
                return False
            
            self._topics[topic]["subscribers"].discard(subscriber_id)
            return True
    
    def get_subscribers(self, topic: str) -> Set[str]:
        """
        获取订阅者列表
        
        Args:
            topic: 主题名称
            
        Returns:
            Set[str]: 订阅者ID集合
        """
        with self._lock:
            if topic not in self._topics:
                return set()
            
            return self._topics[topic]["subscribers"].copy()
    
    def update_message_stats(self, topic: str):
        """
        更新消息统计
        
        Args:
            topic: 主题名称
        """
        import time
        
        with self._lock:
            if topic in self._topics:
                self._topics[topic]["message_count"] += 1
                self._topics[topic]["last_published"] = time.time()
    
    def get_all_topics(self) -> List[str]:
        """
        获取所有主题
        
        Returns:
            List[str]: 所有主题列表
        """
        with self._lock:
            return list(self._topics.keys())
    
    def get_topic_statistics(self) -> Dict[str, Dict]:
        """
        获取主题统计信息
        
        Returns:
            Dict[str, Dict]: 主题统计信息
        """
        with self._lock:
            stats = {}
            for topic, info in self._topics.items():
                stats[topic] = {
                    "type": info["type"].value,
                    "subscriber_count": len(info["subscribers"]),
                    "message_count": info["message_count"],
                    "last_published": info["last_published"]
                }
            return stats
    
    def clear(self):
        """清除所有主题"""
        with self._lock:
            self._topics.clear()
            for topic_set in self._topic_categories.values():
                topic_set.clear()