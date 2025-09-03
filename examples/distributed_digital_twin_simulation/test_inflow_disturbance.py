#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试入流扰动对物理计算核心的影响
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder
from dynamic_disturbance_manager import DynamicDisturbanceManager
from core_lib.central_coordination.collaboration.message_bus import MessageBus
import time

def test_inflow_disturbance():
    print("=== 测试入流扰动对物理计算核心的影响 ===")
    
    # 构建仿真
    builder = SimulationBuilder('.')
    harness = builder.load()
    
    # 获取上游水库
    upstream_reservoir = harness.components.get('Upstream_Reservoir')
    if not upstream_reservoir:
        print("❌ 未找到Upstream_Reservoir组件")
        return
    
    print(f"\n初始状态:")
    print(f"- 上游水库初始入流: {upstream_reservoir._inflow} m³/s")
    print(f"- 上游水库初始水位: {upstream_reservoir.get_state()['water_level']} m")
    
    # 创建消息总线和扰动管理器
    message_bus = MessageBus()
    disturbance_manager = DynamicDisturbanceManager(message_bus)
    
    # 定义入流扰动配置
    inflow_disturbance_config = {
        'type': 'inflow_variation',
        'disturbance_scenario': {
            'type': 'inflow_variation',
            'parameters': {
                'target_component': 'Upstream_Reservoir',
                'magnitude': 50.0,  # 增加50 m³/s
                'pattern': 'step'   # 阶跃变化
            }
        }
    }
    
    # 注册扰动
    start_time = 1.0  # 1秒后开始
    duration = 10.0   # 持续10秒
    disturbance_manager.register_disturbance('inflow_test', inflow_disturbance_config, start_time, duration)
    
    print(f"\n开始仿真，监测入流扰动效果...")
    
    # 运行仿真并监测
    dt = 0.5  # 时间步长
    total_time = 15.0  # 总仿真时间
    current_time = 0.0
    
    while current_time < total_time:
        # 更新扰动管理器
        disturbance_manager.update(current_time, harness)
        
        # 执行一步仿真
        harness.step()
        
        # 记录关键状态
        if current_time % 2.0 < dt:  # 每2秒记录一次
            water_level = upstream_reservoir.get_state()['water_level']
            current_inflow = upstream_reservoir._inflow
            print(f"t={current_time:.1f}s: 入流={current_inflow:.1f} m³/s, 水位={water_level:.3f} m")
        
        current_time += dt
    
    print(f"\n仿真完成!")
    final_state = upstream_reservoir.get_state()
    print(f"最终状态:")
    print(f"- 最终入流: {upstream_reservoir._inflow} m³/s")
    print(f"- 最终水位: {final_state['water_level']} m")
    
    # 检查扰动是否生效
    if upstream_reservoir._inflow != 100.0:
        print("✅ 入流扰动成功影响了物理计算核心!")
    else:
        print("❌ 入流扰动未能影响物理计算核心")

if __name__ == '__main__':
    test_inflow_disturbance()