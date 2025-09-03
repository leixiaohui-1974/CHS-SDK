#!/usr/bin/env python3
"""测试多种扰动类型

验证扰动框架支持的不同扰动类型：
1. 入流扰动 (InflowDisturbance)
2. 传感器噪声扰动 (SensorNoiseDisturbance)
3. 多个扰动同时作用
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
    DisturbanceConfig, DisturbanceType, InflowDisturbance, SensorNoiseDisturbance, create_disturbance
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

def test_inflow_disturbance(harness):
    """测试入流扰动"""
    logger.info("\n=== 测试入流扰动 ===")
    
    # 创建入流扰动配置
    inflow_config = DisturbanceConfig(
        disturbance_id="inflow_test",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id="Upstream_Reservoir",
        start_time=5.0,
        end_time=10.0,
        intensity=1.0,
        parameters={
            'target_inflow': 3000.0  # 增加入流到3000 m³/s
        },
        description="测试入流扰动"
    )
    
    # 创建并添加扰动
    inflow_disturbance = create_disturbance(inflow_config)
    harness.add_disturbance(inflow_disturbance)
    
    logger.info(f"添加入流扰动: {inflow_config.disturbance_id}")
    return inflow_config.disturbance_id

def test_sensor_noise_disturbance(harness):
    """测试传感器噪声扰动"""
    logger.info("\n=== 测试传感器噪声扰动 ===")
    
    # 创建传感器噪声扰动配置
    sensor_config = DisturbanceConfig(
        disturbance_id="sensor_noise_test",
        disturbance_type=DisturbanceType.SENSOR_NOISE,
        target_component_id="Upstream_Reservoir",
        start_time=12.0,
        end_time=18.0,
        intensity=0.5,
        parameters={
            'noise_std': 0.01,  # 标准差为1cm的噪声
            'sensor_type': 'water_level'
        },
        description="测试传感器噪声扰动"
    )
    
    # 创建并添加扰动
    sensor_disturbance = create_disturbance(sensor_config)
    harness.add_disturbance(sensor_disturbance)
    
    logger.info(f"添加传感器噪声扰动: {sensor_config.disturbance_id}")
    return sensor_config.disturbance_id

def test_multiple_disturbances():
    """测试多种扰动类型"""
    logger.info("开始测试多种扰动类型")
    
    # 加载仿真环境
    harness = load_simulation_harness()
    
    # 检查组件
    logger.info(f"可用组件: {list(harness.components.keys())}")
    
    # 确认上游水库存在
    upstream_reservoir_id = "Upstream_Reservoir"
    if upstream_reservoir_id not in harness.components:
        logger.error(f"未找到上游水库组件: {upstream_reservoir_id}")
        return
    
    upstream_reservoir = harness.components[upstream_reservoir_id]
    logger.info(f"找到上游水库: {upstream_reservoir_id}")
    
    # 添加不同类型的扰动
    inflow_id = test_inflow_disturbance(harness)
    sensor_id = test_sensor_noise_disturbance(harness)
    
    # 运行仿真
    logger.info("\n开始运行仿真...")
    
    # 记录关键时间点的状态
    key_times = [4.0, 6.0, 8.0, 11.0, 14.0, 16.0, 19.0]
    recorded_states = {}
    
    while harness.t < harness.end_time:
        # 记录关键时间点的状态
        if any(abs(harness.t - key_time) < 0.1 for key_time in key_times):
            state = upstream_reservoir.get_state()
            active_disturbances = harness.get_active_disturbances()
            
            recorded_states[harness.t] = {
                'water_level': state.get('water_level', 0),
                'volume': state.get('volume', 0),
                'inflow': getattr(upstream_reservoir, '_inflow', 0),
                'active_disturbances': active_disturbances
            }
            
            logger.info(f"时间 {harness.t:.1f}s: 水位={state.get('water_level', 0):.6f}m, "
                       f"入流={getattr(upstream_reservoir, '_inflow', 0):.1f}m³/s, "
                       f"活跃扰动={len(active_disturbances)}个")
        
        # 执行一个仿真步骤
        harness.step()
    
    # 分析结果
    logger.info("\n=== 仿真结果分析 ===")
    
    # 分析入流扰动效果 (5.0s - 10.0s)
    if 4.0 in recorded_states and 8.0 in recorded_states:
        before_inflow = recorded_states[4.0]['water_level']
        during_inflow = recorded_states[8.0]['water_level']
        inflow_effect = (during_inflow - before_inflow) * 1000  # 转换为mm
        
        logger.info(f"入流扰动效果分析:")
        logger.info(f"  扰动前水位 (4.0s): {before_inflow:.6f} m")
        logger.info(f"  扰动中水位 (8.0s): {during_inflow:.6f} m")
        logger.info(f"  水位变化: {inflow_effect:.3f} mm")
    
    # 分析传感器噪声扰动效果 (12.0s - 18.0s)
    sensor_times = [t for t in recorded_states.keys() if 12.0 <= t <= 18.0]
    if len(sensor_times) >= 2:
        logger.info(f"\n传感器噪声扰动期间水位变化:")
        for t in sorted(sensor_times):
            state = recorded_states[t]
            logger.info(f"  时间 {t:.1f}s: 水位={state['water_level']:.6f}m")
    
    # 显示扰动历史统计
    disturbance_history = harness.get_disturbance_history()
    logger.info(f"\n扰动历史记录总数: {len(disturbance_history)}")
    
    # 按扰动类型统计
    inflow_records = [r for r in disturbance_history if inflow_id in r['effects']]
    sensor_records = [r for r in disturbance_history if sensor_id in r['effects']]
    
    logger.info(f"入流扰动记录数: {len(inflow_records)}")
    logger.info(f"传感器噪声扰动记录数: {len(sensor_records)}")
    
    # 显示扰动重叠期间的记录
    overlap_records = [r for r in disturbance_history 
                      if len(r['effects']) > 1]  # 多个扰动同时作用
    
    if overlap_records:
        logger.info(f"\n扰动重叠期间记录数: {len(overlap_records)}")
        logger.info("扰动重叠样本:")
        for i, record in enumerate(overlap_records[:3]):
            logger.info(f"  {i+1}. 时间={record['time']:.1f}s, 同时作用的扰动={list(record['effects'].keys())}")
    
    # 验证扰动管理功能
    logger.info("\n=== 扰动管理功能验证 ===")
    
    # 测试移除扰动
    if inflow_id in [d.config.disturbance_id for d in harness.disturbance_manager.active_disturbances.values()]:
        logger.info(f"移除入流扰动: {inflow_id}")
        harness.remove_disturbance(inflow_id)
    
    remaining_disturbances = harness.get_active_disturbances()
    logger.info(f"剩余活跃扰动: {remaining_disturbances}")
    
    logger.info("\n多种扰动类型测试完成")

def main():
    """主函数"""
    try:
        test_multiple_disturbances()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())