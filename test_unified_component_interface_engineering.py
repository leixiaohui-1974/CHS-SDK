#!/usr/bin/env python3
"""
工程级别的统一组件接口测试套件

该测试套件提供全面的测试覆盖，包括：
- 组件类型系统测试
- 工厂模式测试  
- 配置驱动创建测试
- 参数验证测试
- 异常处理测试
- 性能基准测试
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

# 导入被测试的模块
from core_lib.core_engine.testing.component_types import (
    ComponentType, DeviceLevel, ComponentConfig, DeviceConfig,
    StationConfig, InfrastructureConfig, ComponentTypeMapping,
    ComponentCreationError, UnsupportedComponentTypeError,
    ComponentConfigError, ComponentValidationError
)
from core_lib.core_engine.testing.unified_component_factory import UnifiedComponentFactory
from core_lib.core_engine.testing.config_driven_builder import (
    ConfigDrivenComponentBuilder, ComponentConfigLoader, ConfigurationError
)
from core_lib.core_engine.testing.simulation_builder import HardcodedSimulationBuilder

class TestComponentTypeSystem:
    """组件类型系统测试"""
    
    def test_component_type_enum(self):
        """测试组件类型枚举"""
        # 验证所有组件类型都能正确创建
        expected_types = [
            'reservoir', 'canal', 'gate', 'pump', 'valve', 'water_turbine',
            'gate_station', 'pump_station', 'valve_station', 'hydropower_station'
        ]
        
        for type_name in expected_types:
            component_type = ComponentType(type_name)
            assert component_type.value == type_name
    
    def test_device_level_enum(self):
        """测试设备级别枚举"""
        expected_levels = ['infrastructure', 'device', 'station']
        
        for level_name in expected_levels:
            device_level = DeviceLevel(level_name)
            assert device_level.value == level_name
    
    def test_component_type_mapping(self):
        """测试组件类型映射"""
        # 测试默认级别映射
        assert ComponentTypeMapping.get_default_level(ComponentType.RESERVOIR) == DeviceLevel.INFRASTRUCTURE
        assert ComponentTypeMapping.get_default_level(ComponentType.GATE) == DeviceLevel.DEVICE
        assert ComponentTypeMapping.get_default_level(ComponentType.PUMP_STATION) == DeviceLevel.STATION
        
        # 测试站类型到设备类型的映射
        assert ComponentTypeMapping.get_station_device_type(ComponentType.PUMP_STATION) == ComponentType.PUMP
        assert ComponentTypeMapping.get_station_device_type(ComponentType.GATE_STATION) == ComponentType.GATE
    
    def test_component_config_creation(self):
        """测试组件配置对象创建"""
        # 测试基础配置
        config = ComponentConfig(
            component_id="test_component",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={'opening': 0.5}
        )
        
        assert config.component_id == "test_component"
        assert config.component_type == ComponentType.GATE
        assert config.level == DeviceLevel.DEVICE
        assert config.parameters['opening'] == 0.5
        
        # 测试站配置
        station_config = StationConfig(
            component_id="test_station",
            component_type=ComponentType.PUMP_STATION,
            level=DeviceLevel.STATION,
            parameters={'max_flow_rate': 10.0},
            device_count=3
        )
        
        assert station_config.device_count == 3
        assert isinstance(station_config, ComponentConfig)
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试空component_id应该抛出异常
        with pytest.raises(ValueError):
            ComponentConfig(
                component_id="",
                component_type=ComponentType.GATE,
                level=DeviceLevel.DEVICE,
                parameters={}
            )

class TestUnifiedComponentFactory:
    """统一组件工厂测试"""
    
    @pytest.fixture
    def factory(self):
        """创建工厂实例"""
        return UnifiedComponentFactory()
    
    def test_factory_initialization(self, factory):
        """测试工厂初始化"""
        assert factory is not None
        assert len(factory.get_supported_types()) > 0
    
    def test_reservoir_creation(self, factory):
        """测试水库创建"""
        config = InfrastructureConfig(
            component_id="test_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={
                'water_level': 15.0,
                'surface_area': 50000
            }
        )
        
        reservoir = factory.create_component(config)
        assert reservoir is not None
        assert reservoir.name == "test_reservoir"
    
    def test_gate_device_creation(self, factory):
        """测试闸门设备创建"""
        config = DeviceConfig(
            component_id="test_gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={
                'opening': 0.6,
                'max_flow_rate': 80.0
            }
        )
        
        gate = factory.create_component(config)
        assert gate is not None
        assert gate.name == "test_gate"
    
    def test_pump_station_creation(self, factory):
        """测试泵站创建"""
        config = StationConfig(
            component_id="test_pump_station",
            component_type=ComponentType.PUMP,
            level=DeviceLevel.STATION,
            parameters={
                'max_flow_rate': 15.0,
                'max_head': 25.0,
                'power_consumption': 60.0
            },
            device_count=4
        )
        
        pump_station = factory.create_component(config)
        assert pump_station is not None
        assert pump_station.name == "test_pump_station"
        assert len(pump_station.pumps) == 4
    
    def test_gate_station_creation(self, factory):
        """测试闸站创建"""
        config = StationConfig(
            component_id="test_gate_station",
            component_type=ComponentType.GATE,
            level=DeviceLevel.STATION,
            parameters={
                'max_flow_rate': 50.0
            },
            device_count=3
        )
        
        gate_station = factory.create_component(config)
        assert gate_station is not None
        assert gate_station.name == "test_gate_station"
        assert len(gate_station.gates) == 3
    
    def test_hydropower_station_creation(self, factory):
        """测试水电站创建"""
        config = StationConfig(
            component_id="test_hydropower_station",
            component_type=ComponentType.WATER_TURBINE,
            level=DeviceLevel.STATION,
            parameters={
                'efficiency': 0.85,
                'max_flow_rate': 100.0
            },
            device_count=2
        )
        
        hydropower_station = factory.create_component(config)
        assert hydropower_station is not None
        assert hydropower_station.name == "test_hydropower_station"
        assert len(hydropower_station.turbines) == 2
    
    def test_canal_creation(self, factory):
        """测试渠道创建"""
        config = InfrastructureConfig(
            component_id="test_canal", 
            component_type=ComponentType.CANAL,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={
                'model_type': 'integral_delay',
                'water_level': 3.0,
                'gain': 0.002,
                'delay': 180.0
            }
        )
        
        canal = factory.create_component(config)
        assert canal is not None
        assert canal.name == "test_canal"
    
    def test_unsupported_component_type(self, factory):
        """测试不支持的组件类型"""
        # 创建一个不存在的组件类型配置（通过修改枚举值）
        config = DeviceConfig(
            component_id="invalid_component",
            component_type=ComponentType.VALVE,  # 假设Valve尚未实现
            level=DeviceLevel.DEVICE,
            parameters={}
        )
        
        with pytest.raises(UnsupportedComponentTypeError):
            factory.create_component(config)
    
    def test_parameter_validation_errors(self, factory):
        """测试参数验证错误"""
        # 测试无效的水库参数
        config = InfrastructureConfig(
            component_id="invalid_reservoir",
            component_type=ComponentType.RESERVOIR,
            level=DeviceLevel.INFRASTRUCTURE,
            parameters={
                'water_level': -5.0,  # 负水位
                'surface_area': 0     # 零面积
            }
        )
        
        with pytest.raises(ComponentValidationError):
            factory.create_component(config)
        
        # 测试无效的闸门参数
        config = DeviceConfig(
            component_id="invalid_gate",
            component_type=ComponentType.GATE,
            level=DeviceLevel.DEVICE,
            parameters={
                'opening': 1.5,  # 超出范围
                'max_flow_rate': -10.0  # 负流量
            }
        )
        
        with pytest.raises(ComponentValidationError):
            factory.create_component(config)
    
    def test_create_from_dict(self, factory):
        """测试从字典创建组件"""
        config_dict = {
            'component_id': 'dict_reservoir',
            'component_type': 'reservoir',
            'parameters': {
                'water_level': 12.0,
                'surface_area': 60000
            }
        }
        
        component = factory.create_from_dict(config_dict)
        assert component is not None
        assert component.name == 'dict_reservoir'

class TestConfigDrivenBuilder:
    """配置驱动构建器测试"""
    
    @pytest.fixture
    def factory(self):
        return UnifiedComponentFactory()
    
    @pytest.fixture
    def config_loader(self):
        return ComponentConfigLoader()
    
    @pytest.fixture
    def builder(self, factory, config_loader):
        return ConfigDrivenComponentBuilder(factory, config_loader)
    
    def test_config_loader_json(self, config_loader):
        """测试JSON配置加载"""
        config_data = {
            'component': {
                'component_id': 'json_test',
                'component_type': 'gate',
                'parameters': {'opening': 0.7}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            loaded_config = config_loader.load_from_file(temp_path)
            assert loaded_config['component']['component_id'] == 'json_test'
        finally:
            Path(temp_path).unlink()
    
    def test_config_loader_yaml(self, config_loader):
        """测试YAML配置加载"""
        config_data = {
            'component': {
                'component_id': 'yaml_test',
                'component_type': 'pump',
                'level': 'station',
                'parameters': {'device_count': 3}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            loaded_config = config_loader.load_from_file(temp_path)
            assert loaded_config['component']['component_id'] == 'yaml_test'
        finally:
            Path(temp_path).unlink()
    
    def test_template_application(self, config_loader):
        """测试模板应用"""
        # 设置模板
        template = {
            'component_type': 'pump',
            'level': 'station',
            'parameters': {
                'device_count': 3,
                'max_flow_rate': 10.0,
                'max_head': 20.0
            }
        }
        config_loader.templates['test_template'] = template
        
        # 应用模板
        base_config = {
            'component_id': 'templated_pump',
            'parameters': {
                'device_count': 4  # 覆盖模板值
            }
        }
        
        result = config_loader.apply_template(base_config, 'test_template')
        
        assert result['component_type'] == 'pump'
        assert result['level'] == 'station'
        assert result['parameters']['device_count'] == 4  # 覆盖值
        assert result['parameters']['max_flow_rate'] == 10.0  # 模板值
    
    def test_single_component_build(self, builder):
        """测试单组件构建"""
        config = {
            'component': {
                'component_id': 'single_test',
                'component_type': 'reservoir',
                'parameters': {
                    'water_level': 8.0,
                    'surface_area': 40000
                }
            }
        }
        
        components = builder.build_from_config(config)
        assert len(components) == 1
        assert 'single_test' in components
    
    def test_multiple_components_build(self, builder):
        """测试多组件构建"""
        config = {
            'components': [
                {
                    'component_id': 'multi_reservoir',
                    'component_type': 'reservoir',
                    'parameters': {'water_level': 10.0, 'surface_area': 50000}
                },
                {
                    'component_id': 'multi_gate',
                    'component_type': 'gate',
                    'parameters': {'opening': 0.5, 'max_flow_rate': 100.0}
                }
            ]
        }
        
        components = builder.build_from_config(config)
        assert len(components) == 2
        assert 'multi_reservoir' in components
        assert 'multi_gate' in components
    
    def test_pump_station_system_build(self, builder):
        """测试泵站系统构建"""
        config = {
            'systems': [
                {
                    'type': 'pump_station_system',
                    'name': 'test_pump_system',
                    'source_reservoir': {'water_level': 12.0},
                    'pump_station': {'device_count': 2},
                    'target_reservoir': {'water_level': 28.0}
                }
            ]
        }
        
        components = builder.build_from_config(config)
        assert len(components) == 3
        assert 'test_pump_system_source' in components
        assert 'test_pump_system_pumps' in components
        assert 'test_pump_system_target' in components
    
    def test_hydropower_system_build(self, builder):
        """测试水电系统构建"""
        config = {
            'systems': [
                {
                    'type': 'hydropower_system',
                    'name': 'test_hydro_system',
                    'upstream_reservoir': {'water_level': 120.0},
                    'hydropower_station': {'device_count': 3},
                    'downstream_reservoir': {'water_level': 15.0}
                }
            ]
        }
        
        components = builder.build_from_config(config)
        assert len(components) == 3
        assert 'test_hydro_system_upstream' in components
        assert 'test_hydro_system_station' in components  
        assert 'test_hydro_system_downstream' in components
    
    def test_invalid_config_handling(self, builder):
        """测试无效配置处理"""
        # 缺少必需字段
        config = {
            'component': {
                'component_type': 'gate',  # 缺少component_id
                'parameters': {'opening': 0.5}
            }
        }
        
        with pytest.raises(ConfigurationError):
            builder.build_from_config(config)
    
    def test_file_not_found_error(self, builder):
        """测试文件不存在错误"""
        with pytest.raises(ConfigurationError):
            builder.build_from_file('non_existent_file.yml')

class TestSimulationBuilderIntegration:
    """仿真构建器集成测试"""
    
    @pytest.fixture
    def builder(self):
        config = {'end_time': 100, 'time_step': 1.0}
        return HardcodedSimulationBuilder(config)
    
    def test_new_unified_interface(self, builder):
        """测试新的统一接口"""
        # 使用新接口创建组件
        reservoir = builder.add_component(
            "integration_reservoir",
            ComponentType.RESERVOIR,
            water_level=20.0,
            surface_area=80000
        )
        
        gate = builder.add_component(
            "integration_gate",
            ComponentType.GATE,
            DeviceLevel.DEVICE,
            opening=0.8,
            max_flow_rate=120.0
        )
        
        pump_station = builder.add_component(
            "integration_pump_station",
            ComponentType.PUMP,
            DeviceLevel.STATION,
            device_count=5,
            max_flow_rate=12.0
        )
        
        assert reservoir is not None
        assert gate is not None  
        assert pump_station is not None
        
        # 验证组件已添加到构建器
        assert "integration_reservoir" in builder.components
        assert "integration_gate" in builder.components
        assert "integration_pump_station" in builder.components
    
    def test_config_driven_creation(self, builder):
        """测试配置驱动创建"""
        config_dict = {
            'component_id': 'config_driven_canal',
            'component_type': 'canal',  
            'parameters': {
                'model_type': 'linear_reservoir',
                'water_level': 2.8,
                'storage_constant': 900.0
            }
        }
        
        canal = builder.add_component_from_config(config_dict)
        assert canal is not None
        assert "config_driven_canal" in builder.components
    
    def test_supported_types_check(self, builder):
        """测试支持的类型检查"""
        supported_types = builder.get_supported_component_types()
        assert len(supported_types) > 0
        
        # 检查特定类型是否支持
        assert builder.is_component_supported(ComponentType.RESERVOIR, DeviceLevel.INFRASTRUCTURE)
        assert builder.is_component_supported(ComponentType.PUMP, DeviceLevel.STATION)
    
    def test_backward_compatibility(self, builder):
        """测试向后兼容性"""
        # 确保旧接口仍然可用
        reservoir = builder.add_reservoir("old_interface_reservoir", water_level=5.0)
        gate = builder.add_gate("old_interface_gate", opening=0.3)
        
        assert reservoir is not None
        assert gate is not None
        assert "old_interface_reservoir" in builder.components
        assert "old_interface_gate" in builder.components

class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    def test_component_creation_performance(self):
        """测试组件创建性能"""
        import time
        
        factory = UnifiedComponentFactory()
        
        # 创建大量组件并测量时间
        start_time = time.time()
        
        for i in range(100):
            config = DeviceConfig(
                component_id=f"perf_gate_{i}",
                component_type=ComponentType.GATE,
                level=DeviceLevel.DEVICE,
                parameters={'opening': 0.5, 'max_flow_rate': 100.0}
            )
            factory.create_component(config)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 每个组件创建应该在合理时间内完成
        avg_time_per_component = creation_time / 100
        assert avg_time_per_component < 0.1  # 小于100ms每个组件
        
        print(f"Average component creation time: {avg_time_per_component:.4f}s")
    
    def test_config_loading_performance(self):
        """测试配置加载性能"""
        import time
        
        # 创建大配置文件
        large_config = {
            'components': [
                {
                    'component_id': f'perf_component_{i}',
                    'component_type': 'gate',
                    'parameters': {'opening': 0.5}
                }
                for i in range(1000)
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_config, f)
            temp_path = f.name
        
        try:
            config_loader = ComponentConfigLoader()
            
            start_time = time.time()
            loaded_config = config_loader.load_from_file(temp_path)
            end_time = time.time()
            
            loading_time = end_time - start_time
            
            assert len(loaded_config['components']) == 1000
            assert loading_time < 1.0  # 加载应在1秒内完成
            
            print(f"Large config loading time: {loading_time:.4f}s")
            
        finally:
            Path(temp_path).unlink()

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])