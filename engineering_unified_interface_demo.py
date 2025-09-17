#!/usr/bin/env python3
"""
工程级别统一组件接口完整演示

该脚本展示了完整的工程级别统一组件接口系统，包括：
1. 类型系统和工厂模式
2. 配置驱动的组件创建  
3. 复杂系统的构建
4. 错误处理和验证
5. 性能监控和日志记录
"""

import sys
import json
import yaml
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.component_types import (
    ComponentType, DeviceLevel, ComponentConfig, StationConfig, ComponentTypeMapping
)
from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory
from core_lib.core_engine.testing.config_driven_builder import (
    ConfigDrivenComponentBuilder, ComponentConfigLoader
)
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
# Add imports for specific station classes
from core_lib.physical_objects.pump import PumpStation
from core_lib.physical_objects.stations import GateStation, HydropowerStation

def create_demo_configurations():
    """创建演示配置文件"""
    configs_dir = Path("demo_configs")
    configs_dir.mkdir(exist_ok=True)
    
    # 1. 复杂水利系统配置
    complex_system_config = {
        "metadata": {
            "name": "Complex Water Management System",
            "version": "1.0",
            "description": "A comprehensive water management system with multiple stations and controls"
        },
        "systems": [
            {
                "type": "pump_station_system",
                "name": "primary_water_supply",
                "source_reservoir": {
                    "water_level": 25.0,
                    "surface_area": 2000000
                },
                "pump_station": {
                    "device_count": 6,
                    "max_flow_rate": 20.0,
                    "max_head": 35.0,
                    "power_consumption": 75.0
                },
                "target_reservoir": {
                    "water_level": 45.0,
                    "surface_area": 1500000
                }
            },
            {
                "type": "hydropower_system", 
                "name": "renewable_energy_plant",
                "upstream_reservoir": {
                    "water_level": 150.0,
                    "surface_area": 500000
                },
                "hydropower_station": {
                    "device_count": 4,
                    "efficiency": 0.92,
                    "max_flow_rate": 200.0
                },
                "downstream_reservoir": {
                    "water_level": 30.0,
                    "surface_area": 800000
                }
            },
            {
                "type": "canal_gate_system",
                "name": "irrigation_control",
                "upstream_canal": {
                    "model_type": "integral_delay",
                    "water_level": 4.0,
                    "gain": 0.003,
                    "delay": 240.0
                },
                "gate": {
                    "opening": 0.7,
                    "max_flow_rate": 80.0,
                    "control_topic": "irrigation.gate_control"
                },
                "downstream_canal": {
                    "model_type": "linear_reservoir",
                    "water_level": 3.2,
                    "storage_constant": 1500.0
                }
            }
        ],
        "additional_components": [
            {
                "component_id": "emergency_gate_station",
                "component_type": "gate",
                "level": "station",
                "parameters": {
                    "device_count": 4,
                    "max_flow_rate": 60.0
                },
                "control_topic": "emergency.gate_control"
            },
            {
                "component_id": "monitoring_reservoir",
                "component_type": "reservoir",
                "parameters": {
                    "water_level": 12.0,
                    "surface_area": 300000
                }
            }
        ]
    }
    
    with open(configs_dir / "complex_system.yml", 'w', encoding='utf-8') as f:
        yaml.dump(complex_system_config, f, default_flow_style=False, indent=2)
    
    # 2. 单个组件配置示例
    single_components_config = {
        "components": [
            {
                "component_id": "main_supply_reservoir",
                "component_type": "reservoir",
                "parameters": {
                    "water_level": 18.0,
                    "surface_area": 1200000,
                    "volume": 21600000
                }
            },
            {
                "component_id": "primary_control_gate",
                "component_type": "gate",
                "parameters": {
                    "opening": 0.8,
                    "max_flow_rate": 150.0
                },
                "control_topic": "primary.gate_control"
            },
            {
                "component_id": "backup_pump_station",
                "component_type": "pump",
                "level": "station",
                "parameters": {
                    "device_count": 3,
                    "max_flow_rate": 18.0,
                    "max_head": 28.0,
                    "power_consumption": 65.0
                },
                "control_topic": "backup.pump_control"
            }
        ]
    }
    
    with open(configs_dir / "single_components.json", 'w', encoding='utf-8') as f:
        json.dump(single_components_config, f, indent=2)
    
    print(f"✅ Demo configuration files created in {configs_dir}")
    return configs_dir

def demonstrate_type_system():
    """演示类型系统功能"""
    print("\n🔧 === 类型系统演示 ===")
    
    # 1. 组件类型和级别
    print("\n1. 组件类型和级别映射:")
    for component_type in ComponentType:
        default_level = ComponentTypeMapping.get_default_level(component_type)
        print(f"   {component_type.value:20} -> {default_level.value}")
    
    # 2. 站类型到设备类型映射
    print("\n2. 站类型到设备类型映射:")
    station_types = [ComponentType.PUMP_STATION, ComponentType.GATE_STATION, ComponentType.HYDROPOWER_STATION]
    for station_type in station_types:
        device_type = ComponentTypeMapping.get_station_device_type(station_type)
        if device_type:
            print(f"   {station_type.value:20} -> {device_type.value}")
    
    # 3. 配置对象创建
    print("\n3. 配置对象创建示例:")
    configs = [
        StationConfig(
            component_id="demo_pump_station",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 15.0},
            device_count=4
        ),
        ComponentConfig(
            component_id="demo_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 20.0, 'surface_area': 100000}
        )
    ]
    
    for config in configs:
        print(f"   {config.component_id}: {config.component_type.value} ({config.level.value})")

def demonstrate_factory_pattern():
    """演示工厂模式功能"""
    print("\n🏭 === 工厂模式演示 ===")
    
    factory = UnifiedComponentFactory()
    
    # 1. 支持的组件类型
    print(f"\n1. 支持的组件类型 ({len(factory.get_supported_types())} 种):")
    for type_key in factory.get_supported_types():
        print(f"   ✓ {type_key}")
    
    # 2. 创建各种类型组件
    print("\n2. 创建不同类型的组件:")
    
    test_configs = [
        # 水库
        ComponentConfig(
            component_id="factory_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': 22.0, 'surface_area': 150000}
        ),
        # 单个闸门
        ComponentConfig(
            component_id="factory_gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 0.6, 'max_flow_rate': 90.0}
        ),
        # 泵站
        StationConfig(
            component_id="factory_pump_station",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 12.0, 'max_head': 25.0, 'power_consumption': 55.0},
            device_count=3
        ),
        # 水电站
        StationConfig(
            component_id="factory_hydropower_station",
            component_type=ComponentType.WATER_TURBINE,
            level=DeviceLevel.STATION,
            parameters={'efficiency': 0.88, 'max_flow_rate': 120.0},
            device_count=2
        )
    ]
    
    created_components = {}
    for config in test_configs:
        try:
            start_time = time.time()
            component = factory.create_component(config)
            creation_time = time.time() - start_time
            
            created_components[config.component_id] = component
            
            # 显示创建信息
            component_info = f"{config.component_type.value} ({config.level.value})"
            print(f"   ✅ {config.component_id}: {component_info} - {creation_time*1000:.2f}ms")
            
            # 显示特殊属性
            if isinstance(component, PumpStation):
                print(f"      └── 包含 {len(component.pumps)} 个泵设备")
            elif isinstance(component, GateStation):
                print(f"      └── 包含 {len(component.gates)} 个闸门设备")  
            elif isinstance(component, HydropowerStation):
                print(f"      └── 包含 {len(component.turbines)} 个水轮机设备")

        except Exception as e:
            print(f"   ❌ {config.component_id}: 创建失败 - {e}")
    
    return created_components

def demonstrate_config_driven_creation():
    """演示配置驱动创建"""
    print("\n📋 === 配置驱动创建演示 ===")
    
    factory = UnifiedComponentFactory()
    config_loader = ComponentConfigLoader()
    builder = ConfigDrivenComponentBuilder(factory, config_loader)
    
    configs_dir = Path("demo_configs")
    
    # 1. 从单组件配置文件创建
    if (configs_dir / "single_components.json").exists():
        print("\n1. 从单组件配置文件创建:")
        components = builder.build_from_file(configs_dir / "single_components.json")
        
        for comp_id, component in components.items():
            print(f"   ✅ {comp_id}: {type(component).__name__}")
    
    # 2. 从复杂系统配置创建
    if (configs_dir / "complex_system.yml").exists():
        print("\n2. 从复杂系统配置创建:")
        components = builder.build_from_file(configs_dir / "complex_system.yml")
        
        print(f"   创建了 {len(components)} 个组件:")
        for comp_id, component in components.items():
            component_type = type(component).__name__
            print(f"   ✅ {comp_id}: {component_type}")
    
    # 3. 动态配置创建
    print("\n3. 动态配置创建:")
    dynamic_config = {
        "components": [
            {
                "component_id": "dynamic_canal",
                "component_type": "canal",
                "parameters": {
                    "model_type": "integral_delay_zero",
                    "water_level": 3.5,
                    "gain": 0.0025,
                    "delay": 200.0,
                    "zero_time_constant": 60.0
                }
            }
        ]
    }
    
    dynamic_components = builder.build_from_config(dynamic_config)
    for comp_id, component in dynamic_components.items():
        print(f"   ✅ {comp_id}: {type(component).__name__} (动态创建)")

def demonstrate_simulation_harness_integration():
    """演示仿真框架集成"""
    print("\n🚀 === 仿真框架集成演示 ===")
    
    # 创建仿真框架
    config = {'end_time': 3600, 'time_step': 1.0}
    harness = SimulationHarness(config)
    factory = UnifiedComponentFactory(harness=harness, message_bus=getattr(harness, 'message_bus', None))
    
    print(f"\n1. 仿真配置: {config}")
    print(f"2. 支持的组件类型: {len(factory.get_supported_types())} 种")
    
    # 使用统一工厂创建复杂系统
    print("\n3. 使用统一工厂创建完整水利系统:")
    
    try:
        # 主水库
        main_reservoir_config = ComponentConfig(
            component_id="main_water_reservoir",
            component_type=ComponentType.RESERVOIR,
            parameters={'water_level': 35.0, 'surface_area': 3000000},
            level=DeviceLevel.INFRASTRUCTURE
        )
        main_reservoir = factory.create_component(main_reservoir_config)
        print(f"   ✅ 主水库: {main_reservoir.name}")
        
        # 主控闸门
        control_gate_config = ComponentConfig(
            component_id="main_control_gate",
            component_type=ComponentType.GATE,
            parameters={'opening': 0.75, 'max_flow_rate': 200.0},
            level=DeviceLevel.DEVICE,
            control_topic="main.gate_control"
        )
        control_gate = factory.create_component(control_gate_config)
        print(f"   ✅ 主控闸门: {control_gate.name}")
        
        # 输水渠道
        transport_canal_config = ComponentConfig(
            component_id="main_transport_canal",
            component_type=ComponentType.CANAL,
            parameters={'model_type': 'integral_delay', 'water_level': 4.5, 'gain': 0.0035, 'delay': 300.0},
            level=DeviceLevel.INFRASTRUCTURE,
            control_topic="canal.flow_control"
        )
        transport_canal = factory.create_component(transport_canal_config)
        print(f"   ✅ 输水渠道: {transport_canal.name}")
        
        # 加压泵站
        booster_pumps_config = StationConfig(
            component_id="booster_pump_station",
            component_type=ComponentType.PUMP,
            parameters={'max_flow_rate': 25.0, 'max_head': 40.0, 'power_consumption': 80.0},
            level=DeviceLevel.STATION,
            control_topic="booster.pump_control",
            device_count=5
        )
        booster_pumps = factory.create_component(booster_pumps_config)
        if isinstance(booster_pumps, PumpStation):
            pump_count = len(booster_pumps.pumps)
        else:
            pump_count = 0
        print(f"   ✅ 加压泵站: {booster_pumps.name} ({pump_count} 个泵)")
        
        # 应急闸站
        emergency_gates_config = StationConfig(
            component_id="emergency_gate_station",
            component_type=ComponentType.GATE,
            parameters={'max_flow_rate': 70.0},
            level=DeviceLevel.STATION,
            control_topic="emergency.gate_control",
            device_count=3
        )
        emergency_gates = factory.create_component(emergency_gates_config)
        if isinstance(emergency_gates, GateStation):
            gate_count = len(emergency_gates.gates)
        else:
            gate_count = 0
        print(f"   ✅ 应急闸站: {emergency_gates.name} ({gate_count} 个闸门)")
        
        # 终端水库
        terminal_reservoir_config = ComponentConfig(
            component_id="terminal_reservoir",
            component_type=ComponentType.RESERVOIR,
            parameters={'water_level': 15.0, 'surface_area': 1000000},
            level=DeviceLevel.INFRASTRUCTURE
        )
        terminal_reservoir = factory.create_component(terminal_reservoir_config)
        print(f"   ✅ 终端水库: {terminal_reservoir.name}")
        
        # 建立连接
        connections = [
            ("main_water_reservoir", "main_control_gate"),
            ("main_control_gate", "main_transport_canal"),
            ("main_transport_canal", "booster_pump_station"),
            ("booster_pump_station", "emergency_gate_station"),
            ("emergency_gate_station", "terminal_reservoir")
        ]
        
        for upstream_id, downstream_id in connections:
            harness.add_connection(upstream_id, downstream_id)
        
        print(f"\n4. 建立了 {len(connections)} 个组件连接")
        
        # 构建仿真
        harness.build()
        print("5. ✅ 仿真系统构建完成")
        
        # 系统统计
        total_components = len([comp for comp_id, comp in harness.components.items()])
        print(f"\n📊 系统统计:")
        print(f"   - 总组件数: {total_components}")
        print(f"   - 水库数: 2")
        print(f"   - 闸门/闸站数: 2") 
        print(f"   - 泵站数: 1")
        print(f"   - 渠道数: 1")
        print(f"   - 连接数: {len(connections)}")
        
    except Exception as e:
        print(f"   ❌ 系统创建失败: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_error_handling():
    """演示错误处理"""
    print("\n⚠️  === 错误处理演示 ===")
    
    factory = UnifiedComponentFactory()
    
    # 1. 参数验证错误
    print("\n1. 参数验证错误:")
    invalid_configs = [
        # 负水位
        ComponentConfig(
            component_id="invalid_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={'water_level': -10.0, 'surface_area': 100000}
        ),
        # 开度超范围
        ComponentConfig(
            component_id="invalid_gate", 
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 1.5, 'max_flow_rate': 100.0}
        ),
        # 零设备数量
        StationConfig(
            component_id="invalid_pump_station",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 10.0},
            device_count=0
        )
    ]
    
    for config in invalid_configs:
        try:
            factory.create_component(config)
            print(f"   ❌ {config.component_id}: 应该失败但成功了")
        except Exception as e:
            print(f"   ✅ {config.component_id}: 正确捕获错误 - {type(e).__name__}")
    
    # 2. 不支持的组件类型
    print("\n2. 不支持的组件类型:")
    try:
        # 尝试创建阀门（假设未实现）
        unsupported_config = ComponentConfig(
            component_id="unsupported_valve",
            component_type=ComponentType.VALVE,
            level=DeviceLevel.DEVICE,
            parameters={}
        )
        factory.create_component(unsupported_config)
        print("   ❌ 应该抛出UnsupportedComponentTypeError")
    except Exception as e:
        print(f"   ✅ 正确捕获错误: {type(e).__name__}")

def demonstrate_performance_monitoring():
    """演示性能监控"""
    print("\n📈 === 性能监控演示 ===")
    
    factory = UnifiedComponentFactory()
    
    # 批量创建组件并监控性能
    component_counts = [10, 50, 100]
    
    for count in component_counts:
        print(f"\n创建 {count} 个组件的性能测试:")
        
        start_time = time.time()
        created_components = []
        
        for i in range(count):
            config = ComponentConfig(
                component_id=f"perf_gate_{i}",
                component_type=ComponentType.GATE,
                level=DeviceLevel.DEVICE,
                parameters={'opening': 0.5, 'max_flow_rate': 100.0}
            )
            component = factory.create_component(config)
            created_components.append(component)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / count
        
        print(f"   总时间: {total_time:.4f}s")
        print(f"   平均时间: {avg_time*1000:.2f}ms/组件")
        print(f"   创建速率: {count/total_time:.1f} 组件/秒")

def main():
    """主演示函数"""
    print("🌊 === 工程级别统一组件接口完整演示 ===")
    print("这个演示展示了完整的工程级别统一组件接口系统")
    
    try:
        # 创建演示配置
        configs_dir = create_demo_configurations()
        
        # 各个功能演示
        demonstrate_type_system()
        demonstrate_factory_pattern()
        demonstrate_config_driven_creation()
        demonstrate_simulation_harness_integration()
        demonstrate_error_handling()
        demonstrate_performance_monitoring()
        
        print("\n🎉 === 演示完成 ===")
        print("\n✨ 主要改進成果:")
        print("   ✅ 完整的类型系统 - 清晰的组件分类和级别")
        print("   ✅ 统一的工厂模式 - 一致的创建接口")
        print("   ✅ 配置驱动创建 - 支持YAML/JSON配置")
        print("   ✅ 参数验证系统 - 完整的错误处理")
        print("   ✅ 工程级别测试 - 全面的测试覆盖")
        print("   ✅ 性能优化设计 - 高效的组件创建")
        print("   ✅ 向后兼容性 - 保持现有API可用")
        
        print(f"\n📁 配置文件位置: {configs_dir.absolute()}")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)