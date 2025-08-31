# 物理模型: 管道 (Pipe)

*   **源代码**: `core_lib/physical_objects/pipe.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Pipe` 对象是系统中用于模拟承压管道水流的基本组件。它代表了一段连接两个节点的、具有特定物理属性的管道。

## 2. 数学模型

`Pipe` 模型支持两种业界标准的水力计算方法，可通过 `calculation_method` 参数进行选择：

1.  **`darcy_weisbach` (默认)**: 采用 **达西-韦斯巴赫 (Darcy-Weisbach)** 方程。这是计算承压管道水头损失的经典公式，适用于大多数管网仿真。
    *   **流量计算**: `Q = A * sqrt(2 * g * h_L * D / (f * L))`
    *   **核心参数**: `friction_factor` (摩擦系数)

2.  **`manning`**: 采用 **曼宁 (Manning)** 公式。该公式通常用于明渠流，但也适用于满管重力流的情况。
    *   **流量计算**: `Q = (1.0/n) * A * R_h^(2/3) * S^(1/2)`
    *   **核心参数**: `manning_n` (曼宁糙率系数)

## 3. 关键参数 (`parameters`)

在创建 `Pipe` 实例时，需要提供以下核心参数：

*   `diameter` (米): 管道直径。
*   `length` (米): 管道长度。
*   `calculation_method` (字符串, 可选): 计算方法，可以是 `'darcy_weisbach'` (默认) 或 `'manning'`。
*   `friction_factor` (无量纲): **如果** `calculation_method` 是 `darcy_weisbach`，则需要此参数。
*   `manning_n` (无量纲): **如果** `calculation_method` 是 `manning`，则需要此参数。

## 4. 状态变量 (`state`)

`Pipe` 对象维护并输出以下状态变量：

*   `outflow` (立方米/秒): 通过管道的流量。
*   `head_loss` (米): 管道两端的水头损失。

## 5. 交互与局限

*   `Pipe` 模型通过 `step()` 方法接收上、下游节点的 `head` （水头）作为输入，并计算出 `outflow`。
*   这是一个相对简化的模型，它假设了稳定的紊流状态，并且没有考虑非满管流或水锤等瞬变现象。它适用于大规模管网的稳态或准稳态仿真。

## 6. 高级功能：参数辨识

`Pipe` 对象还包含一个 `identify_parameters()` 方法。这是一个强大的功能，允许模型根据实测数据（如历史流量和水位数据）自动校准其水力参数（`friction_factor` 或 `manning_n`）。

这对于提高模型的仿真精度、使其更贴近物理实际至关重要。关于如何使用此功能，请参考 `IdentificationAgent` 的相关文档。
