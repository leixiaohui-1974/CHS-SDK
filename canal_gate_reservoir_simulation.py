#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渠道-闸门-渠道-水库仿真系统
基于core_lib实现水利系统仿真

系统组成：
渠道1 -> 闸门 -> 渠道2 -> 水库

作者: CHS-SDK Team
创建时间: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from typing import Dict, Any, Optional, List
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory
from core_lib.core_engine.testing.component_types import (
    ComponentConfig, ComponentType, DeviceLevel, InfrastructureConfig, 
    DeviceConfig
)
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.core.event_bus import get_global_event_bus
from core_lib.core_engine.testing.common_agents import ScheduledEventAgent


def create_canal_gate_canal_reservoir_system(config: Optional[Dict[str, Any]] = None) -> SimulationHarness:
    """
    创建渠道-闸门-渠道-水库系统
    
    系统拓扑：
    渠道1 -> 闸门 -> 渠道2 -> 水库
    
    Args:
        config: 仿真配置
        
    Returns:
        配置好的SimulationHarness实例
    """
    # 默认配置
    default_config = {
        'start_time': 0,
        'end_time': 3600,  # 1小时仿真
        'time_step': 10.0   # 10秒时间步长
    }
    
    final_config = config or default_config
    final_config.update(default_config)  # 确保必要参数存在
    
    print("=== 创建渠道-闸门-渠道-水库仿真系统 ===\n")
    
    # 使用统一组件工厂创建系统
    harness = SimulationHarness(final_config)
    factory = UnifiedComponentFactory()
    
    # 添加上游渠道
    upstream_canal_config = InfrastructureConfig(
        component_id="upstream_canal",
        component_type=ComponentType.CANAL,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'model_type': 'integral_delay', 'water_level': 3.0, 'gain': 0.002, 'delay': 120.0}
    )
    upstream_canal = factory.create_component(upstream_canal_config)
    harness.add_component("upstream_canal", upstream_canal)
    
    # 添加控制闸门
    gate_config = DeviceConfig(
        component_id="control_gate",
        component_type=ComponentType.GATE,
        level=DeviceLevel.DEVICE,
        parameters={'opening': 0.6, 'max_flow_rate': 50.0}
    )
    gate = factory.create_component(gate_config)
    harness.add_component("control_gate", gate)
    
    # 添加下游渠道
    downstream_canal_config = InfrastructureConfig(
        component_id="downstream_canal",
        component_type=ComponentType.CANAL,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'model_type': 'linear_reservoir', 'water_level': 2.5, 'gain': 0.001}
    )
    downstream_canal = factory.create_component(downstream_canal_config)
    harness.add_component("downstream_canal", downstream_canal)
    
    # 添加终端水库
    reservoir_config = InfrastructureConfig(
        component_id="terminal_reservoir",
        component_type=ComponentType.RESERVOIR,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'water_level': 10.0, 'surface_area': 50000}
    )
    reservoir = factory.create_component(reservoir_config)
    harness.add_component("terminal_reservoir", reservoir)
    
    # 连接组件
    harness.add_connection("upstream_canal", "control_gate")
    harness.add_connection("control_gate", "downstream_canal")
    harness.add_connection("downstream_canal", "terminal_reservoir")
    
    print("=== 系统拓扑连接完成 ===")
    print("连接关系:")
    print("  upstream_canal -> control_gate")
    print("  control_gate -> downstream_canal")
    print("  downstream_canal -> terminal_reservoir")
    
    return harness


def create_gate_control_agent() -> ScheduledEventAgent:
    """
    创建闸门控制智能体
    
    模拟真实的闸门操作场景：
    - 初始保持60%开度
    - 30分钟后调整到80%开度
    - 45分钟后调整到40%开度
    
    Returns:
        配置好的ScheduledEventAgent
    """
    # 定义闸门控制事件 - 转换为ScheduledEventAgent需要的格式
    control_events: Dict[float, Dict[str, Any]] = {
        0: {      # 0分钟：初始设置
            'topic': 'action.control_gate',
            'data': {'opening': 0.6, 'description': '初始开度60%'}
        },
        1800: {   # 30分钟：增加开度
            'topic': 'action.control_gate', 
            'data': {'opening': 0.8, 'description': '调整开度至80%'}
        },
        2700: {   # 45分钟：减少开度
            'topic': 'action.control_gate',
            'data': {'opening': 0.4, 'description': '调整开度至40%'}
        }
    }
    
    # 创建调度事件智能体
    agent = ScheduledEventAgent(
        agent_id="gate_controller",
        events=control_events,
        message_bus=get_global_event_bus()
    )
    
    print("=== 创建闸门控制智能体 ===")
    print("控制计划:")
    for event_time, event_data in control_events.items():
        time_min = int(event_time) // 60
        opening = event_data['data']['opening']
        print(f"  {time_min:2d}分钟: 闸门开度 {opening*100:3.0f}%")
    
    return agent


def create_inflow_disturbance_agent() -> ScheduledEventAgent:
    """
    创建入流扰动智能体
    
    模拟自然水流变化：
    - 初始15 m³/s
    - 20分钟后增加到25 m³/s 
    - 40分钟后减少到10 m³/s
    
    Returns:
        配置好的ScheduledEventAgent
    """
    # 定义入流扰动事件 - 转换为ScheduledEventAgent需要的格式
    inflow_events: Dict[float, Dict[str, Any]] = {
        0: {
            'topic': 'inflow.upstream_canal',
            'data': {'inflow': 15.0, 'description': '正常入流'}
        },
        1200: {   # 20分钟
            'topic': 'inflow.upstream_canal',
            'data': {'inflow': 25.0, 'description': '洪峰期入流增加'}
        },
        2400: {   # 40分钟
            'topic': 'inflow.upstream_canal', 
            'data': {'inflow': 10.0, 'description': '枯水期入流减少'}
        }
    }
    
    agent = ScheduledEventAgent(
        agent_id="inflow_controller",
        events=inflow_events,
        message_bus=get_global_event_bus()
    )
    
    print("=== 创建入流扰动智能体 ===")
    print("入流变化计划:")
    for event_time, event_data in inflow_events.items():
        time_min = int(event_time) // 60
        inflow = event_data['data']['inflow']
        print(f"  {time_min:2d}分钟: 入流 {inflow:4.1f} m³/s")
        
    return agent


def run_simulation():
    """
    运行渠道-闸门-渠道-水库仿真
    """
    print("\\n" + "="*60)
    print("  渠道-闸门-渠道-水库仿真系统")
    print("="*60)
    
    try:
        # 1. 创建仿真系统
        config = {
            'start_time': 0,
            'end_time': 3600,    # 1小时
            'time_step': 30.0    # 30秒时间步
        }
        
        builder = create_canal_gate_canal_reservoir_system(config)
        
        # 2. 添加控制智能体
        gate_agent = create_gate_control_agent()
        inflow_agent = create_inflow_disturbance_agent()
        
        builder.add_agent(gate_agent)
        builder.add_agent(inflow_agent)
        
        # 3. 构建仿真环境
        print("\\n=== 构建仿真环境 ===")
        builder.build()
        
        # 4. 打印初始状态
        print("\\n=== 初始系统状态 ===")
        builder.print_final_states()
        
        # 5. 运行仿真
        print("\\n=== 开始仿真 ===")
        print(f"仿真时间: {config['start_time']}s - {config['end_time']}s")
        print(f"时间步长: {config['time_step']}s")
        print("仿真进行中...")
        
        # 运行多智能体仿真
        builder.run_mas_simulation()
        
        # 6. 分析结果
        print("\\n=== 仿真结果分析 ===")
        analyze_simulation_results(builder)
        
        # 7. 导出数据（如果配置了输出）
        history = builder.get_history()
        if history:
            export_simulation_data(history, "canal_gate_reservoir_simulation.csv")
        
        print("\\n=== 仿真完成 ===")
        return builder
        
    except Exception as e:
        print(f"\\n❌ 仿真执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def analyze_simulation_results(builder: SimulationHarness):
    """
    分析仿真结果
    
    Args:
        builder: 仿真构建器实例
    """
    history = builder.history
    
    if not history:
        print("没有仿真历史数据")
        return
    
    print(f"仿真步数: {len(history)}")
    
    # 获取最终状态
    final_state = history[-1] if history else {}
    
    print("\\n最终系统状态:")
    components = ['upstream_canal', 'control_gate', 'downstream_canal', 'terminal_reservoir']
    
    for comp_id in components:
        if comp_id in final_state:
            state = final_state[comp_id]
            print(f"  {comp_id}:")
            
            if 'water_level' in state:
                print(f"    水位: {state['water_level']:.2f} m")
            if 'outflow' in state:
                print(f"    出流: {state['outflow']:.2f} m³/s")
            if 'opening' in state:
                print(f"    开度: {state['opening']*100:.1f}%")
            if 'volume' in state:
                print(f"    水量: {state['volume']:.0f} m³")
    
    # 计算一些统计信息
    if len(history) > 1:
        print("\\n系统性能指标:")
        
        # 水库水位变化
        initial_reservoir_level = history[0].get('terminal_reservoir', {}).get('water_level', 0)
        final_reservoir_level = final_state.get('terminal_reservoir', {}).get('water_level', 0)
        level_change = final_reservoir_level - initial_reservoir_level
        
        print(f"  水库水位变化: {level_change:+.2f} m")
        
        # 平均流量
        total_outflow = sum(step.get('upstream_canal', {}).get('outflow', 0) 
                          for step in history)
        avg_outflow = total_outflow / len(history) if history else 0
        print(f"  上游渠道平均出流: {avg_outflow:.2f} m³/s")


def export_simulation_data(history: List[Dict[str, Any]], filename: str):
    """
    导出仿真数据到CSV文件
    
    Args:
        history: 仿真历史数据
        filename: 输出文件名
    """
    try:
        import pandas as pd
        
        # 展平历史数据
        flattened_data = []
        
        for step in history:
            row = {'time': step['time']}
            
            for comp_id, comp_state in step.items():
                if comp_id == 'time':
                    continue
                if isinstance(comp_state, dict):
                    for state_key, state_value in comp_state.items():
                        column_name = f"{comp_id}_{state_key}"
                        row[column_name] = state_value
            
            flattened_data.append(row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False)
        
        print(f"\\n📊 仿真数据已导出至: {filename}")
        print(f"   数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
        
    except ImportError:
        print("\\n⚠️  未安装pandas，跳过数据导出")
    except Exception as e:
        print(f"\\n⚠️  数据导出失败: {str(e)}")


def print_system_architecture():
    """
    打印系统架构信息
    """
    print("\\n" + "="*60)
    print("          系统架构说明")
    print("="*60)
    print("""
    系统组成:
    ┌─────────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────────┐
    │             │    │          │    │              │    │             │
    │  上游渠道   │────│  控制闸门  │────│   下游渠道   │────│   末端水库  │
    │             │    │          │    │              │    │             │
    └─────────────┘    └──────────┘    └──────────────┘    └─────────────┘
    
    组件说明:
    • 上游渠道: 积分延迟模型，模拟渠道水流传输延迟
    • 控制闸门: 可调节开度，控制通过流量
    • 下游渠道: 线性储水库模型，平滑流量波动  
    • 末端水库: 储存水量，监测水位变化
    
    智能体:
    • 闸门控制智能体: 按时间表调节闸门开度
    • 入流扰动智能体: 模拟自然入流变化
    
    基于技术:
    • core_lib框架: 统一的物理对象接口
    • core_engine: 仿真生命周期管理
    • 事件总线: 组件间消息通信
    """)


if __name__ == "__main__":
    # 打印系统架构
    print_system_architecture()
    
    # 运行仿真
    simulation_result = run_simulation()
    
    if simulation_result:
        print("\\n🎉 仿真成功完成!")
        print("\\n💡 提示: 可以调整配置参数来探索不同的系统行为")
    else:
        print("\\n❌ 仿真执行失败")
        sys.exit(1)