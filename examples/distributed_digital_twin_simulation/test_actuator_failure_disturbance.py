#!/usr/bin/env python3
"""测试执行器故障扰动

验证执行器故障扰动的三种模式：
1. 延迟故障：控制信号延迟生效
2. 部分故障：执行器效率下降
3. 完全故障：执行器无响应
"""

import os
import sys
import yaml
import logging
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder
from core_lib.disturbances.disturbance_framework import (
    DisturbanceConfig, DisturbanceType, ActuatorFailureDisturbance, create_disturbance
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_harness():
    """加载仿真环境"""
    scenario_path = os.path.dirname(__file__)
    
    try:
        builder = SimulationBuilder(scenario_path=scenario_path)
        harness = builder.load()
        return harness
    except Exception as e:
        logger.error(f"加载仿真环境失败: {e}")
        raise

def test_delay_failure(harness):
    """测试延迟故障"""
    logger.info("\n=== 测试执行器延迟故障 ===")
    
    # 创建延迟故障配置
    delay_config = DisturbanceConfig(
        disturbance_id="gate_delay_failure",
        disturbance_type=DisturbanceType.ACTUATOR_FAILURE,
        target_component_id="Upstream_Reservoir",
        start_time=5.0,
        end_time=15.0,
        intensity=1.0,
        parameters={
            'failure_type': 'delay',
            'delay_time': 3.0,  # 3秒延迟
            'target_actuator': 'outlet_gate'
        },
        description="测试闸门延迟故障：控制信号延迟3秒生效"
    )
    
    # 创建并添加扰动
    delay_disturbance = create_disturbance(delay_config)
    harness.add_disturbance(delay_disturbance)
    
    logger.info(f"添加延迟故障扰动: {delay_config.disturbance_id}")
    logger.info(f"延迟时间: {delay_config.parameters['delay_time']} 秒")
    
    return delay_config.disturbance_id

def test_partial_failure(harness):
    """测试部分故障"""
    logger.info("\n=== 测试执行器部分故障 ===")
    
    # 创建部分故障配置
    partial_config = DisturbanceConfig(
        disturbance_id="pump_efficiency_failure",
        disturbance_type=DisturbanceType.ACTUATOR_FAILURE,
        target_component_id="Downstream_Reservoir",
        start_time=8.0,
        end_time=18.0,
        intensity=0.6,
        parameters={
            'failure_type': 'partial',
            'efficiency_factor': 0.6,  # 效率降至60%
            'target_actuator': 'main_pump'
        },
        description="测试泵站效率故障：效率降至60%"
    )
    
    # 创建并添加扰动
    partial_disturbance = create_disturbance(partial_config)
    harness.add_disturbance(partial_disturbance)
    
    logger.info(f"添加部分故障扰动: {partial_config.disturbance_id}")
    logger.info(f"效率因子: {partial_config.parameters['efficiency_factor']}")
    
    return partial_config.disturbance_id

def test_complete_failure(harness):
    """测试完全故障"""
    logger.info("\n=== 测试执行器完全故障 ===")
    
    # 创建完全故障配置
    complete_config = DisturbanceConfig(
        disturbance_id="valve_complete_failure",
        disturbance_type=DisturbanceType.ACTUATOR_FAILURE,
        target_component_id="Upstream_Reservoir",
        start_time=12.0,
        end_time=20.0,
        intensity=1.0,
        parameters={
            'failure_type': 'complete',
            'target_actuator': 'control_valve'
        },
        description="测试控制阀完全故障：无响应"
    )
    
    # 创建并添加扰动
    complete_disturbance = create_disturbance(complete_config)
    harness.add_disturbance(complete_disturbance)
    
    logger.info(f"添加完全故障扰动: {complete_config.disturbance_id}")
    
    return complete_config.disturbance_id

def analyze_component_behavior(component, component_id, time):
    """分析组件行为"""
    state = component.get_state()
    
    behavior = {
        'time': time,
        'component_id': component_id,
        'water_level': state.get('water_level', 0),
        'volume': state.get('volume', 0),
        'inflow': getattr(component, '_inflow', 0),
        'outflow': getattr(component, '_outflow', 0)
    }
    
    # 检查执行器相关属性
    if hasattr(component, '_efficiency'):
        behavior['efficiency'] = getattr(component, '_efficiency')
    
    if hasattr(component, '_actuator_status'):
        behavior['actuator_status'] = getattr(component, '_actuator_status')
    
    return behavior

def test_actuator_failure_disturbances():
    """测试执行器故障扰动"""
    logger.info("开始测试执行器故障扰动")
    
    # 加载仿真环境
    harness = load_simulation_harness()
    
    # 检查组件
    logger.info(f"可用组件: {list(harness.components.keys())}")
    
    # 确认目标组件存在
    upstream_id = "Upstream_Reservoir"
    downstream_id = "Downstream_Reservoir"
    
    if upstream_id not in harness.components:
        logger.error(f"未找到上游水库组件: {upstream_id}")
        return
    
    if downstream_id not in harness.components:
        logger.warning(f"未找到下游水库组件: {downstream_id}，将跳过相关测试")
        downstream_id = None
    
    upstream_reservoir = harness.components[upstream_id]
    downstream_reservoir = harness.components.get(downstream_id) if downstream_id else None
    
    # 添加不同类型的执行器故障扰动
    delay_id = test_delay_failure(harness)
    
    if downstream_reservoir:
        partial_id = test_partial_failure(harness)
    else:
        partial_id = None
        logger.info("跳过部分故障测试（缺少下游水库）")
    
    complete_id = test_complete_failure(harness)
    
    # 运行仿真
    logger.info("\n开始运行仿真...")
    
    # 记录关键时间点的状态
    key_times = [4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 21.0]
    recorded_states = {}
    component_behaviors = []
    
    while harness.t < harness.end_time:
        # 记录关键时间点的状态
        if any(abs(harness.t - key_time) < 0.1 for key_time in key_times):
            active_disturbances = harness.get_active_disturbances()
            
            # 分析上游水库行为
            upstream_behavior = analyze_component_behavior(upstream_reservoir, upstream_id, harness.t)
            component_behaviors.append(upstream_behavior)
            
            # 分析下游水库行为（如果存在）
            if downstream_reservoir:
                downstream_behavior = analyze_component_behavior(downstream_reservoir, downstream_id, harness.t)
                component_behaviors.append(downstream_behavior)
            
            recorded_states[harness.t] = {
                'active_disturbances': active_disturbances,
                'upstream': upstream_behavior,
                'downstream': downstream_behavior if downstream_reservoir else None
            }
            
            logger.info(f"时间 {harness.t:.1f}s: 活跃扰动={len(active_disturbances)}个, "
                       f"上游水位={upstream_behavior['water_level']:.6f}m, "
                       f"上游入流={upstream_behavior['inflow']:.1f}m³/s")
        
        # 执行一个仿真步骤
        harness.step()
    
    # 分析结果
    logger.info("\n=== 执行器故障扰动结果分析 ===")
    
    # 分析延迟故障效果
    logger.info("\n1. 延迟故障分析:")
    delay_times = [t for t in recorded_states.keys() if 5.0 <= t <= 15.0]
    if delay_times:
        logger.info(f"  延迟故障期间记录的时间点: {[f'{t:.1f}s' for t in sorted(delay_times)]}")
        for t in sorted(delay_times):
            state = recorded_states[t]
            if delay_id in state['active_disturbances']:
                logger.info(f"    时间 {t:.1f}s: 延迟故障活跃")
    
    # 分析部分故障效果
    if partial_id:
        logger.info("\n2. 部分故障分析:")
        partial_times = [t for t in recorded_states.keys() if 8.0 <= t <= 18.0]
        if partial_times:
            logger.info(f"  部分故障期间记录的时间点: {[f'{t:.1f}s' for t in sorted(partial_times)]}")
            for t in sorted(partial_times):
                state = recorded_states[t]
                if partial_id in state['active_disturbances']:
                    logger.info(f"    时间 {t:.1f}s: 部分故障活跃")
    
    # 分析完全故障效果
    logger.info("\n3. 完全故障分析:")
    complete_times = [t for t in recorded_states.keys() if 12.0 <= t <= 20.0]
    if complete_times:
        logger.info(f"  完全故障期间记录的时间点: {[f'{t:.1f}s' for t in sorted(complete_times)]}")
        for t in sorted(complete_times):
            state = recorded_states[t]
            if complete_id in state['active_disturbances']:
                logger.info(f"    时间 {t:.1f}s: 完全故障活跃")
    
    # 显示扰动历史统计
    disturbance_history = harness.get_disturbance_history()
    logger.info(f"\n扰动历史记录总数: {len(disturbance_history)}")
    
    # 按扰动类型统计
    delay_records = [r for r in disturbance_history if delay_id in r['effects']]
    partial_records = [r for r in disturbance_history if partial_id and partial_id in r['effects']]
    complete_records = [r for r in disturbance_history if complete_id in r['effects']]
    
    logger.info(f"延迟故障记录数: {len(delay_records)}")
    logger.info(f"部分故障记录数: {len(partial_records)}")
    logger.info(f"完全故障记录数: {len(complete_records)}")
    
    # 显示故障重叠期间的记录
    overlap_records = [r for r in disturbance_history 
                      if len(r['effects']) > 1]  # 多个故障同时作用
    
    if overlap_records:
        logger.info(f"\n故障重叠期间记录数: {len(overlap_records)}")
        logger.info("故障重叠样本:")
        for i, record in enumerate(overlap_records[:3]):
            logger.info(f"  {i+1}. 时间={record['time']:.1f}s, 同时作用的故障={list(record['effects'].keys())}")
    
    # 验证故障恢复
    logger.info("\n=== 故障恢复验证 ===")
    
    # 检查故障结束后的状态
    post_failure_times = [t for t in recorded_states.keys() if t > 20.0]
    if post_failure_times:
        recovery_time = min(post_failure_times)
        recovery_state = recorded_states[recovery_time]
        logger.info(f"故障恢复后状态 (时间 {recovery_time:.1f}s):")
        logger.info(f"  活跃扰动数量: {len(recovery_state['active_disturbances'])}")
        logger.info(f"  上游水位: {recovery_state['upstream']['water_level']:.6f}m")
        
        if recovery_state['downstream']:
            logger.info(f"  下游水位: {recovery_state['downstream']['water_level']:.6f}m")
    
    # 显示组件行为变化趋势
    logger.info("\n=== 组件行为变化趋势 ===")
    
    upstream_behaviors = [b for b in component_behaviors if b['component_id'] == upstream_id]
    if len(upstream_behaviors) >= 2:
        initial = upstream_behaviors[0]
        final = upstream_behaviors[-1]
        
        water_level_change = (final['water_level'] - initial['water_level']) * 1000  # mm
        volume_change = final['volume'] - initial['volume']  # m³
        
        logger.info(f"上游水库变化:")
        logger.info(f"  水位变化: {water_level_change:.3f} mm")
        logger.info(f"  体积变化: {volume_change:.1f} m³")
        logger.info(f"  初始入流: {initial['inflow']:.1f} m³/s")
        logger.info(f"  最终入流: {final['inflow']:.1f} m³/s")
    
    logger.info("\n执行器故障扰动测试完成")

def main():
    """主函数"""
    try:
        test_actuator_failure_disturbances()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())