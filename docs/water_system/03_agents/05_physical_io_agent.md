# 05. 物理IO智能体 (`PhysicalIOAgent`)

## 概述

`PhysicalIOAgent` 是连接数字控制智能体与物理世界（或其模拟环境）的关键接口层。它旨在模拟真实世界中监控与数据采集（SCADA）系统里的硬件组件，如传感器和执行器。

其核心角色是作为一座桥梁，将上层智能体发出的高级控制指令，转化为对物理实体的直接状态改变；同时，将物理世界的“真实”状态，以带有模拟噪声的传感器数据的形式，反馈给系统中的其他智能体。

## 核心职责

1.  **模拟传感器 (Sensing)**: 从物理模型对象（如 `Canal`）读取“真值”状态，选择性地加入高斯噪声以模拟传感器的不精确性，然后将处理后的数据发布到 `MessageBus`，供其他智能体使用。
2.  **模拟执行器 (Actuating)**: 订阅 `MessageBus` 上的特定“动作”主题。当收到控制指令（如“设置闸门开度为0.5米”）时，它会将该指令转化为对相应物理模型对象属性的直接修改（例如，设置 `Gate` 对象的 `target_opening` 属性）。

## 配置

`PhysicalIOAgent` 通过以下参数进行初始化：

-   `agent_id` (str): 智能体的唯一标识符。
-   `message_bus` (MessageBus): 系统消息总线的实例。
-   `sensors_config` (dict): 定义此智能体管理的所有传感器的配置。
-   `actuators_config` (dict): 定义此智能体管理的所有执行器的配置。

### `sensors_config`

该字典的键是每个传感器的唯一名称，值是包含以下键的另一字典：

-   `obj` (PhysicalObjectInterface): 需要读取状态的物理对象实例（如 `Canal` 或 `Reservoir` 对象）。
-   `state_key` (str): 从物理对象的 `get_state()` 方法返回的状态字典中，用于查找目标值的键。
-   `topic` (str): 用于发布传感器读数的 `MessageBus` 主题。
-   `noise_std` (float, optional): 添加到真值上的高斯噪声的标准差。默认为 `0.0`。

**示例:**
```python
sensors_config = {
    'canal_level_sensor': {
        'obj': upstream_canal,          # 需要监控的渠池对象
        'state_key': 'water_level',     # 从其状态中读取 'water_level'
        'topic': 'state.canal.level',   # 发布到此主题
        'noise_std': 0.02               # 添加标准差为 0.02 米的噪声
    }
}
```

### `actuators_config`

该字典的键是每个执行器的唯一名称，值是包含以下键的另一字典：

-   `obj` (PhysicalObjectInterface): 需要控制的物理对象实例（如 `Gate` 或 `Pump` 对象）。
-   `target_attr` (str): 物理对象上需要被智能体设置的目标状态属性名（如 `target_opening`）。物理对象自身的 `step` 方法负责使其当前状态向此目标状态演化。
-   `topic` (str): 执行器监听控制指令的 `MessageBus` 主题。
-   `control_key` (str): 在收到的指令消息体中，用于查找控制值的键。

**示例:**
```python
actuators_config = {
    'gate_actuator': {
        'obj': control_gate,                # 需要控制的闸门对象
        'target_attr': 'target_opening',    # 设置该对象的 'target_opening' 属性
        'topic': 'action.gate.opening',     # 在此主题上监听指令
        'control_key': 'control_signal'     # 指令消息中用于查找控制值的键
    }
}
```

## 与`SimulationHarness`和`OntologySimulationAgent`的关系

在 `core_lib` 架构中，`PhysicalIOAgent` 的角色和定位与“世界”的驱动方式密切相关。理解它与 `SimulationHarness` 和 `OntologySimulationAgent` 的关系至关重要。

`SimulationHarness` 和 `OntologySimulationAgent` 代表了两种**不同且互斥**的仿真设计哲学：

### 1. 模块化架构: `SimulationHarness` + 物理模型 + `PhysicalIOAgent`

在这种模式下，系统由多个独立的、可组合的模块构成：
-   **`SimulationHarness`**: 扮演“世界引擎”的角色。它管理仿真时钟，并按顺序驱动一个两阶段（智能体阶段 -> 物理阶段）的循环。
-   **物理模型 (`Gate`, `Canal` 等)**: 是被动的、包含自身物理逻辑的独立对象。它们的 `step()` 方法由 `SimulationHarness` 在物理阶段调用。
-   **`PhysicalIOAgent`**: 在此架构中，它**是必需的**。
    -   在“智能体阶段”，`PhysicalIOAgent` 的 `run()` 方法被调用，它从物理模型中读取状态，并发布到消息总线。
    -   它异步地监听来自其他控制智能体的指令，并更新物理模型的目标属性（如 `target_opening`）。
    -   它充当了被动的物理世界和主动的智能体世界之间的“I/O驱动程序”。

这个架构非常灵活，允许开发者通过YAML配置自由组合不同的物理组件和智能体，来构建任意复杂的系统。

### 2. 一体化架构: `OntologySimulationAgent` + 控制智能体

在这种模式下，整个物理世界被封装在一个单一的、高保真的智能体中：
-   **`OntologySimulationAgent`**: 它本身就是“物理世界”。其内部硬编码了物理状态、水动力学逻辑、执行器行为和传感器噪声。它在一个方法（如 `run_step()`）内完成了物理演化和数据发布的全部工作。
-   **`PhysicalIOAgent`**: 在此架构中**完全不需要**。`OntologySimulationAgent` 已经承担了`PhysicalIOAgent`的全部职责（模拟传感器并发布数据）以及所有物理模型的职责。

这个架构的目的是提供一个**标准、可复现的测试环境**（就像一个“精装样板房”），用于测试和验证其他独立智能体（如一个新的PID控制器或一个预测算法）的性能。

### 总结

| 架构模式 | `SimulationHarness` 模式 | `OntologySimulationAgent` 模式 |
| :--- | :--- | :--- |
| **核心** | `SimulationHarness` (世界引擎) | `OntologySimulationAgent` (世界本身) |
| **物理** | 独立的被动对象 (`Gate`, `Canal`) | 硬编码在 `OntologySimulationAgent` 内部 |
| **`PhysicalIOAgent`角色** | **必需的**，作为物理层和智能体层之间的I/O桥梁 | **不需要**，其功能已由 `OntologySimulationAgent` 实现 |
| **适用场景** | 构建、仿真和研究**任意结构**的复杂水系统 | 在**标准、固定**的环境中测试单个智能体的性能 |

因此，您会根据您的任务目标选择其中一种架构，而`PhysicalIOAgent`仅在第一种模块化架构中扮演核心角色。

### `PhysicalIOAgent` vs `DigitalTwinAgent`：职责分工

在更精细的 `SimulationHarness` 架构中，`PhysicalIOAgent` 和 `DigitalTwinAgent` 共同协作，代表了从物理世界到数字世界的两个不同抽象层次。

-   **`PhysicalIOAgent` (硬件I/O层)**:
    -   **角色**: 模拟最底层的硬件，如PLC或RTU。
    -   **职责**: 它的任务是“忠实但有缺陷地”读取。它直接从物理模型获取“真值”，通过**添加噪声**来模拟真实传感器的物理限制，然后将这些原始、带噪声的数据发布到消息总线。它不进行任何数据清洗或处理。

-   **`DigitalTwinAgent` (数字认知层)**:
    -   **角色**: 物理资产的“数字镜像”或“数字大脑”。
    -   **职责**: 它的任务是“理解并提炼”。它**订阅**由 `PhysicalIOAgent` 发布的原始数据，利用其“认知增强”能力（如指数移动平均滤波）对数据进行**清洗、平滑和校正**，最终发布一个高质量、可信的“官方”状态给系统中的其他决策智能体使用。

#### 数据流管道

这种分层设计形成了一个清晰、真实的数据处理管道：

```mermaid
graph TD
    subgraph 物理世界
        A[物理模型<br>(e.g., Canal)]
    end

    subgraph 硬件接口层
        B(PhysicalIOAgent)
    end

    subgraph 数字世界
        subgraph 原始数据总线
            C[MessageBus<br>(e.g., state.raw.level)]
        end
        subgraph 认知层
            D(DigitalTwinAgent)
        end
        subgraph 清洁数据总线
            E[MessageBus<br>(e.g., state.twin.level)]
        end
        subgraph 决策层
            F[控制智能体<br>(如 LocalControlAgent)]
        end
    end

    A -- get_state() --> B;
    B -- "发布原始、带噪声数据" --> C;
    C -- "订阅原始数据" --> D;
    D -- "发布清洁、平滑数据" --> E;
    E -- "订阅清洁数据" --> F;
```

**总结**: `PhysicalIOAgent` 负责“感知”，而 `DigitalTwinAgent` 负责“认知”。这种关注点分离的模式，使得整个系统架构更加清晰，也更贴近真实世界中数据从采集到应用的处理流程。
