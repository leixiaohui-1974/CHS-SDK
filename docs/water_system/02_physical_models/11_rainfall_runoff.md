# 物理模型: 降雨径流 (RainfallRunoff)

*   **源代码**: `core_lib/physical_objects/rainfall_runoff.py`
*   **核心方程**: 推理公式法 (Rational Method) `Q = C * i * A`

## 概述

`RainfallRunoff` 模型用于模拟一个集水区域的降雨到径流的转化过程。它是一个**无状态的 (stateless)** 组件，其输出（径流）仅取决于当前的输入（降雨），而与历史状态无关。

该模型在仿真中的角色通常是作为系统的“水源”之一。它会订阅一个消息主题以获取实时的降雨强度数据，然后将计算出的径流量作为自身的 `outflow`。在系统拓扑中，这个 `outflow` 可以连接到下游的一个有状态组件（如 `Reservoir` 或 `RiverChannel`），作为其入流的一部分。

## 工作机制

1.  **订阅降雨数据**: 在初始化时，模型可以订阅一个 `rainfall_topic`。外部的降雨模拟智能体（如 `RainfallAgent`）会向该主题发布消息。消息体需要包含一个 `rainfall_intensity` 键，其值为单位是米/秒 (m/s) 的降雨强度。
2.  **计算径流**: 在每个 `step` 中，模型会使用**推理公式法**来计算径流量 `Q`：
    `Q = C * i * A`
    -   `Q`: 径流量 (m³/s)，即模型的 `outflow`。
    -   `C`: 径流系数 `runoff_coefficient`，代表了转换效率。
    -   `i`: 降雨强度 `rainfall_intensity` (m/s)。
    -   `A`: 集水区面积 `catchment_area` (m²)。
3.  **状态重置**: 在计算完成后，模型会将内部的 `rainfall_intensity` 变量重置为0。这意味着，如果在下一个时间步没有新的降雨消息到达，模型会默认降雨为零。

## 关键参数 (`parameters`)

-   `catchment_area` (float): 集水区的面积 (m²)。
-   `runoff_coefficient` (float): 径流系数，一个介于0和1之间的无量纲数，表示有多大比例的降雨量会转化为地表径流。

## 状态变量 (`state`)

作为一个无状态组件，`RainfallRunoff` 只有一个核心输出：
-   `outflow` (float): 根据当前降雨强度计算出的径流量 (m³/s)。

## 参数辨识功能

该模型还包含一个 `identify_parameters` 方法，这是一个非常实用的高级功能。

-   **目的**: 如果您有某个集水区历史的降雨和实测流量数据，该方法可以自动地反算出最能拟合这些数据的 `runoff_coefficient` (径流系数)。
-   **方法**: 它通过一个优化算法 (`SLSQP`)，不断调整径流系数值，模拟径流过程，并计算模拟径流与实测径流之间的均方根误差 (RMSE)。算法的目标是找到使这个误差最小的径流系数值。
-   **使用**: 调用此方法需要提供一个包含 `rainfall` 和 `observed_runoff` 两个 `numpy` 数组的历史数据集。成功辨识后，模型会自动将其内部的 `runoff_coefficient` 参数更新为辨识出的最优值。
