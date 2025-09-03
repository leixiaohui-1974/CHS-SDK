#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强入流扰动测试
使用足够大的扰动来验证扰动功能确实有效
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder
import time

def test_strong_inflow_disturbance():
    print("=== 强入流扰动测试 ===")
    
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
    
    # 计算理论水位变化（使用强扰动）
    surface_area = 1000000  # 100万平方米（从之前的测试得出）
    inflow_increase = 5000.0  # 大幅增加入流：从100增加到5100 m³/s
    disturbance_duration = 10.0  # 10秒扰动
    volume_increase = inflow_increase * disturbance_duration  # 额外体积
    theoretical_level_change = volume_increase / surface_area
    
    print(f"\n强扰动设计:")
    print(f"- 入流增加: {inflow_increase} m³/s (从100增加到{100+inflow_increase} m³/s)")
    print(f"- 扰动持续时间: {disturbance_duration} s")
    print(f"- 额外体积: {volume_increase} m³")
    print(f"- 理论水位变化: {theoretical_level_change:.3f} m")
    
    print(f"\n开始仿真，应用强入流扰动...")
    
    # 运行仿真并手动应用强扰动
    total_time = 20.0  # 总仿真时间
    current_time = 0.0
    step_count = 0
    dt = harness.dt
    
    # 记录初始水位
    initial_water_level = upstream_reservoir.get_state()['water_level']
    water_levels = [initial_water_level]
    times = [0.0]
    
    while current_time < total_time:
        # 执行一步仿真
        harness.step()
        
        # 在仿真步骤之后应用强扰动
        if 2.0 <= current_time <= 12.0:  # 2-12秒期间应用强扰动
            new_inflow = 100.0 + inflow_increase  # 大幅增加入流
            upstream_reservoir.set_inflow(new_inflow)
            if step_count % 2 == 0:  # 每2步记录一次
                print(f"t={current_time:.1f}s: 应用强扰动，入流={new_inflow:.0f} m³/s")
        elif current_time > 12.0:
            # 扰动结束，恢复原始入流
            original_inflow = 100.0
            upstream_reservoir.set_inflow(original_inflow)
            if current_time <= 13.0 and step_count % 2 == 0:
                print(f"t={current_time:.1f}s: 扰动结束，恢复入流={original_inflow:.0f} m³/s")
        
        # 记录关键状态
        if step_count % 2 == 0:  # 每2步记录一次
            water_level = upstream_reservoir.get_state()['water_level']
            current_inflow = upstream_reservoir._inflow
            water_levels.append(water_level)
            times.append(current_time)
            print(f"t={current_time:.1f}s: 入流={current_inflow:.0f} m³/s, 水位={water_level:.6f} m")
        
        current_time += dt
        step_count += 1
    
    # 分析结果
    final_water_level = upstream_reservoir.get_state()['water_level']
    final_inflow = upstream_reservoir._inflow
    
    print(f"\n仿真完成!")
    print(f"最终状态:")
    print(f"- 最终入流: {final_inflow} m³/s")
    print(f"- 最终水位: {final_water_level:.6f} m")
    
    # 计算实际水位变化
    max_water_level = max(water_levels)
    min_water_level = min(water_levels)
    actual_level_change = max_water_level - initial_water_level
    
    print(f"\n水位变化分析:")
    print(f"- 初始水位: {initial_water_level:.6f} m")
    print(f"- 最高水位: {max_water_level:.6f} m")
    print(f"- 最低水位: {min_water_level:.6f} m")
    print(f"- 实际最大水位变化: {actual_level_change:.6f} m ({actual_level_change*1000:.3f} mm)")
    print(f"- 理论水位变化: {theoretical_level_change:.6f} m ({theoretical_level_change*1000:.3f} mm)")
    
    if actual_level_change > 0.001:  # 如果水位变化超过1毫米
        print(f"\n✅ 强入流扰动成功影响了物理计算核心!")
        print(f"   水位变化: {actual_level_change:.6f} m")
        return True
    else:
        print(f"\n❌ 即使使用强扰动，水位变化仍然很小")
        print(f"   实际变化: {actual_level_change*1000:.3f} mm")
        return False

if __name__ == '__main__':
    test_strong_inflow_disturbance()