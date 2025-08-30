# 物理模型: 水电站 (Hydropower Station)

本篇文档介绍用于模拟水力发电的两个核心物理模型：`WaterTurbine` (水轮机) 和 `HydropowerStation` (水电站)。

## 1. `WaterTurbine` (水轮机)

*   **源代码**: `core_lib/physical_objects/water_turbine.py`
*   **核心方程**: 水力发电方程 `P = η * ρ * g * Q * H`

### 概述

`WaterTurbine` 模型代表了水电站中的单个发电机组。它的主要功能是根据水流条件（流量和水头）计算发电量。该模型的设计允许它通过消息总线接收外部控制指令，从而动态调整其出力。

### 状态变量 (State)

-   `outflow` (float): 当前时间步通过水轮机的实际水流量 (m³/s)。
-   `power` (float): 当前时间步产生的电能功率 (Watts)。

### 参数 (Parameters)

-   `efficiency` (float): 水轮机的发电效率，一个0到1之间的小数。
-   `max_flow_rate` (float): 水轮机能够处理的最大流量 (m³/s)。

### 工作机制

1.  **控制指令**: 水轮机可以订阅一个 `action_topic`。当控制智能体在该主题上发布带有 `target_outflow` 的消息时，水轮机会更新其内部的目标出流量。
2.  **流量约束**: 在 `step` 方法中，实际的 `outflow` 会受到三个因素的约束：上游来水 (`inflow`)、自身最大流量 (`max_flow_rate`) 和控制智能体设定的目标 (`target_outflow`)。实际出流量为这三者的最小值。
3.  **水头计算**: 模型从 `action` 字典中获取由 `SimulationHarness` 提供的上、下游水位 (`upstream_head`, `downstream_head`)，并计算有效水头 `H`。
4.  **发电量计算**: 最后，根据水力发电基础方程 `P = η * ρ * g * Q * H` 计算当前步的发电量 `power`。

---

## 2. `HydropowerStation` (水电站)

*   **源代码**: `core_lib/physical_objects/hydropower_station.py`

### 概述

`HydropowerStation` 模型是一个**聚合模型**，它代表一个完整的水电站设施。一个水电站通常包含多个 `WaterTurbine` (水轮机) 用于发电，以及多个 `Gate` (泄洪闸) 用于水量调度和控制洪水。

这个模型本身不包含复杂的水力学计算，而是通过**组合**其内部的各个组件（水轮机和闸门）的行为，来提供一个站级的整体视图。

### 状态变量 (State)

-   `total_outflow` (float): 水电站总出流量，等于所有水轮机和闸门出流量之和 (m³/s)。
-   `total_power_generation` (float): 水电站总发电量，等于所有水轮机发电量之和 (Watts)。
-   `turbine_outflow` (float): 所有水轮机的总出流量 (m³/s)。
-   `spillway_outflow` (float): 所有泄洪闸的总出流量 (m³/s)。

### 参数 (Parameters)

该模型没有自己独立的参数，其行为由其包含的组件决定。

### 初始化

在创建 `HydropowerStation` 实例时，必须传入一个预先初始化好的 `WaterTurbine` 对象列表和一个 `Gate` 对象列表。

```python
# 示例：创建一个包含2台水轮机和1个闸门的水电站
turbines = [WaterTurbine(name="T1", ...), WaterTurbine(name="T2", ...)]
gates = [Gate(name="G1", ...)]

station = HydropowerStation(
    name="main_station",
    turbines=turbines,
    gates=gates,
    ...
)
```

### 工作机制

`HydropowerStation` 的 `step` 方法非常直观：
1.  它会遍历其内部所有的 `WaterTurbine` 对象，并依次调用它们的 `step` 方法。
2.  然后，它会遍历其内部所有的 `Gate` 对象，并依次调用它们的 `step` 方法。
3.  最后，它会收集所有组件的 `outflow` 和 `power` 状态，将它们加总，更新自身的站级状态变量（如 `total_outflow`, `total_power_generation`）。

**重要提示**: `HydropowerStation` 模型本身是**无状态的 (stateless)**。它不储存水，只处理通过它的水流。在仿真中，水电站通常与一个 `Reservoir` (水库) 模型关联，而水库是负责处理水量存储和演化的有状态组件。
