#!/usr/bin/env python3
"""
工程级别的组件类型系统和接口定义

该模块定义了仿真系统中所有组件的类型系统、抽象接口和创建规范，
确保组件层次清晰、接口统一、类型安全。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Type, Union, Protocol
from dataclasses import dataclass

# ================================
# 组件类型系统
# ================================

class ComponentType(Enum):
    """标准化组件类型枚举"""
    # 基础设施类型
    RESERVOIR = "reservoir"
    CANAL = "canal"
    
    # 单体设备类型
    GATE = "gate"
    PUMP = "pump"
    VALVE = "valve"
    WATER_TURBINE = "water_turbine"
    
    # 复合设施类型（站）
    GATE_STATION = "gate_station"
    PUMP_STATION = "pump_station"
    VALVE_STATION = "valve_station"
    HYDROPOWER_STATION = "hydropower_station"

class DeviceLevel(Enum):
    """设备级别枚举"""
    INFRASTRUCTURE = "infrastructure"  # 基础设施（水库、渠道）
    DEVICE = "device"                  # 单体设备
    STATION = "station"               # 复合设施（站）

class ComponentCategory(Enum):
    """组件功能分类"""
    STORAGE = "storage"           # 存储类（水库）
    TRANSPORT = "transport"       # 输送类（渠道、管道）
    CONTROL = "control"          # 控制类（闸门、阀门）
    POWER = "power"              # 动力类（泵、水轮机）
    FACILITY = "facility"        # 设施类（各种站）

# ================================
# 配置数据结构
# ================================

@dataclass
class ComponentConfig:
    """组件配置基类"""
    component_id: str
    component_type: ComponentType
    parameters: Dict[str, Any]
    level: DeviceLevel
    control_topic: Optional[str] = None
    
    def __post_init__(self):
        """配置验证"""
        if not self.component_id.strip():
            raise ValueError("component_id cannot be empty")

@dataclass
class DeviceConfig(ComponentConfig):
    """单体设备配置"""
    level: DeviceLevel = DeviceLevel.DEVICE

@dataclass 
class StationConfig(ComponentConfig):
    """站类设施配置"""
    level: DeviceLevel = DeviceLevel.STATION
    device_count: int = 1
    device_configs: Optional[List[Dict[str, Any]]] = None

@dataclass
class InfrastructureConfig(ComponentConfig):
    """基础设施配置"""
    level: DeviceLevel = DeviceLevel.INFRASTRUCTURE

# ================================
# 抽象接口定义
# ================================

class ComponentCreator(ABC):
    """组件创建器抽象接口"""
    
    @abstractmethod
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        """检查是否能创建指定类型的组件"""
        pass
    
    @abstractmethod
    def create(self, config: ComponentConfig) -> Any:
        """创建组件实例"""
        pass
    
    @abstractmethod
    def validate_config(self, config: ComponentConfig) -> bool:
        """验证配置有效性"""
        pass

class ComponentValidator(Protocol):
    """组件验证器协议"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        ...
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证约束条件"""
        ...

# ================================
# 组件类型映射
# ================================

class ComponentTypeMapping:
    """组件类型映射工具类"""
    
    # 类型到级别的默认映射
    DEFAULT_LEVELS = {
        ComponentType.RESERVOIR: DeviceLevel.INFRASTRUCTURE,
        ComponentType.CANAL: DeviceLevel.INFRASTRUCTURE,
        ComponentType.GATE: DeviceLevel.DEVICE,
        ComponentType.PUMP: DeviceLevel.DEVICE,
        ComponentType.VALVE: DeviceLevel.DEVICE,
        ComponentType.WATER_TURBINE: DeviceLevel.DEVICE,
        ComponentType.GATE_STATION: DeviceLevel.STATION,
        ComponentType.PUMP_STATION: DeviceLevel.STATION,
        ComponentType.VALVE_STATION: DeviceLevel.STATION,
        ComponentType.HYDROPOWER_STATION: DeviceLevel.STATION,
    }
    
    # 类型到分类的映射
    TYPE_CATEGORIES = {
        ComponentType.RESERVOIR: ComponentCategory.STORAGE,
        ComponentType.CANAL: ComponentCategory.TRANSPORT,
        ComponentType.GATE: ComponentCategory.CONTROL,
        ComponentType.PUMP: ComponentCategory.POWER,
        ComponentType.VALVE: ComponentCategory.CONTROL,
        ComponentType.WATER_TURBINE: ComponentCategory.POWER,
        ComponentType.GATE_STATION: ComponentCategory.FACILITY,
        ComponentType.PUMP_STATION: ComponentCategory.FACILITY,
        ComponentType.VALVE_STATION: ComponentCategory.FACILITY,
        ComponentType.HYDROPOWER_STATION: ComponentCategory.FACILITY,
    }
    
    @classmethod
    def get_default_level(cls, component_type: ComponentType) -> DeviceLevel:
        """获取组件类型的默认级别"""
        return cls.DEFAULT_LEVELS.get(component_type, DeviceLevel.DEVICE)
    
    @classmethod
    def get_category(cls, component_type: ComponentType) -> ComponentCategory:
        """获取组件类型的功能分类"""
        return cls.TYPE_CATEGORIES.get(component_type, ComponentCategory.FACILITY)
    
    @classmethod
    def get_station_device_type(cls, station_type: ComponentType) -> Optional[ComponentType]:
        """获取站类型对应的设备类型"""
        mapping = {
            ComponentType.GATE_STATION: ComponentType.GATE,
            ComponentType.PUMP_STATION: ComponentType.PUMP,
            ComponentType.VALVE_STATION: ComponentType.VALVE,
            ComponentType.HYDROPOWER_STATION: ComponentType.WATER_TURBINE,
        }
        return mapping.get(station_type)

# ================================
# 异常体系
# ================================

class ComponentCreationError(Exception):
    """组件创建异常基类"""
    pass

class UnsupportedComponentTypeError(ComponentCreationError):
    """不支持的组件类型异常"""
    def __init__(self, component_type: ComponentType, level: DeviceLevel):
        super().__init__(f"Unsupported component type: {component_type} at level {level}")
        self.component_type = component_type
        self.level = level

class ComponentConfigError(ComponentCreationError):
    """组件配置异常"""
    def __init__(self, message: str, config: ComponentConfig):
        super().__init__(f"Configuration error for {config.component_id}: {message}")
        self.config = config

class ComponentValidationError(ComponentCreationError):
    """组件验证异常"""
    def __init__(self, component_id: str, validation_errors: List[str]):
        error_msg = f"Validation failed for {component_id}: {'; '.join(validation_errors)}"
        super().__init__(error_msg)
        self.component_id = component_id
        self.validation_errors = validation_errors

# ================================
# 工厂接口
# ================================

class ComponentFactory(ABC):
    """组件工厂抽象基类"""
    
    def __init__(self):
        self._creators: Dict[str, ComponentCreator] = {}
        self._validators: Dict[ComponentType, ComponentValidator] = {}
    
    def register_creator(self, key: str, creator: ComponentCreator):
        """注册组件创建器"""
        self._creators[key] = creator
    
    def register_validator(self, component_type: ComponentType, validator: ComponentValidator):
        """注册组件验证器"""
        self._validators[component_type] = validator
    
    @abstractmethod
    def create_component(self, config: ComponentConfig) -> Any:
        """创建组件"""
        pass
    
    def _get_creator_key(self, component_type: ComponentType, level: DeviceLevel) -> str:
        """获取创建器键值"""
        return f"{component_type.value}_{level.value}"
    
    def _validate_config(self, config: ComponentConfig) -> List[str]:
        """验证配置并返回错误列表"""
        errors = []
        
        # 基础验证
        if not config.component_id.strip():
            errors.append("component_id cannot be empty")
        
        # 类型验证器验证
        validator = self._validators.get(config.component_type)
        if validator:
            try:
                if not validator.validate_parameters(config.parameters):
                    errors.append("parameter validation failed")
                if not validator.validate_constraints(config):
                    errors.append("constraint validation failed")
            except Exception as e:
                errors.append(f"validation error: {str(e)}")
        
        return errors