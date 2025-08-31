# 示例 4: 出水阀 PID 水位控制 (重构版)

## 1. 场景目标

本示例是前一个场景的“反向”问题。目标同样是**将一个水箱的水位维持在预设的目标值 (10.0m)**。

不同之处在于，这次的**扰动项是不可控的进水流量**，而我们**控制的执行器是水箱的出水阀**。当水位高于目标时，控制器需要开大阀门增加出流；当水位低于目标时，则需要关小阀门减少出流。

## 2. 架构设计

本示例充分利用了仿真平台基于物理拓扑的自动连接能力。

### 物理组件与拓扑

-   **组件 (`components.yml`)**:
    1.  `Reservoir`: 被控水箱。其入流量由一个外部扰动智能体提供。
    2.  `Valve`: 布置在水箱出口的可控阀门。
-   **拓扑 (`topology.yml`)**:
    -   定义了 `Reservoir` -> `Valve` 的连接。
    -   基于此拓扑，仿真引擎会自动将水箱的水位 (`water_level`) 作为上游水头 (`upstream_head`) 传递给阀门，阀门则根据该水头和自身开度计算实际出流量，并将此流量从水箱中扣除。这套机制完美地模拟了真实的物理连接，无需额外的聚合智能体。

### 智能体 (`agents.yml`)

1.  **`inflow_disturbance_agent` (`CsvInflowAgent`)**:
    -   **角色**: 扰动模拟层。
    -   **行为**: 从 `inflow_disturbance.csv` 读取时变的入流扰动，并发布到 `inflow_disturbance_topic`。`Reservoir` 组件会订阅此主题。

2.  **`reservoir_perception_agent` (`DigitalTwinAgent`)**:
    -   **角色**: 感知层。
    -   **行为**: “观察” `Reservoir` 组件，并将其实时水位发布到 `water_level_topic`。

3.  **`valve_pid_control_agent` (`LocalControlAgent`)**:
    -   **角色**: 决策与控制层。
    -   **行为**:
        -   订阅 `water_level_topic` 获取当前水位。
        -   通过内部的 `PIDController`，将观测值与目标值 (10.0m) 比较，计算出阀门需要达到的**开度百分比 (0-100)**。
        -   **注意**: 此处我们使用**正的PID增益**，因为这是一个正向作用关系（水位越高，需要的开度越大）。
        -   将计算出的开度指令发布到 `valve_command_topic`。`Valve` 组件自身已配置为监听此主题并执行相应开度动作。

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/04_pid_control_outlet
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。

您可以重点观察 `water_level_topic` 主题的记录。由于初始水位为 12.0m 高于目标值 10.0m，您会看到PID控制器迅速开大阀门，使水位快速下降，并最终在目标值 10.0m 附近稳定下来，以应对持续变化的入流扰动。
