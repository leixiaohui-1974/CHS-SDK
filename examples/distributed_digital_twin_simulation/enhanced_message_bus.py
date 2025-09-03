#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的消息总线，支持网络延迟扰动
在原有MessageBus基础上添加延迟消息传递功能
"""

import time
import threading
import queue
import random
import logging
from typing import Callable, Dict, Any, List, Optional, Tuple
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message, Listener

logger = logging.getLogger(__name__)

class DelayedMessage:
    """延迟消息类"""
    def __init__(self, topic: str, message: Message, delivery_time: float, 
                 original_publish_time: float, delay_amount: float):
        self.topic = topic
        self.message = message
        self.delivery_time = delivery_time
        self.original_publish_time = original_publish_time
        self.delay_amount = delay_amount
        self.message_id = f"msg_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

class NetworkDisturbanceConfig:
    """网络扰动配置类"""
    def __init__(self):
        self.enabled = False
        self.base_delay = 0.0  # 基础延迟（秒）
        self.jitter_range = 0.0  # 抖动范围（秒）
        self.packet_loss_rate = 0.0  # 丢包率（0-1）
        self.affected_topics = set()  # 受影响的主题
        self.affected_agents = set()  # 受影响的代理
        
class EnhancedMessageBus(MessageBus):
    """增强的消息总线，支持网络延迟扰动"""
    
    def __init__(self):
        super().__init__()
        self.network_disturbance = NetworkDisturbanceConfig()
        self.delayed_messages = queue.PriorityQueue()
        self.message_delivery_thread = None
        self.stop_delivery_thread = False
        self.delivery_thread_lock = threading.Lock()
        self.message_stats = {
            'total_published': 0,
            'delayed_messages': 0,
            'dropped_messages': 0,
            'delivered_messages': 0
        }
        self._start_delivery_thread()
        
    def _start_delivery_thread(self):
        """启动消息传递线程"""
        if self.message_delivery_thread is None or not self.message_delivery_thread.is_alive():
            self.stop_delivery_thread = False
            self.message_delivery_thread = threading.Thread(
                target=self._message_delivery_worker, 
                daemon=True
            )
            self.message_delivery_thread.start()
            logger.info("消息传递线程已启动")
    
    def _message_delivery_worker(self):
        """消息传递工作线程"""
        while not self.stop_delivery_thread:
            try:
                # 检查是否有需要传递的延迟消息
                current_time = time.time()
                
                # 从队列中获取到期的消息
                messages_to_deliver = []
                temp_messages = []
                
                # 取出所有消息检查
                while not self.delayed_messages.empty():
                    try:
                        delivery_time, delayed_msg = self.delayed_messages.get_nowait()
                        if delivery_time <= current_time:
                            messages_to_deliver.append(delayed_msg)
                        else:
                            temp_messages.append((delivery_time, delayed_msg))
                    except queue.Empty:
                        break
                
                # 将未到期的消息放回队列
                for delivery_time, delayed_msg in temp_messages:
                    self.delayed_messages.put((delivery_time, delayed_msg))
                
                # 传递到期的消息
                for delayed_msg in messages_to_deliver:
                    self._deliver_delayed_message(delayed_msg)
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.error(f"消息传递线程错误: {e}")
                time.sleep(0.01)
    
    def _deliver_delayed_message(self, delayed_msg: DelayedMessage):
        """传递延迟消息"""
        try:
            # 添加延迟信息到消息中
            enhanced_message = delayed_msg.message.copy()
            enhanced_message['_network_delay_info'] = {
                'original_publish_time': delayed_msg.original_publish_time,
                'delivery_time': time.time(),
                'delay_amount': delayed_msg.delay_amount,
                'message_id': delayed_msg.message_id
            }
            
            # 使用父类的发布方法直接传递消息
            super().publish(delayed_msg.topic, enhanced_message)
            
            self.message_stats['delivered_messages'] += 1
            logger.debug(f"延迟消息已传递: {delayed_msg.message_id}, 延迟: {delayed_msg.delay_amount:.3f}s")
            
        except Exception as e:
            logger.error(f"传递延迟消息失败: {e}")
    
    def publish(self, topic: str, message: Message):
        """发布消息，支持网络延迟扰动"""
        self.message_stats['total_published'] += 1
        current_time = time.time()
        
        # 检查是否需要应用网络扰动
        if self._should_apply_network_disturbance(topic, message):
            # 检查是否丢包
            if self._should_drop_packet():
                self.message_stats['dropped_messages'] += 1
                logger.debug(f"消息丢包: topic={topic}")
                return
            
            # 计算延迟
            delay = self._calculate_network_delay()
            
            if delay > 0:
                # 创建延迟消息
                delayed_msg = DelayedMessage(
                    topic=topic,
                    message=message,
                    delivery_time=current_time + delay,
                    original_publish_time=current_time,
                    delay_amount=delay
                )
                
                # 添加到延迟队列
                self.delayed_messages.put((delayed_msg.delivery_time, delayed_msg))
                self.message_stats['delayed_messages'] += 1
                
                logger.debug(f"消息延迟发送: {delayed_msg.message_id}, 延迟: {delay:.3f}s")
                return
        
        # 正常发送消息
        super().publish(topic, message)
    
    def _should_apply_network_disturbance(self, topic: str, message: Message) -> bool:
        """判断是否应该应用网络扰动"""
        if not self.network_disturbance.enabled:
            return False
        
        # 检查主题是否受影响
        if self.network_disturbance.affected_topics:
            topic_affected = any(affected_topic in topic for affected_topic in self.network_disturbance.affected_topics)
            if not topic_affected:
                return False
        
        # 检查代理是否受影响（通过消息中的发送者信息）
        if self.network_disturbance.affected_agents:
            sender = message.get('sender', '')
            agent_affected = any(affected_agent in sender for affected_agent in self.network_disturbance.affected_agents)
            if not agent_affected:
                return False
        
        return True
    
    def _should_drop_packet(self) -> bool:
        """判断是否应该丢包"""
        return random.random() < self.network_disturbance.packet_loss_rate
    
    def _calculate_network_delay(self) -> float:
        """计算网络延迟"""
        base_delay = self.network_disturbance.base_delay
        jitter = 0.0
        
        if self.network_disturbance.jitter_range > 0:
            # 添加随机抖动
            jitter = random.uniform(-self.network_disturbance.jitter_range/2, 
                                  self.network_disturbance.jitter_range/2)
        
        total_delay = max(0, base_delay + jitter)
        return total_delay
    
    def enable_network_disturbance(self, base_delay: float = 0.1, 
                                 jitter_range: float = 0.05,
                                 packet_loss_rate: float = 0.01,
                                 affected_topics: Optional[List[str]] = None,
                                 affected_agents: Optional[List[str]] = None):
        """启用网络扰动"""
        self.network_disturbance.enabled = True
        self.network_disturbance.base_delay = base_delay
        self.network_disturbance.jitter_range = jitter_range
        self.network_disturbance.packet_loss_rate = packet_loss_rate
        
        if affected_topics:
            self.network_disturbance.affected_topics = set(affected_topics)
        else:
            self.network_disturbance.affected_topics = set()
            
        if affected_agents:
            self.network_disturbance.affected_agents = set(affected_agents)
        else:
            self.network_disturbance.affected_agents = set()
        
        logger.info(f"网络扰动已启用: 基础延迟={base_delay}s, 抖动范围={jitter_range}s, 丢包率={packet_loss_rate}")
    
    def disable_network_disturbance(self):
        """禁用网络扰动"""
        self.network_disturbance.enabled = False
        logger.info("网络扰动已禁用")
    
    def get_network_disturbance_status(self) -> Dict[str, Any]:
        """获取网络扰动状态"""
        return {
            'enabled': self.network_disturbance.enabled,
            'base_delay': self.network_disturbance.base_delay,
            'jitter_range': self.network_disturbance.jitter_range,
            'packet_loss_rate': self.network_disturbance.packet_loss_rate,
            'affected_topics': list(self.network_disturbance.affected_topics),
            'affected_agents': list(self.network_disturbance.affected_agents),
            'pending_messages': self.delayed_messages.qsize(),
            'stats': self.message_stats.copy()
        }
    
    def clear_delayed_messages(self):
        """清空延迟消息队列"""
        while not self.delayed_messages.empty():
            try:
                self.delayed_messages.get_nowait()
            except queue.Empty:
                break
        logger.info("延迟消息队列已清空")
    
    def shutdown(self):
        """关闭消息总线"""
        self.stop_delivery_thread = True
        if self.message_delivery_thread and self.message_delivery_thread.is_alive():
            self.message_delivery_thread.join(timeout=1.0)
        self.clear_delayed_messages()
        logger.info("增强消息总线已关闭")
    
    def __del__(self):
        """析构函数"""
        try:
            self.shutdown()
        except:
            pass