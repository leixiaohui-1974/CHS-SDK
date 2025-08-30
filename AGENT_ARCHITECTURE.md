# 智能体架构设计文档

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.0 | 2023-10-27 |

## 1. 简介

本文档是水系统智能控制平台的核心设计文档，旨在为平台开发提供一套标准、统一的智能体（Agent）架构。该架构基于**水系统控制论**，对现有代码库进行了深度分析和归纳，将所有智能体清晰地划分为“被控对象代理”、“控制对象代理”、“中央协调代理”和“任务与模拟支持智能体”四大类。

本文档的目标是：
*   **明确职责边界**：清晰定义每一类智能体的功能和通信范围。
*   **规范继承关系**：所有智能体设计严格遵循既有的代码基类，确保架构的一致性。
*   **提供开发参考**：罗列当前已实现和建议新增的智能体清单及其源码路径，作为未来开发的基准。

## 2. 核心架构原则

为了保证系统的稳定性、可扩展性和模块化，所有智能体的设计与实现均需遵循以下核心原则：

1.  **被控对象代理 (Controlled Object Agents)**
    *   **职责**：代表水系统中的物理单元（如水库、河道、泵站），其核心职责是**提供状态感知能力**，作为物理世界的数字孪生。
    *   **行为**：这类代理**不执行主动控制**，仅向上层或协调者报告自身状态。

2.  **控制对象代理 (Control Object Agents)**
    *   **职责**：代表具有主动控制能力的物理单元（如水泵、水闸、水电站）。
    *   **行为**：既具备被控对象的感知能力，又可**接收并执行控制指令**。控制逻辑可以分层，例如，站级代理（泵站）负责协调，并将具体指令（如启停、开度）下发给机组级代理（单个水泵）。

3.  **中央协调代理 (Central Agents)**
    *   **职责**：作为系统的最高决策层，负责**全局状态感知、优化计算和集中调度**。
    *   **行为**：仅与**控制对象代理**进行通信，下发宏观控制目标或指令，不直接干预被控对象。

4.  **代码基类继承 (Codebase Consistency)**
    *   **原则**：所有智能体的分类严格基于代码库中已定义的基类（如 `DigitalTwinAgent`, `LocalControlAgent`），不引入新的抽象概念，保证架构与代码实现的高度统一。

## 3. 智能体分类与清单

### 3.1 水系统被控对象代理 (Controlled Object Agents)
*   **继承关系**：继承自 `DigitalTwinAgent` 或其变体，扮演物理单元数字孪生的角色。
*   **核心功能**：状态感知与报告。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `ReservoirPerceptionAgent` | 水库感知，提供水位、库容等状态 | `core_lib/local_agents/perception/reservoir_perception_agent.py` |
| `PipelinePerceptionAgent` | 有压管道感知，提供流量、压力等状态 | `core_lib/local_agents/perception/pipeline_perception_agent.py` |
| `ChannelPerceptionAgent` | 无压渠道/河道感知，提供水位、流量等状态 | `core_lib/local_agents/perception/channel_perception_agent.py` |
| `HydropowerStationPerceptionAgent` | 水电站感知，提供上下游水位、总发电量等状态 | `core_lib/local_agents/perception/hydropower_station_perception_agent.py` |
| `PumpStationPerceptionAgent` | 泵站感知，提供集水池水位、总流量等站级状态 | `core_lib/local_agents/perception/pump_station_perception_agent.py` |
| `ValveStationPerceptionAgent` | 阀门/水闸站感知，提供上下游水位、总流量等站级状态 | `core_lib/local_agents/perception/valve_station_perception_agent.py` |
| `RiverChannelPerceptionAgent` | 专注于不规则断面河道的感知，处理更复杂的河道水力学模型。 | `core_lib/local_agents/perception/river_channel_perception_agent.py` |
| `GatePerceptionAgent`| 针对单个闸门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/gate_perception_agent.py` |
| `PumpPerceptionAgent`| 针对单个水泵的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/pump_perception_agent.py` |
| `ValvePerceptionAgent`| 针对单个阀门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/valve_perception_agent.py` |

### 3.2 水系统控制对象代理 (Control Object Agents)
*   **继承关系**：大多继承自 `LocalControlAgent`。此类智能体通过封装一个**控制器**（例如PID）来实现具体的控制逻辑，因此非常灵活。
*   **核心功能**：接收指令和观测值，执行本地闭环或开环控制。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `LocalControlAgent` | **本地控制通用基类**，封装了控制器，并通过消息总线处理观测和动作。是实现大多数本地控制任务的核心。 | `core_lib/local_agents/control/local_control_agent.py` |
| `PumpControlAgent` | 控制一个**泵站**（PumpStation），根据流量需求决定开启或关闭站内**多个离散水泵**。(*注意: 该代理直接继承自 Agent，而非 LocalControlAgent*) | `core_lib/local_agents/control/pump_control_agent.py` |
| `ValveControlAgent` | 控制单个阀门。它本身是 `LocalControlAgent` 的一个轻量级实现，需在初始化时配置具体的控制器（如PID）。 | `core_lib/local_agents/control/valve_control_agent.py` |
| `GateControlAgent` | 控制单个闸门，与 `ValveControlAgent` 类似，是 `LocalControlAgent` 的轻量级实现。 | `core_lib/local_agents/control/gate_control_agent.py` |
| `PumpStationControlAgent` | 泵站控制的**站级代理**，负责站级总调度（如决定总流量），并将指令下发给机组级代理（如 `PumpControlAgent`）。 | `core_lib/local_agents/control/pump_station_control_agent.py` |
| `ValveStationControlAgent` | 阀门站控制的**站级代理**，负责实现站级流量或水位目标，并将计算出的开度指令下发给站内每个阀门。 | `core_lib/local_agents/control/valve_station_control_agent.py` |
| `HydropowerStationAgent` | 水电站控制，负责制定站级策略，并向下游发布针对单个水轮机或水闸的控制指令。 | `core_lib/local_agents/control/hydropower_station_agent.py` |
| `HydropowerStationControlAgent` | 水电站控制，同上。 | `core_lib/local_agents/control/hydropower_station_control_agent.py` |
| `PressureControlAgent` | 压力控制，一个 `LocalControlAgent` 的应用实例，专用于需要维持特定压力的控制场景。 | `core_lib/local_agents/control/pressure_control_agent.py` |

### 3.3 中央协调代理 (Central Agents)
*   **继承关系**：无统一基类，为逻辑分组。
*   **核心功能**：全局感知、集中决策与调度。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `CentralDispatcherAgent` | 中央调度，系统的最高决策者，负责全局优化和指令分发。 | `core_lib/central_coordination/dispatch/central_dispatcher_agent.py`|
| `CentralMPCAgent` | 中央MPC控制，采用模型预测控制（MPC）算法进行全局优化调度。 | `core_lib/central_coordination/dispatch/central_mpc_agent.py` |
| `CentralPerceptionAgent` | 中央感知，汇集所有本地感知信息，形成全局态势图。 | `core_lib/central_coordination/perception/central_perception_agent.py` |
| `CentralAnomalyDetectionAgent` | 订阅所有本地感知状态，利用全局算法（如图论、机器学习）识别跨区域的复杂异常模式。 | `core_lib/central_coordination/dispatch/central_anomaly_detection_agent.py` |
| `DemandForecastingAgent` | 预测整个水系统的用水需求，为中央调度提供前瞻性的决策依据。 | `core_lib/central_coordination/dispatch/demand_forecasting_agent.py` |

### 3.4 任务与模拟支持智能体 (Task & Simulation Support Agents)
*   **继承关系**：大多直接继承自 `Agent` 或 `BaseAgent`。
*   **核心功能**：提供数据输入、模拟扰动、执行特定任务（如预测、辨识）。

| 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- |
| `CsvInflowAgent` | 从CSV文件读取并提供入流数据。 | `core_lib/data_access/csv_inflow_agent.py` |
| `EmergencyAgent` | 应急响应，监测特定条件并触发应急预案。 | `core_lib/local_agents/supervisory/emergency_agent.py` |
| `IdentificationAgent` | 参数辨识，在线或离线辨识物理模型的参数。 | `core_lib/identification/identification_agent.py` |
| `RainfallAgent` | 降雨模拟，根据预设模式提供降雨数据。 | `core_lib/disturbances/rainfall_agent.py` |
| `DynamicRainfallAgent` | 动态降雨模拟，可根据外部输入动态调整降雨过程。 | `core_lib/disturbances/dynamic_rainfall_agent.py` |
| `ForecastingAgent` | 预测通用代理。 | `core_lib/local_agents/prediction/forecasting_agent.py` |
| `InflowForecasterAgent` | 入流预测，基于历史数据和模型预测未来的入流量。 | `core_lib/local_agents/prediction/inflow_forecaster_agent.py` |
| `WaterUseAgent` | 用水模拟，模拟城市或农业的用水行为。 | `core_lib/disturbances/water_use_agent.py` |
| `PhysicalIOAgent` | 物理I/O模拟，作为物理层和数字层的桥梁。模拟传感器（可带噪声）和执行器，响应控制指令。 | `core_lib/local_agents/io/physical_io_agent.py` |
| `CsvReaderAgent` | CSV数据读取器，通用的CSV文件解析代理。 | `core_lib/disturbances/csv_reader_agent.py` |
| `OntologySimulationAgent` | 物理仿真本体，驱动物理模型进行仿真计算。 | `core_lib/local_agents/ontology_simulation_agent.py` |
| `ModelUpdaterAgent` | 订阅 `IdentificationAgent` 的输出，自动将新参数更新到相应的数字孪生模型中。 | `core_lib/identification/model_updater_agent.py` |
| `ScenarioAgent` | 根据预设脚本，在特定时间协调并触发各种扰动（如洪水、故障），用于自动化测试和应急演练。 | `core_lib/mission/scenario_agent.py` |


