#!/usr/bin/env python3
"""测试集成的扰动框架

验证扰动管理器是否正确集成到SimulationHarness中，
并测试入流扰动功能。
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core_lib.io.yaml_loader import SimulationBuilder
from core_lib.disturbances.disturbance_framework import (
    DisturbanceConfig, DisturbanceType, InflowDisturbance, create_disturbance
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

def test_integrated_disturbance_framework():
    """测试集成的扰动框架"""
    logger.info("开始测试集成的扰动框架")
    
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
    
    # 创建入流扰动配置
    disturbance_config = DisturbanceConfig(
        disturbance_id="test_inflow_disturbance",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id=upstream_reservoir_id,
        start_time=10.0,
        end_time=15.0,
        intensity=1.0,
        parameters={
            'target_inflow': 5100.0  # 强扰动：从100增加到5100 m³/s
        },
        description="测试入流扰动：增加入流到5100 m³/s"
    )
    
    # 创建扰动实例
    disturbance = create_disturbance(disturbance_config)
    
    # 添加扰动到仿真中
    harness.add_disturbance(disturbance)
    
    logger.info(f"扰动配置: {disturbance_config}")
    
    # 运行仿真
    logger.info("开始运行仿真...")
    
    # 记录关键时间点的状态
    key_times = [9.0, 10.0, 12.5, 15.0, 16.0]
    recorded_states = {}
    
    while harness.t < harness.end_time:
        # 记录关键时间点的状态
        if any(abs(harness.t - key_time) < 0.1 for key_time in key_times):
            state = upstream_reservoir.get_state()
            recorded_states[harness.t] = {
                'water_level': state.get('water_level', 0),
                'volume': state.get('volume', 0),
                'inflow': getattr(upstream_reservoir, '_inflow', 0),
                'active_disturbances': harness.get_active_disturbances()
            }
            
            logger.info(f"时间 {harness.t:.1f}s: 水位={state.get('water_level', 0):.6f}m, "
                       f"入流={getattr(upstream_reservoir, '_inflow', 0):.1f}m³/s, "
                       f"活跃扰动={harness.get_active_disturbances()}")
        
        # 执行一个仿真步骤
        harness.step()
    
    # 分析结果
    logger.info("\n=== 仿真结果分析 ===")
    
    # 计算水位变化
    if 9.0 in recorded_states and 15.0 in recorded_states:
        initial_level = recorded_states[9.0]['water_level']
        final_level = recorded_states[15.0]['water_level']
        level_change = (final_level - initial_level) * 1000  # 转换为mm
        
        logger.info(f"扰动前水位 (9.0s): {initial_level:.6f} m")
        logger.info(f"扰动后水位 (15.0s): {final_level:.6f} m")
        logger.info(f"水位变化: {level_change:.3f} mm")
        
        # 验证扰动效果
        if abs(level_change) > 50:  # 期望显著的水位变化
            logger.info("✅ 扰动效果显著，框架工作正常")
        else:
            logger.warning("⚠️ 扰动效果不明显，可能存在问题")
    
    # 显示扰动历史
    disturbance_history = harness.get_disturbance_history()
    logger.info(f"\n扰动历史记录数量: {len(disturbance_history)}")
    
    if disturbance_history:
        logger.info("扰动历史样本:")
        for i, record in enumerate(disturbance_history[:3]):  # 显示前3条记录
            logger.info(f"  {i+1}. 时间={record['time']:.1f}s, 效果={record['effects']}")
    
    # 显示所有记录的状态
    logger.info("\n=== 关键时间点状态记录 ===")
    for time, state in sorted(recorded_states.items()):
        logger.info(f"时间 {time:.1f}s: {state}")
    
    logger.info("\n测试完成")

def main():
    """主函数"""
    try:
        test_integrated_disturbance_framework()
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())