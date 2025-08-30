# 10. 系统集成与工作流程

本篇文档旨在将前面所有模块的介绍整合起来，从一个完整的端到端(End-to-End)视角，描述`core_lib`中各个组件和智能体是如何协同工作的。

## 1. 核心架构图

`core_lib`的架构可以概括为下图：

```
+-------------------------------------------------------------------+
|                     Simulation Harness (The World)                |
|                                                                   |
|  +-----------------------+         +---------------------------+  |
|  |   Physical Objects    |         |        Message Bus        |  |
|  | (Pipe, Gate, River...) |<------->|      (Central Broker)     |  |
|  +-----------------------+         +---------------------------+  |
|      ^         |                           ^           |          |
|      | Action  | State                     | Subscribe | Publish  |
|      |_________|                           |___________|          |
|                                                                   |
|  +---------------------------------------------------------------+  |
|  |                            Agents                             |  |
|  |---------------------------------------------------------------|  |
|  | Perception Agents |   Local Control   | Central Dispatch Agents |  |
|  | (DigitalTwin,     |   Agents (PID,    | (Rule-Based, MPC)       |  |
|  |  Identification)  |    Custom Logic)  | (Scheduling, Diagnosis) |  |
|  +---------------------------------------------------------------+  |
|                                                                   |
+-------------------------------------------------------------------+
```

*   **Simulation Harness**: 扮演着“上帝”或“物理世界”的角色，它驱动时间，并调用物理对象和智能体的`step()`或`run()`方法。
*   **Physical Objects**: 物理世界的被动模型，它们根据水力学公式计算状态，但不具备主动决策能力。
*   **Message Bus**: 所有智能体之间通信的唯一渠道，实现了信息的解耦。
*   **Agents**: 系统的“大脑”，分为不同类型，执行不同的任务。

## 2. 一个完整的信息与控制闭环

让我们以一个“**通过MPC调度器控制水库下游河道水位**”的场景为例，来追踪一个完整的信息流闭环：

**[时间步 T]**

1.  **物理演化 (Physics Step)**: `SimulationHarness`调用`RiverChannel`和`Reservoir`等物理对象的`step()`方法。计算得出在T时刻，水库的当前水位是`150.2m`，下游河道的观测点水位是`55.1m`。

2.  **感知与孪生 (Perception Step)**:
    *   `SimulationHarness`调用所有智能体的`run()`方法。
    *   与水库和河道绑定的`DigitalTwinAgent`被触发。它们分别从自己的物理模型中获取状态。
    *   水库孪生体向`topic_reservoir_state`发布消息：`{"level": 150.2, ...}`。
    *   河道孪生体向`topic_channel_state`发布消息：`{"level": 55.1, ...}`。

3.  **中心化调度 (Dispatch Step)**:
    *   `CentralMPCAgent`订阅了`topic_reservoir_state`和`topic_channel_state`，因此它收到了这两个最新状态。
    *   同时，它也订阅了`topic_inflow_forecast`，并收到了未来24小时的入流预测。
    *   `CentralMPCAgent`的`run()`方法被触发。它以当前状态为初始条件，以入流预测为外部扰动，运行其内部的MPC优化算法。
    *   优化计算的结果是，为了在未来24小时内将下游水位维持在`55.0m`的目标，当前这个时间步，水库大坝闸门的目标设定点应该是`opening_height = 2.5m`。
    *   `CentralMPCAgent`向`topic_gate_setpoint_cmd`发布指令消息：`{"new_setpoint": 2.5}`。

4.  **本地化控制 (Local Control Step)**:
    *   一个与大坝闸门绑定的`LocalControlAgent`（其内部封装了一个`PIDController`）订阅了`topic_gate_setpoint_cmd`。
    *   它接收到`{"new_setpoint": 2.5}`指令，并更新其内部PID控制器的设定点为`2.5`。
    *   这个`LocalControlAgent`同时也订阅了闸门物理模型的孪生体发布的`topic_gate_state`，其中包含了闸门当前的实际开度，例如`{"opening_height": 2.45m}`。
    *   它将设定点`2.5`和过程变量`2.45`传递给`PIDController`。
    *   PID控制器计算出一个具体的控制动作（例如，一个表示“向上移动”的脉冲信号）。
    *   `LocalControlAgent`将这个脉冲信号发布到`topic_gate_action`。

5.  **动作执行 (Action Step)**:
    *   闸门的`Gate`物理对象模型订阅了`topic_gate_action`。
    *   它接收到脉冲信号，并在其`step()`方法中更新自己的开度状态。

**[时间步 T+1]**

*   新的一轮循环开始，`SimulationHarness`再次调用物理模型的`step()`方法。这一次，由于闸门的开度已经发生了变化，计算出的水库和河道水位也将随之改变，从而形成一个完整的动态闭环。

这个流程清晰地展示了系统如何通过分层的智能体和事件驱动的消息总线，将感知、决策和控制有机地结合在一起。
