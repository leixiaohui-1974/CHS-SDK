# 核心智能体: 复杂/站级控制智能体

本篇文档介绍一系列用于实现对一个“站”（如泵站、阀门站、水电站）进行整体协调控制的智能体。与简单控制智能体不同，这些智能体的逻辑更复杂，体现了**分层控制**的思想。

## 1. 核心理念：目标分解与分层控制

这些站级控制智能体的共同特点是：
1.  **接收高层目标**: 它们不直接控制单个设备的物理参数，而是从上层（如中央调度智能体或一个人机交互界面）接收一个宏观的、站级的控制目标。例如“启动3台水泵”、“让泵站总流量达到 5 m³/s”或“水电站发电功率维持在 50 MW”。
2.  **订阅站级状态**: 它们会订阅对应的站级感知智能体（如 `PumpStationPerceptionAgent`）发布的状态主题，以获取当前站点的整体运行状态作为反馈。
3.  **分解目标，下发指令**: 它们内部包含**控制逻辑**，负责将宏观的站级目标分解为对站内每个独立设备（如单个水泵、阀门）的具体、底层的控制指令。
4.  **发布底层指令**: 最后，它们将这些底层指令发布到每个设备自己监听的动作主题上。

这种分层架构将复杂的站级调度逻辑（“做什么”）与底层的设备执行（“怎么做”）解耦，使得系统结构更清晰，也更容易维护和扩展。

## 2. 已实现的站级控制智能体

---

### `PumpStationControlAgent`
*   **源代码**: `core_lib/local_agents/control/pump_station_control_agent.py`
*   **职责**: 控制一个泵站，使其满足**目标运行泵数**。
*   **工作机制**:
    -   **输入**: 监听 `goal_topic`，获取 `target_active_pumps` (目标开启泵数)。
    -   **逻辑**: 收到新目标后，它会按顺序向下属的每个水泵发布 `control_signal` (1 为开启, 0 为关闭)，直到达到目标开启数量。例如，目标为3，它就会向列表中的前3台水泵发送“开启”指令，向其余水泵发送“关闭”指令。
    -   **输出**: 向每个水泵的 `action_topic` 发布控制指令。

---

### `PumpControlAgent`
*   **源代码**: `core_lib/local_agents/control/pump_control_agent.py`
*   **职责**: 控制一个泵站，使其满足**目标流量需求**。
*   **工作机制**:
    -   **输入**: 监听 `demand_topic`，获取 `value` (目标流量, m³/s)。
    -   **逻辑**: 假设站内所有水泵的单泵流量相同，它会用 `ceil(目标流量 / 单泵流量)` 来计算出需要开启的水泵数量，然后按顺序开启相应数量的水泵。
    -   **输出**: 向每个水泵的 `action_topic` 发布控制指令。
    -   **注**: 该智能体与 `PumpStationControlAgent` 功能相似，但控制目标不同（流量 vs. 泵数）。

---

### `ValveStationControlAgent`
*   **源代码**: `core_lib/local_agents/control/valve_station_control_agent.py`
*   **职责**: 控制一个阀门站，使其满足**目标总流量**。
*   **工作机制**:
    -   **输入**: 监听 `goal_topic` 获取 `target_total_flow`，并监听 `state_topic` 获取当前总流量 `current_total_flow`。
    -   **逻辑**: 实现了一个简单的**比例控制器 (P-Controller)**。它计算目标与当前流量的误差 `error = target - current`，然后根据 `adjustment = Kp * error` 来计算一个开度调整量，并将其应用到**所有阀门**上。
    -   **输出**: 向站内所有阀门的 `action_topic` 发布相同的目标开度 `control_signal`。

---

### `HydropowerStationControlAgent`
*   **源代码**: `core_lib/local_agents/control/hydropower_station_control_agent.py`
*   **职责**: 控制一个水电站，使其同时满足**发电功率**和**总出流量**两个宏观目标。
*   **工作机制**:
    -   **输入**: 监听 `goal_topic` 获取 `target_power_generation` 和 `target_total_outflow`。同时监听 `state_topic` 获取当前的 `current_head` (水头) 和 `current_turbine_outflow` (水轮机流量)。
    -   **逻辑**: 采用一个简化的解耦策略：
        1.  **优先满足发电**: 首先，根据水力发电公式的反函数 (`Q = P / (η * ρ * g * H)`)，计算出要达到目标功率所需的总流量，并将其平均分配给所有水轮机。
        2.  **再用闸门补足流量**: 然后，用总流量目标减去当前水轮机的实际流量，得到需要通过泄洪闸补充的剩余流量，并将其平均分配给所有闸门。
    -   **输出**: 分别向所有水轮机和所有闸门的 `action_topic` 发布各自的目标流量指令。
