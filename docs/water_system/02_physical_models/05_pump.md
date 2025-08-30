# 物理模型: 水泵与泵站 (Pump & PumpStation)

*   **源代码**: `core_lib/physical_objects/pump.py`

本篇文档介绍用于模拟加压输水系统的两个核心模型：`Pump` (水泵) 和 `PumpStation` (泵站)。

---

## 1. `Pump` (单个水泵)

`Pump` 对象用于模拟单个水泵。水泵是向承压管网中提供能量（增加水头）的核心动力设备，也是一个关键的**可控**组件。

### 核心逻辑

`Pump` 模型的行为被简化，主要由其运行状态 `status` (0 for Off, 1 for On) 决定。

1.  **控制**: `Pump` 可以订阅一个 `action_topic`。控制智能体（如 `PumpControlAgent`）通过发布包含 `control_signal` (0或1) 的消息来设置水泵的目标开关状态 `target_status`。
2.  **流量计算**: 在 `step` 方法中，如果水泵状态为开启，模型会根据上、下游水位计算 `outflow`。其逻辑是：如果需要克服的扬程 (`downstream_level - upstream_level`) 小于水泵的最大扬程 (`max_head`)，则水泵以其最大流量 (`max_flow_rate`) 出水；否则，流量为0。
3.  **功耗计算**: 如果水泵有出流，其功耗 (`power_draw_kw`) 会被设置为一个固定的参数值 `power_consumption_kw`。

### 关键参数 (`parameters`)

*   `max_head` (float): 水泵能提供的最大扬程 (m)。
*   `max_flow_rate` (float): 水泵在正常工况下的流量 (m³/s)。
*   `power_consumption_kw` (float): 水泵在运行时固定的功耗 (kW)。

### 状态变量 (`state`)

*   `status` (int): 0代表关闭，1代表开启。
*   `outflow` (float): 当前的出水流量 (m³/s)。
*   `power_draw_kw` (float): 当前的耗电功率 (kW)。

---

## 2. `PumpStation` (泵站)

`PumpStation` 模型是一个**聚合模型**，它代表一个由多个独立 `Pump` 实例组成的泵站。它的主要作用是提供一个站级的整体状态视图。

### 概述

`PumpStation` 本身不包含复杂的水力学或电气计算。它的核心职责是在每个仿真步长中，**依次调用**其包含的每个 `Pump` 对象的 `step` 方法，然后**汇总**它们的独立状态，形成一个站级报告。

对单个水泵的控制由专门的控制智能体负责，`PumpStation` 模型不直接参与控制决策。

### 初始化

在创建 `PumpStation` 实例时，必须传入一个预先初始化好的 `Pump` 对象列表。

```python
# 示例：创建一个包含3台水泵的泵站
pumps = [
    Pump(name="P1", ...),
    Pump(name="P2", ...),
    Pump(name="P3", ...)
]

station = PumpStation(
    name="main_pump_station",
    pumps=pumps,
    ...
)
```

### 状态变量 (`state`)

-   `total_outflow` (float): 泵站内所有开启水泵的总出流量 (m³/s)。
-   `active_pumps` (int): 当前正在运行的水泵数量。
-   `total_power_draw_kw` (float): 泵站内所有开启水泵的总功耗 (kW)。

### 工作机制

`PumpStation` 的 `step` 方法非常直观：
1.  它会遍历其内部所有的 `Pump` 对象。
2.  将从 `SimulationHarness` 接收到的 `action`（主要包含上、下游水位信息）传递给每个 `Pump` 对象的 `step` 方法并调用它。
3.  累加每个 `Pump` 返回的状态（`outflow`, `power_draw_kw`, `status`）。
4.  更新自身的站级聚合状态。
