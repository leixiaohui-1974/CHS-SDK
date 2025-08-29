# 3. 孪生 (Twinning) - 对象文档

## 概述

`DigitalTwin` 对象是构建水系统数字孪生应用的核心。数字孪生不仅仅是一个静态的模型或一次性的仿真，它是一个与物理水系统实时或准实时同步、持续运行的动态系统。它集成了仿真、辨识、数据接入等多种能力，旨在创建一个与真实世界精准映射的虚拟副本。

## `DigitalTwin` 对象

### 属性

`DigitalTwin` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 数字孪生实例的唯一标识符。
    *   **示例:** `"twin_main_city_pipeline"`

*   **`name` (String):**
    *   **描述:** 数字孪生的名称。
    *   **示例:** `"主城区供水管网数字孪生"`

*   **`base_simulation_model` (Simulation):**
    *   **描述:** 作为数字孪生基础的仿真模型。这个模型通常是经过参数辨识校准过的，具有较高的精度。数字孪生的“推演”能力就基于此模型。
    *   **重要:** 这是一个“模板”模型，孪生系统会基于它创建内部的、持续运行的仿真实例。

*   **`data_source_connections` (Array<DataSourceConnection>):**
    *   **描述:** 定义了如何从外部数据源（如SCADA系统、IoT平台、数据库）获取实时数据。这是实现物理世界到数字世界单向同步的关键。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "id": "scada_source_1",
            "source_type": "opc_ua",
            "endpoint_url": "opc.tcp://192.168.1.100:4840",
            "node_mappings": {
              "SCADA.Node.Pressure.N5": { "element_type": "node", "element_id": "n5", "parameter_name": "pressure" },
              "SCADA.Pipe.Flow.P3": { "element_type": "pipe", "element_id": "p3", "parameter_name": "flow" }
            }
          }
        ]
        ```

*   **`synchronization_policy` (SyncPolicy):**
    *   **描述:** 定义了数字孪生与物理系统之间的同步策略。
    *   **数据结构 (示例):**
        ```json
        {
          "sync_interval_seconds": 60, // 每隔60秒与物理世界同步一次
          "state_correction_strategy": "kalman_filter", // 状态校正策略，用于融合模型预测和实际观测
          "auto_recalibration_trigger": { // 自动再校准触发器
            "enabled": true,
            "error_threshold": 0.15, // 当模型预测与观测的平均误差超过15%时触发
            "cooldown_period_hours": 24 // 触发一次后，24小时内不再触发
          }
        }
        ```

*   **`state` (TwinState):**
    *   **描述:** 数字孪生当前的状态。这不仅仅是一个简单的字符串，而是一个包含了整个水系统在“现在”这个时间点上所有状态的快照。
    *   **数据结构 (示例):**
        ```json
        {
          "timestamp": "2023-09-01T10:00:00Z",
          "node_states": {
            "n1": { "pressure": 15.1, "quality": 0.98 },
            "n2": { "pressure": 14.7, "quality": 0.97 }
          },
          "pipe_states": { ... },
          "sync_status": {
            "last_sync_time": "2023-09-01T09:59:58Z",
            "last_sync_error": 0.05 // 上次同步时，模型与现实的误差
          }
        }
        ```

*   **`status` (String):**
    *   **描述:** 数字孪生服务的运行状态。可以是 `running`, `stopped`, `degraded` (例如，数据源中断), `recalibrating`。
    *   **默认值:** `stopped`

### 设计理念

`DigitalTwin` 的设计核心是“持续同步”和“动态演化”。

1.  **持续同步:** 通过 `data_source_connections` 和 `synchronization_policy`，`DigitalTwin` 对象不再是一次性的计算任务，而是一个长期运行的服务。它周期性地从物理世界拉取数据，并使用如卡尔曼滤波等数据融合技术，将观测数据与 `base_simulation_model` 的预测结果相融合，从而不断修正自身的 `state`，使其尽可能逼近真实世界。

2.  **动态演化:** 数字孪生不是一成不变的。物理系统自身会发生变化（如管道老化），`DigitalTwin` 通过 `auto_recalibration_trigger` 机制，能够感知到模型精度的下降，并在必要时自动触发一个新的参数辨识任务（`Identification`），从而实现模型的自我完善和演化。

它将仿真、辨识、数据处理等能力有机地组织在一起，构成了一个能够反映物理实体全生命周期的动态虚拟映射。
