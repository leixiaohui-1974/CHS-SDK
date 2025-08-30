# 1. 仿真 (Simulation) - 对象文档

## 概述

`Simulation` 对象是水系统仿真模块的核心。它封装了水系统的拓扑结构、物理属性和动态行为模型。通过该对象，用户可以方便地构建、配置和运行水系统仿真。

## `Simulation` 对象

### 属性

`Simulation` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 仿真实例的唯一标识符。
    *   **示例:** `"sim_20230829_001"`

*   **`name` (String):**
    *   **描述:** 仿真的名称，用于人类可读的识别。
    *   **示例:** `"某流域“闸-泵-站-河-库”联合调度仿真"`

*   **`description` (String):**
    *   **描述:** 对仿真的详细描述。
    *   **示例:** `"本仿真用于模拟汛期上游来水增加时，通过联合调度，确保下游控制断面水位不超警戒水位。"`

*   **`system_topology` (SystemTopology):**
    *   **描述:** 水系统的拓扑结构。这是一个复杂的对象，现在可以同时包含承压管网和开放渠系的对象，例如节点(`Node`)、管道(`Pipe`)、河道(`Reach`)、闸门(`Gate`)、水泵(`Pump`)、阀门(`Valve`)和水库(`Reservoir`)等。
    *   **数据结构 (示例):**
        ```json
        {
          "nodes": [
            { "id": "n1", "type": "junction", "elevation": 10.5 },
            { "id": "n2", "type": "storage_node", "bed_elevation": 12.0 }
          ],
          "pipes": [
            { "id": "p1", "from_node": "n1", "to_node": "n2", "length": 100, "diameter": 0.3 }
          ],
          "reaches": [
            { "id": "r1", "from_node": "n_upstream", "to_node": "n_downstream", "length": 5000, "manning_n": 0.03, "cross_section": { "type": "trapezoidal", "bottom_width": 20, "slope": 1.0 } }
          ],
          "gates": [
            { "id": "g1", "from_node": "n_gate_in", "to_node": "n_gate_out", "type": "sluice", "height": 5, "width": 10, "discharge_coeff": 0.6 }
          ],
          "hydropower_stations": [
            { "id": "hydro1", "node_id": "n_dam", "max_flow": 1500, "efficiency_curve": { "...": "..." } }
          ]
        }
        ```

*   **`time_settings` (TimeSettings):**
    *   **描述:** 仿真的时间配置，包括开始时间、结束时间、时间步长等。
    *   **数据结构 (示例):**
        ```json
        {
          "start_time": "2023-09-01T00:00:00Z",
          "end_time": "2023-09-01T23:59:59Z",
          "time_step_seconds": 600
        }
        ```

*   **`solver_options` (SolverOptions):**
    *   **描述:** 求解器的配置选项，例如数值精度、最大迭代次数等。
    *   **数据结构 (示例):**
        ```json
        {
          "tolerance": 1e-6,
          "max_iterations": 100
        }
        ```

*   **`status` (String):**
    *   **描述:** 仿真的当前状态。可以是 `created`, `running`, `completed`, `failed`。
    *   **默认值:** `created`

*   **`results` (SimulationResults):**
    *   **描述:** 仿真运行后产生的结果。这是一个只读属性，在仿真完成前为 `null`。
    *   **数据结构 (示例):**
        ```json
        {
          "timestamps": ["2023-09-01T00:00:00Z", ...],
          "node_pressures": {
            "n1": [15.2, 15.1, ...],
            "n2": [14.8, 14.7, ...]
          },
          "pipe_flows": {
            "p1": [0.5, 0.51, ...]
          }
        }
        ```

### 设计理念

`Simulation` 对象的设计遵循了“配置与执行分离”的原则。用户首先通过设置 `system_topology`, `time_settings`, 和 `solver_options` 等属性来完整地定义一个仿真场景。然后，通过调用 `run()` 方法来启动仿真计算。这种设计使得仿真场景的定义和复用变得非常方便。

此外，将仿真结果 `results` 设计为一个独立的对象，有助于在不影响仿真配置的情况下，对结果进行独立的分析、可视化和存储。

## 关联对象

### `SystemTopology` 对象

`SystemTopology` 对象定义了水系统的物理结构，是仿真的基础。它现在是一个更通用的概念，可以同时描述传统的承压管网和包含河道、闸门、水电站等的开放渠系。它通常从外部文件（如 EPANET INP, HEC-RAS 文件）导入，或通过 API 动态构建。

### `TimeSettings` 对象

`TimeSettings` 对象控制仿真的时间维度，对于动态仿真至关重要。

### `SolverOptions` 对象

`SolverOptions` 对象允许高级用户对底层的数值求解器进行微调，以适应不同的仿真精度和性能要求。

### `SimulationResults` 对象

`SimulationResults` 对象是仿真运行的产出，它以结构化的方式存储了所有时间步上的所有网络元素的状态（如节点的压力、管段的流量等）。
