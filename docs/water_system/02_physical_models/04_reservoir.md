# 物理模型: 水库/湖泊 (Reservoir)

*   **源代码**: `core_lib/physical_objects/reservoir.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Reservoir` 对象用于模拟系统中的蓄水单元，如水库、湖泊、蓄水池等。它的核心功能是根据水量平衡原理，更新自身的蓄水量和水位。

## 2. 数学模型

该模型基于**水量平衡方程 (Water Balance Equation)**。在每个时间步长 `dt` 内，它执行以下计算：
`delta_volume = (total_inflow - total_outflow) * dt`

其中 `total_inflow` 和 `total_outflow` 不仅仅是来自上下游物理连接的水量，还可以包含通过消息总线接收的**数据驱动流量**。

更新后的蓄水量 `new_volume` 会通过查询**库容曲线 (Storage Curve)** 或基于**表面积 (Surface Area)** 的线性假设，来换算出新的水位 `new_water_level`。

## 3. 关键参数 (`parameters`)

创建 `Reservoir` 实例时，需要提供以下核心参数：

*   **`storage_curve` 或 `surface_area`**:
    *   `storage_curve`: **(推荐)** 一个由 `[库容, 水位]` 对组成的列表，用于精确描述水位-库容关系。
    *   `surface_area` (或 `area`): (平方米) 如果不提供库容曲线，则必须提供一个恒定的水库表面积，模型将基于此进行线性化的水量-水位换算。
*   **`inflow_topics` / `outflow_topics`** (可选):
    *   这是 `Reservoir` 模型的一个强大功能。您可以提供一个主题列表，让水库订阅这些主题。
    *   例如，您可以定义一个 `inflow_topics`，让水库监听 `rainfall_runoff_topic`。当降雨产流智能体发布产流量时，水库会自动将其计入总入流，从而模拟降雨对水库的影响。
    *   同样，`outflow_topics` 可以用于模拟蒸发、渗漏或直接取水等。

## 4. 状态变量 (`state`)

`Reservoir` 对象维护并输出以下核心状态变量：

*   `volume` (立方米): 当前的总蓄水量。
*   `water_level` (米): 当前的水位。
*   `inflow` (立方米/秒): 该时间步的总入流量 (物理 + 数据)。
*   `outflow` (立方米/秒): 该时间步的总出流量 (物理 + 数据)。

## 5. 交互

*   `Reservoir` 是一个**状态型**对象 (`is_stateful = True`)。它的状态（尤其是水位）是系统中最重要的变量之一。
*   它的水位 (`water_level`) 会作为其下游连接件（如闸门、管道）计算流量时的**上游水头**。
*   它的水位也会被 `DigitalTwinAgent` 发布到消息总线上，作为上层调度决策（如`CentralMPCAgent`）的关键输入。例如，调度器需要确保水库水位保持在防洪限制水位和供水死水位之间。

## 6. 高级功能：参数辨识

`Reservoir` 模型提供了一个非常强大的 `identify_parameters()` 方法。与其它模型不同，此方法旨在**校准整个库容曲线**。

通过提供历史的入流、出流和水位观测数据，该方法可以利用优化算法，微调 `storage_curve` 中每个点对应的水位值，从而使得模拟结果与历史观测数据之间的误差最小化。这对于构建高保真的数字孪生至关重要。

## 5. 交互

*   `Reservoir` 是一个**状态型**对象 (`is_stateful = True`)。它的状态（尤其是水位）是系统中最重要的变量之一。
*   它的水位 (`water_level`) 会作为其下游连接件（如闸门、管道）计算流量时的**上游水头**。
*   它的水位也会被 `DigitalTwinAgent` 发布到消息总线上，作为上层调度决策（如`CentralMPCAgent`）的关键输入。例如，调度器需要确保水库水位保持在防洪限制水位和供水死水位之间。
