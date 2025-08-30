# 示例 5: 泵阀联合控制 (重构版)

## 1. 场景目标

本示例演示了一种更高级的**协调控制**策略。系统需要通过协同调度**进水泵**和**出水阀**，来将水箱水位维持在目标值 (10.0m)，同时应对一个不可控的外部扰动出流。

其核心控制逻辑在于：根据当前的水位误差，统一决策应该增加多少入流或出流，然后将该决策分配给合适的执行器（水泵或水阀）。

## 2. 架构设计 (组件 + 智能体)

与早期版本不同，本次重构采用了**物理组件**与**智能体**分离的清晰架构，这也是本仿真框架推荐的最佳实践。

### 物理组件 (`components.yml`)

-   **`reservoir_1` (`Reservoir`)**:
    -   **角色**: 核心的物理模型。
    -   **行为**: 它模拟水库的真实物理过程。其 `inflow_topics` 和 `outflow_topics` 属性被配置为监听来自控制智能体和扰动智能体的流量指令。它根据所有流入和流出的总和来更新自身的水位状态。

### 智能体 (`agents.yml`)

1.  **`reservoir_perception` (`DigitalTwinAgent`)**:
    -   **角色**: 物理世界的“数字眼”。
    -   **行为**: 这是一个通用的感知智能体。它被配置为监视 `reservoir_1` 的状态，并将其 `water_level` 变量发布到 `water_level_topic` 主题上，供控制智能体使用。

2.  **`coordinator_agent` (`LocalControlAgent`)**:
    -   **角色**: 控制大脑 / 协调器。
    -   **行为**: 这是一个**通用的**本地控制智能体。它的强大之处在于其控制逻辑是**可插拔**的。在本例中，它被配置为使用一个特殊的控制器：`JointPIDController`。

3.  **`disturbance_outflow_agent` (`CsvInflowAgent`)**:
    -   **角色**: 扰动模拟器。
    -   **行为**: 一个通用的数据注入智能体，从 `disturbance.csv` 读取不可控的扰动出流量，并将其发布到 `disturbance_outflow_topic`。

### 控制器 (`JointPIDController`)

这是本次重构的核心。它不是一个智能体，而是一个可重用的**控制器(Controller)**类，被封装在 `core_lib` 中。

-   **内部逻辑**:
    1.  它包含一个标准的 `PIDController`，用于根据水位误差计算出一个总体的“净流量需求”。
    2.  它包含一套**分程控制 (Split-Range Control)** 逻辑，将这个净流量需求分配给水泵和水阀：
        -   若净需求为正（缺水），则生成一个水泵指令，阀门指令为0。
        -   若净需求为负（水多），则生成一个水阀指令，水泵指令为0。
-   **输出**: 它不直接发布消息，而是返回一个**字典**，将主题名称映射到控制信号，例如：`{'pump_command_topic': 5.0, 'valve_command_topic': 0.0}`。
-   **优势**: `LocalControlAgent` 接收到这个字典后，会自动将每个信号发布到对应的 `topic`。这使得控制逻辑（在`Controller`里）与通信任务（在`Agent`里）完全解耦。

### 数据流闭环

`Reservoir` (物理状态) -> `DigitalTwinAgent` (发布状态) -> `LocalControlAgent` (接收状态) -> `JointPIDController` (计算动作) -> `LocalControlAgent` (发布动作) -> `Reservoir` (接收动作)

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/05_joint_control
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。

您可以重点观察 `pump_command_topic` 和 `valve_command_topic` 的数据。您会发现，这两个主题的控制信号是**互斥**的：当一个有值时，另一个总是为0。这清晰地展示了协调器的分程控制策略。同时，`reservoir_perception` 记录的 `water_level` 数据会显示水位在各种扰动下，始终被努力地控制在目标值 10.0m 附近。
