# 9. 测试与仿真平台 (Testing & Simulation Harness)

本篇文档详细介绍 `core_lib` 中用于构建、运行和测试仿真场景的核心组件：`SimulationHarness`。

## 1. 核心理念：作为“世界”的仿真平台

在 `core_lib` 中，"测试"的概念与传统的单元测试或集成测试有所不同。它指的是通过构建一个完整的、可运行的**仿真场景(Simulation Scenario)**来验证系统在特定条件下的行为。

`SimulationHarness` (`core_lib/core_engine/testing/simulation_harness.py`) 扮演了这个“世界”或“沙盘”的角色。它的职责不是断言代码的正确性，而是：
1.  提供一个框架来**组装**一个水力系统模型。
2.  **驱动**该模型随时间演化。
3.  记录下整个过程的**历史状态**，供后续分析。

开发者或测试工程师可以通过分析 `harness.history` 中的结果来验证系统的行为是否符合预期。

## 2. 构建一个仿真场景

使用 `SimulationHarness` 构建一个场景通常遵循以下步骤：

1.  **初始化Harness**: `harness = SimulationHarness(config)`，传入仿真时长、时间步长等基本配置。
2.  **添加物理组件**: `harness.add_component(component)`，将所有物理对象（如`Pipe`, `Gate`, `RiverChannel`的实例）添加到平台中。
3.  **定义连接关系**: `harness.add_connection(upstream_id, downstream_id)`，通过定义上、下游关系，构建出系统的拓扑结构图。平台内部使用这个图来进行拓扑排序，以决定正确的计算顺序。
4.  **添加智能体**: `harness.add_agent(agent)`，将所有智能体（如`DigitalTwinAgent`, `LocalControlAgent`, `CentralMPCAgent`等）添加到平台中。
5.  **构建平台**: `harness.build()`，此步骤会执行拓扑排序并使平台准备好运行。

## 3. 运行仿真

`SimulationHarness` 提供了两种不同的运行模式，对应了两种不同的架构。

### 3.1 `run_simulation()` (简单仿真模式)

*   **描述**: 这是一个简化的、中心化的仿真循环。它主要用于测试简单的、不包含复杂智能体交互的反馈控制回路。
*   **循环逻辑**:
    1.  遍历所有控制器，计算控制动作。
    2.  根据拓扑顺序，依次调用每个物理模型的 `step()` 方法，并传递上一步的计算结果。
    3.  记录当前时间步的状态。
    4.  重复以上步骤。

### 3.2 `run_mas_simulation()` (多智能体系统仿真模式)

*   **描述**: 这是 `core_lib` 架构的核心，用于运行一个完整的、包含多个自治智能体的多智能体系统（Multi-Agent System, MAS）。
*   **循环逻辑**:
    1.  **智能体阶段**: 遍历所有已注册的`Agent`，并调用它们的 `run()` 方法。这允许所有智能体（感知、决策、控制）根据上一个时间步的状态进行思考和行动，并将它们的决定（如新设定点、新告警）发布到消息总线。
    2.  **物理阶段**: 根据拓扑顺序，依次调用每个物理模型的 `step()` 方法，计算出系统在当前时间步的物理状态演化。
    3.  **记录与重复**: 记录当前时间步的状态，然后进入下一个循环。

这个两阶段的循环完美地体现了“感知-行动-环境演化”的智能体系统核心思想。绝大多数复杂的系统行为测试都应通过 `run_mas_simulation()` 来进行。
