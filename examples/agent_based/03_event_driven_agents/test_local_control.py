#!/usr/bin/env python3
"""
测试LocalControlAgent消息处理的脚本
用于验证LocalControlAgent是否能正确接收和处理消息
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent

def test_local_control_agent():
    """
    测试LocalControlAgent的消息处理功能
    """
    print("=== LocalControlAgent Message Test ===")
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 创建PID控制器
    pid_controller = PIDController(
        Kp=10.0,
        Ki=1.0,
        Kd=0.0,
        setpoint=12.0,
        min_output=0.0,
        max_output=1.0
    )
    
    # 创建LocalControlAgent
    control_agent = LocalControlAgent(
        agent_id="test_control_agent",
        message_bus=message_bus,
        dt=0.5,
        target_component="test_gate",
        control_type="gate_control",
        data_sources={"primary_data": "test.reservoir.level"},
        control_targets={"primary_target": "test.gate.action"},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic="test.reservoir.level",
        observation_key='water_level',
        action_topic="test.gate.action"
    )
    
    # 模拟发送水位消息
    test_message = {'water_level': 14.0}
    print(f"Sending message: {test_message}")
    
    # 手动调用handle_observation方法
    print("\nCalling handle_observation directly...")
    control_agent.handle_observation(test_message)
    
    # 通过消息总线发送消息
    print("\nPublishing message to bus...")
    message_bus.publish("test.reservoir.level", test_message)
    
    # 检查消息总线中的订阅者
    print(f"\nSubscribers to 'test.reservoir.level': {len(message_bus._subscriptions.get('test.reservoir.level', []))}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_local_control_agent()