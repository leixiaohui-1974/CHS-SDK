#!/usr/bin/env python3
"""
测试泵控制逻辑的简化脚本
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.local_agents.control.pump_control_strategies import OptimalControlStrategy
from core_lib.physical_objects.pump import Pump
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def test_control_strategy():
    """测试控制策略"""
    print("=== Testing Control Strategy ===")
    
    strategy = OptimalControlStrategy()
    pumps_info = [
        {'max_flow': 15.0, 'rated_power': 75},
        {'max_flow': 12.0, 'rated_power': 80},
        {'max_flow': 18.0, 'rated_power': 70},
        {'max_flow': 10.0, 'rated_power': 85}
    ]
    current_status = {'total_flow': 0, 'running_pumps': [], 'total_pumps': 4}
    
    # 测试不同需求
    demands = [5.0, 15.0, 25.0, 35.0]
    
    for demand in demands:
        result = strategy.compute_control_action(demand, pumps_info, current_status)
        print(f"Demand: {demand} m³/s")
        print(f"  Strategy: {result.get('strategy', 'unknown')}")
        print(f"  Commands: {result.get('pump_commands', {})}")
        print(f"  Efficiency: {result.get('expected_efficiency', 0):.3f}")
        print()

def test_pump_response():
    """测试泵的响应"""
    print("=== Testing Pump Response ===")
    
    message_bus = MessageBus()
    
    # 创建泵
    pump = Pump(
        name="test_pump",
        initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0},
        parameters={'max_flow_rate': 15.0, 'max_head': 25.0, 'power_consumption_kw': 75},
        message_bus=message_bus,
        action_topic="action.pump.test_pump"
    )
    
    print(f"Initial pump state: {pump.get_state()}")
    
    # 发送控制信号
    print("Sending control signal: 1")
    message_bus.publish("action.pump.test_pump", {'control_signal': 1})
    
    # 步进泵
    pump.step({'upstream_head': 0, 'downstream_head': 10}, 1.0)
    
    print(f"After control signal: {pump.get_state()}")
    
    # 发送停止信号
    print("Sending control signal: 0")
    message_bus.publish("action.pump.test_pump", {'control_signal': 0})
    
    # 步进泵
    pump.step({'upstream_head': 0, 'downstream_head': 10}, 1.0)
    
    print(f"After stop signal: {pump.get_state()}")

if __name__ == "__main__":
    test_control_strategy()
    test_pump_response()
