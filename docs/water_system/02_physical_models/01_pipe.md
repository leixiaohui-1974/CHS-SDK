# 物理模型: 管道 (Pipe)

*   **源代码**: `core_lib/physical_objects/pipe.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Pipe` 对象是系统中用于模拟承压管道水流的基本组件。它代表了一段连接两个节点的、具有特定物理属性的管道。

## 2. 数学模型

该模型采用 **达西-韦斯巴赫 (Darcy-Weisbach)** 方程来计算流量。这是一个经典的水力学公式，用于计算流体在管道中因摩擦而产生的能量损失（水头损失）。

在 `pipe.py` 的实现中，该公式被简化并重构为一个**流量系数 (flow_coefficient)**，该系数在对象初始化时根据管道的物理参数预先计算出来：

```python
# self.flow_coefficient = area * sqrt(2 * g * diameter / (friction_factor * length))
```

在每个 `step()` 中，流量 `Q` 的计算就简化为：

`Q = flow_coefficient * sqrt(head_difference)`

其中 `head_difference` 是管道上、下游节点的水头差。

## 3. 关键参数 (`parameters`)

在创建 `Pipe` 实例时，需要提供以下核心参数：

*   `diameter` (米): 管道直径。
*   `length` (米): 管道长度。
*   `friction_factor` (无量纲): 达西-韦斯巴赫摩擦系数。这是一个经验值，取决于管道的材料和状况。

## 4. 状态变量 (`state`)

`Pipe` 对象维护并输出以下状态变量：

*   `outflow` (立方米/秒): 通过管道的流量。
*   `head_loss` (米): 管道两端的水头损失。

## 5. 交互与局限

*   `Pipe` 模型通过 `step()` 方法接收上、下游节点的 `head` （水头）作为输入，并计算出 `outflow`。
*   这是一个相对简化的模型，它假设了稳定的紊流状态，并且没有考虑非满管流或水锤等瞬变现象。它适用于大规模管网的稳态或准稳态仿真。
