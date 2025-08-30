# 示例 5: 泵阀联合控制 (重构版)

## 1. 场景目标

本示例演示了一种更高级的**协调控制**策略。系统需要通过协同调度**进水泵**和**出水阀**，来将水箱水位维持在目标值 (10.0m)，同时应对一个不可控的外部扰动出流。

其核心是一个**协调器智能体 (`Coordinator Agent`)**，它扮演着控制中心的角色，根据当前的水位误差，统一决策应该增加多少入流、减少多少出流，并将指令分别下发给水泵和水阀。

## 2. 架构设计 (“一切皆为智能体”)

为了最忠实地复现原脚本中包含的复杂控制逻辑，本次重构采用了一种**纯智能体**的架构。这意味着，不仅控制逻辑，就连水库自身的物理过程也被封装在了一个自定义的智能体中。

因此，本场景不包含任何物理组件 (`components.yml` 为空)。

### 智能体 (`agents.yml`)

1.  **`reservoir_sim_agent` (`ReservoirSimulationAgent`)**:
    -   **角色**: 物理世界模拟器。
    -   **行为**: 这是本场景的核心自定义智能体之一。它内部包含了水库的水量平衡方程。它会同时订阅来自水泵、水阀和外部扰动的三个流量主题，计算出净流量，更新内部的水位状态，然后将新的水位发布到 `water_level_topic`。

2.  **`coordinator_agent` (`BusAwareCoordinatorAgent`)**:
    -   **角色**: 控制大脑 / 协调器。
    -   **行为**: 这是对原脚本中 `JointControlCoordinatorAgent` 的封装。它订阅 `water_level_topic` 获取水位。其内部的PID控制器会计算出一个总的“净流量需求”。随后，它根据一套**分程控制**策略，将这个需求分配给水泵和水阀：
        -   若净需求为正（缺水），则指令发给水泵，阀门指令为0。
        -   若净需求为负（水多），则指令发给水阀，水泵指令为0。
    -   最后，它将分离的指令发布到 `pump_command_topic` 和 `valve_command_topic`。

3.  **`disturbance_outflow_agent` (`CsvInflowAgent`)**:
    -   **角色**: 扰动模拟器。
    -   **行为**: 从 `disturbance.csv` 读取不可控的扰动出流量，并发布到 `disturbance_outflow_topic`。

### 数据流闭环

`ReservoirSimulationAgent` -> (水位) -> `coordinator_agent` -> (泵阀指令) -> `ReservoirSimulationAgent`

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/05_joint_control
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。

您可以重点观察 `pump_command_topic` 和 `valve_command_topic` 的数据。您会发现，这两个主题的控制信号是**互斥**的：当一个有值时，另一个总是为0。这清晰地展示了协调器的分程控制策略。同时，`water_level_topic` 的数据会显示水位在各种扰动下，始终被努力地控制在目标值 10.0m 附近。
