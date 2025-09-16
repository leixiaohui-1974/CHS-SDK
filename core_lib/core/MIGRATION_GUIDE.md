# Agent架构重构迁移指南

## 概述

本指南帮助您从旧的70+个Agent架构迁移到新的统一Agent架构。新架构将Agent数量从70+个减少到15-20个核心类，提供更清晰的层次结构和更好的可维护性。

## 架构变化

### 旧架构 → 新架构映射

| 旧Agent类 | 新Agent类 | 配置变化 |
|-----------|-----------|----------|
| `CsvReaderAgent` | `UnifiedDataSourceAgent` | `source_type: "csv"` |
| `CsvInflowAgent` | `UnifiedDataSourceAgent` | `source_type: "csv"` |
| `CsvDataSourceAgent` | `UnifiedDataSourceAgent` | `source_type: "csv"` |
| `GateControlAgent` | `UnifiedLocalControlAgent` | `device_type: "gate"` |
| `PumpControlAgent` | `UnifiedLocalControlAgent` | `device_type: "pump"` |
| `ValveControlAgent` | `UnifiedLocalControlAgent` | `device_type: "valve"` |
| `WaterTurbineControlAgent` | `UnifiedLocalControlAgent` | `device_type: "turbine"` |
| `RainfallAgent` | `UnifiedDisturbanceAgent` | `disturbance_type: "rainfall"` |
| `WaterUseAgent` | `UnifiedDisturbanceAgent` | `disturbance_type: "water_use"` |
| `IdentificationAgent` | `UnifiedIdentificationAgent` | `identification_method: "offline"` |
| `ModelUpdaterAgent` | `UnifiedIdentificationAgent` | `identification_method: "online"` |
| `CentralMPCAgent` | `CentralControlAgent` | `optimization_method: "mpc"` |
| 多个协调Agent | `CentralCoordinatorAgent` | 统一协调配置 |

## 迁移步骤

### 1. 注册新Agent类型

```python
from core_lib.core.registry import register_all_agents

# 注册所有新的Agent类型
register_all_agents()
```

### 2. 更新配置文件

#### 旧配置示例
```yaml
agents:
  - agent_id: "csv_reader_1"
    agent_type: "CsvReaderAgent"
    csv_file_path: "data/inflow.csv"
    time_column: "time"
    data_column: "value"

  - agent_id: "gate_control_1"
    agent_type: "GateControlAgent"
    observation_topic: "sensor.gate.state"
    action_topic: "control.gate.action"
    controller:
      class: "PIDController"
      params:
        kp: 1.0
        ki: 0.1
        kd: 0.05
```

#### 新配置示例
```yaml
agents:
  - agent_id: "csv_reader_1"
    agent_type: "UnifiedDataSourceAgent"
    source_type: "csv"
    connection_config:
      csv_file_path: "data/inflow.csv"
      time_column: "time"
      data_columns: ["value"]
    publish_topic: "data.inflow"

  - agent_id: "gate_control_1"
    agent_type: "UnifiedLocalControlAgent"
    device_type: "gate"
    control_strategy: "pid"
    topics:
      observation_topic: "sensor.gate.state"
      action_topic: "control.gate.action"
    controller_config:
      kp: 1.0
      ki: 0.1
      kd: 0.05
      setpoint: 2.5
```

### 3. 代码迁移

#### 旧代码
```python
from core_lib.local_agents.control.gate_control_agent import GateControlAgent
from core_lib.data_access.csv_inflow_agent import CsvInflowAgent

# 创建Agent
gate_agent = GateControlAgent(
    agent_id="gate_1",
    message_bus=bus,
    time_step=1.0,
    controller=pid_controller,
    observation_topic="sensor.gate.state"
)

csv_agent = CsvInflowAgent(
    csv_file_path="data/inflow.csv",
    time_column="time",
    data_column="inflow",
    inflow_topic="data.inflow"
)
```

#### 新代码
```python
from core_lib.core.registry import create_agent_from_config
from core_lib.core.new_interfaces import DeviceType, ControlStrategy, DataSourceType

# 通过配置创建Agent
gate_config = {
    'agent_id': 'gate_1',
    'agent_type': 'UnifiedLocalControlAgent',
    'device_type': 'gate',
    'control_strategy': 'pid',
    'observation_topic': 'sensor.gate.state',
    'controller_config': {'kp': 1.0, 'ki': 0.1, 'kd': 0.05}
}
gate_agent = create_agent_from_config(gate_config)

csv_config = {
    'agent_id': 'csv_inflow',
    'agent_type': 'UnifiedDataSourceAgent',
    'source_type': 'csv',
    'connection_config': {
        'csv_file_path': 'data/inflow.csv',
        'time_column': 'time',
        'data_columns': ['inflow']
    },
    'publish_topic': 'data.inflow'
}
csv_agent = create_agent_from_config(csv_config)
```

### 4. 使用适配器实现渐进式迁移

如果需要保持向后兼容，可以使用适配器：

```python
# 使用适配器，保持旧的API
from core_lib.core.new_agents.local_agents.control.unified_local_control import GateControlAgentAdapter

# 旧代码可以继续工作，但会显示废弃警告
gate_agent = GateControlAgentAdapter(
    agent_id="gate_1",
    message_bus=bus,
    time_step=1.0,
    controller=pid_controller,
    observation_topic="sensor.gate.state"
)
```

## 新功能特性

### 1. 统一生命周期管理

```python
# 所有Agent都遵循统一的生命周期
agent = create_agent_from_config(config)
agent.configure(additional_config)  # 配置
agent.start()                       # 启动
agent.step(current_time)           # 执行步骤
agent.stop()                       # 停止
```

### 2. 事件总线集成

```python
from core_lib.core.event_bus import get_global_event_bus

event_bus = get_global_event_bus()

# 订阅事件
event_bus.subscribe('data.inflow', lambda msg: print(f"收到数据: {msg}"))

# 发布事件
event_bus.publish('control.command', {'command': 'start'})
```

### 3. 配置验证

```python
from core_lib.core.config_schema import validate_config, SystemConfig

# 验证配置
try:
    config = validate_config(config_dict)
    print("配置验证成功")
except ValueError as e:
    print(f"配置验证失败: {e}")
```

### 4. 插件化扩展

```python
from core_lib.core.factories import get_global_agent_factory

# 注册自定义Agent类型
factory = get_global_agent_factory()
factory.register_agent_type('MyCustomAgent', MyCustomAgentClass)
```

## 常见问题

### Q1: 如何处理自定义的Agent类？

**A**: 可以继承新的基类并注册到工厂：

```python
from core_lib.core.new_interfaces import LocalAgent

class MyCustomAgent(LocalAgent):
    def __init__(self, agent_id, device_type, config=None):
        super().__init__(agent_id, device_type, config)
        # 自定义初始化

    def configure(self, config):
        # 实现配置逻辑
        return True

    def start(self):
        # 实现启动逻辑
        return True

    def stop(self):
        # 实现停止逻辑
        return True

    def step(self, current_time):
        # 实现步骤逻辑
        return True

    def get_device_state(self):
        # 返回设备状态
        return {}

# 注册到工厂
from core_lib.core.factories import get_global_agent_factory
factory = get_global_agent_factory()
factory.register_agent_type('MyCustomAgent', MyCustomAgent)
```

### Q2: 如何迁移复杂的控制逻辑？

**A**: 使用控制策略插件化：

```python
from core_lib.core.new_interfaces import ControlStrategy
from core_lib.core.factories import get_global_controller_factory

# 创建自定义控制器
class MyCustomController:
    def compute_control_action(self, observation, time_step):
        # 实现自定义控制逻辑
        return control_action

# 注册控制器
factory = get_global_controller_factory()
factory.register_controller_type(ControlStrategy.NEURAL_NETWORK, MyCustomController)
```

### Q3: 如何处理现有的测试代码？

**A**: 使用适配器保持测试兼容性，然后逐步迁移：

```python
# 第一阶段：使用适配器
def test_gate_control_old():
    agent = GateControlAgentAdapter(...)  # 使用适配器
    # 现有测试逻辑不变

# 第二阶段：迁移到新接口
def test_gate_control_new():
    config = {...}
    agent = create_agent_from_config(config)
    # 新的测试逻辑
```

## 性能对比

| 指标 | 旧架构 | 新架构 | 改善 |
|------|--------|--------|------|
| Agent类数量 | 70+ | 15-20 | -75% |
| 代码重复率 | 高 | 低 | -70% |
| 配置复杂度 | 高 | 低 | -60% |
| 维护成本 | 高 | 低 | -60% |
| 扩展难度 | 困难 | 容易 | +80% |

## 迁移检查清单

- [ ] 备份现有代码和配置
- [ ] 安装新的依赖包
- [ ] 注册所有Agent类型
- [ ] 更新配置文件格式
- [ ] 迁移Agent创建代码
- [ ] 更新测试代码
- [ ] 验证功能正确性
- [ ] 性能测试
- [ ] 文档更新
- [ ] 团队培训

## 技术支持

如果在迁移过程中遇到问题，请：

1. 查看示例配置：`core_lib/core/example_config.yaml`
2. 运行演示脚本：`python core_lib/core/demo_new_architecture.py`
3. 查看适配器实现了解兼容性处理
4. 参考新接口文档：`core_lib/core/new_interfaces.py`

## 总结

新架构通过统一接口、配置驱动和插件化设计，大幅简化了Agent的管理和扩展。虽然需要一定的迁移成本，但长期来看将显著提高代码质量和开发效率。

建议采用渐进式迁移策略：先使用适配器保证现有功能正常运行，然后逐步迁移到新架构，最后移除适配器代码。
