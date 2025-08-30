# 核心智能体: 扰动智能体

本篇文档介绍一系列用于在仿真过程中引入外部“扰动”的智能体。这些智能体对于测试控制系统在应对突发事件（如暴雨、突发用水）时的鲁棒性和恢复能力至关重要。

---

## 1. `RainfallAgent` (固定降雨智能体)

*   **源代码**: `core_lib/disturbances/rainfall_agent.py`

### 概述

`RainfallAgent` 用于模拟一个**强度恒定**的矩形降雨事件。它会在预设的开始时间，向一个指定的主题发布一个固定的入流量，并持续一段指定的时间。

### 工作机制

1.  **初始化**:
    -   `topic`: 发布降雨消息的目标主题。这个主题通常会被某个物理模型（如 `UnifiedCanal(model_type='integral')`）或 `RainfallRunoff` 模型订阅。
    -   `start_time`: 降雨事件的开始时间 (s)。
    -   `duration`: 降雨事件的持续时间 (s)。
    -   `inflow_rate`: 降雨期间恒定的入流量 (m³/s)。
2.  **执行**: 在 `run()` 方法中，智能体会检查当前仿真时间 `current_time` 是否在其活动窗口 `[start_time, start_time + duration)` 之内。
3.  **发布**: 如果在活动窗口内，它会发布一个包含 `{'inflow_rate': ...}` 的消息。窗口结束后，它便不再发布。

---

## 2. `DynamicRainfallAgent` (动态降雨智能体)

*   **源代码**: `core_lib/disturbances/dynamic_rainfall_agent.py`

### 概述

`DynamicRainfallAgent` 用于模拟一个更真实的、动态变化的降雨过程，具体来说是一个**三角形状的入流过程线（Hydrograph）**。这对于测试需要进行趋势预测或变化率响应的智能体（如 `ForecastingAgent`）非常有用。

### 工作机制

1.  **初始化**:
    -   `topic`: 发布降雨消息的目标主题。
    -   `start_time`: 过程线的开始时间。
    -   `peak_time`: 达到流量峰值的时间。
    -   `end_time`: 过程线的结束时间。
    -   `peak_inflow`: 在 `peak_time` 达到的最大入流量。
2.  **执行**: 在 `run()` 方法中，它会根据当前时间在过程线中的位置，通过线性插值计算出当前的入流量：
    -   如果 `current_time` 在 `start_time` 和 `peak_time` 之间，流量会从0线性增加到 `peak_inflow`。
    -   如果 `current_time` 在 `peak_time` 和 `end_time` 之间，流量会从 `peak_inflow` 线性减少到0。
3.  **发布**: 它会将计算出的动态入流量发布出去。

---

## 3. `WaterUseAgent` (用水智能体)

*   **源代码**: `core_lib/disturbances/water_use_agent.py`

### 概述

`WaterUseAgent` 在概念上与 `RainfallAgent` 完全相反。它不模拟入流，而是模拟一个**用水需求**，例如农业灌溉或工业取水。这在仿真中表现为一个**负的入流量**（即一个出流）。

### 工作机制

它的工作机制与 `RainfallAgent` 几乎完全相同，唯一的区别在于：
-   在初始化时，它接收一个 `demand_rate` (需求速率)，并将其存储为一个**负的** `inflow_rate`。
-   在活动窗口期间，它会向指定主题发布一个带有负值的 `inflow_rate` 消息。

这个智能体对于测试系统在应对需求侧扰动时的表现至关重要。
