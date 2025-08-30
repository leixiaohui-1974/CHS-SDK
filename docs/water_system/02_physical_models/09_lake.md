# 物理模型: 湖泊 (Lake)

*   **源代码**: `core_lib/physical_objects/lake.py`

## 概述

`Lake` 模型用于模拟具有**恒定表面积**的湖泊或水库的水平衡过程。它是一个有状态的（stateful）组件，意味着它能够存储水量，其当前状态会影响未来的状态。

该模型的核心是质量平衡方程，它考虑了所有进入和离开系统的水量，包括：
-   上游来水 (Inflow)
-   下游出流 (Outflow)
-   蒸发损失 (Evaporation)

## 状态变量 (State)

-   `volume` (float): 湖泊当前的总蓄水量 (m³)。
-   `water_level` (float): 根据当前蓄水量和表面积计算出的水位 (m)。
-   `outflow` (float): 当前时间步的实际出流量 (m³/s)。

## 参数 (Parameters)

-   `surface_area` (float): 湖泊的表面积 (m²)。该模型假设此值在仿真过程中保持不变。
-   `max_volume` (float): 湖泊的最大蓄水容量 (m³)。
-   `evaporation_rate_m_per_s` (float, optional): 水面蒸发速率，单位为米/秒 (m/s)。这是一个可选参数，默认为0。

## 工作机制

在每个仿真步长 (`dt`) 中，`Lake` 模型的 `step` 方法执行以下计算：

1.  **获取输入**: 模型从 `SimulationHarness` 获取上游来水 `inflow` 和下游组件请求的出流量 `outflow`（包含在 `action` 字典中）。
2.  **计算蒸发**: 根据参数 `evaporation_rate_m_per_s` 和 `surface_area` 计算出总的蒸发损失量（单位：m³/s）。
3.  **约束出流量**: 模型会检查下游请求的 `outflow` 是否物理上可行。实际出流量不能超过当前湖泊蓄水量所能提供的最大可能流量 (`available_volume / dt`)。
4.  **更新水量**: 应用质量平衡方程，更新湖泊的 `volume`：
    `delta_volume = (inflow - outflow - evaporation_volume_per_second) * dt`
    `volume += delta_volume`
5.  **施加物理约束**: 确保更新后的 `volume` 不会超过 `max_volume` 且不会低于0。
6.  **更新水位**: 最后，根据新的 `volume` 和恒定的 `surface_area` 计算出新的 `water_level`。

**重要区别**: 与 `Reservoir` 模型（通常使用水位-库容曲线）不同，`Lake` 模型使用一个固定的表面积来简化水位和库容之间的关系，这使得它的计算非常高效，适用于对水位变化不剧烈的大型水体进行建模。
