# Physical Objects Gymnasium 重构

基于 Gymnasium 的物理对象统一接口重构，提供标准化的 Action 定义和强化学习环境接口。

## 🎯 重构目标

1. **统一 Action 接口** - 所有物理对象使用一致的 Action 定义
2. **类型安全** - 强类型 Action 验证，避免运行时错误  
3. **Gymnasium 兼容** - 支持标准强化学习框架
4. **向后兼容** - 现有代码无需修改即可运行
5. **可扩展性** - 易于添加新的 Action 类型和物理对象

## 🏗️ 架构概览

```
core_lib/physical_objects/
├── base_gym.py          # 基础 Gymnasium 框架
├── gym_adapter.py       # 兼容性适配器
├── examples_gym.py      # 使用示例
└── README_GYMNASIUM.md  # 本文档
```

## 📋 Action 类型定义

### BaseAction (基类)
```python
@dataclass
class BaseAction(ABC):
    action_type: ActionType
    timestamp: Optional[float] = None
    
    @abstractmethod
    def validate(self) -> bool: pass
    
    @abstractmethod  
    def to_dict(self) -> Dict[str, Any]: pass
```

### 具体 Action 类型

#### 1. ControlSignalAction - 控制信号动作
用于阀门开度、设备控制等：
```python
action = ControlSignalAction(control_signal=0.8)  # 80% 开度
```

#### 2. FlowControlAction - 流量控制动作
直接指定目标流量：
```python
action = FlowControlAction(target_flow=25.0)  # 25 m³/s
```

#### 3. LevelControlAction - 水位控制动作
提供上下游水位信息：
```python
action = LevelControlAction(
    upstream_level=20.0, 
    downstream_level=10.0
)
```

#### 4. StatusControlAction - 状态控制动作
设备开关控制：
```python
action = StatusControlAction(status=1)  # 开启
```

#### 5. MixedControlAction - 混合控制动作
包含多种控制参数：
```python
action = MixedControlAction(
    control_signal=0.7,
    upstream_level=18.0,
    status=1
)
```

## 🚀 快速开始

### 1. 基本使用 - 兼容现有代码

```python
from core_lib.physical_objects import (
    Valve, make_gym_compatible, ControlSignalAction
)

# 创建物理对象（原有方式）
valve = Valve("test_valve", initial_state, parameters)

# 包装为兼容对象
compatible_valve = make_gym_compatible(valve)

# 方式1：使用新 Action 接口
action = ControlSignalAction(control_signal=0.8)
state = compatible_valve.step_with_action(action, 1.0)

# 方式2：原有字典接口仍然可用
state = compatible_valve.step({'control_signal': 0.8}, 1.0)
```

### 2. Gymnasium 环境使用

```python
from core_lib.physical_objects import auto_create_env

# 自动创建合适的环境
env = auto_create_env(valve)

# 标准 gymnasium 接口
observation, info = env.reset()
for step in range(100):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    
    if terminated or truncated:
        observation, info = env.reset()
```

### 3. 类型特化环境

```python
from core_lib.physical_objects import create_typed_env

# 为特定类型创建优化环境
valve_env = create_typed_env(valve, "valve")
pump_env = create_typed_env(pump, "pump") 
reservoir_env = create_typed_env(reservoir, "reservoir")
```

## 📖 详细使用示例

### 阀门控制示例
```python
from core_lib.physical_objects import *

# 创建阀门
valve = Valve("control_valve", state, params)
compatible_valve = make_gym_compatible(valve)

# 使用不同类型的动作
actions = [
    ControlSignalAction(control_signal=0.8),  # 开度控制
    ControlSignalAction(control_signal=0.3),  # 减小开度  
    ControlSignalAction(control_signal=1.0),  # 全开
]

for action in actions:
    state = compatible_valve.step_with_action(action, 1.0)
    print(f"开度: {state['opening']:.2f}, 出流: {state['outflow']:.2f}")
```

### 泵站控制示例
```python
# 泵站开关控制
pump_actions = [
    StatusControlAction(status=1),  # 开启
    MixedControlAction(
        status=1, 
        upstream_level=20.0, 
        downstream_level=10.0
    ),  # 运行状态
    StatusControlAction(status=0),  # 关闭
]

for action in pump_actions:
    state = compatible_pump.step_with_action(action, 1.0)
    print(f"状态: {state['status']}, 功率: {state['power_draw']:.2f}")
```

### 协调控制示例
```python
# 多对象协调控制
valve = make_gym_compatible(Valve(...))
pump = make_gym_compatible(Pump(...))

for step in range(10):
    # 泵站控制
    pump_action = StatusControlAction(status=1 if step % 2 == 0 else 0)
    pump_state = pump.step_with_action(pump_action, 1.0)
    
    # 阀门根据泵站状态调节
    target_opening = 0.8 if pump_state['status'] > 0 else 0.3
    valve_action = ControlSignalAction(control_signal=target_opening)
    valve_state = valve.step_with_action(valve_action, 1.0)
```

## 🔧 扩展开发

### 添加新的 Action 类型

```python
@dataclass
class CustomAction(BaseAction):
    custom_param: float
    action_type: ActionType = ActionType.CUSTOM  # 需要添加到枚举
    
    def validate(self) -> bool:
        return 0 <= self.custom_param <= 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'custom_param': self.custom_param,
            'action_type': self.action_type.value
        }
```

### 创建专门的环境类

```python
class CustomPhysicalObjectEnv(PhysicalObjectEnv):
    def _calculate_reward(self, state: State, action: BaseAction) -> float:
        # 自定义奖励函数
        return custom_reward_logic(state, action)
    
    def _create_action_space(self, action_type: ActionType):
        # 自定义动作空间
        return custom_action_space()
```

## 🔄 迁移指南

### 现有代码迁移 (零修改)
```python
# 原有代码
valve = Valve(name, state, params)
result = valve.step({'control_signal': 0.5}, 1.0)

# 使用适配器后 - 代码完全不变
compatible_valve = make_gym_compatible(valve)  # 只需添加这一行
result = compatible_valve.step({'control_signal': 0.5}, 1.0)
```

### 逐步升级到新接口
```python
# 第一步：包装现有对象
compatible_valve = make_gym_compatible(valve)

# 第二步：使用新 Action (可以混用)
old_action = {'control_signal': 0.5}
new_action = ControlSignalAction(control_signal=0.5)

state1 = compatible_valve.step(old_action, 1.0)      # 旧接口
state2 = compatible_valve.step_with_action(new_action, 1.0)  # 新接口

# 第三步：使用 Gymnasium 环境
env = create_typed_env(valve, "valve")
```

## 🎮 Gymnasium 特性

### 标准接口
- `env.step(action)` - 执行动作
- `env.reset()` - 重置环境  
- `env.render()` - 渲染状态
- `env.action_space` - 动作空间
- `env.observation_space` - 观测空间

### 类型特化奖励
不同类型的物理对象有专门优化的奖励函数：

- **阀门**: 鼓励稳定流量控制，避免过度操作
- **泵站**: 鼓励高效运行，惩罚无用功耗
- **水库**: 保持合理水位，避免极端情况

### 自动类型检测
```python
object_type = detect_object_type(physical_object)
# 自动检测 -> "valve", "pump", "reservoir" 等
```

## ✅ 运行示例

```bash
cd core_lib/physical_objects
python examples_gym.py
```

示例包含：
- 阀门控制示例
- 泵站控制示例  
- 水库控制示例
- 混合控制示例
- 向后兼容性测试

## 🚦 最佳实践

1. **使用类型特化环境**: 调用 `create_typed_env()` 而不是通用环境
2. **Action 验证**: 总是调用 `action.validate()` 验证动作有效性
3. **兼容性优先**: 新项目使用新接口，现有项目使用适配器
4. **奖励函数定制**: 为具体应用场景重写 `_calculate_reward()` 方法
5. **错误处理**: 使用 try-catch 处理动作验证失败

## 🔍 调试支持

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查 Action 有效性
action = ControlSignalAction(control_signal=1.5)  # 无效值
if not action.validate():
    print(f"无效动作: {action}")

# 查看生成的字典
print(f"Action 字典: {action.to_dict()}")
```

## 📦 依赖要求

```txt
gymnasium>=0.26.0
numpy>=1.20.0
scipy>=1.7.0  # 仅 reservoir 需要
```

安装方式：
```bash
pip install gymnasium numpy scipy
```

---

基于 Gymnasium 的重构提供了统一、类型安全、可扩展的物理对象控制接口，同时保持完全向后兼容。
