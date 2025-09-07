#!/usr/bin/env python3
"""
简化的PID控制器测试脚本
用于验证PID控制器是否能正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core_lib.local_agents.control.pid_controller import PIDController

def test_pid_controller():
    """
    测试PID控制器的基本功能
    """
    print("=== PID Controller Test ===")
    
    # 创建PID控制器
    pid = PIDController(
        Kp=10.0,
        Ki=1.0,
        Kd=0.0,
        setpoint=12.0,
        min_output=0.0,
        max_output=1.0
    )
    
    # 测试不同的水位值
    test_levels = [14.0, 13.0, 12.5, 12.0, 11.5, 11.0]
    dt = 0.5
    
    for level in test_levels:
        observation = {'process_variable': level}
        control_signal = pid.compute_control_action(observation, dt)
        error = pid.setpoint - level
        print(f"Level: {level:.1f}m, Error: {error:.1f}, Control Signal: {control_signal:.4f}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_pid_controller()