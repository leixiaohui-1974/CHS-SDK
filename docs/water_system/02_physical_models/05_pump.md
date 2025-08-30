# 物理模型: 水泵 (Pump)

*   **源代码**: `core_lib/physical_objects/pump.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Pump` 对象用于模拟水泵。水泵是向承压管网中提供能量（增加水头）的核心动力设备，也是一个关键的**可控**组件。

## 2. 数学模型

水泵的行为由其**特性曲线 (Characteristic Curve)** 定义。该曲线描述了水泵的**扬程 (Head)**、**流量 (Flow)**、**效率 (Efficiency)** 和**功率 (Power)** 之间的关系。

在 `pump.py` 的实现中，`step()` 方法的核心逻辑是：

1.  接收一个 `action` 字典，其中包含 `control_signal`。这个信号可以代表水泵的**开关状态 (On/Off)** 或**转速 (Speed)**。
2.  根据当前的控制信号和水泵的特性曲线，计算出在该工况下，水泵能够提供的流量 `outflow` 和增加的水头 `head_gain`。
3.  同时，根据效率曲线计算出当前工况下的耗电功率 `power_consumption`。

## 3. 关键参数 (`parameters`)

在创建 `Pump` 实例时，需要提供以下核心参数：

*   `pump_curve`: 一个定义了水泵特性曲线的数据结构。这通常是一个包含多个(流量, 扬程)数据点的列表或一个多项式函数的系数。
*   `efficiency_curve`: 定义了效率与流量/转速之间关系的数据结构。
*   `max_power_kw`: 水泵的最大功率（千瓦）。

## 4. 状态变量 (`state`)

`Pump` 对象维护并输出以下状态变量：

*   `outflow` (立方米/秒): 当前的出水流量。
*   `head_gain` (米): 提供的扬程。
*   `power_consumption` (千瓦): 当前的耗电功率。
*   `status` (On/Off): 当前的运行状态。
*   `speed` (0-1): 当前的相对转速。

## 5. 交互

*   与 `Gate` 类似，`Pump` 的行为也主要由 `control_signal` 驱动。
*   上层的调度智能体 (`Scheduling Agent`) 会根据电价、需水量预测等因素，计算出最优的水泵运行计划（开关机顺序、转速等）。
*   这个计划会通过 `LocalControlAgent` 转换为具体的 `control_signal`，并发布到该 `Pump` 对象监听的动作主题上。
*   `Pump` 对象的 `power_consumption` 状态是进行能耗评价和成本优化的关键输出。
