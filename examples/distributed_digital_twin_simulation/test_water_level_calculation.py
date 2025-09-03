#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水位变化计算测试
验证理论计算是否正确
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder

def test_water_level_calculation():
    print("=== 水位变化计算测试 ===")
    
    # 构建仿真
    builder = SimulationBuilder('.')
    harness = builder.load()
    
    # 获取上游水库
    upstream_reservoir = harness.components.get('Upstream_Reservoir')
    if not upstream_reservoir:
        print("❌ 未找到Upstream_Reservoir组件")
        return
    
    # 获取水库参数
    initial_state = upstream_reservoir.get_state()
    parameters = upstream_reservoir.get_parameters()
    
    print(f"\n水库参数:")
    print(f"- 初始水位: {initial_state['water_level']} m")
    print(f"- 初始体积: {initial_state['volume']} m³")
    print(f"- 表面积: {parameters.get('surface_area', '未定义')} m²")
    print(f"- 库容曲线: {parameters.get('storage_curve', '未定义')}")
    
    # 如果有库容曲线，计算表面积
    storage_curve = parameters.get('storage_curve')
    if storage_curve:
        print(f"\n库容曲线分析:")
        for i, (volume, level) in enumerate(storage_curve):
            print(f"  点{i+1}: 体积={volume} m³, 水位={level} m")
        
        # 计算当前水位对应的表面积（近似）
        current_level = initial_state['water_level']
        current_volume = initial_state['volume']
        
        # 找到相邻的两个点进行插值
        for i in range(len(storage_curve) - 1):
            v1, l1 = storage_curve[i]
            v2, l2 = storage_curve[i + 1]
            if l1 <= current_level <= l2:
                # 计算该段的平均表面积
                if l2 != l1:
                    avg_surface_area = (v2 - v1) / (l2 - l1)
                    print(f"  当前水位段({l1}-{l2}m)的平均表面积: {avg_surface_area:.0f} m²")
                    
                    # 计算扰动的理论水位变化
                    inflow_increase = 50.0  # 从100增加到150 m³/s
                    disturbance_duration = 10.0  # 10秒扰动
                    volume_increase = inflow_increase * disturbance_duration  # 额外体积
                    theoretical_level_change = volume_increase / avg_surface_area
                    
                    print(f"\n扰动分析:")
                    print(f"- 入流增加: {inflow_increase} m³/s")
                    print(f"- 扰动持续时间: {disturbance_duration} s")
                    print(f"- 额外体积: {volume_increase} m³")
                    print(f"- 理论水位变化: {theoretical_level_change:.6f} m")
                    print(f"- 理论水位变化: {theoretical_level_change*1000:.3f} mm")
                    
                    if theoretical_level_change < 0.001:
                        print(f"\n⚠️  水位变化太小（{theoretical_level_change*1000:.3f} mm），可能无法在仿真中观察到！")
                        print(f"   建议：")
                        print(f"   1. 增加扰动强度（更大的入流变化）")
                        print(f"   2. 延长扰动时间")
                        print(f"   3. 使用更小的水库或更高精度的输出")
                    else:
                        print(f"\n✅ 水位变化足够大，应该能在仿真中观察到")
                break
    else:
        print("\n❌ 未找到库容曲线，无法计算表面积")

if __name__ == '__main__':
    test_water_level_calculation()