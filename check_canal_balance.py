#!/usr/bin/env python3
"""
检查渠道水量平衡问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接导入需要的类
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.unified_canal import UnifiedCanal

def test_canal_water_balance():
    """测试渠道水量平衡"""
    print("🔧 渠道水量平衡测试")
    print("=" * 50)
    
    try:
        # 创建仿真平台
        config = {
            'start_time': 0,
            'end_time': 30,
            'time_step': 5
        }
        harness = SimulationHarness(config)
        
        # 创建上游水库
        upstream_reservoir = Reservoir(
            name="Upstream_Reservoir",
            initial_state={'water_level': 100.0, 'volume': 5000000.0, 'inflow': 0.0, 'outflow': 25.0},
            parameters={
                'surface_area': 50000.0,
                'capacity': 10000000.0,
                'min_level': 80.0,
                'max_level': 120.0,
                'outflow': 25.0  # 固定出流
            }
        )
        
        # 创建渠道（积分延迟模型）
        channel = UnifiedCanal(
            name="Test_Channel",
            initial_state={'water_level': 62.83, 'inflow': 25.0, 'outflow': 25.0},
            parameters={
                'length': 1000.0,
                'width': 10.0,
                'roughness': 0.025,
                'slope': 0.001,
                'model_type': 'integral_delay',
                'gain': 0.1,
                'delay': 10.0,
                'inflow': 25.0
            }
        )
        
        # 创建下游水库
        downstream_reservoir = Reservoir(
            name="Downstream_Reservoir",
            initial_state={'water_level': 57.83, 'volume': 1000000.0, 'inflow': 0.0, 'outflow': 25.0},
            parameters={
                'surface_area': 20000.0,
                'capacity': 5000000.0,
                'min_level': 50.0,
                'max_level': 70.0,
                'outflow': 25.0  # 固定出流
            }
        )
        
        # 添加组件到仿真平台
        harness.add_component("Upstream_Reservoir", upstream_reservoir)
        harness.add_component("Test_Channel", channel)
        harness.add_component("Downstream_Reservoir", downstream_reservoir)
        
        # 建立连接
        harness.add_connection("Upstream_Reservoir", "Test_Channel")
        harness.add_connection("Test_Channel", "Downstream_Reservoir")
        
        # 构建仿真
        harness.build()
        
        print(f"✅ 成功创建仿真系统，包含 {len(harness.components)} 个组件")
        
        # 运行几步仿真并检查水量平衡
        for step in range(5):
            print(f"\n--- 步骤 {step}: t={harness.t:.1f}s ---")
            
            # 获取仿真前状态
            print("仿真前状态:")
            for comp_name in ["Upstream_Reservoir", "Test_Channel", "Downstream_Reservoir"]:
                component = harness.components[comp_name]
                state = component.get_state()
                print(f"  {comp_name}: 入流={state.get('inflow', 0):.2f}, 出流={state.get('outflow', 0):.2f}, "
                      f"水位={state.get('water_level', 0):.3f}")
            
            # 执行一步仿真
            harness.step()
            
            # 获取仿真后状态
            print("仿真后状态:")
            for comp_name in ["Upstream_Reservoir", "Test_Channel", "Downstream_Reservoir"]:
                component = harness.components[comp_name]
                state = component.get_state()
                print(f"  {comp_name}: 入流={state.get('inflow', 0):.2f}, 出流={state.get('outflow', 0):.2f}, "
                      f"水位={state.get('water_level', 0):.3f}")
            
            # 检查渠道水量平衡
            channel_state = harness.components["Test_Channel"].get_state()
            inflow = channel_state.get('inflow', 0)
            outflow = channel_state.get('outflow', 0)
            balance_error = abs(inflow - outflow)
            
            print(f"渠道水量平衡检查: 入流={inflow:.2f}, 出流={outflow:.2f}, 不平衡量={balance_error:.2f}")
            
            # 检查渠道库容变化
            if step > 0:
                prev_channel_state = harness.history[-2]["Test_Channel"]
                prev_water_level = prev_channel_state.get('water_level', 0)
                current_water_level = channel_state.get('water_level', 0)
                level_change = current_water_level - prev_water_level
                storage_change = level_change * 10.0 * 1000.0  # width * length
                expected_storage_change = (inflow - outflow) * 5.0  # time_step
                print(f"渠道库容变化检查: 实际变化={storage_change:.2f}, 预期变化={expected_storage_change:.2f}")
            
            if balance_error < 1.0:
                print("✅ 渠道水量基本平衡")
            else:
                print("⚠️  渠道水量不平衡")
                
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_canal_water_balance()
    
    if success:
        print("\n🎉 渠道水量平衡测试完成！")
    else:
        print("\n❌ 渠道水量平衡测试失败！")

if __name__ == "__main__":
    main()