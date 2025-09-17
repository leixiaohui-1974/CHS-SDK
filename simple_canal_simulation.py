#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版渠道-闸门-渠道-水库仿真系统
基于core_lib实现，避免序列化问题

系统组成：
渠道1 -> 闸门 -> 渠道2 -> 水库

作者: CHS-SDK Team
创建时间: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from typing import Dict, Any
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir


def create_simple_canal_system():
    """
    创建简化的渠道-闸门-渠道-水库系统
    """
    print("=== 创建简化仿真系统 ===")
    
    # 仿真配置
    config = {
        'start_time': 0,
        'end_time': 1800,    # 30分钟
        'time_step': 60.0    # 1分钟时间步
    }
    
    # 创建仿真框架
    harness = SimulationHarness(config)
    
    print(f"仿真时间: {config['start_time']}s - {config['end_time']}s")
    print(f"时间步长: {config['time_step']}s")
    
    # 1. 创建上游渠道
    upstream_canal = UnifiedCanal(
        name="upstream_canal",
        initial_state={
            'water_level': 3.0,
            'inflow': 20.0,
            'outflow': 0.0
        },
        parameters={
            'model_type': 'integral_delay',
            'gain': 0.002,
            'delay': 120.0,  # 2分钟延迟
        }
    )
    harness.add_component("upstream_canal", upstream_canal)
    print("✓ 上游渠道创建完成")
    
    # 2. 创建控制闸门
    control_gate = Gate(
        name="control_gate",
        initial_state={'opening': 0.5, 'outflow': 0},
        parameters={
            'max_flow_rate': 30.0,
            'discharge_coefficient': 0.6,
            'width': 2.0
        }
    )
    harness.add_component("control_gate", control_gate)
    print("✓ 控制闸门创建完成")
    
    # 3. 创建下游渠道
    downstream_canal = UnifiedCanal(
        name="downstream_canal", 
        initial_state={
            'water_level': 2.0,
            'inflow': 0.0,
            'outflow': 0.0
        },
        parameters={
            'model_type': 'linear_reservoir',
            'storage_constant': 600.0,
            'level_storage_ratio': 0.01
        }
    )
    harness.add_component("downstream_canal", downstream_canal)
    print("✓ 下游渠道创建完成")
    
    # 4. 创建末端水库
    terminal_reservoir = Reservoir(
        name="terminal_reservoir",
        initial_state={
            'water_level': 10.0,
            'volume': 1000000.0,  # 100万m³
            'outflow': 0
        },
        parameters={'surface_area': 100000.0}  # 10万m²
    )
    harness.add_component("terminal_reservoir", terminal_reservoir)
    print("✓ 末端水库创建完成")
    
    # 5. 连接组件
    connections = [
        ("upstream_canal", "control_gate"),
        ("control_gate", "downstream_canal"),
        ("downstream_canal", "terminal_reservoir")
    ]
    
    for upstream, downstream in connections:
        harness.add_connection(upstream, downstream)
        print(f"✓ 连接: {upstream} -> {downstream}")
    
    return harness


def run_simple_simulation():
    """
    运行简化仿真
    """
    print("\\n" + "="*60)
    print("   简化版渠道-闸门-渠道-水库仿真")
    print("="*60)
    
    try:
        # 创建仿真系统
        harness = create_simple_canal_system()
        
        # 构建仿真
        print("\\n=== 构建仿真环境 ===")
        harness.build()
        print("✓ 仿真环境构建完成")
        
        # 打印初始状态
        print("\\n=== 初始系统状态 ===")
        print_system_state(harness, 0)
        
        # 运行仿真（简单模式，不使用智能体）
        print("\\n=== 开始仿真 ===")
        
        # 手动控制仿真循环
        time_step = harness.time_step
        current_time = harness.start_time
        
        history = []
        step_count = 0
        
        while current_time < harness.end_time:
            step_count += 1
            
            # 创建控制动作（模拟闸门控制）
            actions = create_control_actions(current_time)
            
            # 手动步进物理模型
            step_physical_models_manually(harness, time_step, actions)
            
            # 记录历史
            step_data = {'time': current_time}
            for comp_id, component in harness.components.items():
                step_data[comp_id] = component.get_state().copy()
            history.append(step_data)
            
            # 打印进度（每5步打印一次）
            if step_count % 5 == 0:
                print(f"仿真进度: t={current_time:.0f}s ({step_count}步)")
                print_system_state(harness, current_time)
            
            current_time += time_step
        
        print("\\n=== 仿真完成 ===")
        print(f"总步数: {len(history)}")
        
        # 分析结果
        analyze_results(history)
        
        return history
        
    except Exception as e:
        print(f"\\n❌ 仿真执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_control_actions(current_time: float) -> Dict[str, Any]:
    """
    创建控制动作（模拟智能体行为）
    
    Args:
        current_time: 当前仿真时间
        
    Returns:
        控制动作字典
    """
    # 简单的时间基控制策略
    if current_time < 600:  # 前10分钟
        gate_opening = 0.5
    elif current_time < 1200:  # 10-20分钟
        gate_opening = 0.8
    else:  # 20分钟后
        gate_opening = 0.3
    
    return {
        'control_gate': {
            'control_signal': gate_opening
        }
    }


def step_physical_models_manually(harness, time_step: float, actions: Dict[str, Any]):
    """
    手动步进物理模型，避免序列化问题
    
    Args:
        harness: 仿真框架
        time_step: 时间步长
        actions: 控制动作
    """
    # 按拓扑顺序更新组件
    for comp_id in harness.sorted_components:
        component = harness.components[comp_id]
        
        # 计算上游入流
        upstream_outflow = 0.0
        if comp_id in harness.inverse_topology:
            for upstream_id in harness.inverse_topology[comp_id]:
                upstream_comp = harness.components[upstream_id]
                upstream_state = upstream_comp.get_state()
                upstream_outflow += upstream_state.get('outflow', 0.0)
        
        # 设置入流
        component.set_inflow(upstream_outflow)
        
        # 准备动作参数
        action = actions.get(comp_id, {})
        
        # 对于闸门，需要提供水位信息
        if comp_id == 'control_gate':
            # 获取上游水位
            upstream_level = 0.0
            if 'upstream_canal' in harness.components:
                upstream_state = harness.components['upstream_canal'].get_state()
                upstream_level = upstream_state.get('water_level', 0.0)
            
            # 获取下游水位
            downstream_level = 0.0
            if 'downstream_canal' in harness.components:
                downstream_state = harness.components['downstream_canal'].get_state()
                downstream_level = downstream_state.get('water_level', 0.0)
            
            action.update({
                'upstream_head': upstream_level,
                'downstream_head': downstream_level
            })
        
        # 步进组件
        component.step(action, time_step)


def print_system_state(harness, current_time: float):
    """
    打印系统状态
    """
    print(f"\\n--- 系统状态 (t={current_time:.0f}s) ---")
    
    components = ['upstream_canal', 'control_gate', 'downstream_canal', 'terminal_reservoir']
    
    for comp_id in components:
        if comp_id in harness.components:
            component = harness.components[comp_id]
            state = component.get_state()
            
            print(f"  {comp_id}:")
            if 'water_level' in state:
                print(f"    水位: {state['water_level']:.2f} m")
            if 'opening' in state:
                print(f"    开度: {state['opening']*100:.1f}%")
            if 'outflow' in state:
                print(f"    出流: {state['outflow']:.2f} m³/s")
            if 'volume' in state:
                print(f"    水量: {state['volume']:.0f} m³")


def analyze_results(history):
    """
    分析仿真结果
    """
    print("\\n=== 结果分析 ===")
    
    if not history:
        print("没有历史数据")
        return
    
    # 水库水位变化
    initial_level = history[0]['terminal_reservoir']['water_level'] 
    final_level = history[-1]['terminal_reservoir']['water_level']
    level_change = final_level - initial_level
    
    print(f"水库水位变化: {level_change:+.2f} m")
    
    # 平均流量统计
    total_inflow = sum(step['upstream_canal']['outflow'] for step in history)
    avg_inflow = total_inflow / len(history)
    print(f"上游渠道平均出流: {avg_inflow:.2f} m³/s")
    
    # 闸门开度统计
    openings = [step['control_gate']['opening'] for step in history]
    avg_opening = sum(openings) / len(openings) * 100
    print(f"闸门平均开度: {avg_opening:.1f}%")
    
    # 系统效率（粗略估算）
    final_reservoir_volume = history[-1]['terminal_reservoir']['volume']
    initial_reservoir_volume = history[0]['terminal_reservoir']['volume']
    volume_increase = final_reservoir_volume - initial_reservoir_volume
    
    print(f"水库蓄水增量: {volume_increase:.0f} m³")


def export_simple_results(history, filename="simple_simulation_results.csv"):
    """
    导出简化结果
    """
    try:
        import pandas as pd
        
        # 准备数据
        data = []
        for step in history:
            row = {
                'time': step['time'],
                'upstream_canal_water_level': step['upstream_canal']['water_level'],
                'upstream_canal_outflow': step['upstream_canal']['outflow'],
                'control_gate_opening': step['control_gate']['opening'],
                'control_gate_outflow': step['control_gate']['outflow'],
                'downstream_canal_water_level': step['downstream_canal']['water_level'],
                'downstream_canal_outflow': step['downstream_canal']['outflow'],
                'terminal_reservoir_water_level': step['terminal_reservoir']['water_level'],
                'terminal_reservoir_volume': step['terminal_reservoir']['volume']
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"\\n📊 结果已导出至: {filename}")
        
    except ImportError:
        print("\\n⚠️  未安装pandas，跳过数据导出")


if __name__ == "__main__":
    print("\\n🚀 启动简化版仿真系统...")
    
    # 运行仿真
    results = run_simple_simulation()
    
    if results:
        print("\\n🎉 仿真成功完成!")
        
        # 导出结果
        export_simple_results(results)
        
        print("\\n💡 提示:")
        print("  - 这是一个简化版本，避免了复杂的智能体和事件总线")
        print("  - 系统展示了基本的水力学连接和控制逻辑")
        print("  - 可以基于这个版本进一步扩展功能")
    else:
        print("\\n❌ 仿真执行失败")
        sys.exit(1)