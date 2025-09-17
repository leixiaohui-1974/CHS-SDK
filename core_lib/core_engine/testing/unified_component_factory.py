#!/usr/bin/env python3
"""
工程级别的统一组件工厂实现

该模块实现了完整的组件工厂模式，包括创建器注册、参数验证、
配置驱动的组件创建等功能，确保工程级别的代码质量和可维护性。
"""

from typing import Dict, Any, List, Optional, Type, Union
import logging
from dataclasses import asdict

from .component_types import (
    ComponentType, DeviceLevel, ComponentConfig, DeviceConfig, 
    StationConfig, InfrastructureConfig, ComponentCreator, 
    ComponentValidator, ComponentFactory, ComponentTypeMapping,
    ComponentCreationError, UnsupportedComponentTypeError,
    ComponentConfigError, ComponentValidationError
)

from core_lib.core.interfaces import PhysicalObjectInterface
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.stations import (
    GateStation, HydropowerStation, ValveStation,
    create_gate_station, create_hydropower_station, create_valve_station
)
from core_lib.core.event_bus import SimpleEventBus

logger = logging.getLogger(__name__)

# ================================
# 组件验证器实现
# ================================

class ReservoirValidator:
    """水库组件验证器"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证水库参数"""
        water_level = parameters.get('water_level', 0)
        surface_area = parameters.get('surface_area', 0)
        
        if water_level < 0:
            return False
        if surface_area <= 0:
            return False
        
        return True
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证水库约束条件"""
        return config.level == DeviceLevel.INFRASTRUCTURE

class GateValidator:
    """闸门组件验证器"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证闸门参数"""
        opening = parameters.get('opening', 0.5)
        max_flow_rate = parameters.get('max_flow_rate', 0)
        
        if not (0.0 <= opening <= 1.0):
            return False
        if max_flow_rate <= 0:
            return False
            
        return True
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证闸门约束条件"""
        return config.level in [DeviceLevel.DEVICE, DeviceLevel.STATION]

class PumpValidator:
    """泵组件验证器"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证泵参数"""
        max_flow_rate = parameters.get('max_flow_rate', 0)
        max_head = parameters.get('max_head', 0)
        power_consumption = parameters.get('power_consumption', 0)
        
        if max_flow_rate <= 0 or max_head <= 0 or power_consumption <= 0:
            return False
            
        return True
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证泵约束条件"""
        if config.level == DeviceLevel.STATION:
            # 站级别需要设备数量信息
            if isinstance(config, StationConfig):
                return config.device_count >= 1
            return False
        return config.level == DeviceLevel.DEVICE

class TurbineValidator:
    """水轮机组件验证器"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证水轮机参数"""
        efficiency = parameters.get('efficiency', 0)
        max_flow_rate = parameters.get('max_flow_rate', 0)
        
        if not (0.0 <= efficiency <= 1.0):
            return False
        if max_flow_rate <= 0:
            return False
            
        return True
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证水轮机约束条件"""
        return config.level in [DeviceLevel.DEVICE, DeviceLevel.STATION]

class CanalValidator:
    """渠道组件验证器"""
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证渠道参数"""
        model_type = parameters.get('model_type', '')
        water_level = parameters.get('water_level', 0)
        
        valid_models = ['integral', 'integral_delay', 'integral_delay_zero', 'linear_reservoir']
        if model_type not in valid_models:
            return False
        if water_level < 0:
            return False
            
        return True
    
    def validate_constraints(self, config: ComponentConfig) -> bool:
        """验证渠道约束条件"""
        return config.level == DeviceLevel.INFRASTRUCTURE

# ================================
# 组件创建器实现
# ================================

class ReservoirCreator(ComponentCreator):
    """水库创建器"""
    
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        return (component_type == ComponentType.RESERVOIR and 
                level == DeviceLevel.INFRASTRUCTURE)
    
    def create(self, config: ComponentConfig) -> Reservoir:
        """创建水库组件"""
        self.validate_config(config)
        
        water_level = config.parameters.get('water_level', 10.0)
        surface_area = config.parameters.get('surface_area', 1e6)
        volume = config.parameters.get('volume')
        
        if volume is None:
            volume = water_level * surface_area
        
        initial_state = {
            'water_level': water_level,
            'volume': volume,
            'outflow': 0
        }
        
        parameters = {'surface_area': surface_area}
        
        return Reservoir(config.component_id, initial_state, parameters)
    
    def validate_config(self, config: ComponentConfig) -> bool:
        validator = ReservoirValidator()
        if not validator.validate_parameters(config.parameters):
            raise ComponentConfigError("Invalid reservoir parameters", config)
        if not validator.validate_constraints(config):
            raise ComponentConfigError("Invalid reservoir constraints", config)
        return True

class GateCreator(ComponentCreator):
    """闸门创建器"""
    
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        return (component_type == ComponentType.GATE and 
                level in [DeviceLevel.DEVICE, DeviceLevel.STATION])
    
    def create(self, config: ComponentConfig) -> Union[Gate, GateStation]:
        """创建闸门组件"""
        self.validate_config(config)
        
        if config.level == DeviceLevel.DEVICE:
            return self._create_gate_device(config)
        else:
            # 确保config是StationConfig类型
            if not isinstance(config, StationConfig):
                # 创建StationConfig实例
                station_config = StationConfig(
                    component_id=config.component_id,
                    component_type=config.component_type,
                    level=config.level,
                    parameters=config.parameters,
                    control_topic=config.control_topic,
                    device_count=config.parameters.get('device_count', 3)
                )
                return self._create_gate_station(station_config)
            return self._create_gate_station(config)
    
    def _create_gate_device(self, config: ComponentConfig) -> Gate:
        """创建单个闸门设备"""
        opening = config.parameters.get('opening', 0.5)
        max_flow_rate = config.parameters.get('max_flow_rate', 100.0)
        
        initial_state = {'opening': opening, 'outflow': 0}
        parameters = {'max_flow_rate': max_flow_rate}
        
        # TODO: 需要从config获取message_bus
        return Gate(config.component_id, initial_state, parameters)
    
    def _create_gate_station(self, config: StationConfig) -> GateStation:
        """创建闸站"""
        device_count = config.device_count
        device_configs = config.device_configs or []
        
        # 如果没有提供详细配置，使用默认配置
        if not device_configs:
            device_configs = [
                {
                    'name': f"{config.component_id}_gate_{i+1}",
                    'initial_state': {'opening': 0.5, 'outflow': 0.0},
                    'parameters': {'max_flow_rate': 50.0}
                }
                for i in range(device_count)
            ]
        
        return create_gate_station(
            name=config.component_id,
            gate_configs=device_configs,
            station_params=config.parameters
        )
    
    def validate_config(self, config: ComponentConfig) -> bool:
        validator = GateValidator()
        if not validator.validate_parameters(config.parameters):
            raise ComponentConfigError("Invalid gate parameters", config)
        if not validator.validate_constraints(config):
            raise ComponentConfigError("Invalid gate constraints", config)
        return True

class PumpCreator(ComponentCreator):
    """泵创建器"""
    
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        return (component_type == ComponentType.PUMP and 
                level in [DeviceLevel.DEVICE, DeviceLevel.STATION])
    
    def create(self, config: ComponentConfig) -> Union[Pump, PumpStation]:
        """创建泵组件"""
        self.validate_config(config)
        
        if config.level == DeviceLevel.DEVICE:
            return self._create_pump_device(config)
        else:
            # 确保config是StationConfig类型
            if not isinstance(config, StationConfig):
                # 创建StationConfig实例
                station_config = StationConfig(
                    component_id=config.component_id,
                    component_type=config.component_type,
                    level=config.level,
                    parameters=config.parameters,
                    control_topic=config.control_topic,
                    device_count=config.parameters.get('device_count', 3)
                )
                return self._create_pump_station(station_config)
            return self._create_pump_station(config)
    
    def _create_pump_device(self, config: ComponentConfig) -> Pump:
        """创建单个泵设备"""
        max_flow_rate = config.parameters.get('max_flow_rate', 10.0)
        max_head = config.parameters.get('max_head', 20.0)
        power_consumption = config.parameters.get('power_consumption', 50.0)
        
        pump_params = {
            'max_flow_rate': max_flow_rate,
            'max_head': max_head,
            'power_consumption_kw': power_consumption
        }
        
        # TODO: 需要从config获取message_bus和control_topic
        return Pump(config.component_id, {}, pump_params)
    
    def _create_pump_station(self, config: StationConfig) -> PumpStation:
        """创建泵站"""
        device_count = config.device_count
        max_flow_rate = config.parameters.get('max_flow_rate', 10.0)
        max_head = config.parameters.get('max_head', 20.0)
        power_consumption = config.parameters.get('power_consumption', 50.0)
        
        pump_params = {
            'max_flow_rate': max_flow_rate,
            'max_head': max_head,
            'power_consumption_kw': power_consumption
        }
        
        pumps = []
        for i in range(1, device_count + 1):
            pump_id = f"p{i}"
            # TODO: 处理control_topic和message_bus
            pump = Pump(pump_id, {}, pump_params)
            pumps.append(pump)
        
        return PumpStation(config.component_id, {}, {}, pumps)
    
    def validate_config(self, config: ComponentConfig) -> bool:
        validator = PumpValidator()
        if not validator.validate_parameters(config.parameters):
            raise ComponentConfigError("Invalid pump parameters", config)
        if not validator.validate_constraints(config):
            raise ComponentConfigError("Invalid pump constraints", config)
        return True

class TurbineCreator(ComponentCreator):
    """水轮机创建器"""
    
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        return (component_type == ComponentType.WATER_TURBINE and 
                level in [DeviceLevel.DEVICE, DeviceLevel.STATION])
    
    def create(self, config: ComponentConfig) -> Union[WaterTurbine, HydropowerStation]:
        """创建水轮机组件"""
        self.validate_config(config)
        
        if config.level == DeviceLevel.DEVICE:
            return self._create_turbine_device(config)
        else:
            # 确保config是StationConfig类型
            if not isinstance(config, StationConfig):
                # 创建StationConfig实例
                station_config = StationConfig(
                    component_id=config.component_id,
                    component_type=config.component_type,
                    level=config.level,
                    parameters=config.parameters,
                    control_topic=config.control_topic,
                    device_count=config.parameters.get('device_count', 2)
                )
                return self._create_hydropower_station(station_config)
            return self._create_hydropower_station(config)
    
    def _create_turbine_device(self, config: ComponentConfig) -> WaterTurbine:
        """创建单个水轮机设备"""
        efficiency = config.parameters.get('efficiency', 0.9)
        max_flow_rate = config.parameters.get('max_flow_rate', 50.0)
        target_outflow = config.parameters.get('target_outflow')
        
        initial_state = {'power': 0, 'outflow': 0}
        parameters = {
            'efficiency': efficiency,
            'max_flow_rate': max_flow_rate
        }
        
        turbine = WaterTurbine(config.component_id, initial_state, parameters)
        
        if target_outflow is not None:
            turbine.target_outflow = target_outflow
        
        return turbine
    
    def _create_hydropower_station(self, config: StationConfig) -> HydropowerStation:
        """创建水电站"""
        device_count = config.device_count
        device_configs = config.device_configs or []
        
        # 如果没有提供详细配置，使用默认配置
        if not device_configs:
            device_configs = [
                {
                    'name': f"{config.component_id}_turbine_{i+1}",
                    'initial_state': {'power': 0.0, 'outflow': 0.0},
                    'parameters': {
                        'efficiency': 0.9,
                        'max_flow_rate': 100.0,
                        'rated_power': 50.0
                    }
                }
                for i in range(device_count)
            ]
        
        return create_hydropower_station(
            name=config.component_id,
            turbine_configs=device_configs,
            station_params=config.parameters
        )
    
    def validate_config(self, config: ComponentConfig) -> bool:
        validator = TurbineValidator()
        if not validator.validate_parameters(config.parameters):
            raise ComponentConfigError("Invalid turbine parameters", config)
        if not validator.validate_constraints(config):
            raise ComponentConfigError("Invalid turbine constraints", config)
        return True

class CanalCreator(ComponentCreator):
    """渠道创建器"""
    
    def can_create(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        return (component_type == ComponentType.CANAL and 
                level == DeviceLevel.INFRASTRUCTURE)
    
    def create(self, config: ComponentConfig) -> UnifiedCanal:
        """创建渠道组件"""
        self.validate_config(config)
        
        model_type = config.parameters.get('model_type', 'integral_delay')
        water_level = config.parameters.get('water_level', 2.0)
        length = config.parameters.get('length')
        surface_area = config.parameters.get('surface_area')
        gain = config.parameters.get('gain')
        delay = config.parameters.get('delay')
        
        # 初始状态
        initial_state = {
            'water_level': water_level,
            'inflow': config.parameters.get('initial_inflow', 0.0),
            'outflow': config.parameters.get('initial_outflow', 0.0)
        }
        
        # 参数配置
        parameters: Dict[str, Any] = {'model_type': model_type}
        
        # 添加模型特定参数
        if model_type == 'integral':
            parameters['surface_area'] = surface_area or 10000.0
            parameters['outlet_coefficient'] = config.parameters.get('outlet_coefficient', 5.0)
        elif model_type in ['integral_delay', 'integral_delay_zero']:
            parameters['gain'] = gain or 0.001
            parameters['delay'] = delay or 300.0
            if model_type == 'integral_delay_zero':
                parameters['zero_time_constant'] = config.parameters.get('zero_time_constant', 50.0)
        elif model_type == 'linear_reservoir':
            parameters['storage_constant'] = config.parameters.get('storage_constant', 1200.0)
            parameters['level_storage_ratio'] = config.parameters.get('level_storage_ratio', 0.005)
        
        # 添加长度参数
        if length is not None:
            parameters['length'] = length
        
        # TODO: 处理message_bus和control_topic
        return UnifiedCanal(
            name=config.component_id,
            initial_state=initial_state,
            parameters=parameters
        )
    
    def validate_config(self, config: ComponentConfig) -> bool:
        validator = CanalValidator()
        if not validator.validate_parameters(config.parameters):
            raise ComponentConfigError("Invalid canal parameters", config)
        if not validator.validate_constraints(config):
            raise ComponentConfigError("Invalid canal constraints", config)
        return True

# ================================
# 统一组件工厂实现
# ================================

class UnifiedComponentFactory(ComponentFactory):
    """统一组件工厂实现"""
    
    def __init__(self, harness=None, message_bus: Optional[SimpleEventBus] = None):
        super().__init__()
        self.harness = harness
        self.message_bus = message_bus
        self._register_default_creators()
        self._register_default_validators()
        
        logger.info("UnifiedComponentFactory initialized")
    
    def _register_default_creators(self):
        """注册默认创建器"""
        # 水库创建器
        reservoir_key = self._get_creator_key(ComponentType.RESERVOIR, DeviceLevel.INFRASTRUCTURE)
        self.register_creator(reservoir_key, ReservoirCreator())
        
        # 闸门创建器
        gate_device_key = self._get_creator_key(ComponentType.GATE, DeviceLevel.DEVICE)
        gate_station_key = self._get_creator_key(ComponentType.GATE, DeviceLevel.STATION)
        gate_creator = GateCreator()
        self.register_creator(gate_device_key, gate_creator)
        self.register_creator(gate_station_key, gate_creator)
        
        # 泵创建器
        pump_device_key = self._get_creator_key(ComponentType.PUMP, DeviceLevel.DEVICE)
        pump_station_key = self._get_creator_key(ComponentType.PUMP, DeviceLevel.STATION)
        pump_creator = PumpCreator()
        self.register_creator(pump_device_key, pump_creator)
        self.register_creator(pump_station_key, pump_creator)
        
        # 水轮机创建器
        turbine_device_key = self._get_creator_key(ComponentType.WATER_TURBINE, DeviceLevel.DEVICE)
        turbine_station_key = self._get_creator_key(ComponentType.WATER_TURBINE, DeviceLevel.STATION)
        turbine_creator = TurbineCreator()
        self.register_creator(turbine_device_key, turbine_creator)
        self.register_creator(turbine_station_key, turbine_creator)
        
        # 渠道创建器
        canal_key = self._get_creator_key(ComponentType.CANAL, DeviceLevel.INFRASTRUCTURE)
        self.register_creator(canal_key, CanalCreator())
        
        logger.info("Default component creators registered")
    
    def _register_default_validators(self):
        """注册默认验证器"""
        self.register_validator(ComponentType.RESERVOIR, ReservoirValidator())
        self.register_validator(ComponentType.GATE, GateValidator())
        self.register_validator(ComponentType.PUMP, PumpValidator())
        self.register_validator(ComponentType.WATER_TURBINE, TurbineValidator())
        self.register_validator(ComponentType.CANAL, CanalValidator())
        
        logger.info("Default component validators registered")
    
    def create_component(self, config: ComponentConfig) -> PhysicalObjectInterface:
        """
        创建组件实例
        
        Args:
            config: 组件配置
            
        Returns:
            创建的组件实例
            
        Raises:
            UnsupportedComponentTypeError: 不支持的组件类型
            ComponentValidationError: 组件验证失败
            ComponentCreationError: 组件创建失败
        """
        try:
            # 验证配置
            validation_errors = self._validate_config(config)
            if validation_errors:
                raise ComponentValidationError(config.component_id, validation_errors)
            
            # 获取创建器
            creator_key = self._get_creator_key(config.component_type, config.level)
            creator = self._creators.get(creator_key)
            
            if not creator:
                raise UnsupportedComponentTypeError(config.component_type, config.level)
            
            if not creator.can_create(config.component_type, config.level):
                raise UnsupportedComponentTypeError(config.component_type, config.level)
            
            # 创建组件
            component = creator.create(config)
            
            # 添加到仿真框架（如果有）
            if self.harness:
                self.harness.add_component(config.component_id, component)
            
            logger.info(f"Successfully created component: {config.component_id} "
                       f"({config.component_type.value}, {config.level.value})")
            
            return component
            
        except (ComponentValidationError, UnsupportedComponentTypeError) as e:
            logger.error(f"Component creation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating component {config.component_id}: {e}")
            raise ComponentCreationError(f"Failed to create component: {str(e)}")
    
    def create_from_dict(self, config_dict: Dict[str, Any]) -> PhysicalObjectInterface:
        """
        从字典配置创建组件
        
        Args:
            config_dict: 组件配置字典
            
        Returns:
            创建的组件实例
        """
        # 转换为配置对象
        component_type = ComponentType(config_dict['component_type'])
        level = DeviceLevel(config_dict.get('level', 
                           ComponentTypeMapping.get_default_level(component_type).value))
        
        if level == DeviceLevel.STATION:
            config = StationConfig(
                component_id=config_dict['component_id'],
                component_type=component_type,
                level=level,
                parameters=config_dict.get('parameters', {}),
                control_topic=config_dict.get('control_topic'),
                device_count=config_dict.get('device_count', 1),
                device_configs=config_dict.get('device_configs')
            )
        elif level == DeviceLevel.INFRASTRUCTURE:
            config = InfrastructureConfig(
                component_id=config_dict['component_id'],
                component_type=component_type,
                level=level,
                parameters=config_dict.get('parameters', {}),
                control_topic=config_dict.get('control_topic')
            )
        else:
            config = DeviceConfig(
                component_id=config_dict['component_id'],
                component_type=component_type,
                level=level,
                parameters=config_dict.get('parameters', {}),
                control_topic=config_dict.get('control_topic')
            )
        
        return self.create_component(config)
    
    def get_supported_types(self) -> List[str]:
        """获取支持的组件类型列表"""
        return [key for key in self._creators.keys()]
    
    def is_supported(self, component_type: ComponentType, level: DeviceLevel) -> bool:
        """检查是否支持指定的组件类型和级别"""
        creator_key = self._get_creator_key(component_type, level)
        return creator_key in self._creators