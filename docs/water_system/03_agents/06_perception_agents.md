# 核心智能体: 感知智能体 (Perception Agents)

本篇文档介绍一系列用于“感知”物理世界状态的智能体。在 `core_lib` 的架构中，这些智能体是**数字孪生 (`DigitalTwinAgent`)** 的具体化实现，每一个都对应一种特定的物理模型。

## 1. 核心理念：继承与专一化

所有感知智能体的设计都遵循一个统一的模式：
1.  **继承 `DigitalTwinAgent`**: 它们都直接继承自 `DigitalTwinAgent` 类。这意味着它们天生就具备了 `DigitalTwinAgent` 的所有核心功能：
    -   在内部封装一个物理对象模型。
    -   在每个仿真步长 (`run()` 方法) 中，从物理模型获取最新状态。
    -   对状态数据进行可选的认知增强（如平滑滤波）。
    -   将最终的状态发布到指定的消息总线主题上。
2.  **构造函数的专一化**: 每个感知智能体类都提供了一个专一化的构造函数，其参数被明确类型提示为它所对应的物理模型。例如，`ReservoirPerceptionAgent` 的构造函数要求传入一个 `Reservoir` 对象。

这种设计的好处是：
-   **架构清晰**: 在构建一个仿真场景时，使用 `ReservoirPerceptionAgent(reservoir_model, ...)` 这样的代码，比使用通用的 `DigitalTwinAgent(reservoir_model, ...)` 更能清晰地表达开发者的意图。
-   **便于扩展**: 虽然现在这些类只是简单的包装器，但未来可以很方便地在各自的类中添加针对特定物理模型的独有逻辑（例如，在 `ReservoirPerceptionAgent` 中添加基于库区特性的蒸发量估算逻辑），而无需修改通用的 `DigitalTwinAgent`。

## 2. 已实现的感知智能体

以下是当前已实现的、遵循上述模式的感知智能体清单。它们的功能和工作机制与 `DigitalTwinAgent` 完全一致。

---

### `ReservoirPerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/reservoir_perception_agent.py`
*   **对应物理模型**: `Reservoir`
*   **职责**: 模拟对一个**水库**的感知，发布其水位、库容等状态。

---

### `PipelinePerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/pipeline_perception_agent.py`
*   **对应物理模型**: `Pipe`
*   **职责**: 模拟对一段**有压管道**的感知，发布其流量、压力等状态。

---

### `ChannelPerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/channel_perception_agent.py`
*   **对应物理模型**: `Canal` 或 `RiverChannel`
*   **职责**: 模拟对一段**明渠或河道**的感知，发布其水位、流量等状态。

---

### `HydropowerStationPerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/hydropower_station_perception_agent.py`
*   **对应物理模型**: `HydropowerStation`
*   **职责**: 模拟对一个**水电站**的感知，发布其总出流量、总发电量等站级聚合状态。

---

### `PumpStationPerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/pump_station_perception_agent.py`
*   **对应物理模型**: `PumpStation`
*   **职责**: 模拟对一个**泵站**的感知，发布其总出流量、总功耗、运行泵数等站级聚合状态。

---

### `ValveStationPerceptionAgent`
*   **源代码**: `core_lib/local_agents/perception/valve_station_perception_agent.py`
*   **对应物理模型**: `ValveStation`
*   **职责**: 模拟对一个**阀门站**的感知，发布其总出流量等站级聚合状态。
