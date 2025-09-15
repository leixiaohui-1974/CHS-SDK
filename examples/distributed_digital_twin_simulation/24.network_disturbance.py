#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络扰动类
实现网络延迟、丢包等网络层面的扰动
"""

import logging
import random
import time
from typing import Dict, Any, List, Optional
from enhanced_message_bus import EnhancedMessageBus

logger = logging.getLogger(__name__)

class NetworkDelayDisturbance:
    """网络延迟扰动类"""
    
    def __init__(self, disturbance_id: str, enhanced_message_bus: EnhancedMessageBus):
        self.disturbance_id = disturbance_id
        self.message_bus = enhanced_message_bus
        self.is_active = False
        self.start_time = None
        self.end_time = None
        self.config = {}
        
    def configure(self, config: Dict[str, Any]):
        """配置扰动参数"""
        self.config = config
        parameters = config.get('parameters', {})
        
        # 解析配置参数
        self.base_delay = parameters.get('base_delay', 100) / 1000.0  # 转换为秒
        self.jitter_range = parameters.get('jitter', 50) / 1000.0  # 转换为秒
        self.packet_loss_rate = parameters.get('packet_loss', 0.05)
        
        # 受影响的主题和代理
        self.affected_topics = parameters.get('affected_topics', [])
        self.affected_agents = parameters.get('affected_agents', [])
        
        # 延迟模式
        self.delay_mode = parameters.get('delay_mode', 'fixed')  # fixed, random, gradual
        
        logger.info(f"网络延迟扰动 {self.disturbance_id} 配置完成: "
                   f"基础延迟={self.base_delay*1000:.1f}ms, "
                   f"抖动={self.jitter_range*1000:.1f}ms, "
                   f"丢包率={self.packet_loss_rate:.3f}")
    
    def activate(self, start_time: float, duration: float):
        """激活扰动"""
        self.start_time = start_time
        self.end_time = start_time + duration
        self.is_active = True
        
        # 启用消息总线的网络扰动
        self.message_bus.enable_network_disturbance(
            base_delay=self.base_delay,
            jitter_range=self.jitter_range,
            packet_loss_rate=self.packet_loss_rate,
            affected_topics=self.affected_topics,
            affected_agents=self.affected_agents
        )
        
        logger.info(f"网络延迟扰动 {self.disturbance_id} 已激活，持续时间: {duration}s")
    
    def deactivate(self):
        """停用扰动"""
        self.is_active = False
        self.message_bus.disable_network_disturbance()
        logger.info(f"网络延迟扰动 {self.disturbance_id} 已停用")
    
    def update(self, current_time: float):
        """更新扰动状态"""
        if not self.is_active:
            return
        
        # 检查是否应该停用
        if current_time >= self.end_time:
            self.deactivate()
            return
        
        # 根据延迟模式更新参数
        if self.delay_mode == 'gradual':
            self._update_gradual_delay(current_time)
        elif self.delay_mode == 'random':
            self._update_random_delay()
    
    def _update_gradual_delay(self, current_time: float):
        """渐变延迟模式"""
        if self.start_time is None:
            return
        
        # 计算进度（0到1）
        progress = (current_time - self.start_time) / (self.end_time - self.start_time)
        progress = max(0, min(1, progress))
        
        # 延迟从0逐渐增加到最大值，然后逐渐减少
        if progress <= 0.5:
            # 前半段：延迟增加
            delay_factor = progress * 2
        else:
            # 后半段：延迟减少
            delay_factor = (1 - progress) * 2
        
        current_delay = self.base_delay * delay_factor
        
        # 更新消息总线的延迟参数
        self.message_bus.network_disturbance.base_delay = current_delay
    
    def _update_random_delay(self):
        """随机延迟模式"""
        # 每次更新时随机改变延迟
        variation = random.uniform(0.5, 1.5)  # 50%到150%的变化
        current_delay = self.base_delay * variation
        
        # 更新消息总线的延迟参数
        self.message_bus.network_disturbance.base_delay = current_delay
    
    def get_status(self) -> Dict[str, Any]:
        """获取扰动状态"""
        status = {
            'disturbance_id': self.disturbance_id,
            'is_active': self.is_active,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'config': self.config,
            'message_bus_status': self.message_bus.get_network_disturbance_status()
        }
        return status

class PacketLossDisturbance:
    """数据包丢失扰动类"""
    
    def __init__(self, disturbance_id: str, enhanced_message_bus: EnhancedMessageBus):
        self.disturbance_id = disturbance_id
        self.message_bus = enhanced_message_bus
        self.is_active = False
        self.start_time = None
        self.end_time = None
        self.config = {}
        
    def configure(self, config: Dict[str, Any]):
        """配置扰动参数"""
        self.config = config
        parameters = config.get('parameters', {})
        
        # 解析配置参数
        self.packet_loss_rate = parameters.get('packet_loss_rate', 0.1)
        self.burst_loss_probability = parameters.get('burst_loss_probability', 0.05)
        self.burst_loss_duration = parameters.get('burst_loss_duration', 2.0)
        
        # 受影响的主题和代理
        self.affected_topics = parameters.get('affected_topics', [])
        self.affected_agents = parameters.get('affected_agents', [])
        
        logger.info(f"数据包丢失扰动 {self.disturbance_id} 配置完成: "
                   f"丢包率={self.packet_loss_rate:.3f}, "
                   f"突发丢包概率={self.burst_loss_probability:.3f}")
    
    def activate(self, start_time: float, duration: float):
        """激活扰动"""
        self.start_time = start_time
        self.end_time = start_time + duration
        self.is_active = True
        
        # 启用消息总线的网络扰动（主要是丢包）
        self.message_bus.enable_network_disturbance(
            base_delay=0.0,  # 不添加延迟
            jitter_range=0.0,
            packet_loss_rate=self.packet_loss_rate,
            affected_topics=self.affected_topics,
            affected_agents=self.affected_agents
        )
        
        logger.info(f"数据包丢失扰动 {self.disturbance_id} 已激活，持续时间: {duration}s")
    
    def deactivate(self):
        """停用扰动"""
        self.is_active = False
        self.message_bus.disable_network_disturbance()
        logger.info(f"数据包丢失扰动 {self.disturbance_id} 已停用")
    
    def update(self, current_time: float):
        """更新扰动状态"""
        if not self.is_active:
            return
        
        # 检查是否应该停用
        if current_time >= self.end_time:
            self.deactivate()
            return
        
        # 检查是否触发突发丢包
        if random.random() < self.burst_loss_probability:
            self._trigger_burst_loss()
    
    def _trigger_burst_loss(self):
        """触发突发丢包"""
        # 临时提高丢包率
        original_loss_rate = self.message_bus.network_disturbance.packet_loss_rate
        self.message_bus.network_disturbance.packet_loss_rate = min(0.9, original_loss_rate * 5)
        
        logger.warning(f"触发突发丢包，丢包率临时提高到 {self.message_bus.network_disturbance.packet_loss_rate:.3f}")
        
        # 设置定时器恢复正常丢包率
        def restore_loss_rate():
            time.sleep(self.burst_loss_duration)
            self.message_bus.network_disturbance.packet_loss_rate = original_loss_rate
            logger.info(f"突发丢包结束，丢包率恢复到 {original_loss_rate:.3f}")
        
        import threading
        threading.Thread(target=restore_loss_rate, daemon=True).start()
    
    def get_status(self) -> Dict[str, Any]:
        """获取扰动状态"""
        status = {
            'disturbance_id': self.disturbance_id,
            'is_active': self.is_active,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'config': self.config,
            'message_bus_status': self.message_bus.get_network_disturbance_status()
        }
        return status

class NetworkDisturbanceManager:
    """网络扰动管理器"""
    
    def __init__(self, enhanced_message_bus: EnhancedMessageBus):
        self.message_bus = enhanced_message_bus
        self.active_disturbances = {}
        self.disturbance_history = []
        
    def create_network_delay_disturbance(self, disturbance_id: str, config: Dict[str, Any]) -> NetworkDelayDisturbance:
        """创建网络延迟扰动"""
        disturbance = NetworkDelayDisturbance(disturbance_id, self.message_bus)
        disturbance.configure(config)
        self.active_disturbances[disturbance_id] = disturbance
        return disturbance
    
    def create_packet_loss_disturbance(self, disturbance_id: str, config: Dict[str, Any]) -> PacketLossDisturbance:
        """创建数据包丢失扰动"""
        disturbance = PacketLossDisturbance(disturbance_id, self.message_bus)
        disturbance.configure(config)
        self.active_disturbances[disturbance_id] = disturbance
        return disturbance
    
    def activate_disturbance(self, disturbance_id: str, start_time: float, duration: float):
        """激活扰动"""
        if disturbance_id in self.active_disturbances:
            disturbance = self.active_disturbances[disturbance_id]
            disturbance.activate(start_time, duration)
            
            # 记录到历史
            self.disturbance_history.append({
                'disturbance_id': disturbance_id,
                'type': type(disturbance).__name__,
                'start_time': start_time,
                'duration': duration,
                'activated_at': time.time()
            })
        else:
            logger.error(f"扰动 {disturbance_id} 不存在")
    
    def update_all(self, current_time: float):
        """更新所有扰动"""
        for disturbance in self.active_disturbances.values():
            disturbance.update(current_time)
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有扰动状态"""
        status = {
            'active_disturbances': {},
            'message_bus_status': self.message_bus.get_network_disturbance_status(),
            'disturbance_history': self.disturbance_history
        }
        
        for disturbance_id, disturbance in self.active_disturbances.items():
            status['active_disturbances'][disturbance_id] = disturbance.get_status()
        
        return status
    
    def shutdown(self):
        """关闭所有扰动"""
        for disturbance in self.active_disturbances.values():
            if disturbance.is_active:
                disturbance.deactivate()
        
        self.active_disturbances.clear()
        logger.info("网络扰动管理器已关闭")