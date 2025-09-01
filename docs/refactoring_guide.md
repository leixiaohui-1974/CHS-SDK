# 代码重构指南：使用 SimulationBuilder 和通用代理类

本指南介绍了如何使用新的 `SimulationBuilder` 类和通用代理类来简化仿真代码，减少重复代码，并提高代码的可维护性。

## 概述

在分析了多个示例代码后，我们发现了以下重复模式：

1. **仿真设置模式**：创建 `SimulationHarness`、添加组件、建立连接
2. **组件创建模式**：水库、闸门、泵站、水轮机的重复创建代码
3. **代理模式**：需求代理、监控代理、干扰代理的重复实现
4. **仿真循环模式**：相似的仿真执行逻辑

## 新的架构组件

### 1. SimulationBuilder 类

`SimulationBuilder` 类提供了一个高级接口来创建常见的仿真模式：

```python
from core_lib.core_engine.testing.simulation_builder import SimulationBuilder

# 创建仿真构建器
builder = SimulationBuilder({'end_time': 100, 'dt': 1.0})

# 添加组件
builder.add_reservoir("res1", water_level=10.0)
builder.add_gate("gate1", opening=0.5)

# 建立连接
builder.connect_components([("res1", "gate1")])

# 构建并运行
builder.build()
builder.run_mas_simulation()
```

### 2. 预定义系统模式

提供了常见系统的快速创建函数：

```python
from core_lib.core_engine.testing.simulation_builder import (
    create_simple_reservoir_gate_system,
    create_hydropower_system,
    create_pump_station_system
)

# 创建水电站系统
builder = create_hydropower_system({'end_time': 10, 'dt': 1.0})
builder.build()
builder.run_simple_simulation()
```

### 3. 通用代理类

`common_agents.py` 模块提供了可重用的代理实现：

```python
from core_lib.core_engine.testing.common_agents import (
    DemandAgent,
    MonitoringAgent,
    DisturbanceAgent,
    ThresholdAlarmAgent
)

# 创建需求代理
demand_schedule = {100.0: 25.0, 400.0: 8.0}
demand_agent = DemandAgent(
    agent_id="demand_agent",
    message_bus=builder.harness.message_bus,
    demand_topic="demand.flow",
    demand_schedule=demand_schedule
)

# 创建监控代理
monitoring_agent = MonitoringAgent(
    agent_id="monitor_agent",
    components={"pump_station": pump_station},
    monitoring_interval=50.0
)
```

## 重构前后对比

### 重构前（原始代码）

```python
# 大量重复的设置代码
simulation_config = {'duration': 600, 'dt': 1.0}
harness = SimulationHarness(config=simulation_config)
message_bus = harness.message_bus

# 手动创建每个组件
source_reservoir = Reservoir("source_res", {'water_level': 10.0}, {'surface_area': 1.0e6})
downstream_reservoir = Reservoir("downstream_res", {'water_level': 25.0}, {'surface_area': 1.0e6})

# 手动创建泵站
pump_params = {'max_flow_rate': 10.0, 'max_head': 20.0, 'power_consumption_kw': 50}
pumps = [Pump(f"p{i}", {}, pump_params, message_bus, f"action.pump.p{i}") for i in range(1, 4)]
pump_station = PumpStation("ps1", {}, {}, pumps)

# 手动添加组件和连接
harness.add_component("source_res", source_reservoir)
harness.add_component("downstream_res", downstream_reservoir)
harness.add_component("ps1", pump_station)
harness.add_connection("source_res", "ps1")
harness.add_connection("ps1", "downstream_res")

# 自定义需求代理
class DemandAgent(Agent):
    def __init__(self, agent_id, message_bus, demand_topic):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
    
    def run(self, current_time):
        if int(current_time) == 100:
            demand = 25.0
            self.bus.publish(self.demand_topic, {'value': demand})
        # ...

# 手动仿真循环
for i in range(num_steps):
    current_time = i * dt
    demand_agent.run(current_time)
    pump_control_agent.execute_control_logic()
    harness._step_physical_models(dt)
    # 手动历史记录...
```

### 重构后（使用新架构）

```python
# 使用预定义系统
builder = create_pump_station_system({'end_time': 600, 'dt': 1.0})

# 使用通用代理
demand_schedule = {100.0: 25.0, 400.0: 8.0}
demand_agent = DemandAgent(
    agent_id="demand_agent",
    message_bus=builder.harness.message_bus,
    demand_topic="demand.flow",
    demand_schedule=demand_schedule
)
builder.add_agent(demand_agent)

# 添加监控
monitoring_agent = MonitoringAgent(
    agent_id="monitor_agent",
    components={"ps1": builder.get_component("ps1")},
    monitoring_interval=50.0
)
builder.add_agent(monitoring_agent)

# 构建并运行
builder.build()
builder.run_mas_simulation()  # 自动处理仿真循环
```

## 代码减少统计

| 示例 | 原始代码行数 | 重构后代码行数 | 减少比例 |
|------|-------------|---------------|----------|
| 泵站控制 | 119 | 67 | 44% |
| 水电站 | 111 | 58 | 48% |
| 平均 | 115 | 62.5 | 46% |

## 重构的优势

### 1. 代码重用
- **组件创建**：标准化的组件创建方法
- **系统模式**：预定义的常见系统配置
- **代理类**：可重用的代理实现

### 2. 可维护性
- **集中管理**：核心逻辑集中在 `SimulationBuilder` 中
- **一致性**：所有示例使用相同的模式
- **易于修改**：修改核心类即可影响所有示例

### 3. 可读性
- **简洁性**：减少了 46% 的代码量
- **清晰性**：业务逻辑更加突出
- **标准化**：统一的 API 和模式

### 4. 扩展性
- **新组件**：容易添加新的组件类型
- **新代理**：容易创建新的代理类
- **新模式**：容易定义新的系统模式

## 迁移指南

### 步骤 1：识别模式
分析现有代码，识别以下模式：
- 组件创建和配置
- 连接建立
- 代理实现
- 仿真循环

### 步骤 2：选择构建器方法
根据系统类型选择合适的方法：
- 简单系统：使用预定义函数
- 复杂系统：使用 `SimulationBuilder` 类
- 自定义系统：扩展 `SimulationBuilder`

### 步骤 3：替换代理
将自定义代理替换为通用代理：
- `DemandAgent` 替换需求变化代理
- `MonitoringAgent` 替换监控代理
- `DisturbanceAgent` 替换干扰代理

### 步骤 4：简化仿真循环
使用内置的仿真运行方法：
- `run_mas_simulation()` 用于多代理仿真
- `run_simple_simulation()` 用于简单仿真

## 最佳实践

### 1. 组件命名
使用描述性的组件 ID：
```python
builder.add_reservoir("upstream_reservoir", water_level=100.0)
builder.add_reservoir("downstream_reservoir", water_level=20.0)
```

### 2. 配置管理
将配置参数集中管理：
```python
config = {
    'end_time': 600,
    'dt': 1.0,
    'monitoring_interval': 50.0
}
```

### 3. 代理组织
按功能组织代理：
```python
# 控制代理
builder.add_agent(pump_control_agent)

# 监控代理
builder.add_agent(monitoring_agent)

# 外部代理
builder.add_agent(demand_agent)
```

### 4. 错误处理
使用构建器的内置错误处理：
```python
try:
    builder.build()
    builder.run_mas_simulation()
except Exception as e:
    print(f"Simulation failed: {e}")
    builder.print_final_states()
```

## 扩展指南

### 添加新组件类型

```python
def add_custom_component(self, component_id: str, **kwargs):
    """添加自定义组件类型"""
    component = CustomComponent(component_id, **kwargs)
    self.harness.add_component(component_id, component)
    self.components[component_id] = component
    return component

# 扩展 SimulationBuilder
SimulationBuilder.add_custom_component = add_custom_component
```

### 添加新代理类型

```python
class CustomAgent(Agent):
    """自定义代理基类"""
    def __init__(self, agent_id: str, **kwargs):
        super().__init__(agent_id)
        # 自定义初始化
    
    def run(self, current_time: float):
        # 自定义逻辑
        pass
```

### 添加新系统模式

```python
def create_custom_system(config: Optional[Dict[str, Any]] = None) -> SimulationBuilder:
    """创建自定义系统模式"""
    builder = SimulationBuilder(config)
    
    # 添加特定组件
    builder.add_reservoir("res1", water_level=50.0)
    builder.add_custom_component("custom1", param1=value1)
    
    # 建立连接
    builder.connect_components([("res1", "custom1")])
    
    return builder
```

## 总结

通过引入 `SimulationBuilder` 和通用代理类，我们成功地：

1. **减少了 46% 的代码量**
2. **消除了重复代码**
3. **提高了代码可维护性**
4. **标准化了仿真模式**
5. **简化了新示例的创建**

这种重构方法为 CHS-SDK 提供了更加清洁、可维护和可扩展的代码架构，同时保持了原有功能的完整性。