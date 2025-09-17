#!/usr/bin/env python3
"""
配置驱动的组件创建系统

该模块实现了基于YAML/JSON配置文件的组件创建功能，
支持模板化、批量创建、参数验证等工程级特性。
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import asdict

from .component_types import (
    ComponentType, DeviceLevel, ComponentConfig, DeviceConfig,
    StationConfig, InfrastructureConfig, ComponentTypeMapping
)
from .unified_component_factory import UnifiedComponentFactory

class ConfigurationError(Exception):
    """配置错误异常"""
    pass

class ComponentConfigLoader:
    """组件配置加载器"""
    
    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.defaults: Dict[str, Dict[str, Any]] = {}
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        从文件加载配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            ConfigurationError: 配置加载或解析失败
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yml', '.yaml']:
                    return yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {file_path}: {e}")
    
    def load_templates(self, templates_dir: Union[str, Path]):
        """
        加载组件模板
        
        Args:
            templates_dir: 模板目录路径
        """
        templates_dir = Path(templates_dir)
        
        if not templates_dir.exists():
            return
        
        for template_file in templates_dir.glob("*.yml"):
            try:
                template_name = template_file.stem
                template_data = self.load_from_file(template_file)
                self.templates[template_name] = template_data
            except Exception as e:
                print(f"Warning: Failed to load template {template_file}: {e}")
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        return self.templates.get(template_name)
    
    def apply_template(self, config: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """
        应用模板到配置
        
        Args:
            config: 基础配置
            template_name: 模板名称
            
        Returns:
            应用模板后的配置
        """
        template = self.get_template(template_name)
        if not template:
            raise ConfigurationError(f"Template not found: {template_name}")
        
        # 深度合并配置
        merged_config = self._deep_merge(template.copy(), config)
        return merged_config
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

class ConfigDrivenComponentBuilder:
    """配置驱动的组件构建器"""
    
    def __init__(self, factory: UnifiedComponentFactory, config_loader: Optional[ComponentConfigLoader] = None):
        self.factory = factory
        self.config_loader = config_loader or ComponentConfigLoader()
        self.built_components: Dict[str, Any] = {}
    
    def build_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        从配置构建组件
        
        Args:
            config: 组件配置字典
            
        Returns:
            构建的组件字典
        """
        components = {}
        
        # 处理单个组件配置
        if 'component' in config:
            component_config = config['component']
            component = self._build_single_component(component_config)
            components[component_config['component_id']] = component
        
        # 处理多个组件配置
        elif 'components' in config:
            for component_config in config['components']:
                component = self._build_single_component(component_config)
                components[component_config['component_id']] = component
        
        # 处理系统配置（包含多个相关组件）
        elif 'systems' in config:
            for system_config in config['systems']:
                system_components = self._build_system(system_config)
                components.update(system_components)
        
        self.built_components.update(components)
        return components
    
    def build_from_file(self, config_file: Union[str, Path]) -> Dict[str, Any]:
        """
        从配置文件构建组件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            构建的组件字典
        """
        config = self.config_loader.load_from_file(config_file)
        return self.build_from_config(config)
    
    def _build_single_component(self, component_config: Dict[str, Any]) -> Any:
        """构建单个组件"""
        # 应用模板（如果指定）
        if 'template' in component_config:
            template_name = component_config.pop('template')
            component_config = self.config_loader.apply_template(component_config, template_name)
        
        # 验证必需字段
        required_fields = ['component_id', 'component_type']
        for field in required_fields:
            if field not in component_config:
                raise ConfigurationError(f"Missing required field: {field}")
        
        # 创建组件配置对象
        config_obj = self._create_config_object(component_config)
        
        # 使用工厂创建组件
        return self.factory.create_component(config_obj)
    
    def _build_system(self, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建系统（多个相关组件）"""
        system_type = system_config.get('type', 'generic')
        components = {}
        
        if system_type == 'pump_station_system':
            components.update(self._build_pump_station_system(system_config))
        elif system_type == 'hydropower_system':
            components.update(self._build_hydropower_system(system_config))
        elif system_type == 'canal_gate_system':
            components.update(self._build_canal_gate_system(system_config))
        else:
            # 通用系统：按顺序构建组件
            for component_config in system_config.get('components', []):
                component = self._build_single_component(component_config)
                components[component_config['component_id']] = component
        
        return components
    
    def _build_pump_station_system(self, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建泵站系统"""
        components = {}
        system_name = system_config.get('name', 'pump_system')
        
        # 源水库
        source_config = {
            'component_id': f"{system_name}_source",
            'component_type': 'reservoir',
            'parameters': system_config.get('source_reservoir', {
                'water_level': 10.0,
                'surface_area': 1e6
            })
        }
        components[source_config['component_id']] = self._build_single_component(source_config)
        
        # 泵站
        pump_config = {
            'component_id': f"{system_name}_pumps",
            'component_type': 'pump',
            'level': 'station',
            'parameters': system_config.get('pump_station', {
                'device_count': 3,
                'max_flow_rate': 10.0,
                'max_head': 20.0,
                'power_consumption': 50.0
            })
        }
        components[pump_config['component_id']] = self._build_single_component(pump_config)
        
        # 目标水库
        target_config = {
            'component_id': f"{system_name}_target",
            'component_type': 'reservoir',
            'parameters': system_config.get('target_reservoir', {
                'water_level': 25.0,
                'surface_area': 1e6
            })
        }
        components[target_config['component_id']] = self._build_single_component(target_config)
        
        return components
    
    def _build_hydropower_system(self, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建水电系统"""
        components = {}
        system_name = system_config.get('name', 'hydropower_system')
        
        # 上游水库
        upstream_config = {
            'component_id': f"{system_name}_upstream",
            'component_type': 'reservoir',
            'parameters': system_config.get('upstream_reservoir', {
                'water_level': 100.0,
                'surface_area': 1e5
            })
        }
        components[upstream_config['component_id']] = self._build_single_component(upstream_config)
        
        # 水电站
        hydropower_config = {
            'component_id': f"{system_name}_station",
            'component_type': 'water_turbine',
            'level': 'station',
            'parameters': system_config.get('hydropower_station', {
                'device_count': 2,
                'efficiency': 0.9,
                'max_flow_rate': 100.0
            })
        }
        components[hydropower_config['component_id']] = self._build_single_component(hydropower_config)
        
        # 下游水库
        downstream_config = {
            'component_id': f"{system_name}_downstream",
            'component_type': 'reservoir',
            'parameters': system_config.get('downstream_reservoir', {
                'water_level': 20.0,
                'surface_area': 1e5
            })
        }
        components[downstream_config['component_id']] = self._build_single_component(downstream_config)
        
        return components
    
    def _build_canal_gate_system(self, system_config: Dict[str, Any]) -> Dict[str, Any]:
        """构建渠道-闸门系统"""
        components = {}
        system_name = system_config.get('name', 'canal_gate_system')
        
        # 上游渠道
        upstream_canal_config = {
            'component_id': f"{system_name}_upstream_canal",
            'component_type': 'canal',
            'parameters': system_config.get('upstream_canal', {
                'model_type': 'integral_delay',
                'water_level': 3.0
            })
        }
        components[upstream_canal_config['component_id']] = self._build_single_component(upstream_canal_config)
        
        # 控制闸门
        gate_config = {
            'component_id': f"{system_name}_gate",
            'component_type': 'gate',
            'parameters': system_config.get('gate', {
                'opening': 0.6,
                'max_flow_rate': 50.0
            })
        }
        components[gate_config['component_id']] = self._build_single_component(gate_config)
        
        # 下游渠道
        downstream_canal_config = {
            'component_id': f"{system_name}_downstream_canal",
            'component_type': 'canal',
            'parameters': system_config.get('downstream_canal', {
                'model_type': 'linear_reservoir',
                'water_level': 2.5
            })
        }
        components[downstream_canal_config['component_id']] = self._build_single_component(downstream_canal_config)
        
        return components
    
    def _create_config_object(self, component_config: Dict[str, Any]) -> ComponentConfig:
        """创建组件配置对象"""
        component_type = ComponentType(component_config['component_type'])
        level_str = component_config.get('level')
        
        if level_str:
            level = DeviceLevel(level_str)
        else:
            level = ComponentTypeMapping.get_default_level(component_type)
        
        parameters = component_config.get('parameters', {})
        control_topic = component_config.get('control_topic')
        
        if level == DeviceLevel.STATION:
            return StationConfig(
                component_id=component_config['component_id'],
                component_type=component_type,
                level=level,
                parameters=parameters,
                control_topic=control_topic,
                device_count=parameters.get('device_count', 3),
                device_configs=parameters.get('device_configs')
            )
        elif level == DeviceLevel.INFRASTRUCTURE:
            return InfrastructureConfig(
                component_id=component_config['component_id'],
                component_type=component_type,
                level=level,
                parameters=parameters,
                control_topic=control_topic
            )
        else:
            return DeviceConfig(
                component_id=component_config['component_id'],
                component_type=component_type,
                level=level,
                parameters=parameters,
                control_topic=control_topic
            )
    
    def export_config(self, output_file: Union[str, Path], format: str = 'yaml'):
        """
        导出当前组件配置
        
        Args:
            output_file: 输出文件路径
            format: 输出格式 ('yaml' 或 'json')
        """
        config = {
            'components': []
        }
        
        for component_id, component in self.built_components.items():
            # 这里需要根据组件类型生成配置
            # 简化实现，实际应该根据组件属性反向生成配置
            component_config = {
                'component_id': component_id,
                'component_type': 'unknown',  # 需要实现类型推断
                'parameters': {}
            }
            config['components'].append(component_config)
        
        output_file = Path(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(config, f, default_flow_style=False, indent=2)
            else:
                json.dump(config, f, indent=2)

# ================================
# 配置模板示例
# ================================

COMPONENT_TEMPLATES = {
    'standard_pump_station': {
        'component_type': 'pump',
        'level': 'station',
        'parameters': {
            'device_count': 3,
            'max_flow_rate': 10.0,
            'max_head': 20.0,
            'power_consumption': 50.0
        }
    },
    'standard_reservoir': {
        'component_type': 'reservoir',
        'parameters': {
            'water_level': 10.0,
            'surface_area': 1e6
        }
    },
    'control_gate': {
        'component_type': 'gate',
        'parameters': {
            'opening': 0.5,
            'max_flow_rate': 100.0
        }
    },
    'hydropower_station': {
        'component_type': 'water_turbine',
        'level': 'station',
        'parameters': {
            'device_count': 2,
            'efficiency': 0.9,
            'max_flow_rate': 100.0
        }
    }
}

def create_sample_configs():
    """创建示例配置文件"""
    configs_dir = Path('sample_configs')
    configs_dir.mkdir(exist_ok=True)
    
    # 单个组件配置示例
    single_component_config = {
        'component': {
            'template': 'standard_pump_station',
            'component_id': 'main_pump_station',
            'control_topic': 'pump.control',
            'parameters': {
                'device_count': 4  # 覆盖模板中的默认值
            }
        }
    }
    
    with open(configs_dir / 'single_component.yml', 'w') as f:
        yaml.dump(single_component_config, f, default_flow_style=False, indent=2)
    
    # 系统配置示例
    system_config = {
        'systems': [
            {
                'type': 'pump_station_system',
                'name': 'main_water_supply',
                'source_reservoir': {
                    'water_level': 15.0,
                    'surface_area': 500000
                },
                'pump_station': {
                    'device_count': 4,
                    'max_flow_rate': 15.0
                },
                'target_reservoir': {
                    'water_level': 30.0,
                    'surface_area': 800000
                }
            }
        ]
    }
    
    with open(configs_dir / 'system_config.yml', 'w') as f:
        yaml.dump(system_config, f, default_flow_style=False, indent=2)
    
    print(f"Sample configuration files created in {configs_dir}")

if __name__ == "__main__":
    create_sample_configs()