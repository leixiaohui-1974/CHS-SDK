#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 core_lib 原生架构的渠道-闸门-渠道-水库仿真系统

系统拓扑：
[上游渠道] --> [控制闸门] --> [下游渠道] --> [水库]

使用core_lib原生组件：
- UnifiedLocalControlAgent: 闸门控制
- SimulationHarness: 仿真执行
- 消息总线: 组件通信
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List

# 导入核心仿真组件
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.event_bus import get_global_event_bus

# 导入物理对象
from core_lib.physical_objects import UnifiedCanal, Gate, Reservoir

# 导入控制系统
from core_lib.core.new_agents.local_agents.control.unified_local_control import UnifiedLocalControlAgent
from core_lib.core.new_interfaces import DeviceType, ControlStrategy


def create_simulation_system():
    """创建仿真系统组件"""
    
    print("🏗️ 创建仿真系统组件...")
    
    # 创建消息总线
    message_bus = get_global_event_bus()
    
    # 1. 创建上游渠道 (提供恒定入流)
    upstream_canal = UnifiedCanal(
        name="upstream_canal",
        initial_state={
            'water_level': 3.0,
            'inflow': 25.0,    # 25 m³/s 恒定入流
            'outflow': 0.0
        },
        parameters={
            'model_type': 'integral',
            'surface_area': 8000.0,     # 8000 m² 表面积
            'outlet_coefficient': 2.5,   # 出流系数
        },
        message_bus=message_bus
    )
    
    # 2. 创建控制闸门 (支持消息总线控制)
    control_gate = Gate(
        name="control_gate",
        initial_state={
            'opening': 0.8,      # 初始开度 80%
            'outflow': 0.0
        },
        parameters={
            'max_opening': 1.0,           # 最大开度
            'discharge_coefficient': 0.7, # 流量系数
            'gate_width': 5.0,            # 闸门宽度 5m
            'max_rate_of_change': 0.1     # 最大变化率 10%/s
        },
        message_bus=message_bus,
        action_topic="gate_control"  # 控制主题
    )
    
    # 3. 创建下游渠道
    downstream_canal = UnifiedCanal(
        name="downstream_canal", 
        initial_state={
            'water_level': 2.5,
            'inflow': 0.0,
            'outflow': 0.0
        },
        parameters={
            'model_type': 'integral_delay',
            'gain': 0.001,               # 增益系数
            'delay': 120.0,              # 延迟 2分钟
        },
        message_bus=message_bus
    )
    
    # 4. 创建终端水库
    end_reservoir = Reservoir(
        name="end_reservoir",
        initial_state={
            'water_level': 10.0,      # 初始水位 10m
            'volume': 5000000.0       # 初始库容 500万 m³
        },
        parameters={
            'storage_curve': [         # 库容曲线 [库容(m³), 水位(m)]
                [0, 0],
                [2000000, 5],
                [5000000, 10], 
                [10000000, 15],
                [20000000, 25],
                [35000000, 35]
            ]
        },
        message_bus=message_bus
    )
    
    # 5. 创建闸门控制Agent (使用core_lib原生控制器)
    gate_control_config = {
        'target_component': 'control_gate',
        'control_topic': 'gate_control',
        'observation_topics': ['upstream_canal_state'],
        'control_strategy': 'rule_based',
        'control_parameters': {
            'high_level_threshold': 3.5,    # 高水位阈值
            'low_level_threshold': 2.5,     # 低水位阈值
            'high_opening': 0.9,            # 高水位时开度
            'normal_opening': 0.6,          # 正常开度
            'low_opening': 0.3,             # 低水位时开度
        }
    }
    
    gate_controller = UnifiedLocalControlAgent(
        agent_id="gate_controller",
        device_type=DeviceType.GATE,
        control_strategy=ControlStrategy.RULE_BASED,
        config=gate_control_config
    )
    
    components = {
        'upstream_canal': upstream_canal,
        'control_gate': control_gate,
        'downstream_canal': downstream_canal,
        'end_reservoir': end_reservoir
    }
    
    agents = [gate_controller]
    
    print(f"✅ 创建了 {len(components)} 个物理组件和 {len(agents)} 个控制Agent")
    return components, agents, message_bus


def create_control_strategy():
    """创建简单的时间驱动控制策略"""
    
    def time_based_control_strategy(current_time: float, upstream_state: Dict[str, Any]) -> float:
        """
        基于时间的闸门控制策略
        
        Args:
            current_time: 当前仿真时间
            upstream_state: 上游渠道状态
            
        Returns:
            闸门开度 (0-1)
        """
        water_level = upstream_state.get('water_level', 3.0)
        
        # 基于时间和水位的组合控制
        if current_time < 300:
            # 前5分钟：高流量运行
            base_opening = 0.8
        elif current_time < 600:
            # 5-10分钟：中流量运行
            base_opening = 0.5
        else:
            # 10分钟后：根据水位调节
            base_opening = 0.6
        
        # 根据水位微调
        if water_level > 3.5:
            opening = min(1.0, base_opening + 0.2)  # 水位高时增加开度
        elif water_level < 2.5:
            opening = max(0.1, base_opening - 0.3)  # 水位低时减小开度
        else:
            opening = base_opening
            
        return opening
    
    return time_based_control_strategy


def setup_simulation_with_native_control(components: Dict[str, Any], agents: List, message_bus):
    """使用原生控制系统设置仿真"""
    
    print("🔗 设置原生控制仿真系统...")
    
    # 仿真配置
    simulation_config = {
        'start_time': 0.0,
        'end_time': 900.0,        # 15分钟仿真
        'time_step': 5.0,         # 5秒时间步
    }
    
    # 创建仿真执行器
    harness = SimulationHarness(simulation_config)
    
    # 添加物理组件
    for name, component in components.items():
        harness.add_component(name, component)
        print(f"  - 添加组件: {name}")
    
    # 添加控制Agents
    for agent in agents:
        harness.add_agent(agent)
        print(f"  - 添加Agent: {agent.agent_id}")
    
    # 设置拓扑连接关系
    # 上游渠道 -> 闸门 -> 下游渠道 -> 水库
    connections = [
        ('upstream_canal', 'control_gate'),
        ('control_gate', 'downstream_canal'), 
        ('downstream_canal', 'end_reservoir')
    ]
    
    for upstream, downstream in connections:
        harness.add_connection(upstream, downstream)
        print(f"  - 连接: {upstream} -> {downstream}")
    
    # 设置状态广播 (让控制器能观测到上游状态)
    def setup_state_broadcast():
        """设置状态广播功能"""
        def broadcast_upstream_state():
            upstream_state = components['upstream_canal'].get_state()
            message_bus.publish('upstream_canal_state', upstream_state)
        
        return broadcast_upstream_state
    
    state_broadcaster = setup_state_broadcast()
    
    print("✅ 原生控制仿真系统设置完成")
    return harness, state_broadcaster


def setup_simple_message_control(components: Dict[str, Any], message_bus):
    """设置简单的消息控制（不依赖复杂Agent）"""
    
    print("🔗 设置简单消息控制...")
    
    # 仿真配置
    simulation_config = {
        'start_time': 0.0,
        'end_time': 900.0,        # 15分钟仿真
        'time_step': 5.0,         # 5秒时间步
    }
    
    # 创建仿真执行器
    harness = SimulationHarness(simulation_config)
    
    # 添加物理组件
    for name, component in components.items():
        harness.add_component(name, component)
        print(f"  - 添加组件: {name}")
    
    # 设置拓扑连接关系
    connections = [
        ('upstream_canal', 'control_gate'),
        ('control_gate', 'downstream_canal'), 
        ('downstream_canal', 'end_reservoir')
    ]
    
    for upstream, downstream in connections:
        harness.add_connection(upstream, downstream)
        print(f"  - 连接: {upstream} -> {downstream}")
    
    # 创建简单的控制逻辑
    control_strategy = create_control_strategy()
    
    # 控制函数：在每个时间步发送控制信号
    def control_step(current_time: float):
        """执行控制逻辑"""
        # 获取上游状态
        upstream_state = components['upstream_canal'].get_state()
        
        # 计算控制动作
        gate_opening = control_strategy(current_time, upstream_state)
        
        # 发送控制信号到闸门
        control_message = {'control_signal': gate_opening}
        message_bus.publish('gate_control', control_message)
        
        # 记录控制动作
        if hasattr(control_step, 'control_history'):
            control_step.control_history.append({
                'time': current_time,
                'upstream_level': upstream_state.get('water_level', 0),
                'gate_opening': gate_opening
            })
        else:
            control_step.control_history = []
    
    print("✅ 简单消息控制设置完成")
    return harness, control_step


def run_simulation_with_control(harness: SimulationHarness, control_function=None):
    """运行带控制的仿真"""
    
    print("🚀 开始仿真执行...")
    
    try:
        # 如果有控制函数，需要在每步调用
        if control_function:
            # 修改harness的step方法以包含控制
            original_step = harness.step
            
            def step_with_control():
                # 执行控制逻辑
                control_function(harness.t)
                # 执行仿真步进
                return original_step()
            
            harness.step = step_with_control
        
        # 执行仿真
        harness.run()
        
        # 获取仿真历史
        history = harness.get_history()
        
        print(f"✅ 仿真完成! 共 {len(history)} 个时间步")
        return history
        
    except Exception as e:
        print(f"❌ 仿真执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_results(history: List[Dict[str, Any]], control_history=None):
    """分析仿真结果"""
    
    if not history:
        print("❌ 没有仿真数据可供分析")
        return
    
    print("📊 分析仿真结果...")
    
    # 提取数据
    times = [step['time'] for step in history]
    upstream_levels = [step['components']['upstream_canal']['water_level'] for step in history]
    upstream_outflows = [step['components']['upstream_canal']['outflow'] for step in history]
    gate_openings = [step['components']['control_gate']['opening'] for step in history]
    gate_outflows = [step['components']['control_gate']['outflow'] for step in history]
    downstream_levels = [step['components']['downstream_canal']['water_level'] for step in history]
    reservoir_levels = [step['components']['end_reservoir']['water_level'] for step in history]
    reservoir_volumes = [step['components']['end_reservoir']['volume'] / 1e6 for step in history]  # 百万m³
    
    # 创建图表
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('基于Core-Lib原生架构的渠道仿真结果', fontsize=16, fontweight='bold')
    
    # 1. 系统水位
    axes[0, 0].plot(times, upstream_levels, 'b-', linewidth=2, label='上游渠道')
    axes[0, 0].plot(times, downstream_levels, 'g-', linewidth=2, label='下游渠道')
    axes[0, 0].plot(times, reservoir_levels, 'r-', linewidth=2, label='水库')
    axes[0, 0].set_title('系统水位变化')
    axes[0, 0].set_xlabel('时间 (s)')
    axes[0, 0].set_ylabel('水位 (m)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 系统流量
    axes[0, 1].plot(times, upstream_outflows, 'b-', linewidth=2, label='上游出流')
    axes[0, 1].plot(times, gate_outflows, 'orange', linewidth=2, label='闸门出流')
    axes[0, 1].set_title('系统流量变化')
    axes[0, 1].set_xlabel('时间 (s)')
    axes[0, 1].set_ylabel('流量 (m³/s)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 闸门控制
    axes[0, 2].plot(times, gate_openings, 'purple', linewidth=2, marker='o', markersize=3)
    axes[0, 2].set_title('闸门开度控制')
    axes[0, 2].set_xlabel('时间 (s)')
    axes[0, 2].set_ylabel('开度')
    axes[0, 2].set_ylim(0, 1.1)
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. 水库响应
    axes[1, 0].plot(times, reservoir_volumes, 'r-', linewidth=2)
    axes[1, 0].set_title('水库库容变化')
    axes[1, 0].set_xlabel('时间 (s)')
    axes[1, 0].set_ylabel('库容 (百万 m³)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. 控制效果分析
    axes[1, 1].plot(times, upstream_levels, 'b--', alpha=0.7, label='上游水位')
    axes[1, 1].plot(times, gate_openings, 'purple', linewidth=2, label='闸门开度')
    axes[1, 1].set_title('控制响应分析')
    axes[1, 1].set_xlabel('时间 (s)')
    axes[1, 1].set_ylabel('水位(m) / 开度')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 6. 系统效率
    flow_efficiency = np.array(gate_outflows) / (np.array(upstream_outflows) + 1e-6)
    axes[1, 2].plot(times, flow_efficiency, 'green', linewidth=2)
    axes[1, 2].set_title('流量传输效率')
    axes[1, 2].set_xlabel('时间 (s)')
    axes[1, 2].set_ylabel('效率 (出流/入流)')
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存和显示
    filename = 'native_canal_simulation_results.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📈 结果图表已保存为: {filename}")
    plt.show()
    
    # 统计分析
    print("\n📋 仿真统计结果:")
    print(f"  仿真总时长: {times[-1]:.0f} 秒")
    print(f"  最终水库水位: {reservoir_levels[-1]:.2f} m")
    print(f"  最终水库库容: {reservoir_volumes[-1]:.1f} 百万 m³")
    print(f"  水库库容增量: {reservoir_volumes[-1] - reservoir_volumes[0]:.1f} 百万 m³")
    print(f"  平均闸门开度: {np.mean(gate_openings):.3f}")
    print(f"  平均传输效率: {np.mean(flow_efficiency):.3f}")


def main():
    """主函数"""
    
    print("🌊 基于Core-Lib原生架构的渠道仿真系统")
    print("=" * 60)
    
    try:
        # 1. 创建系统组件
        components, agents, message_bus = create_simulation_system()
        
        # 2. 选择控制方案 (使用简单消息控制，避免复杂Agent依赖)
        harness, control_function = setup_simple_message_control(components, message_bus)
        
        # 3. 运行仿真
        history = run_simulation_with_control(harness, control_function)
        
        # 4. 分析结果
        if history:
            control_history = getattr(control_function, 'control_history', None) if control_function else None
            analyze_results(history, control_history)
        
        print("\n🎉 仿真完成! 使用了Core-Lib原生架构")
        print("✅ 特点:")
        print("  - 使用原生SimulationHarness进行仿真管理")
        print("  - 通过消息总线进行组件通信") 
        print("  - 支持物理对象的完整拓扑连接")
        print("  - 集成了时间驱动的闸门控制策略")
        
        return True
        
    except Exception as e:
        print(f"❌ 仿真系统运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
