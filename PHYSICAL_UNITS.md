# 水系统物理单元清单

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.0 | 2023-10-27 |

## 1. 简介

本文档旨在为**水系统智能控制平台**的开发提供一份关于**物理单元**的权威参考。所有在系统中进行建模、仿真或控制的物理实体，都在此进行统一说明。

本文档的核心目标是：
*   **明确物理实体**：清晰定义系统中的每一个物理单元。
*   **关联数字代理**：将物理单元与其在软件中的数字孪生代理（Agent）进行唯一映射。
*   **提供开发基准**：为新功能的开发、测试和集成提供统一的物理单元参考，加速开发进程。

## 2. 物理单元分类

根据其是否具备主动控制能力，物理单元分为两类：

*   **被控对象 (Controlled Objects)**：不具备主动控制能力的物理单元，如水库、河道。其代理的核心职责是**状态感知**。
*   **控制对象 (Control Objects)**：具备主动控制能力的物理单元，如水泵、水闸。其代理在感知状态的同时，还负责**接收并执行控制指令**。

---

## 3. 物理单元清单

### 3.1 被控对象 (Controlled Objects)

这些是系统中仅提供状态感知的物理单元。

| 物理单元 | 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- | :--- |
| 水库 | `ReservoirPerceptionAgent` | 水库感知，提供水位、库容等状态 | `core_lib/local_agents/perception/reservoir_perception_agent.py` |
| 有压管道 | `PipelinePerceptionAgent` | 有压管道感知，提供流量、压力等状态 | `core_lib/local_agents/perception/pipeline_perception_agent.py` |
| 无压渠道/河道 | `ChannelPerceptionAgent` | 无压渠道/河道感知，提供水位、流量等状态 | `core_lib/local_agents/perception/channel_perception_agent.py` |
| 水电站（感知） | `HydropowerStationPerceptionAgent` | 水电站感知，提供上下游水位、总发电量等状态 | `core_lib/local_agents/perception/hydropower_station_perception_agent.py` |
| 泵站（感知） | `PumpStationPerceptionAgent` | 泵站感知，提供集水池水位、总流量等站级状态 | `core_lib/local_agents/perception/pump_station_perception_agent.py` |
| 阀门/水闸站（感知）| `ValveStationPerceptionAgent` | 阀门/水闸站感知，提供上下游水位、总流量等站级状态 | `core_lib/local_agents/perception/valve_station_perception_agent.py` |
| 不规则河道 | `RiverChannelPerceptionAgent` | 专注于不规则断面河道的感知，处理更复杂的河道水力学模型。 | `core_lib/local_agents/perception/river_channel_perception_agent.py` |
| 单个闸门（感知） | `GatePerceptionAgent`| 针对单个闸门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/gate_perception_agent.py` |
| 单个水泵（感知） | `PumpPerceptionAgent`| 针对单个水泵的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/pump_perception_agent.py` |
| 单个阀门（感知） | `ValvePerceptionAgent`| 针对单个阀门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/valve_perception_agent.py` |

### 3.2 控制对象 (Control Objects)

这些是系统中具备主动控制能力的物理单元。

| 物理单元 | 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- | :--- |
| **通用控制器** | `LocalControlAgent` | **本地控制通用基类**，封装了控制器，并通过消息总线处理观测和动作。是实现大多数本地控制任务的核心。 | `core_lib/local_agents/control/local_control_agent.py` |
| 泵机组 | `PumpControlAgent` | 控制一个**泵站**（PumpStation），根据流量需求决定开启或关闭站内**多个离散水泵**。(*注意: 该代理直接继承自 Agent，而非 LocalControlAgent*) | `core_lib/local_agents/control/pump_control_agent.py` |
| 单个阀门（控制） | `ValveControlAgent` | 控制单个阀门。它本身是 `LocalControlAgent` 的一个轻量级实现，需在初始化时配置具体的控制器（如PID）。 | `core_lib/local_agents/control/valve_control_agent.py` |
| 单个闸门（控制） | `GateControlAgent` | 控制单个闸门，与 `ValveControlAgent` 类似，是 `LocalControlAgent` 的轻量级实现。 | `core_lib/local_agents/control/gate_control_agent.py` |
| 泵站（控制） | `PumpStationControlAgent` | 泵站控制的**站级代理**，负责站级总调度（如决定总流量），并将指令下发给机组级代理（如 `PumpControlAgent`）。 | `core_lib/local_agents/control/pump_station_control_agent.py` |
| 阀门站（控制） | `ValveStationControlAgent` | 阀门站控制的**站级代理**，负责实现站级流量或水位目标，并将计算出的开度指令下发给站内每个阀门。 | `core_lib/local_agents/control/valve_station_control_agent.py` |
| 水电站（控制） | `HydropowerStationAgent` | 水电站控制，负责制定站级策略，并向下游发布针对单个水轮机或水闸的控制指令。 | `core_lib/local_agents/control/hydropower_station_agent.py` |
| 水电站（控制） | `HydropowerStationControlAgent` | 水电站控制，同上。 | `core_lib/local_agents/control/hydropower_station_control_agent.py` |
| 压力控制器 | `PressureControlAgent` | 压力控制，一个 `LocalControlAgent` 的应用实例，专用于需要维持特定压力的控制场景。 | `core_lib/local_agents/control/pressure_control_agent.py` |
