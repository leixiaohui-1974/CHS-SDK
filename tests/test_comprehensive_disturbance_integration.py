#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合扰动集成测试套件
验证提炼后的扰动模块能够正常工作
"""

import sys
import os
import unittest
import tempfile
import shutil
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.disturbances.disturbance_framework import (
    DisturbanceConfig, DisturbanceType, DisturbanceManager, create_disturbance
)
from core_lib.core.enhanced_message_bus import EnhancedMessageBus, NetworkDisturbanceConfig
from core_lib.disturbances.network_disturbance import NetworkDisturbanceManager

class MockReservoir:
    """模拟水库类，用于测试"""
    
    def __init__(self, reservoir_id: str, initial_level: float = 100.0):
        self.reservoir_id = reservoir_id
        self.water_level = initial_level
        self._inflow = 0.0
        self.outflow = 0.0
        
    def step(self, dt: float, inflow: float = 0.0, **kwargs):
        """仿真步进"""
        self._inflow = inflow
        net_flow = self._inflow - self.outflow
        self.water_level += net_flow * dt / 100.0
        self.water_level = max(0, min(1000, self.water_level))
        self.outflow = max(0, self.water_level * 0.1)
        
    def set_inflow(self, inflow: float):
        """设置入流"""
        self._inflow = inflow
        
    def get_state(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'water_level': self.water_level,
            'inflow': self._inflow,
            'outflow': self.outflow
        }

class MockAgent:
    """模拟智能体类，用于测试"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.messages_sent = 0
        self.messages_received = 0
        
    def step(self, dt: float, **kwargs):
        """智能体步进"""
        pass
        
    def send_message(self, message: str):
        """发送消息"""
        self.messages_sent += 1
        
    def receive_message(self, message: str):
        """接收消息"""
        self.messages_received += 1

class TestComprehensiveDisturbanceIntegration(unittest.TestCase):
    """综合扰动集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_enhanced_message_bus_creation(self):
        """测试增强消息总线创建"""
        message_bus = EnhancedMessageBus()
        self.assertIsNotNone(message_bus)
        
        # 配置网络扰动
        message_bus.network_disturbance.enabled = True
        message_bus.network_disturbance.base_delay = 0.1
        message_bus.network_disturbance.jitter_range = 0.05
        
        self.assertTrue(message_bus.network_disturbance.enabled)
        
        message_bus.shutdown()
    
    def test_disturbance_framework_creation(self):
        """测试扰动框架的创建和基本功能"""
        # 创建增强消息总线
        message_bus = EnhancedMessageBus()
        
        # 测试入流扰动
        inflow_config = DisturbanceConfig(
            disturbance_id="test_inflow",
            disturbance_type=DisturbanceType.INFLOW_CHANGE,
            target_component_id="reservoir_1",
            start_time=1.0,
            end_time=5.0,
            intensity=1.0,
            parameters={'target_inflow': 50.0}
        )
        
        inflow_disturbance = create_disturbance(inflow_config)
        self.assertIsNotNone(inflow_disturbance)
        self.assertEqual(inflow_disturbance.config.disturbance_id, "test_inflow")
        
        # 测试网络延迟扰动
        network_config = DisturbanceConfig(
            disturbance_id="test_network_delay",
            disturbance_type=DisturbanceType.NETWORK_DELAY,
            target_component_id="message_bus",
            start_time=2.0,
            end_time=6.0,
            intensity=1.0,
            parameters={'delay_time': 0.2, 'base_delay': 0.1, 'jitter_range': 0.05}
        )
        
        network_disturbance = create_disturbance(network_config, message_bus)
        self.assertIsNotNone(network_disturbance)
        self.assertEqual(network_disturbance.config.disturbance_id, "test_network_delay")
        
        # 验证网络扰动配置参数
        self.assertEqual(network_disturbance.config.parameters['delay_time'], 0.2)
        self.assertEqual(network_disturbance.config.parameters['base_delay'], 0.1)
        self.assertEqual(network_disturbance.config.parameters['jitter_range'], 0.05)
        
        # 清理
        message_bus.shutdown()
    
    def test_enhanced_simulation_harness_integration(self):
        """测试增强仿真框架集成"""
        # 创建增强仿真框架
        config = {
            'start_time': 0,
            'end_time': 10,
            'dt': 0.5,
            'enable_network_disturbance': True
        }
        harness = EnhancedSimulationHarness(config)
        
        # 添加组件
        reservoir = MockReservoir("reservoir_1")
        agent = MockAgent("agent_1")
        
        harness.add_component("reservoir_1", reservoir)
        harness.add_agent(agent)
        
        # 添加物理扰动
        inflow_config = DisturbanceConfig(
            disturbance_id="test_inflow",
            disturbance_type=DisturbanceType.INFLOW_CHANGE,
            target_component_id="reservoir_1",
            start_time=1.0,
            end_time=3.0,
            intensity=1.0,
            parameters={'target_inflow': 30.0}
        )
        inflow_disturbance = create_disturbance(inflow_config)
        harness.add_disturbance(inflow_disturbance)
        
        # 添加网络扰动
        network_disturbance = harness.add_network_disturbance(
            "test_network_delay",
            "delay",
            {
                'parameters': {
                    'base_delay': 0.1,
                    'jitter_range': 0.05
                }
            }
        )
        
        # 激活网络扰动
        harness.activate_network_disturbance("test_network_delay", 2.0, 4.0)
        
        # 构建仿真
        harness.build()
        
        # 运行仿真
        initial_level = reservoir.water_level
        harness.run_simulation()
        
        # 验证扰动效果
        final_level = reservoir.water_level
        self.assertNotEqual(initial_level, final_level, "水位应该发生变化")
        
        # 验证扰动状态
        active_disturbances = harness.get_active_disturbances()
        active_physical = active_disturbances['physical']
        active_network = active_disturbances['network']
        
        # 在仿真结束后，扰动应该已经停用
        self.assertEqual(len(active_physical), 0, "物理扰动应该已停用")
        self.assertEqual(len(active_network), 0, "网络扰动应该已停用")
        
        # 清理
        if hasattr(harness, 'shutdown'):
            harness.shutdown()
        elif hasattr(harness, 'close'):
            harness.close()
    
    def test_disturbance_manager_functionality(self):
        """测试扰动管理器功能"""
        manager = DisturbanceManager()
        
        # 创建测试组件
        reservoir = MockReservoir("reservoir_1")
        components = {"reservoir_1": reservoir}
        
        # 注册扰动
        config = DisturbanceConfig(
            disturbance_id="test_disturbance",
            disturbance_type=DisturbanceType.INFLOW_CHANGE,
            target_component_id="reservoir_1",
            start_time=1.0,
            end_time=3.0,
            intensity=1.0,
            parameters={'target_inflow': 25.0}
        )
        
        disturbance = create_disturbance(config)
        manager.register_disturbance(disturbance)
        
        # 测试扰动更新
        initial_level = reservoir.water_level
        
        # 在扰动激活前
        effects = manager.update(0.5, 0.5, components)
        self.assertEqual(len(effects), 0, "扰动尚未激活")
        
        # 在扰动激活期间
        effects = manager.update(2.0, 0.5, components)
        self.assertEqual(len(effects), 1, "扰动应该已激活")
        self.assertIn("test_disturbance", effects)
        
        # 手动步进水库以应用扰动效果
        reservoir.step(0.5, inflow=25.0)
        
        # 在扰动结束后
        effects = manager.update(4.0, 0.5, components)
        self.assertEqual(len(effects), 0, "扰动应该已停用")
        
        # 验证水位变化
        final_level = reservoir.water_level
        self.assertNotEqual(initial_level, final_level, "水位应该发生变化")
    
    def test_network_disturbance_manager(self):
        """测试网络扰动管理器"""
        # 创建增强消息总线
        message_bus = EnhancedMessageBus()
        message_bus.network_disturbance.enabled = True
        message_bus.network_disturbance.base_delay = 0.05
        
        # 创建网络扰动管理器
        network_manager = NetworkDisturbanceManager(message_bus)
        
        # 创建延迟扰动
        delay_config = {
            'parameters': {
                'base_delay': 0.1,
                'jitter_range': 0.05,
                'packet_loss_rate': 0.0
            }
        }
        delay_disturbance = network_manager.create_network_delay_disturbance(
            disturbance_id="test_delay",
            config=delay_config
        )
        
        # 激活扰动
        network_manager.activate_disturbance("test_delay", 1.0, 2.0)
        
        # 测试扰动更新
        network_manager.update_all(2.0)  # 在扰动激活期间
        
        # 验证扰动状态
        status = network_manager.get_all_status()
        self.assertIn("test_delay", status['active_disturbances'], "网络扰动应该已激活")
        
        # 清理
        network_manager.shutdown()
        message_bus.shutdown()

if __name__ == '__main__':
    unittest.main()