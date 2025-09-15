#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的入流扰动测试
直接修改水库的入流参数来验证扰动效果
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder
import time

def test_simple_inflow_disturbance():
    print("=== 简单入流扰动测试 ===")
    
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
    print(f"- 仿真时间步长dt: {harness.dt} s")
    print(f"- 上游水库初始体积: {upstream_reservoir.get_state().get('volume', 0)} m³")
    
    print(f"\n开始仿真，手动应用入流扰动...")
    
    # 计算理论水位变化
    initial_volume = upstream_reservoir.get_state().get('volume', 0)
    surface_area = upstream_reservoir.get_parameters().get('surface_area', 1e6)  # 默认100万平方米
    print(f"- 水库表面积: {surface_area} m²")
    
    # 计算扰动期间的理论水位变化
    inflow_increase = 50.0  # 从100增加到150 m³/s
    disturbance_duration = 10.0  # 10秒扰动
    volume_increase = inflow_increase * disturbance_duration  # 额外体积
    theoretical_level_change = volume_increase / surface_area
    print(f"- 理论水位变化: {theoretical_level_change:.6f} m (扰动期间额外{volume_increase} m³)")
    
    # 运行仿真并手动应用扰动
    total_time = 15.0  # 总仿真时间
    current_time = 0.0
    step_count = 0
    
    while current_time < total_time:
        # 执行一步仿真
        harness.step()
        
        # 在仿真步骤之后应用扰动（因为harness.step()会重置入流）
        if 1.0 <= current_time <= 11.0:  # 1-11秒期间应用扰动
            if step_count % 4 == 0:  # 每4步记录一次扰动应用
                new_inflow = 150.0  # 增加到150 m³/s
                upstream_reservoir.set_inflow(new_inflow)
                print(f"t={current_time:.1f}s: 手动应用入流扰动，新入流={new_inflow:.1f} m³/s")
        elif current_time > 11.0:
            # 扰动结束，恢复原始入流
            if step_count % 4 == 0:
                original_inflow = 100.0
                upstream_reservoir.set_inflow(original_inflow)
                print(f"t={current_time:.1f}s: 扰动结束，恢复入流={original_inflow:.1f} m³/s")
        
        # 记录关键状态
        if step_count % 4 == 0:  # 每4步记录一次
            water_level = upstream_reservoir.get_state()['water_level']
            current_inflow = upstream_reservoir._inflow
            print(f"t={current_time:.1f}s: 入流={current_inflow:.1f} m³/s, 水位={water_level:.3f} m")
        
        current_time = harness.t
        step_count += 1
        
        # 防止无限循环
        if step_count > 100:
            break
    
    print(f"\n仿真完成!")
    final_state = upstream_reservoir.get_state()
    print(f"最终状态:")
    print(f"- 最终入流: {upstream_reservoir._inflow} m³/s")
    print(f"- 最终水位: {final_state['water_level']:.3f} m")
    
    # 检查水位是否发生了变化
    initial_water_level = 15.0
    final_water_level = final_state['water_level']
    water_level_change = abs(final_water_level - initial_water_level)
    
    if water_level_change > 0.001:  # 如果水位变化超过1mm
        print(f"✅ 入流扰动成功影响了物理计算核心!")
        print(f"   水位变化: {water_level_change:.6f} m")
    else:
        print(f"❌ 入流扰动未能明显影响物理计算核心")
        print(f"   水位变化: {water_level_change:.6f} m")
    
    # 额外验证：检查仿真历史
    if hasattr(harness, 'history') and len(harness.history) > 0:
        print(f"\n仿真历史记录:")
        print(f"- 总步数: {len(harness.history)}")
        if len(harness.history) >= 2:
            first_step = harness.history[0]
            last_step = harness.history[-1]
            if 'Upstream_Reservoir' in first_step and 'Upstream_Reservoir' in last_step:
                initial_level = first_step['Upstream_Reservoir']['water_level']
                final_level = last_step['Upstream_Reservoir']['water_level']
                print(f"- 历史记录中的水位变化: {initial_level:.3f} -> {final_level:.3f} m")

if __name__ == '__main__':
    test_simple_inflow_disturbance()