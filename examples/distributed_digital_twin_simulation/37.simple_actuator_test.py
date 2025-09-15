#!/usr/bin/env python3
"""
简化的执行器故障测试
专注于验证执行器故障扰动的基本功能
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.physical_objects.gate import Gate
from core_lib.disturbances.disturbance_framework import DisturbanceConfig, DisturbanceType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_actuator_failure():
    """简单的执行器故障测试"""
    logger.info("开始简单执行器故障测试")
    
    try:
        # 创建仿真配置
        config = {
            'start_time': 0.0,
            'end_time': 10.0,
            'dt': 0.5,
            'use_optimized_managers': True
        }
        harness = EnhancedSimulationHarness(config)
        
        # 添加闸门组件
        initial_state = {
            'opening': 0.5,
            'outflow': 0.0
        }
        parameters = {
            'width': 2.0,
            'discharge_coefficient': 0.6,
            'max_opening': 1.0,
            'min_opening': 0.0
        }
        gate = Gate(
            name="test_gate",
            initial_state=initial_state,
            parameters=parameters
        )
        harness.add_component("test_gate", gate)
        
        # 创建执行器故障扰动配置
        disturbance_config = DisturbanceConfig(
            disturbance_id="simple_actuator_test",
            disturbance_type=DisturbanceType.ACTUATOR_FAILURE,
            target_component_id="test_gate",
            start_time=2.0,
            end_time=8.0,
            intensity=1.0,
            parameters={
                'failure_type': 'partial',
                'efficiency_factor': 0.7,
                'target_actuator': 'outlet_gate'
            }
        )
        
        # 创建扰动实例
        from core_lib.disturbances.disturbance_framework import ActuatorFailureDisturbance
        disturbance = ActuatorFailureDisturbance(disturbance_config)
        
        # 添加扰动到仿真
        harness.add_disturbance(disturbance)
        
        # 构建仿真
        harness.build()
        
        # 运行仿真
        print("开始仿真运行")
        harness.run_simulation()
        
        # 获取最终状态
        final_state = gate.get_state()
        logger.info(f"最终状态: 闸门开度={final_state.get('opening', 0):.2f}")
        
        # 检查扰动状态
        disturbance_status = harness.get_disturbance_status()
        logger.info(f"扰动状态: {disturbance_status}")
        
        logger.info("简单执行器故障测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'harness' in locals():
            print("测试完成")

def main():
    """主函数"""
    logger.info("开始简单执行器故障测试")
    
    success = test_simple_actuator_failure()
    
    if success:
        logger.info("✅ 所有测试通过")
    else:
        logger.error("❌ 测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()