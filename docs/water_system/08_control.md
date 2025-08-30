# 8. 本地控制 (Local Control)

本篇文档详细介绍 `core_lib` 中用于实现本地化、实时反馈控制的功能。这是连接高层调度指令与物理设备执行的“最后一公里”。

## 1. 核心理念：策略模式与分层控制

本地控制层是分层控制架构的执行端。它的核心设计采用了经典的**策略模式 (Strategy Pattern)**。

*   **上下文 (Context)**: `LocalControlAgent` (`local_agents/control/local_control_agent.py`) 扮演了上下文的角色。它负责处理所有与外部世界的通信，包括：
    *   从消息总线订阅观测数据（如传感器读数）。
    *   从消息总线订阅高层指令（如新的设定点）。
    *   向消息总线发布计算出的控制动作。
*   **策略 (Strategy)**: 任何实现了 `Controller` 接口 (`core/interfaces.py`) 的类都可以作为一个控制策略。它封装了具体的控制算法，其核心是 `compute_control_action()` 方法。

这种设计将**通信逻辑**与**控制算法**完全解耦。这使得开发者可以专注于编写控制算法，而无需关心它如何集成到整个智能体系统中。同时，也可以方便地为同一个 `LocalControlAgent` 替换不同的控制算法（例如，从PID切换到模糊控制）。

## 2. 关键组件

### 2.1 `Controller` 接口

*   **位置**: `core_lib/core/interfaces.py`
*   **职责**: 定义所有控制算法必须遵循的统一接口。
    ```python
    # core_lib/core/interfaces.py (示意)
    class Controller:
        def compute_control_action(self, observation: State, dt: float) -> Any:
            """根据当前的观测状态，计算出下一个控制动作。"""
            raise NotImplementedError
    ```

### 2.2 `LocalControlAgent`

*   **位置**: `core_lib/local_agents/control/local_control_agent.py`
*   **职责**:
    1.  在初始化时，持有一个 `Controller` 策略的实例。
    2.  通过 `handle_observation` 回调函数，将从消息总线收到的观测数据传递给 `controller.compute_control_action()`。
    3.  通过 `publish_action` 方法，将控制器计算出的结果发布到相应的动作主题上。
    4.  通过 `handle_command_message` 回调函数，接收来自上层调度器的新设定点，并更新其内部控制器的状态（例如，调用 `controller.set_setpoint()`）。

### 2.3 `PIDController` (具体策略示例)

*   **位置**: `core_lib/local_agents/control/pid_controller.py`
*   **职责**: 提供一个具体、通用的 PID (比例-积分-微分) 控制算法。
*   **特点**:
    *   实现了 `Controller` 接口。
    *   包含一个功能完备的 PID 算法，包括**抗积分饱和 (Anti-Windup)** 机制，这对于处理执行器达到物理极限（如阀门全开或全关）的真实场景至关重要。
    *   提供 `set_setpoint()` 方法，允许被 `LocalControlAgent` 动态更新其控制目标。

## 3. 工作流程示例 (一个闸门的水位控制)

1.  一个 `gate_control_agent` (它是 `LocalControlAgent` 的一个实例) 被创建，其内部封装了一个 `PIDController` 实例。
2.  该 Agent 订阅 `topic_downstream_level` (下游水位观测) 和 `topic_gate1_setpoint_cmd` (来自中央调度的指令)。
3.  `CentralMPCAgent` 经过优化计算，认为下游目标水位应为 55.0 米，于是向 `topic_gate1_setpoint_cmd` 发布消息 `{'new_setpoint': 55.0}`。
4.  `gate_control_agent` 收到消息，调用其内部 `PIDController` 的 `set_setpoint(55.0)` 方法。
5.  在下一个时间步，`DigitalTwinAgent` 发布了最新的下游水位 `{'water_level': 55.2}` 到 `topic_downstream_level`。
6.  `gate_control_agent` 收到这个观测消息，将其传递给 `PIDController`。
7.  `PIDController` 计算出误差 (`55.0 - 55.2 = -0.2`)，并通过PID公式计算出一个控制动作（例如，一个表示“关小闸门”的负值 `-0.05`）。
8.  `gate_control_agent` 将这个动作发布到 `topic_gate1_action` 主题。
9.  `gate` 物理对象的模拟器订阅了此主题，收到 `-0.05` 的信号后，更新自己的开度，从而影响下个时间步的水力计算结果。
10. 这个闭环不断重复，使得下游水位稳定在55.0米左右。
