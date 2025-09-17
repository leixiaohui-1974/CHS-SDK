"""
Gymnasium 适配器 - 让现有物理对象兼容新的 gymnasium 接口

这个模块提供了适配器类，可以将现有的物理对象包装为符合新接口的对象，
无需修改原有代码即可使用新的 Action 接口。
"""

from typing import Dict, Any, Optional, Type
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from .base_gym import (
    BaseAction, ActionType, PhysicalObjectEnv, 
    ControlSignalAction, FlowControlAction, LevelControlAction,
    StatusControlAction, MixedControlAction, dict_to_base_action
)


class GymnasiumCompatiblePhysicalObject(PhysicalObjectInterface):
    """
    让现有物理对象兼容 gymnasium 接口的适配器
    
    包装现有的物理对象，提供新的 step 方法来处理 BaseAction，
    同时保持与原有 step(dict, float) 接口的兼容性。
    """
    
    def __init__(self, wrapped_object: PhysicalObjectInterface):
        """
        包装现有物理对象
        
        Args:
            wrapped_object: 要包装的物理对象
        """
        # 复制被包装对象的基本属性
        super().__init__(
            wrapped_object.name, 
            wrapped_object.get_state(), 
            wrapped_object._params
        )
        self.wrapped = wrapped_object
        
    def step_with_action(self, action: BaseAction, time_step: float) -> State:
        """
        新的 step 方法，接受 BaseAction 参数
        
        Args:
            action: BaseAction 或其子类实例
            time_step: 时间步长
            
        Returns:
            更新后的状态
        """
        if not isinstance(action, BaseAction):
            raise TypeError(f"Expected BaseAction, got {type(action)}")
            
        if not action.validate():
            raise ValueError(f"Invalid action: {action}")
            
        # 转换 BaseAction 为字典格式调用原有 step 方法
        action_dict = action.to_dict()
        return self.wrapped.step(action_dict, time_step)
    
    def step(self, action, time_step: float) -> State:
        """
        保持兼容性的 step 方法
        
        支持两种调用方式：
        1. step(BaseAction, float) - 新接口
        2. step(Dict, float) - 原有接口
        """
        if isinstance(action, BaseAction):
            return self.step_with_action(action, time_step)
        elif isinstance(action, dict):
            # 兼容原有接口
            return self.wrapped.step(action, time_step)
        else:
            # 尝试转换为 BaseAction
            try:
                if isinstance(action, (int, float)):
                    # 假设是控制信号
                    base_action = ControlSignalAction(control_signal=float(action))
                else:
                    raise ValueError(f"Unsupported action type: {type(action)}")
                return self.step_with_action(base_action, time_step)
            except Exception as e:
                raise TypeError(f"Invalid action type {type(action)}: {e}")
    
    # 代理其他方法到被包装对象
    def get_state(self) -> State:
        return self.wrapped.get_state()
    
    def set_inflow(self, inflow: float):
        if hasattr(self.wrapped, 'set_inflow'):
            self.wrapped.set_inflow(inflow)
    
    def set_parameters(self, parameters: Parameters):
        if hasattr(self.wrapped, 'set_parameters'):
            self.wrapped.set_parameters(parameters)
    
    def identify_parameters(self, data: Dict[str, Any], method: str = 'offline') -> Parameters:
        if hasattr(self.wrapped, 'identify_parameters'):
            return self.wrapped.identify_parameters(data, method)
        return {}
    
    @property
    def outflow(self):
        return getattr(self.wrapped, 'outflow', self.get_state().get('outflow', 0))
    
    def __getattr__(self, name):
        """代理未定义的属性到被包装对象"""
        return getattr(self.wrapped, name)


class TypedPhysicalObjectEnv(PhysicalObjectEnv):
    """
    类型特化的物理对象环境
    
    为特定类型的物理对象提供定制化的环境，包括：
    - 特定的动作空间
    - 特定的奖励函数
    - 特定的终止条件
    """
    
    def __init__(self, physical_object: PhysicalObjectInterface, 
                 object_type: str = "generic", **kwargs):
        """
        初始化类型特化环境
        
        Args:
            physical_object: 物理对象实例
            object_type: 对象类型 ("valve", "pump", "reservoir", "gate" 等)
        """
        self.object_type = object_type.lower()
        
        # 根据对象类型选择合适的动作类型
        action_type = self._get_default_action_type(object_type)
        
        super().__init__(physical_object, action_type, **kwargs)
    
    def _get_default_action_type(self, object_type: str) -> ActionType:
        """根据对象类型选择默认动作类型"""
        type_mapping = {
            'valve': ActionType.CONTROL_SIGNAL,
            'gate': ActionType.CONTROL_SIGNAL, 
            'pump': ActionType.STATUS_CONTROL,
            'reservoir': ActionType.LEVEL_CONTROL,
            'turbine': ActionType.MIXED_CONTROL,
            'junction': ActionType.FLOW_CONTROL
        }
        return type_mapping.get(object_type.lower(), ActionType.MIXED_CONTROL)
    
    def _calculate_reward(self, state: State, action: BaseAction) -> float:
        """根据对象类型计算特定奖励"""
        if self.object_type == 'valve':
            return self._valve_reward(state, action)
        elif self.object_type == 'pump':
            return self._pump_reward(state, action)
        elif self.object_type == 'reservoir':
            return self._reservoir_reward(state, action)
        else:
            return super()._calculate_reward(state, action)
    
    def _valve_reward(self, state: State, action: BaseAction) -> float:
        """阀门奖励：鼓励合理的流量控制"""
        outflow = state.get('outflow', 0)
        opening = state.get('opening', 0)
        
        # 奖励稳定的流量控制
        flow_stability_reward = -abs(outflow - 10.0) * 0.1
        
        # 避免过度操作
        if isinstance(action, ControlSignalAction):
            operation_penalty = -abs(action.control_signal - opening) * 0.05
        else:
            operation_penalty = 0
            
        return flow_stability_reward + operation_penalty
    
    def _pump_reward(self, state: State, action: BaseAction) -> float:
        """泵站奖励：鼓励高效运行"""
        outflow = state.get('outflow', 0)
        power = state.get('power_draw', 0)
        efficiency = state.get('efficiency', 0)
        status = state.get('status', 0)
        
        # 效率奖励
        efficiency_reward = efficiency * 10.0 if status > 0 else 0
        
        # 能耗惩罚
        power_penalty = -power * 0.001
        
        # 无用运行惩罚
        useless_operation_penalty = -5.0 if status > 0 and outflow <= 0.1 else 0
        
        return efficiency_reward + power_penalty + useless_operation_penalty
    
    def _reservoir_reward(self, state: State, action: BaseAction) -> float:
        """水库奖励：保持合理水位"""
        water_level = state.get('water_level', 0)
        volume = state.get('volume', 0)
        
        # 水位稳定性奖励 (假设目标水位为 15m)
        target_level = 15.0
        level_deviation = abs(water_level - target_level)
        level_reward = -level_deviation * 0.5
        
        # 避免极端水位
        extreme_penalty = 0
        if water_level < 5.0:  # 过低
            extreme_penalty = -50.0
        elif water_level > 25.0:  # 过高
            extreme_penalty = -30.0
            
        return level_reward + extreme_penalty


def make_gym_compatible(physical_object: PhysicalObjectInterface) -> GymnasiumCompatiblePhysicalObject:
    """
    便捷函数：让现有物理对象兼容 gymnasium
    
    Args:
        physical_object: 要包装的物理对象
        
    Returns:
        兼容 gymnasium 的物理对象
    """
    return GymnasiumCompatiblePhysicalObject(physical_object)


def create_typed_env(physical_object: PhysicalObjectInterface, 
                     object_type: str = "generic", 
                     **kwargs) -> TypedPhysicalObjectEnv:
    """
    便捷函数：创建类型特化的环境
    
    Args:
        physical_object: 物理对象实例
        object_type: 对象类型 ("valve", "pump", "reservoir", "gate" 等)
        **kwargs: 传递给环境的其他参数
        
    Returns:
        TypedPhysicalObjectEnv 实例
    """
    return TypedPhysicalObjectEnv(physical_object, object_type, **kwargs)


# 物理对象类型检测
def detect_object_type(physical_object: PhysicalObjectInterface) -> str:
    """
    自动检测物理对象类型
    
    Args:
        physical_object: 物理对象实例
        
    Returns:
        检测到的对象类型字符串
    """
    class_name = physical_object.__class__.__name__.lower()
    
    if 'valve' in class_name:
        return 'valve'
    elif 'pump' in class_name:
        return 'pump'
    elif 'gate' in class_name:
        return 'gate'
    elif 'reservoir' in class_name:
        return 'reservoir' 
    elif 'turbine' in class_name:
        return 'turbine'
    elif 'junction' in class_name:
        return 'junction'
    else:
        return 'generic'


def auto_create_env(physical_object: PhysicalObjectInterface, 
                    **kwargs) -> TypedPhysicalObjectEnv:
    """
    自动创建适合的 gymnasium 环境
    
    Args:
        physical_object: 物理对象实例
        **kwargs: 传递给环境的其他参数
        
    Returns:
        自动配置的 TypedPhysicalObjectEnv 实例
    """
    object_type = detect_object_type(physical_object)
    return create_typed_env(physical_object, object_type, **kwargs)
