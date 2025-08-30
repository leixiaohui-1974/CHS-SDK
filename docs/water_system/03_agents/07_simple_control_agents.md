# Core Agents: Simple Control Agents (核心智能体: 简单控制智能体)

This document introduces a series of simple control agents designed for direct control of individual devices such as valves, gates, and pumps.

## 1. Core Concept: Lightweight Implementation of `LocalControlAgent`

Similar to how "Perception Agents" are specialized implementations of `DigitalTwinAgent`, agents like `GateControlAgent`, `ValveControlAgent`, and `PumpControlAgent` are lightweight, specialized versions of the core control base class, `LocalControlAgent`.

它们的设计模式是：
1.  **继承 `LocalControlAgent`**: 它们都直接继承自 `LocalControlAgent` 类。这意味着它们天生就具备了 `LocalControlAgent` 的所有核心功能，包括：
    -   在内部封装一个控制器（如 PID 控制器）。
    -   订阅一个或多个观测主题（`observation_topics`）以获取输入。
    -   根据控制器逻辑计算出控制信号。
    -   将控制信号发布到动作主题（`action_topic`）。
2.  **构造函数的统一**: 它们使用与 `LocalControlAgent` 完全相同的构造函数。通过在初始化时传入不同的配置（如不同的主题名、不同的控制器实例），就可以实现对不同设备的控制。

Implementing them as separate classes primarily serves to **enhance architectural clarity and code readability**. When constructing a complex system, using `GateControlAgent(...)` more clearly indicates the agent's purpose is to control a gate than using a generic `LocalControlAgent(...)`.

## 2. Implemented Simple Control Agents

Below are the simple control agents currently implemented following the pattern described above. Their functionality and operational mechanics are identical to `LocalControlAgent`, with their specific control logic determined by the **controller** injected during initialization.

---

### `GateControlAgent`
*   **Source Code**: `core_lib/local_agents/control/gate_control_agent.py`
*   **Corresponding Physical Model**: `Gate`
*   **Responsibility**: To perform closed-loop or open-loop control of a single **gate**.
*   **Typical Applications**:
    -   **Target Water Level Control**: Inject a PID controller to observe upstream or downstream water levels (`observation_topics`), compare it to a setpoint, and automatically calculate and publish the target gate opening (`action_topic`).
    -   **Flow Rate Control**: Observe the flow through the gate and adjust the gate opening to meet a target flow rate.
    -   **Direct Opening Control**: Receive external commands to directly set the gate's target opening.

---

### `ValveControlAgent`
*   **Source Code**: `core_lib/local_agents/control/valve_control_agent.py`
*   **Corresponding Physical Model**: `Valve`
*   **Responsibility**: To perform closed-loop or open-loop control of a single **valve**.
*   **Typical Applications**:
    -   **Pressure Control**: Inject a PID controller to observe pressure at a point in a pipeline and adjust the valve opening to maintain the pressure at a target value.
    -   **Flow Rate Control**: Observe the pipeline flow rate and adjust the valve opening to achieve a target flow.
    -   **Direct Opening Control**: Receive external commands to directly set the valve's target opening.

---

### `PumpControlAgent`
*   **Source Code**: `core_lib/local_agents/control/pump_control_agent.py`
*   **Corresponding Physical Model**: `Pump`
*   **Responsibility**: To perform closed-loop or open-loop control of a single **pump**.
*   **Typical Applications**:
    -   **Flow Rate Control**: Inject a PID controller to observe the outflow of a pump and adjust its speed or status to meet a target flow rate.
    -   **Water Level Control**: Control the pump to maintain a water level in a connected reservoir or tank.
    -   **Direct Speed/Status Control**: Receive external commands to directly set the pump's operational status (on/off) or speed.

---

### `WaterTurbineControlAgent`
*   **Source Code**: `core_lib/local_agents/control/water_turbine_control_agent.py`
*   **Corresponding Physical Model**: `WaterTurbine`
*   **Responsibility**: To perform closed-loop or open-loop control of a single **water turbine**.
*   **Typical Applications**:
    -   **Power Generation Control**: Observe generated power and adjust the turbine's target outflow to meet a power demand setpoint.
    -   **Water Level Control**: Control the turbine's outflow to help maintain a specific water level in an upstream reservoir.
    -   **Flow Rate Control**: Adjust the turbine's operation to achieve a specific downstream flow requirement.
