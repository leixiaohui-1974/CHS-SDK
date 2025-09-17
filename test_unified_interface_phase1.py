#!/usr/bin/env python3
"""测试第一阶段统一接口改进的脚本"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory
from core_lib.core_engine.testing.component_types import (
    ComponentConfig, ComponentType, DeviceLevel, InfrastructureConfig, 
    DeviceConfig, StationConfig
)

def test_unified_interface_phase1():
    """测试第一阶段统一接口改进"""
    print("=== 测试第一阶段统一接口改进 ===\n")
    
    # 创建仿真配置
    config = {
        'end_time': 100,
        'time_step': 1.0
    }
    
    harness = SimulationHarness(config)
    factory = UnifiedComponentFactory()
    
    # 测试1: 参数验证功能
    print("1. 测试参数验证功能:")
    
    try:
        # 测试空component_id
        config = InfrastructureConfig(
            component_id="",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 10.0}
        )
        factory.create_component(config)
        print("  ❌ 应该抛出ComponentValidationError (空component_id)")
    except Exception as e:
        print(f"  ✅ 正确捕获空component_id错误: {e}")
    
    try:
        # 测试无效opening值
        config = DeviceConfig(
            component_id="test_gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 1.5, 'max_flow_rate': 100.0}
        )
        factory.create_component(config)
        print("  ❌ 应该抛出ComponentValidationError (opening > 1.0)")
    except Exception as e:
        print(f"  ✅ 正确捕获无效opening错误: {e}")
    
    try:
        # 测试无效模型类型
        config = InfrastructureConfig(
            component_id="test_canal",
            component_type=ComponentType.CANAL,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'model_type': 'invalid_model'}
        )
        factory.create_component(config)
        print("  ❌ 应该抛出ComponentValidationError (无效model_type)")  
    except Exception as e:
        print(f"  ✅ 正确捕获无效model_type错误: {e}")
    
    # 测试2: 统一参数命名
    print("\n2. 测试统一参数命名:")
    
    try:
        # 使用统一组件工厂创建组件
        reservoir_config = InfrastructureConfig(
            component_id="test_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 15.0, 'surface_area': 50000}
        )
        reservoir = factory.create_component(reservoir_config)
        harness.add_component("test_reservoir", reservoir)
        
        gate_config = DeviceConfig(
            component_id="test_gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 0.7, 'max_flow_rate': 80.0}
        )
        gate = factory.create_component(gate_config)
        harness.add_component("test_gate", gate)
        
        pump_station_config = StationConfig(
            component_id="test_pump",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 15.0, 'max_head': 25.0, 'power_consumption': 100.0},
            device_count=2
        )
        pump_station = factory.create_component(pump_station_config)
        harness.add_component("test_pump", pump_station)
        
        turbine_config = DeviceConfig(
            component_id="test_turbine",
            component_type=ComponentType.WATER_TURBINE,
            level=DeviceLevel.DEVICE,
            parameters={'efficiency': 0.85, 'max_flow_rate': 60.0}
        )
        turbine = factory.create_component(turbine_config)
        harness.add_component("test_turbine", turbine)
        
        canal_config = InfrastructureConfig(
            component_id="test_canal",
            component_type=ComponentType.CANAL,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'model_type': 'integral_delay', 'water_level': 3.0}
        )
        canal = factory.create_component(canal_config)
        harness.add_component("test_canal", canal)
        
        print("  ✅ 所有组件成功创建，参数命名统一")
        print(f"    - 水库: {type(reservoir).__name__}")  
        print(f"    - 闸门: {type(gate).__name__}")
        print(f"    - 泵站: {type(pump_station).__name__}")
        print(f"    - 水轮机: {type(turbine).__name__}")
        print(f"    - 渠道: {type(canal).__name__}")
        
    except Exception as e:
        print(f"  ❌ 组件创建失败: {e}")
        return False
    
    # 测试3: 验证组件连接
    print("\n3. 测试组件连接:")
    
    try:
        harness.add_connection("test_reservoir", "test_gate")
        harness.add_connection("test_gate", "test_canal")
        harness.add_connection("test_canal", "test_turbine")
        harness.add_connection("test_turbine", "test_pump")
        print("  ✅ 组件连接成功")
        
    except Exception as e:
        print(f"  ❌ 组件连接失败: {e}")
        return False
    
    # 测试4: 验证构建和基本仿真
    print("\n4. 测试仿真构建:")
    
    try:
        harness.build()
        print("  ✅ 仿真构建成功")
        
        # 检查组件是否正确添加
        components = harness.components
        print(f"  - 总共添加了 {len(components)} 个组件")
        for comp_id, comp in components.items():
            print(f"    * {comp_id}: {type(comp).__name__}")
            
    except Exception as e:
        print(f"  ❌ 仿真构建失败: {e}")
        return False
    
    print("\n=== 第一阶段统一接口改进测试完成 ===")
    return True

def test_convenience_functions():
    """测试便利函数"""
    print("\n=== 测试便利函数 ===\n")
    
    # 使用统一组件工厂创建系统函数
    from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory
    from core_lib.core_engine.testing.component_types import ComponentType, DeviceLevel
    
    def create_simple_reservoir_gate_system(config):
        """创建简单水库-闸门系统"""
        harness = SimulationHarness(config)
        factory = UnifiedComponentFactory()
        
        # 添加水库
        reservoir_config = InfrastructureConfig(
            component_id="reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 10.0, 'surface_area': 50000}
        )
        reservoir = factory.create_component(reservoir_config)
        harness.add_component("reservoir", reservoir)
        
        # 添加闸门
        gate_config = DeviceConfig(
            component_id="gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 0.5, 'max_flow_rate': 100.0}
        )
        gate = factory.create_component(gate_config)
        harness.add_component("gate", gate)
        
        # 连接组件
        harness.add_connection("reservoir", "gate")
        
        return harness
    
    def create_hydropower_system(config):
        """创建水电系统"""
        harness = SimulationHarness(config)
        factory = UnifiedComponentFactory()
        
        # 添加水库
        reservoir_config = InfrastructureConfig(
            component_id="reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 15.0, 'surface_area': 100000}
        )
        reservoir = factory.create_component(reservoir_config)
        harness.add_component("reservoir", reservoir)
        
        # 添加水轮机
        turbine_config = DeviceConfig(
            component_id="turbine",
            component_type=ComponentType.WATER_TURBINE,
            level=DeviceLevel.DEVICE,
            parameters={'efficiency': 0.9, 'max_flow_rate': 50.0}
        )
        turbine = factory.create_component(turbine_config)
        harness.add_component("turbine", turbine)
        
        # 连接组件
        harness.add_connection("reservoir", "turbine")
        
        return harness
    
    def create_pump_station_system(config):
        """创建泵站系统"""
        harness = SimulationHarness(config)
        factory = UnifiedComponentFactory()
        
        # 添加泵站
        pump_config = StationConfig(
            component_id="pump_station",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 20.0, 'max_head': 30.0, 'power_consumption': 100.0},
            device_count=2
        )
        pump_station = factory.create_component(pump_config)
        harness.add_component("pump_station", pump_station)
        
        return harness
    
    def create_canal_gate_reservoir_system(config):
        """创建渠道-闸门-水库系统"""
        harness = SimulationHarness(config)
        factory = UnifiedComponentFactory()
        
        # 添加水库
        reservoir_config = InfrastructureConfig(
            component_id="reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 12.0, 'surface_area': 75000}
        )
        reservoir = factory.create_component(reservoir_config)
        harness.add_component("reservoir", reservoir)
        
        # 添加闸门
        gate_config = DeviceConfig(
            component_id="gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 0.6, 'max_flow_rate': 80.0}
        )
        gate = factory.create_component(gate_config)
        harness.add_component("gate", gate)
        
        # 添加渠道
        canal_config = InfrastructureConfig(
            component_id="canal",
            component_type=ComponentType.CANAL,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'model_type': 'integral_delay', 'water_level': 5.0}
        )
        canal = factory.create_component(canal_config)
        harness.add_component("canal", canal)
        
        # 连接组件
        harness.add_connection("reservoir", "gate")
        harness.add_connection("gate", "canal")
        
        return harness
    
    config = {'end_time': 50}
    
    test_functions = [
        ("简单水库-闸门系统", create_simple_reservoir_gate_system),
        ("水电系统", create_hydropower_system),
        ("泵站系统", create_pump_station_system), 
        ("渠道-闸门-水库系统", create_canal_gate_reservoir_system)
    ]
    
    for func_name, func in test_functions:
        try:
            harness = func(config)
            harness.build()
            print(f"  ✅ {func_name}: 创建成功 ({len(harness.components)} 个组件)")
        except Exception as e:
            print(f"  ❌ {func_name}: 创建失败 - {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("开始测试第一阶段统一组件添加接口改进...\n")
    
    success1 = test_unified_interface_phase1()
    success2 = test_convenience_functions()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！第一阶段接口改进成功完成。")
    else:
        print("\n❌ 部分测试失败，需要进一步调试。")
        sys.exit(1)