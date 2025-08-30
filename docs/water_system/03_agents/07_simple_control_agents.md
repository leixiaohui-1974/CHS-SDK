# 核心智能体: 简单控制智能体

本篇文档介绍一系列用于实现对单个设备（如阀门、闸门）进行直接控制的简单控制智能体。

## 1. 核心理念：`LocalControlAgent`的轻量级实现

与“感知智能体”是对 `DigitalTwinAgent` 的专一化实现类似，`GateControlAgent` 和 `ValveControlAgent` 是对核心控制基类 `LocalControlAgent` 的轻量级、专一化的实现。

它们的设计模式是：
1.  **继承 `LocalControlAgent`**: 它们都直接继承自 `LocalControlAgent` 类。这意味着它们天生就具备了 `LocalControlAgent` 的所有核心功能，包括：
    -   在内部封装一个控制器（如 PID 控制器）。
    -   订阅一个或多个观测主题（`observation_topics`）以获取输入。
    -   根据控制器逻辑计算出控制信号。
    -   将控制信号发布到动作主题（`action_topic`）。
2.  **构造函数的统一**: 它们使用与 `LocalControlAgent` 完全相同的构造函数。通过在初始化时传入不同的配置（如不同的主题名、不同的控制器实例），就可以实现对不同设备的控制。

将它们实现为独立的类，主要是为了**提升架构的清晰度和代码的可读性**。在构建一个复杂的系统时，使用 `GateControlAgent(...)` 能够比使用 `LocalControlAgent(...)` 更明确地表示该智能体的用途是控制一个闸门。

## 2. 已实现的简单控制智能体

以下是当前已实现的、遵循上述模式的简单控制智能体。它们的功能和工作机制与 `LocalControlAgent` 完全一致，其具体的控制逻辑由初始化时注入的**控制器**决定。

---

### `GateControlAgent`
*   **源代码**: `core_lib/local_agents/control/gate_control_agent.py`
*   **对应物理模型**: `Gate`
*   **职责**: 对单个**闸门**进行闭环或开环控制。
*   **典型应用**:
    -   **目标水位控制**: 注入一个PID控制器，观测上游或下游水位 (`observation_topics`)，将其与一个设定的目标水位比较，自动计算并发布闸门的目标开度 (`action_topic`)。
    -   **流量控制**: 观测过闸流量，将其与目标流量比较，自动调整闸门开度。
    -   **直接开度控制**: 接收外部指令，直接将指令设置为闸门的目标开度。

---

### `ValveControlAgent`
*   **源代码**: `core_lib/local_agents/control/valve_control_agent.py`
*   **对应物理模型**: `Valve`
*   **职责**: 对单个**阀门**进行闭环或开环控制。
*   **典型应用**:
    -   **压力控制**: 注入一个PID控制器，观测管道某点的压力，通过调节阀门开度来将压力维持在目标值。
    -   **流量控制**: 观测管道流量，通过调节阀门开度来实现目标流量。
    -   **直接开度控制**: 接收外部指令，直接将指令设置为阀门的目标开度。
