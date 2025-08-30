# 3. 数字孪生 (Twinning)

本篇文档详细介绍 `core_lib` 中数字孪生功能的设计与实现。

## 1. 核心理念：作为“感知代理”的数字孪生

在 `core_lib` 的架构中，数字孪生并不是一个庞大的、中心化的平台，而是被实现为一系列轻量级的、分布式的**感知代理 (`Perception Agent`)**。

每个 `DigitalTwinAgent` (`core_lib/local_agents/perception/digital_twin_agent.py`) 都与一个具体的物理对象模型 (`PhysicalObjectInterface`) 相绑定，形成该物理对象的一个“数字镜像”或“孪生体”。

这个孪生体的核心职责非常清晰：在仿真的每一个时间步，**感知**其内部物理模型的状态，并将其**发布**到消息总线(`MessageBus`)上，供系统中的其他智能体使用。

## 2. `DigitalTwinAgent` 的工作机制

### 2.1 封装与发布

*   **封装 (Wrapping)**: 在初始化时，`DigitalTwinAgent` 会接收一个实现了 `Simulatable` 接口的对象实例（即一个物理模型）。它将这个模型保存在内部的 `self.model` 属性中。
*   **发布 (Publishing)**: `SimulationHarness` 在每个时间步调用 `DigitalTwinAgent` 的 `run()` 方法。`run()` 方法内部会调用 `publish_state()`，这个方法执行两个关键操作：
    1.  调用 `self.model.get_state()` 从内部物理模型中获取当前的状态。
    2.  将获取到的状态数据作为一条消息，通过 `self.bus.publish()` 发布到一个预先配置好的主题 (`state_topic`) 上。

### 2.2 认知增强 (Cognitive Enhancement)

`DigitalTwinAgent` 的价值不仅仅是作为模型状态的“传声筒”。它还可以对原始状态进行“认知增强”，为系统提供更高质量的数据。

代码中的一个典型例子是**状态平滑 (State Smoothing)**。通过在配置中提供 `smoothing_config`，可以对指定的变量（如 `water_level`）应用**指数移动平均 (Exponential Moving Average, EMA)** 滤波。

```python
# DigitalTwinAgent._apply_smoothing (示意)
raw_value = state[key]
last_smoothed = self.smoothed_states.get(key, raw_value)
# 使用EMA公式进行平滑
new_smoothed = alpha * raw_value + (1 - alpha) * last_smoothed
state[key] = new_smoothed
self.smoothed_states[key] = new_smoothed
```

这个过程可以有效地滤除物理模型或传感器数据中可能存在的高频噪声，为下游的决策智能体（如调度、控制）提供更稳定、更可靠的状态信息。

## 3. 与其他模块的交互

*   **上游**: `DigitalTwinAgent` 的上游是它所封装的**物理对象模型**。
*   **下游**: 系统的几乎所有其他模块都是 `DigitalTwinAgent` 的下游。
    *   **诊断模块** (`Diagnosis`) 会订阅状态主题，以检测异常。
    *   **调度模块** (`Scheduling`) 会订阅状态主题，以获取优化的初始条件。
    *   **人机界面** (HMI/UI) 会订阅状态主题，以实时可视化系统状态。

通过这种方式，`DigitalTwinAgent` 构成了连接物理模拟与上层应用的关键桥梁。
