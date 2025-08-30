# 物理模型: 闸门 (Gate)

*   **源代码**: `core_lib/physical_objects/gate.py`
*   **接口**: `PhysicalObjectInterface`

## 1. 概述

`Gate` 对象用于模拟水利系统中的控制闸门。它是一个关键的**可控**物理组件，其行为直接受到外部控制信号的影响。

## 2. 数学模型

该模型使用标准的**堰流(Weir Flow)**或**孔口流(Orifice Flow)**公式来计算通过闸门的流量。具体使用哪个公式取决于闸门上、下游的水位以及闸门的开启高度。

在 `gate.py` 的实现中，这个逻辑被封装在 `step()` 方法里。它接收一个 `action` 字典，其中包含了`control_signal`，这个信号直接决定了闸门的开启度 `opening`。

`self._state['opening'] = control_signal`

然后，基于这个开启度和上、下游水位，使用相应的水力学公式计算出流量 `outflow`。

## 3. 关键参数 (`parameters`)

在创建 `Gate` 实例时，需要提供以下核心参数：

*   `width` (米): 闸门的宽度。
*   `discharge_coefficient` (无量纲): 流量系数，这是一个综合性的经验系数，用于校正理论公式与实际流量之间的偏差。

## 4. 状态变量 (`state`)

`Gate` 对象维护并输出以下状态变量：

*   `opening` (0-1): 闸门的开启度，0表示全关，1表示全开。
*   `outflow` (立方米/秒): 当前通过闸门的流量。
*   `water_level` (米): 闸前水位。

## 5. 交互

*   `Gate` 模型的核心交互方式是通过 `action` 中的 `control_signal` 来接收控制指令。
*   `LocalControlAgent` 或 `PIDController` 等控制智能体，会计算出最优的 `control_signal` (例如，一个0到1之间的开度值)，并将其发布到该 `Gate` 对象所监听的动作主题上。
*   `Gate` 在其 `step()` 方法中接收到这个信号，并据此调整自己的状态和行为，从而实现了上层决策对物理世界的控制。
