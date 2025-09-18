"""扰动框架

提供通用的扰动基类和管理器，支持动态扰动注入和移除。
"""

import abc
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# 导入网络扰动类
try:
    from .network_disturbance import NetworkDelayDisturbance, PacketLossDisturbance
    NETWORK_DISTURBANCES_AVAILABLE = True
except ImportError:
    NETWORK_DISTURBANCES_AVAILABLE = False
    logger.warning("网络扰动模块不可用，网络扰动功能将被禁用")

class DisturbanceType(Enum):
    """扰动类型枚举"""
    INFLOW_CHANGE = "inflow_change"
    SENSOR_NOISE = "sensor_noise"
    ACTUATOR_FAILURE = "actuator_failure"
    NETWORK_DELAY = "network_delay"
    PACKET_LOSS = "packet_loss"
    DATA_LOSS = "data_loss"
    NODE_FAILURE = "node_failure"
    CONTROL_INTERFERENCE = "control_interference"

@dataclass
class DisturbanceConfig:
    """扰动配置"""
    disturbance_id: str
    disturbance_type: DisturbanceType
    target_component_id: str
    start_time: float
    end_time: float
    intensity: float
    parameters: Dict[str, Any]
    description: str = ""

class BaseDisturbance(abc.ABC):
    """扰动基类"""
    
    def __init__(self, config: DisturbanceConfig):
        self.config = config
        self.is_active = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abc.abstractmethod
    def apply(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用扰动
        
        Args:
            component: 目标组件
            current_time: 当前仿真时间
            time_step: 时间步长
            
        Returns:
            Dict[str, Any]: 扰动效果（如修改的参数值）
        """
        pass
    
    @abc.abstractmethod
    def remove(self, component: Any) -> None:
        """移除扰动
        
        Args:
            component: 目标组件
        """
        pass
    
    def is_time_to_activate(self, current_time: float) -> bool:
        """检查是否到了激活时间"""
        return self.config.start_time <= current_time <= self.config.end_time
    
    def should_be_active(self, current_time: float) -> bool:
        """检查扰动是否应该处于活跃状态"""
        return self.is_time_to_activate(current_time)

class InflowDisturbance(BaseDisturbance):
    """入流扰动"""
    
    def __init__(self, config: DisturbanceConfig):
        super().__init__(config)
        self.original_inflow = None
        self.disturbance_inflow = config.parameters.get('target_inflow', 0)
    
    def apply(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用入流扰动"""
        if hasattr(component, 'set_inflow'):
            # 保存原始入流（仅在第一次应用时）
            if self.original_inflow is None and hasattr(component, '_inflow'):
                self.original_inflow = getattr(component, '_inflow', 0)
            
            # 应用扰动入流
            component.set_inflow(self.disturbance_inflow)
            self.is_active = True
            
            self.logger.info(f"应用入流扰动到组件 {self.config.target_component_id}: "
                           f"设置入流为 {self.disturbance_inflow} m3/s")
            
            return {
                'applied_inflow': self.disturbance_inflow,
                'original_inflow': self.original_inflow
            }
        else:
            self.logger.warning(f"组件 {self.config.target_component_id} 不支持入流设置")
            return {}
    
    def remove(self, component: Any) -> None:
        """移除入流扰动"""
        if self.is_active and hasattr(component, 'set_inflow') and self.original_inflow is not None:
            component.set_inflow(self.original_inflow)
            self.is_active = False
            
            self.logger.info(f"移除入流扰动从组件 {self.config.target_component_id}: "
                           f"恢复入流为 {self.original_inflow} m3/s")

class SensorNoiseDisturbance(BaseDisturbance):
    """传感器噪声扰动"""
    
    def __init__(self, config: DisturbanceConfig):
        super().__init__(config)
        self.noise_std = config.parameters.get('noise_std', 0.1)
        self.affected_sensors = config.parameters.get('affected_sensors', ['water_level'])
    
    def apply(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用传感器噪声"""
        import random
        
        noise_values = {}
        for sensor in self.affected_sensors:
            noise = random.gauss(0, self.noise_std)
            noise_values[sensor] = noise
            
            # 如果组件有相应的状态，添加噪声
            if hasattr(component, 'get_state'):
                state = component.get_state()
                if sensor in state:
                    # 这里需要组件支持噪声注入接口
                    if hasattr(component, 'add_sensor_noise'):
                        component.add_sensor_noise(sensor, noise)
        
        self.is_active = True
        self.logger.info(f"应用传感器噪声到组件 {self.config.target_component_id}: {noise_values}")
        
        return {'sensor_noise': noise_values}
    
    def remove(self, component: Any) -> None:
        """移除传感器噪声"""
        if self.is_active and hasattr(component, 'remove_sensor_noise'):
            for sensor in self.affected_sensors:
                component.remove_sensor_noise(sensor)
            
            self.is_active = False
            self.logger.info(f"移除传感器噪声从组件 {self.config.target_component_id}")

class ActuatorFailureDisturbance(BaseDisturbance):
    """执行器故障扰动
    
    模拟执行器（如闸门、泵站、阀门）的各种故障模式：
    - 响应延迟：控制信号延迟生效
    - 部分故障：执行器效率下降
    - 完全故障：执行器无响应
    """
    
    def __init__(self, config: DisturbanceConfig):
        super().__init__(config)
        self.failure_type = config.parameters.get('failure_type', 'delay')
        self.delay_time = config.parameters.get('delay_time', 1.0)
        self.efficiency_factor = config.parameters.get('efficiency_factor', 0.5)
        self.target_actuator = config.parameters.get('target_actuator', 'outlet_gate')
        self.recovery_time = config.parameters.get('recovery_time', None)
        
        # 故障状态管理
        self.delayed_commands = []  # 存储延迟的控制命令
        self.original_efficiency = 1.0
        self.failure_start_time = None
        
    def apply(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用执行器故障扰动"""
        if self.failure_start_time is None:
            self.failure_start_time = current_time
        
        # 根据故障类型应用不同的故障模式
        if self.failure_type == 'delay':
            return self._apply_delay_failure(component, current_time, time_step)
        elif self.failure_type == 'partial':
            return self._apply_partial_failure(component, current_time, time_step)
        elif self.failure_type == 'complete':
            return self._apply_complete_failure(component, current_time, time_step)
        else:
            return {}
    
    def _apply_delay_failure(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用延迟故障：控制信号延迟生效"""
        effect = {
            'failure_type': 'delay',
            'delay_time': self.delay_time,
            'target_actuator': self.target_actuator,
            'delayed_commands_count': len(self.delayed_commands)
        }
        
        # 检查是否有延迟命令需要执行
        executed_commands = []
        
        for i, (command_time, command_value) in enumerate(self.delayed_commands):
            if current_time >= command_time + self.delay_time:
                # 执行延迟的命令
                if hasattr(component, 'set_control_signal'):
                    component.set_control_signal(command_value)
                elif hasattr(component, 'set_outflow'):
                    component.set_outflow(command_value)
                
                executed_commands.append(i)
                effect['executed_delayed_command'] = command_value
        
        # 移除已执行的命令
        for i in reversed(executed_commands):
            del self.delayed_commands[i]
        
        self.is_active = True
        return effect
    
    def _apply_partial_failure(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用部分故障：执行器效率下降"""
        effect = {
            'failure_type': 'partial',
            'efficiency_factor': self.efficiency_factor,
            'target_actuator': self.target_actuator,
            'original_efficiency': self.original_efficiency
        }
        
        # 降低执行器效率
        if hasattr(component, 'set_efficiency'):
            component.set_efficiency(self.efficiency_factor)
            effect['efficiency_applied'] = True
        elif hasattr(component, '_outflow') and hasattr(component, 'set_outflow'):
            # 对于没有效率接口的组件，直接修改输出
            current_outflow = getattr(component, '_outflow', 0)
            reduced_outflow = current_outflow * self.efficiency_factor
            component.set_outflow(reduced_outflow)
            effect['outflow_reduced'] = {
                'original': current_outflow,
                'reduced': reduced_outflow
            }
        
        self.is_active = True
        return effect
    
    def _apply_complete_failure(self, component: Any, current_time: float, time_step: float) -> Dict[str, Any]:
        """应用完全故障：执行器无响应"""
        effect = {
            'failure_type': 'complete',
            'target_actuator': self.target_actuator,
            'failure_duration': current_time - self.failure_start_time
        }
        
        # 完全禁用执行器响应
        if hasattr(component, 'disable_actuator'):
            component.disable_actuator(self.target_actuator)
            effect['actuator_disabled'] = True
        elif hasattr(component, 'set_outflow'):
            # 保持故障前的最后状态（这里简化为0）
            component.set_outflow(0)
            effect['outflow_frozen'] = 0
        
        self.is_active = True
        return effect
    
    def remove(self, component: Any) -> None:
        """移除执行器故障"""
        if not self.is_active:
            return
        
        # 恢复执行器正常功能
        if self.failure_type == 'partial' and hasattr(component, 'set_efficiency'):
            component.set_efficiency(self.original_efficiency)
        elif self.failure_type == 'complete' and hasattr(component, 'enable_actuator'):
            component.enable_actuator(self.target_actuator)
        
        # 执行所有剩余的延迟命令
        if self.failure_type == 'delay' and self.delayed_commands:
            for command_time, command_value in self.delayed_commands:
                if hasattr(component, 'set_control_signal'):
                    component.set_control_signal(command_value)
                elif hasattr(component, 'set_outflow'):
                    component.set_outflow(command_value)
            
            self.delayed_commands.clear()
        
        # 重置故障状态
        self.failure_start_time = None
        self.is_active = False
        self.logger.info(f"移除执行器故障从组件 {self.config.target_component_id}")

class DisturbanceManager:
    """扰动管理器"""
    
    def __init__(self):
        self.disturbances: Dict[str, BaseDisturbance] = {}
        self.active_disturbances: Dict[str, BaseDisturbance] = {}
        self.disturbance_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.DisturbanceManager")
    
    def register_disturbance(self, disturbance: BaseDisturbance) -> None:
        """注册扰动"""
        disturbance_id = disturbance.config.disturbance_id
        self.disturbances[disturbance_id] = disturbance
        self.logger.info(f"注册扰动: {disturbance_id} ({disturbance.config.disturbance_type.value})")
    
    def remove_disturbance(self, disturbance_id: str) -> None:
        """移除扰动"""
        if disturbance_id in self.disturbances:
            # 如果扰动正在活跃，先停用它
            if disturbance_id in self.active_disturbances:
                self.deactivate_disturbance(disturbance_id, None)
            
            del self.disturbances[disturbance_id]
            self.logger.info(f"移除扰动: {disturbance_id}")
    
    def update(self, current_time: float, time_step: float, components: Dict[str, Any]) -> Dict[str, Any]:
        """更新扰动状态
        
        Args:
            current_time: 当前仿真时间
            time_step: 时间步长
            components: 仿真组件字典
            
        Returns:
            Dict[str, Any]: 扰动效果汇总
        """
        disturbance_effects = {}
        
        for disturbance_id, disturbance in self.disturbances.items():
            target_component_id = disturbance.config.target_component_id
            
            # 检查目标组件是否存在
            if target_component_id not in components:
                continue
            
            component = components[target_component_id]
            
            # 检查是否应该激活扰动
            if disturbance.should_be_active(current_time):
                if disturbance_id not in self.active_disturbances:
                    self.activate_disturbance(disturbance_id, component)
                
                # 应用扰动
                effect = disturbance.apply(component, current_time, time_step)
                if effect:
                    disturbance_effects[disturbance_id] = effect
            
            # 检查是否应该停用扰动
            elif disturbance_id in self.active_disturbances:
                self.deactivate_disturbance(disturbance_id, component)
        
        # 记录扰动历史
        if disturbance_effects:
            self.disturbance_history.append({
                'time': current_time,
                'effects': disturbance_effects
            })
        
        return disturbance_effects
    
    def activate_disturbance(self, disturbance_id: str, component: Any) -> None:
        """激活扰动"""
        if disturbance_id in self.disturbances:
            disturbance = self.disturbances[disturbance_id]
            self.active_disturbances[disturbance_id] = disturbance
            self.logger.info(f"激活扰动: {disturbance_id} 在组件 {disturbance.config.target_component_id}")
    
    def deactivate_disturbance(self, disturbance_id: str, component: Any) -> None:
        """停用扰动"""
        if disturbance_id in self.active_disturbances:
            disturbance = self.active_disturbances[disturbance_id]
            disturbance.remove(component)
            del self.active_disturbances[disturbance_id]
            self.logger.info(f"停用扰动: {disturbance_id} 从组件 {disturbance.config.target_component_id}")
    
    def get_active_disturbances(self) -> List[str]:
        """获取当前活跃的扰动列表"""
        return list(self.active_disturbances.keys())
    
    def get_disturbance_history(self) -> List[Dict[str, Any]]:
        """获取扰动历史"""
        return self.disturbance_history
    
    def clear_history(self) -> None:
        """清空扰动历史"""
        self.disturbance_history.clear()

# 扰动工厂函数
def create_disturbance(config: DisturbanceConfig, enhanced_message_bus=None) -> BaseDisturbance:
    """创建扰动实例"""
    # 网络扰动类型需要特殊处理
    if NETWORK_DISTURBANCES_AVAILABLE and config.disturbance_type in [DisturbanceType.NETWORK_DELAY, DisturbanceType.PACKET_LOSS]:
        if enhanced_message_bus is None:
            # 如果没有提供消息总线，创建一个临时的
            from ..core.enhanced_message_bus import EnhancedMessageBus
            enhanced_message_bus = EnhancedMessageBus()
        
        if config.disturbance_type == DisturbanceType.NETWORK_DELAY:
            disturbance = NetworkDelayDisturbance(config.disturbance_id, enhanced_message_bus)
        elif config.disturbance_type == DisturbanceType.PACKET_LOSS:
            disturbance = PacketLossDisturbance(config.disturbance_id, enhanced_message_bus)
        
        # 配置扰动参数
        disturbance.configure({
            'parameters': {
                'base_delay': config.parameters.get('base_delay', 0.1),
                'jitter': config.parameters.get('jitter_range', 0.05),
                'packet_loss': config.parameters.get('packet_loss_rate', 0.0),
                'affected_topics': config.parameters.get('affected_topics', []),
                'affected_agents': config.parameters.get('affected_agents', []),
                'delay_mode': config.parameters.get('delay_mode', 'fixed')
            }
        })
        
        # 创建一个包装器来兼容BaseDisturbance接口
        class NetworkDisturbanceWrapper(BaseDisturbance):
            def __init__(self, network_disturbance, config):
                self.config = config
                self.network_disturbance = network_disturbance
                self.is_active = False
            
            def apply(self, component):
                """应用扰动到组件"""
                time_end = self.config.end_time - self.config.start_time
                self.network_disturbance.activate(self.config.start_time, time_end)
                self.is_active = True
            
            def remove(self, component):
                """从组件移除扰动"""
                self.network_disturbance.deactivate()
                self.is_active = False
            
            def update(self, current_time: float, component):
                """更新扰动状态"""
                self.network_disturbance.update(current_time)
                self.is_active = self.network_disturbance.is_active
        
        return NetworkDisturbanceWrapper(disturbance, config)
    
    # 处理其他扰动类型
    disturbance_map = {
        DisturbanceType.INFLOW_CHANGE: InflowDisturbance,
        DisturbanceType.SENSOR_NOISE: SensorNoiseDisturbance,
        DisturbanceType.ACTUATOR_FAILURE: ActuatorFailureDisturbance,
    }
    
    disturbance_class = disturbance_map.get(config.disturbance_type)
    if disturbance_class is None:
        available_types = list(disturbance_map.keys())
        if NETWORK_DISTURBANCES_AVAILABLE:
            available_types.extend([DisturbanceType.NETWORK_DELAY, DisturbanceType.PACKET_LOSS])
        raise ValueError(f"不支持的扰动类型: {config.disturbance_type}. 可用类型: {available_types}")
    
    return disturbance_class(config)