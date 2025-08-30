# 物理模型: 水库/湖泊 (Reservoir)

*   **源代码**: `core_lib/physical_objects/reservoir.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Reservoir` 对象用于模拟系统中的蓄水单元，如水库、湖泊、蓄水池等。它的核心功能是根据水量平衡原理，更新自身的蓄水量和水位。

## 2. 数学模型

该模型基于简单的**水量平衡方程 (Water Balance Equation)**。

在每个 `step()` 方法中，它执行以下计算：

1.  **计算体积变化**:
    `delta_volume = (total_inflow - total_outflow) * dt`
    其中 `total_inflow` 是所有上游连接件的来水之和，`total_outflow` 是所有下游连接件的出流之和。

2.  **更新蓄水量**:
    `new_volume = current_volume + delta_volume`

3.  **更新水位**:
    `new_water_level = f(new_volume)`
    其中 `f` 是一个将蓄水量转换为水位的函数。这通常通过查询**库容曲线 (Storage Curve)** 来实现，该曲线定义了水位和蓄水量之间的一一对应关系。

## 3. 关键参数 (`parameters`)

在创建 `Reservoir` 实例时，需要提供以下核心参数：

*   `area` (平方米): 水库的表面积。在简化的模型中，可以假设面积为常数，此时水位变化可以直接通过 `delta_volume / area` 计算。在复杂模型中，`area` 本身可能是水位的函数。
*   `storage_curve` (可选): 一个描述水位-库容关系的数据结构。

## 4. 状态变量 (`state`)

`Reservoir` 对象维护并输出以下核心状态变量：

*   `volume` (立方米): 当前的总蓄水量。
*   `water_level` (米): 当前的水位。

## 5. 交互

*   `Reservoir` 是一个**状态型**对象 (`is_stateful = True`)。它的状态（尤其是水位）是系统中最重要的变量之一。
*   它的水位 (`water_level`) 会作为其下游连接件（如闸门、管道）计算流量时的**上游水头**。
*   它的水位也会被 `DigitalTwinAgent` 发布到消息总线上，作为上层调度决策（如`CentralMPCAgent`）的关键输入。例如，调度器需要确保水库水位保持在防洪限制水位和供水死水位之间。
