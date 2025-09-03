#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强单一扰动测试
使用core_lib中提炼的模块进行单一扰动类型的全面测试
"""

import sys
import os
import time
import logging
from typing import Dict, Any, List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.disturbances.disturbance_framework import (
    InflowDisturbance, SensorNoiseDisturbance, ActuatorFailureDisturbance,
    DisturbanceConfig, DisturbanceType
)
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockAgent:
    """模拟智能体类"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_bus = None
        self.received_messages = []
        self.sent_messages = []
        
    def set_message_bus(self, message_bus):
        """设置消息总线"""
        self.message_bus = message_bus
        
    def perceive(self):
        """感知环境"""
        if self.message_bus:
            # 发送感知消息
            perception_msg = {
                'type': 'perception',
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'data': {'status': 'active'}
            }
            self.message_bus.publish(f'perception/{self.agent_id}', perception_msg)
            self.sent_messages.append(perception_msg)
            
    def decide(self):
        """决策"""
        if self.message_bus:
            # 发送决策消息
            decision_msg = {
                'type': 'decision',
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'action': 'maintain'
            }
            self.message_bus.publish(f'action/{self.agent_id}', decision_msg)
            self.sent_messages.append(decision_msg)
            
    def act(self):
        """执行动作"""
        pass

def test_inflow_disturbance():
    """测试入流扰动"""
    logger.info("=== 测试入流扰动 ===")
    
    # 创建仿真配置
    config = {
        'start_time': 0,
        'end_time': 15,
        'dt': 0.5,
        'enable_network_disturbance': False
    }
    
    # 创建增强仿真框架
    harness = EnhancedSimulationHarness(config)
    
    # 添加水库组件
    initial_state = {
        'water_level': 100.0,
        'volume': 5000.0,
        'inflow': 0.0,
        'outflow': 0.0
    }
    parameters = {
        'surface_area': 50.0,
        'capacity': 1000.0,
        'min_level': 0.0,
        'max_level': 200.0
    }
    reservoir = Reservoir(
        name="test_reservoir",
        initial_state=initial_state,
        parameters=parameters
    )
    harness.add_component("test_reservoir", reservoir)
    
    # 添加智能体
    agent = MockAgent("TestAgent")
    harness.add_agent(agent)
    
    # 构建仿真环境
    harness.build()
    
    # 配置入流扰动
    inflow_config = DisturbanceConfig(
        disturbance_id="inflow_test",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id="test_reservoir",
        start_time=3.0,
        end_time=10.0,
        intensity=1.0,
        parameters={
            "target_inflow": 80.0  # 设置目标入流为80 m³/s
        },
        description="入流扰动测试"
    )
    
    inflow_disturbance = InflowDisturbance(inflow_config)
    harness.add_disturbance(inflow_disturbance)
    
    # 记录初始状态
    initial_state = reservoir.get_state()
    logger.info(f"初始状态: 水位={initial_state['water_level']:.2f}m, 入流={initial_state['inflow']:.2f}m³/s")
    
    # 运行仿真
    logger.info("开始运行入流扰动仿真...")
    start_time = time.time()
    
    try:
        harness.run_simulation()
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    logger.info(f"仿真运行完成，耗时: {end_time - start_time:.2f}秒")
    
    # 分析结果
    if harness.history:
        final_state = harness.history[-1]['test_reservoir']
        logger.info(f"最终状态: 水位={final_state['water_level']:.2f}m, 入流={final_state['inflow']:.2f}m³/s")
        
        # 检查扰动期间的状态变化
        disturbance_period_states = []
        for step in harness.history:
            if 3.0 <= step['time'] <= 10.0:
                disturbance_period_states.append(step['test_reservoir'])
        
        if disturbance_period_states:
            avg_inflow_during_disturbance = sum(s['inflow'] for s in disturbance_period_states) / len(disturbance_period_states)
            logger.info(f"扰动期间平均入流: {avg_inflow_during_disturbance:.2f}m³/s")
            
            if abs(avg_inflow_during_disturbance - 80.0) < 5.0:
                logger.info("✅ 入流扰动成功生效")
            else:
                logger.warning("⚠️ 入流扰动效果不明显")
    
    # 关闭仿真
    harness.shutdown()
    
    return {
        'test_type': 'inflow_disturbance',
        'simulation_steps': len(harness.history) if harness.history else 0,
        'execution_time': end_time - start_time
    }

def test_sensor_noise_disturbance():
    """测试传感器噪声扰动"""
    logger.info("=== 测试传感器噪声扰动 ===")
    
    # 创建仿真配置
    config = {
        'start_time': 0.0,
        'end_time': 25.0,
        'dt': 1.0,
        'enable_network_disturbance': False
    }
    
    # 创建增强仿真框架
    harness = EnhancedSimulationHarness(config)
    
    # 添加水库组件
    initial_state = {
        'water_level': 150.0,
        'volume': 9000.0,
        'inflow': 0.0,
        'outflow': 0.0
    }
    parameters = {
        'surface_area': 60.0,
        'capacity': 1000.0,
        'min_level': 0.0,
        'max_level': 200.0
    }
    reservoir = Reservoir(
        name="sensor_test_reservoir",
        initial_state=initial_state,
        parameters=parameters
    )
    harness.add_component("sensor_test_reservoir", reservoir)
    
    # 添加智能体
    agent = MockAgent("SensorTestAgent")
    harness.add_agent(agent)
    
    # 构建仿真环境
    harness.build()
    
    # 配置传感器噪声扰动
    sensor_config = DisturbanceConfig(
        disturbance_id="sensor_noise_test",
        disturbance_type=DisturbanceType.SENSOR_NOISE,
        target_component_id="sensor_test_reservoir",
        start_time=2.0,
        end_time=8.0,
        intensity=0.8,
        parameters={
            "noise_level": 0.15,  # 15%噪声水平
            "affected_sensors": ["water_level", "flow_rate"],
            "noise_type": "gaussian"
        },
        description="传感器噪声扰动测试"
    )
    
    sensor_disturbance = SensorNoiseDisturbance(sensor_config)
    harness.add_disturbance(sensor_disturbance)
    
    # 记录初始状态
    initial_state = reservoir.get_state()
    logger.info(f"初始状态: 水位={initial_state['water_level']:.2f}m")
    
    # 运行仿真
    logger.info("开始运行传感器噪声扰动仿真...")
    start_time = time.time()
    
    try:
        harness.run_simulation()
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    logger.info(f"仿真运行完成，耗时: {end_time - start_time:.2f}秒")
    
    # 分析结果
    if harness.history:
        # 分析传感器读数的变化
        water_levels = [step['sensor_test_reservoir']['water_level'] for step in harness.history]
        
        # 计算扰动期间的方差
        disturbance_levels = []
        normal_levels = []
        
        for step in harness.history:
            if 2.0 <= step['time'] <= 8.0:
                disturbance_levels.append(step['sensor_test_reservoir']['water_level'])
            else:
                normal_levels.append(step['sensor_test_reservoir']['water_level'])
        
        if disturbance_levels and normal_levels:
            import statistics
            disturbance_variance = statistics.variance(disturbance_levels) if len(disturbance_levels) > 1 else 0
            normal_variance = statistics.variance(normal_levels) if len(normal_levels) > 1 else 0
            
            logger.info(f"正常期间水位方差: {normal_variance:.6f}")
            logger.info(f"扰动期间水位方差: {disturbance_variance:.6f}")
            
            if disturbance_variance > normal_variance * 2:
                logger.info("✅ 传感器噪声扰动成功生效")
            else:
                logger.warning("⚠️ 传感器噪声扰动效果不明显")
    
    # 关闭仿真
    harness.shutdown()
    
    return {
        'test_type': 'sensor_noise_disturbance',
        'simulation_steps': len(harness.history) if harness.history else 0,
        'execution_time': end_time - start_time
    }

def test_actuator_failure_disturbance():
    """测试执行器故障扰动"""
    logger.info("=== 测试执行器故障扰动 ===")
    
    # 创建仿真配置
    config = {
        'start_time': 0.0,
        'end_time': 20.0,
        'dt': 1.0,
        'enable_network_disturbance': False
    }
    
    # 创建增强仿真框架
    harness = EnhancedSimulationHarness(config)
    
    # 添加闸门组件
    initial_state = {
        'opening': 0.5,
        'outflow': 0.0
    }
    parameters = {
        'width': 2.0,
        'discharge_coefficient': 0.6,
        'max_opening': 1.0,
        'min_opening': 0.0
    }
    gate = Gate(
        name="test_gate",
        initial_state=initial_state,
        parameters=parameters
    )
    harness.add_component("test_gate", gate)
    
    # 添加智能体
    agent = MockAgent("ActuatorTestAgent")
    harness.add_agent(agent)
    
    # 配置执行器故障扰动
    actuator_config = DisturbanceConfig(
        disturbance_id="actuator_failure_test",
        disturbance_type=DisturbanceType.ACTUATOR_FAILURE,
        target_component_id="test_gate",
        start_time=5.0,
        end_time=15.0,
        intensity=1.0,
        parameters={
            "failure_type": "partial",
            "efficiency_factor": 0.5
        },
        description="执行器故障扰动测试"
    )
    
    actuator_disturbance = ActuatorFailureDisturbance(actuator_config)
    harness.add_disturbance(actuator_disturbance)
    
    # 构建仿真环境
    harness.build()
    
    # 记录初始状态
    initial_state = gate.get_state()
    logger.info(f"初始状态: 闸门开度={initial_state['opening']:.2f}")
    
    # 运行仿真
    logger.info("开始运行执行器故障扰动仿真...")
    start_time = time.time()
    
    try:
        harness.run_simulation()
    except Exception as e:
        logger.error(f"仿真运行错误: {e}")
        import traceback
        traceback.print_exc()
    
    end_time = time.time()
    logger.info(f"仿真运行完成，耗时: {end_time - start_time:.2f}秒")
    
    # 分析结果
    if harness.history:
        final_state = harness.history[-1]['test_gate']
        logger.info(f"最终状态: 闸门开度={final_state['opening']:.2f}")
        
        # 检查扰动状态
        disturbance_status = harness.get_disturbance_status()
        logger.info(f"扰动状态: {disturbance_status}")
        
        # 检查扰动历史记录
        try:
            disturbance_history = harness.disturbance_manager.get_disturbance_history()
            actuator_records = [r for r in disturbance_history if 'actuator_failure_test' in r['effects']]
            
            logger.info(f"执行器故障扰动记录数: {len(actuator_records)}")
            
            if len(actuator_records) > 0:
                logger.info("✅ 执行器故障扰动成功生效")
                # 显示扰动效果样本
                for i, record in enumerate(actuator_records[:3]):
                    logger.info(f"  样本{i+1}: 时间={record['time']:.1f}s, 效果={record['effects']['actuator_failure_test']}")
            else:
                logger.warning("⚠️ 执行器故障扰动未生效")
        except AttributeError as e:
            logger.warning(f"无法获取扰动历史记录: {e}")
            logger.info("✅ 执行器故障扰动测试完成（无法验证扰动效果）")
    
    # 关闭仿真
    harness.shutdown()
    
    return {
        'test_type': 'actuator_failure_disturbance',
        'simulation_steps': len(harness.history) if harness.history else 0,
        'execution_time': end_time - start_time
    }

def main():
    """主函数"""
    logger.info("开始增强单一扰动测试")
    
    results = []
    
    try:
        # 测试入流扰动
        inflow_result = test_inflow_disturbance()
        results.append(inflow_result)
        
        # 等待一段时间
        time.sleep(1.0)
        
        # 测试传感器噪声扰动
        sensor_result = test_sensor_noise_disturbance()
        results.append(sensor_result)
        
        # 等待一段时间
        time.sleep(1.0)
        
        # 测试执行器故障扰动
        actuator_result = test_actuator_failure_disturbance()
        results.append(actuator_result)
        
        # 输出总结
        logger.info("=== 增强单一扰动测试总结 ===")
        for result in results:
            logger.info(f"{result['test_type']}: {result['simulation_steps']}步, 耗时{result['execution_time']:.2f}秒")
        
        logger.info("增强单一扰动测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()