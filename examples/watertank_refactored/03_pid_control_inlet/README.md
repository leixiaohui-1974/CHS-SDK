# 示例 3: 进水泵 PID 水位控制 (重构版)

## 1. 场景目标

本示例演示了一个经典的水位闭环控制问题。目标是**将一个水箱的水位维持在预设的目标值 (10.0m)**。

为了实现这一目标，我们使用一个 PID 控制器来调节**进水泵的流量**。同时，水箱的出水口存在一个**持续变化的、不可控的扰动**（模拟用户的随机用水），这增加了控制难度。

本场景旨在展示如何利用平台内置的感知、控制智能体和消息总线，构建一个鲁棒的闭环控制系统。

## 2. 架构设计

本示例采用标准的场景驱动架构，其核心组件和数据流如下：

### 物理组件

-   `Reservoir`: 在 `components.yml` 中定义，代表被控的水箱。它的净入流量由一个聚合主题 `aggregated_inflow_topic` 提供。

### 智能体 (`agents.yml`)

1.  **`reservoir_perception_agent` (`DigitalTwinAgent`)**:
    -   **角色**: 感知层。
    -   **行为**: 在每个时间步，它“观察” `Reservoir` 组件的物理状态，并将当前的水位 (`water_level`) 发布到 `tank_water_level_topic` 主题。

2.  **`pump_pid_controller_agent` (`LocalControlAgent`)**:
    -   **角色**: 决策与控制层。
    -   **行为**:
        -   它内部封装了一个 `PIDController`。
        -   它订阅 `tank_water_level_topic` 来获取当前水位。
        -   将观测值与设定的目标值 (10.0m) 进行比较，通过PID算法计算出当前需要开启多大的进水流量。
        -   将计算出的流量值发布到 `control_signal_topic` 主题。

3.  **`disturbance_agent` (`CsvInflowAgent`)**:
    -   **角色**: 扰动模拟层。
    -   **行为**: 从 `disturbance.csv` 文件中读取一个预设的、随时间变化的**负流量**序列，并将其发布到 `disturbance_signal_topic`，用以模拟不可控的用户用水。

4.  **`inflow_aggregator_agent` (`SignalAggregatorAgent`)**:
    -   **角色**: 信号聚合层 (本场景的自定义智能体)。
    -   **行为**: 由于 `Reservoir` 组件只能监听一个入流主题，这个智能体解决了信号合并的问题。它同时订阅 `control_signal_topic` (PID控制的正流量) 和 `disturbance_signal_topic` (扰动的负流量)，将两者相加，得到水箱的**净入流量**，然后发布到最终的 `aggregated_inflow_topic` 主题。

### 数据流闭环

`Reservoir` -> `DigitalTwinAgent` -> (水位) -> `LocalControlAgent` -> (控制指令) -> `SignalAggregatorAgent` -> (净入流) -> `Reservoir`

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/03_pid_control_inlet
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。

您可以打开此文件，重点观察 `tank_water_level_topic` 主题下的数据。您会看到，尽管存在持续的、变化的外部扰动，水箱的水位依然能从初始的 5.0m 被 PID 控制器逐步提升，并最终稳定在目标水位 10.0m 附近，展示了闭环控制系统的鲁棒性。
