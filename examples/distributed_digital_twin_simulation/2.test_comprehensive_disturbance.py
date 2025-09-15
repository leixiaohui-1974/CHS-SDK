#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合扰动测试脚本
测试物理扰动和网络扰动的组合效果
"""

import sys
import os
import time
import logging
import threading
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.disturbances.disturbance_framework import InflowDisturbance, DisturbanceConfig, DisturbanceType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockReservoir:
    """模拟水库类"""
    
    def __init__(self, reservoir_id: str, initial_level: float = 100.0, capacity: float = 1000.0):
        self.reservoir_id = reservoir_id
        self.water_level = initial_level
        self.capacity = capacity
        self.inflow = 0.0
        self.outflow = 0.0
        
    def step(self, dt: float, inflow: float = 0.0, **kwargs):
        """仿真步进"""
        self.inflow = inflow
        
        # 简单的水位计算
        net_flow = self.inflow - self.outflow
        self.water_level += net_flow * dt / 100.0  # 简化的水位变化
        
        # 限制水位范围
        self.water_level = max(0, min(self.capacity, self.water_level))
        
        # 根据水位计算出流
        self.outflow = max(0, self.water_level * 0.1)  # 简化的出流计算
    
    def get_state(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'water_level': self.water_level,
            'inflow': self.inflow,
            'outflow': self.outflow,
            'capacity': self.capacity
        }

class MockGate:
    """模拟闸门类"""
    
    def __init__(self, gate_id: str, initial_opening: float = 0.5):
        self.gate_id = gate_id
        self.opening = initial_opening  # 开度 0-1
        self.inflow = 0.0
        self.outflow = 0.0
        
    def step(self, dt: float, inflow: float = 0.0, opening: float = None, **kwargs):
        """仿真步进"""
        self.inflow = inflow
        
        if opening is not None:
            self.opening = max(0, min(1, opening))
        
        # 根据开度和入流计算出流
        self.outflow = self.inflow * self.opening
    
    def get_state(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'opening': self.opening,
            'inflow': self.inflow,
            'outflow': self.outflow
        }

class MockAgent:
    """模拟智能体类"""
    
    def __init__(self, agent_id: str, message_bus=None):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.received_messages = []
        self.sent_messages = []
        self.perception_data = {}
        self.decision_data = {}
        
        # 网络扰动相关属性
        self._disturbance_delay = 0.0
        self._disturbance_jitter = 0.0
        self._disturbance_packet_loss = 0.0
        
    def set_message_bus(self, message_bus):
        """设置消息总线"""
        self.message_bus = message_bus
        
    def perceive(self):
        """感知阶段"""
        # 模拟感知过程
        self.perception_data = {
            'timestamp': time.time(),
            'agent_id': self.agent_id,
            'status': 'perceiving'
        }
        
        # 订阅相关主题
        if self.message_bus:
            self.message_bus.subscribe(f"perception/{self.agent_id}", self._handle_perception_message)
            self.message_bus.subscribe("global/status", self._handle_global_message)
    
    def decide(self):
        """决策阶段"""
        # 模拟决策过程
        self.decision_data = {
            'timestamp': time.time(),
            'agent_id': self.agent_id,
            'decision': f"action_{len(self.sent_messages)}",
            'based_on_perception': self.perception_data
        }
    
    def act(self):
        """执行阶段"""
        # 发送消息
        if self.message_bus:
            message = {
                'sender': self.agent_id,
                'timestamp': time.time(),
                'content': self.decision_data,
                'message_id': f"{self.agent_id}_{len(self.sent_messages)}"
            }
            
            # 发送到不同主题
            self.message_bus.publish(f"action/{self.agent_id}", message)
            self.message_bus.publish("global/coordination", message)
            
            self.sent_messages.append(message)
    
    def _handle_perception_message(self, message: Dict[str, Any]):
        """处理感知消息"""
        self.received_messages.append({
            'type': 'perception',
            'message': message,
            'received_at': time.time()
        })
    
    def _handle_global_message(self, message: Dict[str, Any]):
        """处理全局消息"""
        self.received_messages.append({
            'type': 'global',
            'message': message,
            'received_at': time.time()
        })

def test_physical_and_network_disturbances():
    """测试物理扰动和网络扰动的组合效果"""
    logger.info("=== 开始综合扰动测试 ===")
    
    # 创建增强仿真框架配置
    config = {
        'start_time': 0,
        'end_time': 20,
        'dt': 1.0,
        'enable_network_disturbance': True
    }
    
    # 创建增强仿真框架
    harness = EnhancedSimulationHarness(config)
    
    # 添加物理组件
    reservoir = MockReservoir("upstream_reservoir", initial_level=200.0)
    gate = MockGate("control_gate", initial_opening=0.6)
    downstream_reservoir = MockReservoir("downstream_reservoir", initial_level=150.0)
    
    harness.add_component("upstream_reservoir", reservoir)
    harness.add_component("control_gate", gate)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    
    # 添加连接
    harness.add_connection("upstream_reservoir", "control_gate")
    harness.add_connection("control_gate", "downstream_reservoir")
    
    # 添加智能体
    reservoir_agent = MockAgent("ReservoirAgent")
    gate_agent = MockAgent("GateAgent")
    coordination_agent = MockAgent("CoordinationAgent")
    
    harness.add_agent(reservoir_agent)
    harness.add_agent(gate_agent)
    harness.add_agent(coordination_agent)
    
    # 构建仿真环境
    harness.build()
    
    # 配置物理扰动 - 入流变化
    inflow_config = DisturbanceConfig(
        disturbance_id="inflow_surge",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id="upstream_reservoir",
        start_time=5.0,
        end_time=13.0,
        intensity=1.0,
        parameters={
            "target_inflow": 150.0  # 设置目标入流为150 m³/s
        },
        description="入流激增扰动测试"
    )
    
    inflow_disturbance = InflowDisturbance(inflow_config)
    harness.add_disturbance(inflow_disturbance)
    
    # 配置动态扰动 - 传感器噪声
    sensor_disturbance_config = {
        'disturbance_id': 'sensor_noise',
        'disturbance_type': 'sensor_noise',
        'parameters': {
            'noise_level': 0.1,
            'affected_sensors': ['water_level', 'flow_rate'],
            'noise_type': 'gaussian'
        }
    }
    
    harness.add_dynamic_disturbance(sensor_disturbance_config)
    harness.activate_dynamic_disturbance('sensor_noise', 'upstream_reservoir', 3.0, 10.0)
    
    # 配置网络扰动 - 延迟扰动
    delay_config = {
        'parameters': {
            'base_delay': 100,  # 100ms基础延迟
            'jitter': 50,       # 50ms抖动
            'packet_loss': 0.05, # 5%丢包率
            'affected_topics': ['action/*', 'global/coordination'],
            'affected_agents': ['ReservoirAgent', 'GateAgent'],
            'delay_mode': 'gradual'
        }
    }
    
    harness.add_network_disturbance('network_delay', 'delay', delay_config)
    harness.activate_network_disturbance('network_delay', 4.0, 12.0)
    
    # 配置网络扰动 - 丢包扰动
    packet_loss_config = {
        'parameters': {
            'packet_loss_rate': 0.15,  # 15%丢包率
            'burst_loss_probability': 0.1,  # 10%突发丢包概率
            'burst_loss_duration': 2.0,  # 突发丢包持续2秒
            'affected_topics': ['perception/*', 'global/status'],
            'affected_agents': ['CoordinationAgent']
        }
    }
    
    harness.add_network_disturbance('packet_loss', 'packet_loss', packet_loss_config)
    harness.activate_network_disturbance('packet_loss', 6.0, 8.0)
    
    # 运行仿真
    logger.info("开始运行综合扰动仿真...")
    start_time = time.time()
    
    try:
        harness.run_mas_simulation()
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    logger.info(f"仿真运行完成，耗时: {end_time - start_time:.2f}秒")
    
    # 分析结果
    logger.info("=== 综合扰动测试结果分析 ===")
    
    # 分析物理状态变化
    if harness.history:
        initial_state = harness.history[0]
        final_state = harness.history[-1]
        
        logger.info("物理状态变化:")
        logger.info(f"上游水库水位: {initial_state['upstream_reservoir']['water_level']:.2f} -> {final_state['upstream_reservoir']['water_level']:.2f}")
        logger.info(f"下游水库水位: {initial_state['downstream_reservoir']['water_level']:.2f} -> {final_state['downstream_reservoir']['water_level']:.2f}")
        logger.info(f"闸门开度: {initial_state['control_gate']['opening']:.2f} -> {final_state['control_gate']['opening']:.2f}")
    
    # 分析智能体通信
    total_sent = sum(len(agent.sent_messages) for agent in [reservoir_agent, gate_agent, coordination_agent])
    total_received = sum(len(agent.received_messages) for agent in [reservoir_agent, gate_agent, coordination_agent])
    
    logger.info("智能体通信统计:")
    logger.info(f"总发送消息数: {total_sent}")
    logger.info(f"总接收消息数: {total_received}")
    
    for agent in [reservoir_agent, gate_agent, coordination_agent]:
        logger.info(f"{agent.agent_id}: 发送 {len(agent.sent_messages)}, 接收 {len(agent.received_messages)}")
    
    # 分析扰动状态
    disturbance_status = harness.get_disturbance_status()
    logger.info("扰动状态:")
    logger.info(f"物理扰动: {disturbance_status['physical']['active']}")
    logger.info(f"动态扰动: {disturbance_status['dynamic']['active']}")
    
    if disturbance_status['network']:
        network_stats = disturbance_status['network']['message_bus_status']['stats']
        logger.info(f"网络扰动统计: {network_stats}")
    
    # 导出数据
    harness.export_output_data("comprehensive_test_output")
    
    # 关闭仿真
    harness.shutdown()
    
    return {
        'simulation_steps': len(harness.history),
        'total_sent_messages': total_sent,
        'total_received_messages': total_received,
        'disturbance_status': disturbance_status,
        'execution_time': end_time - start_time
    }

def test_disturbance_interaction():
    """测试不同类型扰动之间的相互作用"""
    logger.info("=== 开始扰动相互作用测试 ===")
    
    # 创建简化的仿真环境
    config = {
        'start_time': 0,
        'end_time': 15,
        'dt': 0.5,
        'enable_network_disturbance': True
    }
    
    harness = EnhancedSimulationHarness(config)
    
    # 添加单个组件
    reservoir = MockReservoir("test_reservoir", initial_level=100.0)
    harness.add_component("test_reservoir", reservoir)
    
    # 添加智能体
    test_agent = MockAgent("TestAgent")
    harness.add_agent(test_agent)
    
    harness.build()
    
    # 同时激活多种扰动
    
    # 1. 物理扰动 - 入流变化
    inflow_config = DisturbanceConfig(
        disturbance_id="test_inflow",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id="test_reservoir",
        start_time=2.0,
        end_time=12.0,
        intensity=1.0,
        parameters={'target_inflow': 40.0},
        description="测试入流扰动"
    )
    harness.add_disturbance(InflowDisturbance(inflow_config))
    
    # 2. 动态扰动 - 执行器故障
    actuator_config = {
        'disturbance_id': 'actuator_failure',
        'disturbance_type': 'actuator_interference',
        'parameters': {
            'interference_type': 'efficiency_reduction',
            'efficiency_factor': 0.7,
            'affected_actuators': ['valve', 'pump']
        }
    }
    harness.add_dynamic_disturbance(actuator_config)
    harness.activate_dynamic_disturbance('actuator_failure', 'test_reservoir', 3.0, 8.0)
    
    # 3. 网络扰动 - 高延迟
    high_delay_config = {
        'parameters': {
            'base_delay': 300,  # 300ms高延迟
            'jitter': 150,
            'packet_loss': 0.2,  # 20%丢包率
            'affected_topics': ['*'],  # 影响所有主题
            'delay_mode': 'random'
        }
    }
    harness.add_network_disturbance('high_delay', 'delay', high_delay_config)
    harness.activate_network_disturbance('high_delay', 1.0, 12.0)
    
    # 运行仿真
    logger.info("运行扰动相互作用测试...")
    
    try:
        harness.run_mas_simulation()
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 分析相互作用效果
    logger.info("=== 扰动相互作用分析 ===")
    
    if harness.history:
        # 分析水位变化趋势
        water_levels = [step['test_reservoir']['water_level'] for step in harness.history]
        max_level = max(water_levels)
        min_level = min(water_levels)
        level_variance = max_level - min_level
        
        logger.info(f"水位变化范围: {min_level:.2f} - {max_level:.2f} (变化幅度: {level_variance:.2f})")
        
        # 分析扰动叠加效应
        disturbance_periods = []
        for i, step in enumerate(harness.history):
            active_disturbances = []
            if 'disturbance_status' in step:
                status = step['disturbance_status']
                if status['physical']['active']:
                    active_disturbances.extend(status['physical']['active'])
                if status['dynamic']['active']:
                    active_disturbances.extend(status['dynamic']['active'])
                if status['network'] and status['network']['active_disturbances']:
                    active_disturbances.extend(status['network']['active_disturbances'].keys())
            
            disturbance_periods.append({
                'time': step['time'],
                'active_count': len(active_disturbances),
                'active_types': active_disturbances,
                'water_level': step['test_reservoir']['water_level']
            })
        
        # 找出扰动叠加最严重的时期
        max_disturbances = max(disturbance_periods, key=lambda x: x['active_count'])
        logger.info(f"最大扰动叠加时刻: t={max_disturbances['time']}, "
                   f"活跃扰动数: {max_disturbances['active_count']}, "
                   f"水位: {max_disturbances['water_level']:.2f}")
    
    # 分析通信影响
    logger.info(f"智能体通信: 发送 {len(test_agent.sent_messages)}, 接收 {len(test_agent.received_messages)}")
    
    # 导出数据
    harness.export_output_data("interaction_test_output")
    
    harness.shutdown()
    
    return {
        'max_disturbance_overlap': max_disturbances['active_count'] if harness.history else 0,
        'water_level_variance': level_variance if harness.history else 0,
        'communication_efficiency': len(test_agent.received_messages) / max(1, len(test_agent.sent_messages))
    }

def main():
    """主函数"""
    logger.info("开始综合扰动测试")
    
    try:
        # 测试物理和网络扰动组合
        comprehensive_results = test_physical_and_network_disturbances()
        
        # 等待一段时间
        time.sleep(2.0)
        
        # 测试扰动相互作用
        interaction_results = test_disturbance_interaction()
        
        # 输出总结
        logger.info("=== 综合扰动测试总结 ===")
        logger.info(f"综合测试 - 仿真步数: {comprehensive_results['simulation_steps']}, "
                   f"消息传递效率: {comprehensive_results['total_received_messages']}/{comprehensive_results['total_sent_messages']}")
        logger.info(f"相互作用测试 - 最大扰动叠加: {interaction_results['max_disturbance_overlap']}, "
                   f"水位变化幅度: {interaction_results['water_level_variance']:.2f}")
        
        logger.info("综合扰动测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()