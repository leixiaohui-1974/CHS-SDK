#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试扰动功能 - 修复harness自动入流覆盖问题
通过临时修改harness的_step_physical_models方法来避免扰动期间入流被覆盖
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.io.yaml_loader import SimulationBuilder
import json
import time

def load_simulation_harness():
    """使用SimulationBuilder加载仿真配置"""
    scenario_path = os.path.dirname(__file__)
    
    loader = SimulationBuilder(scenario_path)
    
    return loader.load()

def patch_harness_for_disturbance(harness, disturbed_component_id, disturbance_active_flag):
    """为harness打补丁，在扰动期间跳过自动入流设置"""
    original_step_physical_models = harness._step_physical_models
    
    def patched_step_physical_models(dt, controller_actions=None):
        if controller_actions is None:
            controller_actions = {}

        new_states = {}
        current_step_outflows = {}

        for component_id in harness.sorted_components:
            component = harness.components[component_id]
            action = {'control_signal': controller_actions.get(component_id)}

            # 只有在非扰动期间或非扰动组件时才自动设置入流
            if not (disturbance_active_flag['active'] and component_id == disturbed_component_id):
                total_inflow = 0
                for upstream_id in harness.inverse_topology.get(component_id, []):
                    total_inflow += current_step_outflows.get(upstream_id, 0)
                component.set_inflow(total_inflow)

            if hasattr(component, 'is_stateful') and component.is_stateful:
                total_outflow = 0
                for downstream_id in harness.topology.get(component_id, []):
                    downstream_comp = harness.components[downstream_id]
                    downstream_action = {}
                    downstream_action['upstream_head'] = component.get_state().get('water_level', 0)

                    if harness.topology.get(downstream_id):
                        dds_id = harness.topology[downstream_id][0]
                        downstream_action['downstream_head'] = harness.components[dds_id].get_state().get('water_level', 0)

                    import copy
                    temp_downstream_comp = copy.deepcopy(downstream_comp)

                    temp_next_state = temp_downstream_comp.step(downstream_action, dt)
                    total_outflow += temp_next_state.get('outflow', 0)

                action['outflow'] = total_outflow

            else:
                if harness.inverse_topology.get(component_id):
                    up_id = harness.inverse_topology[component_id][0]
                    action['upstream_head'] = harness.components[up_id].get_state().get('water_level', 0)
                if harness.topology.get(component_id):
                    down_id = harness.topology[component_id][0]
                    action['downstream_head'] = harness.components[down_id].get_state().get('water_level', 0)

            new_states[component_id] = component.step(action, dt)
            current_step_outflows[component_id] = new_states[component_id].get('outflow', 0)

        for component_id, state in new_states.items():
            harness.components[component_id].set_state(state)
    
    # 替换方法
    harness._step_physical_models = patched_step_physical_models
    return original_step_physical_models

def main():
    print("=== 测试扰动功能 - 修复harness自动入流覆盖问题 ===")
    
    # 加载仿真harness
    harness = load_simulation_harness()
    
    # 获取上游水库
    upstream_reservoir = harness.components.get('Upstream_Reservoir')
    if not upstream_reservoir:
        print("错误：未找到上游水库组件")
        print(f"可用组件: {list(harness.components.keys())}")
        return
    
    # 记录初始状态
    initial_state = upstream_reservoir.get_state()
    initial_water_level = initial_state.get('water_level', 0)
    initial_volume = initial_state.get('volume', 0)
    initial_inflow = getattr(upstream_reservoir, '_inflow', 0)
    
    print(f"初始状态:")
    print(f"  水位: {initial_water_level:.3f} m")
    print(f"  体积: {initial_volume:.0f} m³")
    print(f"  入流: {initial_inflow:.1f} m³/s")
    
    # 扰动参数
    disturbance_start_time = 5.0  # 5秒后开始扰动
    disturbance_duration = 10.0   # 扰动持续10秒
    original_inflow = initial_inflow
    disturbed_inflow = original_inflow + 5000.0  # 增加5000 m³/s
    
    print(f"\n扰动计划:")
    print(f"  开始时间: {disturbance_start_time:.1f}s")
    print(f"  持续时间: {disturbance_duration:.1f}s")
    print(f"  原始入流: {original_inflow:.1f} m³/s")
    print(f"  扰动入流: {disturbed_inflow:.1f} m³/s")
    
    # 理论计算
    delta_inflow = disturbed_inflow - original_inflow
    delta_volume = delta_inflow * disturbance_duration
    surface_area = 1000000  # 假设表面积1,000,000 m²
    theoretical_water_level_change = delta_volume / surface_area
    
    print(f"\n理论计算:")
    print(f"  入流增量: {delta_inflow:.1f} m³/s")
    print(f"  体积增量: {delta_volume:.0f} m³")
    print(f"  理论水位变化: {theoretical_water_level_change:.3f} m = {theoretical_water_level_change*1000:.0f} mm")
    
    # 设置扰动标志
    disturbance_active_flag = {'active': False}
    
    # 为harness打补丁
    original_method = patch_harness_for_disturbance(harness, 'Upstream_Reservoir', disturbance_active_flag)
    
    # 仿真参数
    dt = 0.1  # 时间步长
    total_time = 20.0  # 总仿真时间
    steps = int(total_time / dt)
    
    print(f"\n开始仿真 (dt={dt}s, 总时间={total_time}s, 步数={steps})...")
    
    # 记录数据
    time_data = []
    water_level_data = []
    inflow_data = []
    
    for step in range(steps):
        current_time = step * dt
        
        # 检查是否需要应用扰动
        if disturbance_start_time <= current_time < disturbance_start_time + disturbance_duration:
            if not disturbance_active_flag['active']:
                print(f"\n时间 {current_time:.1f}s: 开始应用扰动")
                disturbance_active_flag['active'] = True
                upstream_reservoir.set_inflow(disturbed_inflow)
                print(f"  设置入流为: {disturbed_inflow:.1f} m³/s")
        elif current_time >= disturbance_start_time + disturbance_duration:
            if disturbance_active_flag['active']:
                print(f"\n时间 {current_time:.1f}s: 结束扰动")
                disturbance_active_flag['active'] = False
                upstream_reservoir.set_inflow(original_inflow)
                print(f"  恢复入流为: {original_inflow:.1f} m³/s")
        
        # 执行仿真步骤
        harness.step()
        
        # 记录数据
        current_state = upstream_reservoir.get_state()
        current_water_level = current_state.get('water_level', 0)
        current_inflow = getattr(upstream_reservoir, '_inflow', 0)
        
        time_data.append(current_time)
        water_level_data.append(current_water_level)
        inflow_data.append(current_inflow)
        
        # 每秒输出一次状态
        if step % int(1.0/dt) == 0:
            water_level_change = current_water_level - initial_water_level
            print(f"时间 {current_time:5.1f}s: 水位={current_water_level:.6f}m, 变化={water_level_change*1000:+7.3f}mm, 入流={current_inflow:.1f}m³/s")
    
    # 恢复原始方法
    harness._step_physical_models = original_method
    
    # 最终结果
    final_state = upstream_reservoir.get_state()
    final_water_level = final_state.get('water_level', 0)
    actual_water_level_change = final_water_level - initial_water_level
    
    print(f"\n=== 最终结果 ===")
    print(f"初始水位: {initial_water_level:.6f} m")
    print(f"最终水位: {final_water_level:.6f} m")
    print(f"实际水位变化: {actual_water_level_change:.6f} m = {actual_water_level_change*1000:.3f} mm")
    print(f"理论水位变化: {theoretical_water_level_change:.6f} m = {theoretical_water_level_change*1000:.3f} mm")
    
    if abs(actual_water_level_change) > 0.001:  # 1mm
        print("✅ 扰动成功！水位发生了明显变化")
    else:
        print("❌ 扰动失败：水位变化太小或为零")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()