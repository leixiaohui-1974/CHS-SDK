#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络扰动测试脚本
测试网络延迟扰动和数据包丢失扰动的功能
"""

import sys
import os
import time
import logging
import threading
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from enhanced_message_bus import EnhancedMessageBus
from network_disturbance import NetworkDisturbanceManager, NetworkDelayDisturbance, PacketLossDisturbance

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestAgent:
    """测试代理类"""
    
    def __init__(self, agent_id: str, message_bus: EnhancedMessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.received_messages = []
        self.sent_messages = []
        
    def subscribe_to_topic(self, topic: str):
        """订阅主题"""
        self.message_bus.subscribe(topic, self.handle_message)
        logger.info(f"代理 {self.agent_id} 订阅主题: {topic}")
    
    def handle_message(self, message: Dict[str, Any]):
        """处理接收到的消息"""
        receive_time = time.time()
        
        # 记录接收到的消息
        message_info = {
            'receive_time': receive_time,
            'message': message.copy(),
            'agent_id': self.agent_id
        }
        
        # 检查是否有网络延迟信息
        if '_network_delay_info' in message:
            delay_info = message['_network_delay_info']
            actual_delay = receive_time - delay_info['original_publish_time']
            message_info['actual_delay'] = actual_delay
            message_info['expected_delay'] = delay_info['delay_amount']
            
            logger.info(f"代理 {self.agent_id} 收到延迟消息: "
                       f"预期延迟={delay_info['delay_amount']:.3f}s, "
                       f"实际延迟={actual_delay:.3f}s")
        else:
            logger.info(f"代理 {self.agent_id} 收到正常消息")
        
        self.received_messages.append(message_info)
    
    def send_message(self, topic: str, content: str):
        """发送消息"""
        send_time = time.time()
        message = {
            'sender': self.agent_id,
            'content': content,
            'send_time': send_time,
            'message_id': f"{self.agent_id}_{len(self.sent_messages)}"
        }
        
        self.message_bus.publish(topic, message)
        self.sent_messages.append({
            'send_time': send_time,
            'topic': topic,
            'message': message.copy()
        })
        
        logger.info(f"代理 {self.agent_id} 发送消息到 {topic}: {content}")

def test_network_delay_disturbance():
    """测试网络延迟扰动"""
    logger.info("=== 开始测试网络延迟扰动 ===")
    
    # 创建增强消息总线
    message_bus = EnhancedMessageBus()
    
    # 创建网络扰动管理器
    disturbance_manager = NetworkDisturbanceManager(message_bus)
    
    # 创建测试代理
    agent1 = TestAgent("Agent1", message_bus)
    agent2 = TestAgent("Agent2", message_bus)
    
    # 设置订阅
    agent1.subscribe_to_topic("test/communication")
    agent2.subscribe_to_topic("test/communication")
    
    # 发送一些正常消息
    logger.info("发送正常消息...")
    agent1.send_message("test/communication", "正常消息1")
    agent2.send_message("test/communication", "正常消息2")
    time.sleep(0.1)  # 等待消息传递
    
    # 配置网络延迟扰动
    delay_config = {
        'parameters': {
            'base_delay': 200,  # 200ms基础延迟
            'jitter': 100,      # 100ms抖动
            'packet_loss': 0.1, # 10%丢包率
            'affected_topics': ['test/communication'],
            'affected_agents': ['Agent1', 'Agent2'],
            'delay_mode': 'fixed'
        }
    }
    
    # 创建并激活网络延迟扰动
    delay_disturbance = disturbance_manager.create_network_delay_disturbance(
        "test_delay", delay_config
    )
    
    current_time = time.time()
    disturbance_manager.activate_disturbance("test_delay", current_time, 5.0)
    
    # 发送延迟消息
    logger.info("发送延迟消息...")
    for i in range(10):
        agent1.send_message("test/communication", f"延迟消息{i+1}")
        time.sleep(0.2)
    
    # 等待延迟消息传递
    logger.info("等待延迟消息传递...")
    time.sleep(3.0)
    
    # 更新扰动状态
    disturbance_manager.update_all(time.time())
    
    # 等待扰动结束
    time.sleep(3.0)
    
    # 发送扰动结束后的消息
    logger.info("发送扰动结束后的消息...")
    agent1.send_message("test/communication", "扰动结束后的消息")
    time.sleep(0.1)
    
    # 分析结果
    logger.info("=== 网络延迟扰动测试结果 ===")
    logger.info(f"Agent1 发送消息数: {len(agent1.sent_messages)}")
    logger.info(f"Agent1 接收消息数: {len(agent1.received_messages)}")
    logger.info(f"Agent2 接收消息数: {len(agent2.received_messages)}")
    
    # 统计延迟消息
    delayed_messages = [msg for msg in agent1.received_messages + agent2.received_messages 
                       if 'actual_delay' in msg]
    logger.info(f"延迟消息数量: {len(delayed_messages)}")
    
    if delayed_messages:
        avg_delay = sum(msg['actual_delay'] for msg in delayed_messages) / len(delayed_messages)
        logger.info(f"平均延迟: {avg_delay:.3f}s")
    
    # 获取扰动状态
    status = disturbance_manager.get_all_status()
    logger.info(f"消息统计: {status['message_bus_status']['stats']}")
    
    # 关闭
    disturbance_manager.shutdown()
    message_bus.shutdown()
    
    return {
        'agent1_sent': len(agent1.sent_messages),
        'agent1_received': len(agent1.received_messages),
        'agent2_received': len(agent2.received_messages),
        'delayed_messages': len(delayed_messages),
        'avg_delay': avg_delay if delayed_messages else 0,
        'message_stats': status['message_bus_status']['stats']
    }

def test_packet_loss_disturbance():
    """测试数据包丢失扰动"""
    logger.info("=== 开始测试数据包丢失扰动 ===")
    
    # 创建增强消息总线
    message_bus = EnhancedMessageBus()
    
    # 创建网络扰动管理器
    disturbance_manager = NetworkDisturbanceManager(message_bus)
    
    # 创建测试代理
    agent1 = TestAgent("Agent1", message_bus)
    agent2 = TestAgent("Agent2", message_bus)
    
    # 设置订阅
    agent1.subscribe_to_topic("test/packet_loss")
    agent2.subscribe_to_topic("test/packet_loss")
    
    # 配置数据包丢失扰动
    loss_config = {
        'parameters': {
            'packet_loss_rate': 0.3,  # 30%丢包率
            'burst_loss_probability': 0.1,  # 10%突发丢包概率
            'burst_loss_duration': 1.0,  # 突发丢包持续1秒
            'affected_topics': ['test/packet_loss'],
            'affected_agents': ['Agent1', 'Agent2']
        }
    }
    
    # 创建并激活数据包丢失扰动
    loss_disturbance = disturbance_manager.create_packet_loss_disturbance(
        "test_packet_loss", loss_config
    )
    
    current_time = time.time()
    disturbance_manager.activate_disturbance("test_packet_loss", current_time, 5.0)
    
    # 发送大量消息测试丢包
    logger.info("发送消息测试丢包...")
    total_sent = 50
    for i in range(total_sent):
        agent1.send_message("test/packet_loss", f"测试消息{i+1}")
        time.sleep(0.1)
        
        # 定期更新扰动状态
        if i % 10 == 0:
            disturbance_manager.update_all(time.time())
    
    # 等待消息传递完成
    time.sleep(2.0)
    
    # 分析结果
    logger.info("=== 数据包丢失扰动测试结果 ===")
    logger.info(f"总发送消息数: {total_sent}")
    logger.info(f"Agent1 接收消息数: {len(agent1.received_messages)}")
    logger.info(f"Agent2 接收消息数: {len(agent2.received_messages)}")
    
    # 计算丢包率
    total_received = len(agent1.received_messages) + len(agent2.received_messages)
    actual_loss_rate = 1 - (total_received / (total_sent * 2))  # 每条消息应该被两个代理接收
    logger.info(f"实际丢包率: {actual_loss_rate:.3f}")
    
    # 获取扰动状态
    status = disturbance_manager.get_all_status()
    logger.info(f"消息统计: {status['message_bus_status']['stats']}")
    
    # 关闭
    disturbance_manager.shutdown()
    message_bus.shutdown()
    
    return {
        'total_sent': total_sent,
        'total_received': total_received,
        'actual_loss_rate': actual_loss_rate,
        'message_stats': status['message_bus_status']['stats']
    }

def test_combined_network_disturbances():
    """测试组合网络扰动"""
    logger.info("=== 开始测试组合网络扰动 ===")
    
    # 创建增强消息总线
    message_bus = EnhancedMessageBus()
    
    # 创建网络扰动管理器
    disturbance_manager = NetworkDisturbanceManager(message_bus)
    
    # 创建测试代理
    agents = [TestAgent(f"Agent{i+1}", message_bus) for i in range(4)]
    
    # 设置订阅
    for agent in agents:
        agent.subscribe_to_topic("test/combined")
    
    # 配置延迟扰动
    delay_config = {
        'parameters': {
            'base_delay': 150,
            'jitter': 75,
            'packet_loss': 0.05,
            'affected_topics': ['test/combined'],
            'delay_mode': 'gradual'
        }
    }
    
    # 配置丢包扰动
    loss_config = {
        'parameters': {
            'packet_loss_rate': 0.2,
            'burst_loss_probability': 0.15,
            'burst_loss_duration': 1.5,
            'affected_topics': ['test/combined']
        }
    }
    
    # 创建扰动
    delay_disturbance = disturbance_manager.create_network_delay_disturbance(
        "combined_delay", delay_config
    )
    loss_disturbance = disturbance_manager.create_packet_loss_disturbance(
        "combined_loss", loss_config
    )
    
    # 激活扰动（有重叠时间）
    current_time = time.time()
    disturbance_manager.activate_disturbance("combined_delay", current_time, 8.0)
    disturbance_manager.activate_disturbance("combined_loss", current_time + 2.0, 6.0)
    
    # 持续发送消息
    logger.info("开始持续发送消息...")
    message_count = 0
    start_time = time.time()
    
    while time.time() - start_time < 10.0:
        for i, agent in enumerate(agents):
            agent.send_message("test/combined", f"消息{message_count}_{i}")
            message_count += 1
        
        time.sleep(0.5)
        
        # 更新扰动状态
        disturbance_manager.update_all(time.time())
    
    # 等待所有消息传递完成
    time.sleep(3.0)
    
    # 分析结果
    logger.info("=== 组合网络扰动测试结果 ===")
    total_sent = message_count
    total_received = sum(len(agent.received_messages) for agent in agents)
    
    logger.info(f"总发送消息数: {total_sent}")
    logger.info(f"总接收消息数: {total_received}")
    
    # 统计延迟消息
    all_received = []
    for agent in agents:
        all_received.extend(agent.received_messages)
    
    delayed_messages = [msg for msg in all_received if 'actual_delay' in msg]
    normal_messages = [msg for msg in all_received if 'actual_delay' not in msg]
    
    logger.info(f"延迟消息数量: {len(delayed_messages)}")
    logger.info(f"正常消息数量: {len(normal_messages)}")
    
    if delayed_messages:
        avg_delay = sum(msg['actual_delay'] for msg in delayed_messages) / len(delayed_messages)
        max_delay = max(msg['actual_delay'] for msg in delayed_messages)
        min_delay = min(msg['actual_delay'] for msg in delayed_messages)
        
        logger.info(f"平均延迟: {avg_delay:.3f}s")
        logger.info(f"最大延迟: {max_delay:.3f}s")
        logger.info(f"最小延迟: {min_delay:.3f}s")
    
    # 获取最终状态
    status = disturbance_manager.get_all_status()
    logger.info(f"最终消息统计: {status['message_bus_status']['stats']}")
    
    # 关闭
    disturbance_manager.shutdown()
    message_bus.shutdown()
    
    return {
        'total_sent': total_sent,
        'total_received': total_received,
        'delayed_messages': len(delayed_messages),
        'normal_messages': len(normal_messages),
        'avg_delay': avg_delay if delayed_messages else 0,
        'message_stats': status['message_bus_status']['stats']
    }

def main():
    """主函数"""
    logger.info("开始网络扰动测试")
    
    try:
        # 测试网络延迟扰动
        delay_results = test_network_delay_disturbance()
        
        # 等待一段时间
        time.sleep(2.0)
        
        # 测试数据包丢失扰动
        loss_results = test_packet_loss_disturbance()
        
        # 等待一段时间
        time.sleep(2.0)
        
        # 测试组合网络扰动
        combined_results = test_combined_network_disturbances()
        
        # 输出总结
        logger.info("=== 网络扰动测试总结 ===")
        logger.info(f"延迟扰动测试 - 平均延迟: {delay_results['avg_delay']:.3f}s, "
                   f"延迟消息: {delay_results['delayed_messages']}")
        logger.info(f"丢包扰动测试 - 实际丢包率: {loss_results['actual_loss_rate']:.3f}")
        logger.info(f"组合扰动测试 - 延迟消息: {combined_results['delayed_messages']}, "
                   f"平均延迟: {combined_results['avg_delay']:.3f}s")
        
        logger.info("网络扰动测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()