# 物理模型: 阀门与阀门站 (Valve & ValveStation)

*   **源代码**: `core_lib/physical_objects/valve.py`

本篇文档介绍用于模拟管道系统中流量控制的两个核心模型：`Valve` (阀门) 和 `ValveStation` (阀门站)。

---

## 1. `Valve` (单个阀门)

`Valve` 对象用于模拟单个阀门。阀门是管网系统中最常见的流量控制设备，它通过改变自身的开度来调节水流。

### 核心逻辑

`Valve` 模型的行为主要由其 `opening` (开度, 0-100%) 决定。

1.  **控制**: `Valve` 可以订阅一个 `action_topic`。控制智能体通过发布包含 `control_signal` (一个0到100之间的浮点数) 的消息来设置阀门的目标开度 `target_opening`。
2.  **流量计算**: `step` 方法中的流量计算逻辑分为两种情况：
    *   **有上游来水 (`inflow` > 0)**: 这种情况下，模型简化地认为，只要阀门开度大于0，所有来水都能通过，即 `outflow = inflow`。如果阀门关闭，则 `outflow = 0`。
    *   **无上游来水 (`inflow` = 0)**: 这种情况下，模型会使用一个简化的**孔口流公式** `_calculate_flow`，根据上、下游水位差 (`head_diff`) 和阀门自身的属性（直径、流量系数）来计算 `outflow`。阀门的有效流量系数 `effective_C_d` 会随开度线性变化。
3.  **状态更新**: 在 `step` 方法中，阀门的当前开度 `opening` 会被直接设置为 `target_opening`。这是一个简化的瞬时响应模型。

### 关键参数 (`parameters`)

*   `discharge_coefficient` (float): 阀门全开时的流量系数 `C_d`，反映了阀门的过流能力。
*   `diameter` (float): 阀门所在管道的直径 (m)。

### 状态变量 (`state`)

*   `opening` (float): 当前的阀门开度 (0-100%)。
*   `outflow` (float): 当前的出水流量 (m³/s)。

---

## 2. `ValveStation` (阀门站)

`ValveStation` 模型是一个**聚合模型**，它代表一个由多个独立 `Valve` 实例组成的阀门站。它的主要作用是提供一个站级的整体状态视图。

### 概述

与 `PumpStation` 类似，`ValveStation` 本身不包含复杂的水力学计算。它的核心职责是在每个仿真步长中，**依次调用**其包含的每个 `Valve` 对象的 `step` 方法，然后**汇总**它们的出流量，形成一个站级总流量。

对单个阀门的控制由专门的控制智能体负责，`ValveStation` 模型不直接参与控制决策。

### 初始化

在创建 `ValveStation` 实例时，必须传入一个预先初始化好的 `Valve` 对象列表。

```python
# 示例：创建一个包含2台阀门的阀门站
valves = [
    Valve(name="V1", ...),
    Valve(name="V2", ...)
]

station = ValveStation(
    name="main_valve_station",
    valves=valves,
    ...
)
```

### 状态变量 (`state`)

-   `total_outflow` (float): 阀门站的总出流量，等于其包含的所有阀门的出流量之和 (m³/s)。
-   `valve_count` (int): 该站包含的阀门数量。

### 工作机制

`ValveStation` 的 `step` 方法非常直观：
1.  它会遍历其内部所有的 `Valve` 对象。
2.  将从 `SimulationHarness` 接收到的 `action`（主要包含上、下游水位信息）传递给每个 `Valve` 对象的 `step` 方法并调用它。
3.  累加每个 `Valve` 返回的 `outflow` 状态。
4.  更新自身的 `total_outflow` 状态。
