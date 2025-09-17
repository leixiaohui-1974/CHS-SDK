"""
基于 Gymnasium 的物理对象基础框架

这个模块定义了统一的 Action 接口和基于 gymnasium 的环境接口，
用于重构所有物理对象的接口，确保一致性和可扩展性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters


class ActionType(Enum):
    """动作类型枚举"""
    CONTROL_SIGNAL = "control_signal"
    FLOW_CONTROL = "flow_control" 
    LEVEL_CONTROL = "level_control"
    STATUS_CONTROL = "status_control"
    MIXED_CONTROL = "mixed_control"


@dataclass
class BaseAction(ABC):
    """
    所有 Action 的基类
    
    定义了统一的 Action 接口，所有具体的 Action 类型都必须继承此类。
    """
    action_type: ActionType
    timestamp: Optional[float] = None
    
    @abstractmethod
    def validate(self) -> bool:
        """验证 Action 的有效性"""
        pass
    
    @abstractmethod  
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于与现有代码兼容"""
        pass


@dataclass
class ControlSignalAction(BaseAction):
    """控制信号动作 - 用于阀门开度、泵站开关等"""
    action_type: ActionType = ActionType.CONTROL_SIGNAL
    control_signal: float = 0.0
    
    def validate(self) -> bool:
        return isinstance(self.control_signal, (int, float)) and 0 <= self.control_signal <= 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'control_signal': self.control_signal,
            'action_type': self.action_type.value,
            'timestamp': self.timestamp
        }


@dataclass  
class FlowControlAction(BaseAction):
    """流量控制动作 - 直接指定目标流量"""
    action_type: ActionType = ActionType.FLOW_CONTROL
    target_flow: float = 0.0
    
    def validate(self) -> bool:
        return isinstance(self.target_flow, (int, float)) and self.target_flow >= 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target_flow': self.target_flow,
            'action_type': self.action_type.value,
            'timestamp': self.timestamp
        }


@dataclass
class LevelControlAction(BaseAction):
    """水位控制动作 - 提供上下游水位信息"""
    action_type: ActionType = ActionType.LEVEL_CONTROL
    upstream_level: float = 0.0
    downstream_level: float = 0.0
    
    def validate(self) -> bool:
        return (isinstance(self.upstream_level, (int, float)) and 
                isinstance(self.downstream_level, (int, float)))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'upstream_level': self.upstream_level,
            'downstream_level': self.downstream_level,
            'upstream_head': self.upstream_level,  # 兼容现有代码
            'downstream_head': self.downstream_level,  # 兼容现有代码
            'action_type': self.action_type.value,
            'timestamp': self.timestamp
        }


@dataclass
class StatusControlAction(BaseAction):
    """状态控制动作 - 开关设备"""
    action_type: ActionType = ActionType.STATUS_CONTROL
    status: int = 0  # 0=关闭, 1=开启
    
    def validate(self) -> bool:
        return self.status in [0, 1]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'control_signal': self.status,  # 兼容现有代码
            'action_type': self.action_type.value,
            'timestamp': self.timestamp
        }


@dataclass
class MixedControlAction(BaseAction):
    """混合控制动作 - 包含多种控制信号"""
    control_signal: Optional[float] = None
    target_flow: Optional[float] = None
    upstream_level: Optional[float] = None
    downstream_level: Optional[float] = None
    status: Optional[int] = None
    additional_params: Optional[Dict[str, Any]] = None
    action_type: ActionType = ActionType.MIXED_CONTROL
    
    def validate(self) -> bool:
        # 至少需要一个有效的控制参数
        valid_controls = [
            self.control_signal is not None,
            self.target_flow is not None, 
            self.upstream_level is not None,
            self.downstream_level is not None,
            self.status is not None
        ]
        return any(valid_controls)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'action_type': self.action_type.value,
            'timestamp': self.timestamp
        }
        
        if self.control_signal is not None:
            result['control_signal'] = self.control_signal
        if self.target_flow is not None:
            result['target_flow'] = result['flow'] = self.target_flow
        if self.upstream_level is not None:
            result['upstream_level'] = result['upstream_head'] = self.upstream_level
        if self.downstream_level is not None:
            result['downstream_level'] = result['downstream_head'] = self.downstream_level
        if self.status is not None:
            result['status'] = self.status
        if self.additional_params:
            result.update(self.additional_params)
            
        return result


class PhysicalObjectEnv(gym.Env):
    """
    基于 Gymnasium 的物理对象环境基类
    
    为所有物理对象提供统一的 gymnasium 接口，包括：
    - 标准化的 action 和 observation spaces
    - step(), reset(), render() 方法
    - 与现有 PhysicalObjectInterface 的兼容性
    """
    
    def __init__(self, physical_object: PhysicalObjectInterface, 
                 action_type: ActionType = ActionType.MIXED_CONTROL,
                 time_step: float = 1.0):
        super().__init__()
        
        self.physical_object = physical_object
        self.action_type = action_type
        self.time_step = time_step
        self._step_count = 0
        
        # 根据 action_type 定义 action_space
        self.action_space = self._create_action_space(action_type)
        
        # 定义 observation_space (基于物理对象的状态)
        self.observation_space = self._create_observation_space()
        
        # 记录初始状态用于重置
        self.initial_state = physical_object.get_state().copy()
        
    def _create_action_space(self, action_type: ActionType) -> spaces.Space:
        """根据动作类型创建动作空间"""
        if action_type == ActionType.CONTROL_SIGNAL:
            return spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        elif action_type == ActionType.FLOW_CONTROL:
            return spaces.Box(low=0.0, high=1000.0, shape=(1,), dtype=np.float32)
        elif action_type == ActionType.LEVEL_CONTROL:
            return spaces.Box(low=-100.0, high=100.0, shape=(2,), dtype=np.float32)
        elif action_type == ActionType.STATUS_CONTROL:
            return spaces.Discrete(2)
        else:  # MIXED_CONTROL
            return spaces.Dict({
                'control_signal': spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32),
                'target_flow': spaces.Box(low=0.0, high=1000.0, shape=(1,), dtype=np.float32),
                'upstream_level': spaces.Box(low=-100.0, high=100.0, shape=(1,), dtype=np.float32),
                'downstream_level': spaces.Box(low=-100.0, high=100.0, shape=(1,), dtype=np.float32),
                'status': spaces.Discrete(2)
            })
    
    def _create_observation_space(self) -> spaces.Space:
        """基于物理对象状态创建观测空间"""
        # 获取当前状态示例以确定空间维度
        state_sample = self.physical_object.get_state()
        state_keys = sorted(state_sample.keys())
        
        # 为每个状态变量创建合理的范围
        low_vals = []
        high_vals = []
        
        for key in state_keys:
            if 'level' in key or 'head' in key:
                low_vals.append(-100.0)
                high_vals.append(100.0)
            elif 'flow' in key or 'outflow' in key or 'inflow' in key:
                low_vals.append(0.0)
                high_vals.append(1000.0)
            elif 'opening' in key or 'efficiency' in key:
                low_vals.append(0.0)
                high_vals.append(1.0)
            elif 'power' in key:
                low_vals.append(0.0)
                high_vals.append(10000.0)
            elif 'status' in key:
                low_vals.append(0.0)
                high_vals.append(1.0)
            else:
                # 默认范围
                low_vals.append(-1000.0)
                high_vals.append(1000.0)
        
        return spaces.Box(
            low=np.array(low_vals, dtype=np.float32),
            high=np.array(high_vals, dtype=np.float32),
            dtype=np.float32
        )
    
    def _gym_action_to_base_action(self, action) -> BaseAction:
        """将 gym action 转换为 BaseAction"""
        if self.action_type == ActionType.CONTROL_SIGNAL:
            return ControlSignalAction(control_signal=float(action[0]))
        elif self.action_type == ActionType.FLOW_CONTROL:
            return FlowControlAction(target_flow=float(action[0]))
        elif self.action_type == ActionType.LEVEL_CONTROL:
            return LevelControlAction(
                upstream_level=float(action[0]),
                downstream_level=float(action[1])
            )
        elif self.action_type == ActionType.STATUS_CONTROL:
            return StatusControlAction(status=int(action))
        else:  # MIXED_CONTROL
            return MixedControlAction(
                control_signal=float(action.get('control_signal', [0])[0]) if 'control_signal' in action else None,
                target_flow=float(action.get('target_flow', [0])[0]) if 'target_flow' in action else None,
                upstream_level=float(action.get('upstream_level', [0])[0]) if 'upstream_level' in action else None,
                downstream_level=float(action.get('downstream_level', [0])[0]) if 'downstream_level' in action else None,
                status=int(action.get('status', 0)) if 'status' in action else None
            )
    
    def _state_to_observation(self, state: State) -> np.ndarray:
        """将物理对象状态转换为观测向量"""
        state_keys = sorted(state.keys())
        return np.array([float(state.get(key, 0)) for key in state_keys], dtype=np.float32)
    
    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """执行一个时间步"""
        # 转换 action
        base_action = self._gym_action_to_base_action(action)
        
        if not base_action.validate():
            raise ValueError(f"Invalid action: {base_action}")
        
        # 调用物理对象的 step 方法
        action_dict = base_action.to_dict()
        new_state = self.physical_object.step(action_dict, self.time_step)
        
        # 转换为观测
        observation = self._state_to_observation(new_state)
        
        # 简单的奖励函数 (可以在子类中重写)
        reward = self._calculate_reward(new_state, base_action)
        
        # 终止条件 (可以在子类中重写)  
        terminated = False
        truncated = False
        
        self._step_count += 1
        
        info = {
            'step_count': self._step_count,
            'action_type': base_action.action_type.value,
            'raw_state': new_state
        }
        
        return observation, reward, terminated, truncated, info
    
    def _calculate_reward(self, state: State, action: BaseAction) -> float:
        """计算奖励 - 子类应重写此方法"""
        # 默认奖励：基于系统稳定性
        outflow = state.get('outflow', 0)
        return -abs(outflow - 10.0) if outflow > 0 else -10.0  # 简单示例
    
    def reset(self, seed: Optional[int] = None, 
              options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """重置环境"""
        super().reset(seed=seed)
        
        # 重置物理对象到初始状态
        self.physical_object._state = self.initial_state.copy()
        self._step_count = 0
        
        observation = self._state_to_observation(self.initial_state)
        info = {'step_count': self._step_count}
        
        return observation, info
    
    def render(self, mode='human'):
        """渲染环境状态"""
        if mode == 'human':
            state = self.physical_object.get_state()
            print(f"\n=== {self.physical_object.name} 状态 ===")
            for key, value in state.items():
                print(f"{key}: {value:.4f}")
            print("=" * 40)
        elif mode == 'rgb_array':
            # 返回状态的图形表示 (简化版本)
            return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
    def close(self):
        """关闭环境"""
        pass


def create_gym_env(physical_object: PhysicalObjectInterface, 
                   action_type: ActionType = ActionType.MIXED_CONTROL,
                   time_step: float = 1.0) -> PhysicalObjectEnv:
    """
    便捷函数：为任何物理对象创建 gymnasium 环境
    
    Args:
        physical_object: 物理对象实例
        action_type: 动作类型
        time_step: 时间步长
        
    Returns:
        PhysicalObjectEnv 实例
    """
    return PhysicalObjectEnv(physical_object, action_type, time_step)


# 兼容性函数：将旧的 action dict 转换为新的 BaseAction
def dict_to_base_action(action_dict: Dict[str, Any]) -> BaseAction:
    """将字典格式的 action 转换为 BaseAction"""
    # 过滤掉元数据字段
    data_fields = {k: v for k, v in action_dict.items() 
                   if k not in ['action_type', 'timestamp']}
    
    # 根据原始 action_type 优先判断（如果提供）
    original_type = action_dict.get('action_type')
    if original_type:
        if original_type == 'control_signal':
            return ControlSignalAction(control_signal=data_fields.get('control_signal', 0.0))
        elif original_type == 'status_control':
            return StatusControlAction(status=data_fields.get('status', 0))
        elif original_type == 'flow_control':
            return FlowControlAction(target_flow=data_fields.get('target_flow', 0.0))
        elif original_type == 'level_control':
            return LevelControlAction(
                upstream_level=data_fields.get('upstream_level', data_fields.get('upstream_head', 0.0)),
                downstream_level=data_fields.get('downstream_level', data_fields.get('downstream_head', 0.0))
            )
    
    # 根据字段组合确定 Action 类型（后备方案）
    if len(data_fields) == 1:
        if 'control_signal' in data_fields:
            return ControlSignalAction(control_signal=data_fields['control_signal'])
        elif 'target_flow' in data_fields:
            return FlowControlAction(target_flow=data_fields['target_flow'])
        elif 'status' in data_fields:
            return StatusControlAction(status=data_fields['status'])
    
    # 特殊情况：status + control_signal（StatusControlAction 的兼容字段）
    if 'status' in data_fields and 'control_signal' in data_fields and len(data_fields) == 2:
        if data_fields['control_signal'] == data_fields['status']:
            return StatusControlAction(status=data_fields['status'])
    
    # 检查是否为水位控制
    if 'upstream_level' in data_fields and 'downstream_level' in data_fields:
        # 如果只有水位字段（加上兼容字段）
        level_fields = {'upstream_level', 'downstream_level', 'upstream_head', 'downstream_head'}
        if set(data_fields.keys()).issubset(level_fields):
            return LevelControlAction(
                upstream_level=data_fields.get('upstream_level', data_fields.get('upstream_head', 0.0)),
                downstream_level=data_fields.get('downstream_level', data_fields.get('downstream_head', 0.0))
            )
    
    # 其他情况使用混合控制
    return MixedControlAction(
        control_signal=data_fields.get('control_signal'),
        target_flow=data_fields.get('target_flow', data_fields.get('flow')),
        upstream_level=data_fields.get('upstream_level', data_fields.get('upstream_head')),  
        downstream_level=data_fields.get('downstream_level', data_fields.get('downstream_head')),
        status=data_fields.get('status'),
        additional_params={k: v for k, v in data_fields.items() 
                         if k not in ['control_signal', 'target_flow', 'flow',
                                    'upstream_level', 'downstream_level', 
                                    'upstream_head', 'downstream_head', 'status']}
    )
