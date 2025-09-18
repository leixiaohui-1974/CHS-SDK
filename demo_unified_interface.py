#!/usr/bin/env python3
"""统一组件添加接口改进演示脚本"""

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
from core_lib.physical_objects.pump import PumpStation

def demo_unified_interface():
    """演示统一组件添加接口"""
    print("=== 统一组件添加接口演示 ===\n")
    
    config = {'end_time': 100, 'time_step': 1.0}
    harness = SimulationHarness(config)
    factory = UnifiedComponentFactory()
    
    print("1. 使用统一接口添加组件：\n")
    
    # 使用统一接口添加不同类型的组件
    print("添加水库设施...")
    reservoir_config = InfrastructureConfig(
        component_id="main_reservoir",
        component_type=ComponentType.RESERVOIR,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'water_level': 15.0, 'surface_area': 50000}
    )
    reservoir = factory.create_component(reservoir_config)
    harness.add_component("main_reservoir", reservoir)
    print(f"  ✅ 创建了 {type(reservoir).__name__}: main_reservoir")
    
    print("\n添加单个闸门设备...")
    gate_config = DeviceConfig(
        component_id="control_gate",
        component_type=ComponentType.GATE,
        level=DeviceLevel.DEVICE,
        parameters={'opening': 0.6, 'max_flow_rate': 80.0}
    )
    gate = factory.create_component(gate_config)
    harness.add_component("control_gate", gate)
    print(f"  ✅ 创建了 {type(gate).__name__}: control_gate")
    
    print("\n添加泵站（包含多个泵设备）...")
    pump_station_config = StationConfig(
        component_id="main_pump_station",
        component_type=ComponentType.PUMP,
        level=DeviceLevel.STATION,
        parameters={'max_flow_rate': 20.0, 'max_head': 25.0, 'power_consumption': 100.0},
        device_count=3
    )
    pump_station = factory.create_component(pump_station_config)
    harness.add_component("main_pump_station", pump_station)
    print(f"  ✅ 创建了 {type(pump_station).__name__}: main_pump_station")
    
    print("\n添加单个水轮机设备...")
    turbine_config = DeviceConfig(
        component_id="power_turbine",
        component_type=ComponentType.WATER_TURBINE,
        level=DeviceLevel.DEVICE,
        parameters={'efficiency': 0.85, 'max_flow_rate': 60.0}
    )
    turbine = factory.create_component(turbine_config)
    harness.add_component("power_turbine", turbine)
    print(f"  ✅ 创建了 {type(turbine).__name__}: power_turbine")
    
    print("\n添加渠道设施...")
    canal_config = InfrastructureConfig(
        component_id="main_canal",
        component_type=ComponentType.CANAL,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'model_type': 'integral_delay', 'water_level': 3.0, 'gain': 0.002, 'delay': 180.0}
    )
    canal = factory.create_component(canal_config)
    harness.add_component("main_canal", canal)
    print(f"  ✅ 创建了 {type(canal).__name__}: main_canal")

def demo_business_logic_clarity():
    """演示业务逻辑清晰度改进"""
    print("\n\n=== 业务逻辑清晰度对比 ===\n")
    
    config = {'end_time': 100}
    harness = SimulationHarness(config)
    factory = UnifiedComponentFactory()
    
    print("2. 新接口清晰区分设备和站：\n")
    
    # 明确区分设备级别和站级别
    print("【设备级别】- 单个物理设备：")
    
    # 单个设备
    gate_config = DeviceConfig(
        component_id="gate_001",
        component_type=ComponentType.GATE,
        level=DeviceLevel.DEVICE,
        parameters={'opening': 0.5, 'max_flow_rate': 100.0}
    )
    gate_device = factory.create_component(gate_config)
    harness.add_component("gate_001", gate_device)
    print(f"  - 单个闸门设备: {gate_device.name}")
    
    turbine_config = DeviceConfig(
        component_id="turbine_001",
        component_type=ComponentType.WATER_TURBINE,
        level=DeviceLevel.DEVICE,
        parameters={'efficiency': 0.9, 'max_flow_rate': 30.0}
    )
    turbine_device = factory.create_component(turbine_config)
    harness.add_component("turbine_001", turbine_device)
    print(f"  - 单个水轮机设备: {turbine_device.name}")
    
    print("\n【站/设施级别】- 管理和运营单元：")
    
    # 站级别（包含多个设备）
    pump_config = StationConfig(
        component_id="ps_001",
        component_type=ComponentType.PUMP,
        level=DeviceLevel.STATION,
        parameters={'max_flow_rate': 15.0, 'max_head': 30.0, 'power_consumption': 100.0},
        device_count=4
    )
    pump_station = factory.create_component(pump_config)
    harness.add_component("ps_001", pump_station)
    # 类型断言确保是PumpStation
    assert isinstance(pump_station, PumpStation)
    print(f"  - 泵站（包含{len(pump_station.pumps)}个泵）: {pump_station.name}")
    
    # 设施级别
    reservoir_config = InfrastructureConfig(
        component_id="res_001",
        component_type=ComponentType.RESERVOIR,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'water_level': 20.0, 'surface_area': 100000}
    )
    reservoir = factory.create_component(reservoir_config)
    harness.add_component("res_001", reservoir)
    print(f"  - 水库设施: {reservoir.name}")
    
    canal_config = InfrastructureConfig(
        component_id="canal_001",
        component_type=ComponentType.CANAL,
        level=DeviceLevel.INFRASTRUCTURE,
        parameters={'model_type': 'linear_reservoir', 'water_level': 2.5}
    )
    canal = factory.create_component(canal_config)
    harness.add_component("canal_001", canal)
    print(f"  - 渠道设施: {canal.name}")

def demo_old_vs_new_api():
    """演示旧接口 vs 新接口对比"""
    print("\n\n=== 接口对比演示 ===\n")
    
    config = {'end_time': 100}
    harness = SimulationHarness(config)
    factory = UnifiedComponentFactory()
    
    print("3. 旧接口 vs 新统一接口：\n")
    
    print("【旧接口方式】- 混乱的命名：")
    print("  builder.add_pump_station()    # 为什么是'站'？")
    print("  builder.add_gate()            # 为什么不是'站'？")
    print("  builder.add_water_turbine()   # 为什么不是'站'？")
    print("  # 业务逻辑不清晰，命名不一致")
    
    print("\n【新统一接口】- 清晰的业务逻辑：")
    print("  # 统一方法，明确类型和级别")
    print("  factory.create_component(ComponentType.PUMP, DeviceLevel.DEVICE)     # 单个泵设备")
    print("  factory.create_component(ComponentType.PUMP, DeviceLevel.STATION)    # 泵站")
    print("  factory.create_component(ComponentType.GATE, DeviceLevel.DEVICE)     # 单个闸门")
    print("  factory.create_component(ComponentType.GATE, DeviceLevel.STATION)    # 闸站")
    
    # 实际创建示例
    print("\n实际创建示例：")
    
    # 使用新接口创建相同功能
    pump_station_config = StationConfig(
        component_id="new_pump_station",
        component_type=ComponentType.PUMP,
        level=DeviceLevel.STATION,
        parameters={'max_flow_rate': 10.0, 'max_head': 30.0, 'power_consumption': 100.0},
        device_count=3
    )
    pump_station_new = factory.create_component(pump_station_config)
    harness.add_component("new_pump_station", pump_station_new)
    # 类型断言确保是PumpStation
    assert isinstance(pump_station_new, PumpStation)
    print(f"  ✅ 新接口创建泵站: {pump_station_new.name} ({len(pump_station_new.pumps)}个泵)")

def show_todo_implementations():
    """显示已实现的功能"""
    print("\n\n=== 已实现功能 ===\n")
    
    print("4. 已实现的组件类型：\n")
    
    print("【已实现】✅")
    print("  - ComponentType.RESERVOIR (水库设施)")
    print("  - ComponentType.GATE + DeviceLevel.DEVICE (单个闸门)")  
    print("  - ComponentType.PUMP + DeviceLevel.STATION (泵站)")
    print("  - ComponentType.WATER_TURBINE + DeviceLevel.DEVICE (单个水轮机)")
    print("  - ComponentType.CANAL (渠道设施)")
    print("  - ComponentType.GATE + DeviceLevel.STATION (闸站)")
    print("  - ComponentType.HYDROPOWER_STATION (水电站)")
    print("  - ComponentType.VALVE + DeviceLevel.STATION (阀门站)")
    print("  ✅ 演示完成")

if __name__ == "__main__":
    print("开始演示统一组件添加接口改进...\n")
    
    try:
        demo_unified_interface()
        demo_business_logic_clarity()
        demo_old_vs_new_api()
        show_todo_implementations()
        
        print("\n🎉 统一接口演示完成！")
        print("\n💡 关键改进：")
        print("   ✅ 统一的add_component方法")
        print("   ✅ 明确的ComponentType枚举")
        print("   ✅ 清晰的DeviceLevel区分")
        print("   ✅ 一致的业务逻辑抽象")
        print("   ✅ 可扩展的架构设计")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)