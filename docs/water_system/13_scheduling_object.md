# 7. 调度 (Scheduling) - 对象文档

## 概述

`Scheduling` 对象是水系统优化调度模块的核心。它的主要任务是基于对未来的预测（尤其是需水量预测），结合水力模型、电价信息和业务规则，计算出一套最优的设备（主要是水泵和阀门）控制计划。其核心目标通常是在满足供水安全的前提下，实现总运行成本（主要是电费）的最小化。

## `Scheduling` 对象

### 属性

`Scheduling` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 优化调度任务的唯一标识符。
    *   **示例:** `"sched_pump_station_A_24h"`

*   **`name` (String):**
    *   **描述:** 调度任务的名称。
    *   **示例:** `"A泵站未来24小时优化调度"`

*   **`target_simulation_model` (Simulation):**
    *   **描述:** 调度优化所基于的水力模型。优化器需要利用这个模型来推演不同控制方案（如开启某台水泵）对系统状态（如压力、流量）的影响。这个模型通常是经过校准的，以保证准确性。

*   **`control_variables` (Array<ControlVariable>):**
    *   **描述:** 定义了在优化过程中可以被控制的设备及其操作范围。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "element_type": "pump",
            "element_id": "pump_A1",
            "control_type": "status" // 控制类型: status (启停), speed (转速)
          },
          {
            "element_type": "pump",
            "element_id": "pump_A2",
            "control_type": "status"
          },
          {
            "element_type": "valve",
            "element_id": "valve_V3",
            "control_type": "setting" // 例如，减压阀的出口压力设定
          }
        ]
        ```

*   **`objective_function` (ObjectiveFunction):**
    *   **描述:** 定义了优化的目标。这是调度问题的核心。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "minimize_cost",
          "cost_components": [
            { "type": "energy_cost", "electricity_price_forecast_id": "price_forecast_24h" },
            { "type": "maintenance_cost", "pump_switch_penalty": 5.0 } // 水泵每次开关的虚拟成本，以减少频繁启停
          ]
        }
        ```

*   **`constraints` (Array<Constraint>):**
    *   **描述:** 定义了在优化过程中必须满足的约束条件，以保证供水安全。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "type": "node_pressure",
            "node_id": "node_critical_1",
            "min_pressure": 22.0,
            "max_pressure": 45.0
          },
          {
            "type": "reservoir_level",
            "reservoir_id": "reservoir_R1",
            "min_level": 3.0,
            "end_of_period_target_level": 4.5 // 要求在调度周期结束时，水库水位不低于某个值
          }
        ]
        ```

*   **`input_forecasts` (Object):**
    *   **描述:** 调度所需的外部输入预测。
    *   **数据结构 (示例):**
        ```json
        {
          "demand_forecast_id": "pred_zonal_demand_24h",
          "electricity_price_forecast_id": "price_forecast_24h"
        }
        ```

*   **`latest_schedule` (ControlSchedule):**
    *   **描述:** 一个只读属性，包含了最近一次优化计算生成的最优控制计划。
    *   **数据结构 (示例):**
        ```json
        {
          "schedule_id": "cs_202309011500",
          "generated_at": "2023-09-01T15:05:10Z",
          "start_time": "2023-09-01T16:00:00Z",
          "time_steps": ["2023-09-01T16:00:00Z", "2023-09-01T17:00:00Z", ...],
          "control_plan": {
            "pump_A1": { "status": [1, 1, 0, 0, ...] }, // 1=开, 0=关
            "pump_A2": { "status": [0, 1, 1, 1, ...] },
            "valve_V3": { "setting": [28.0, 28.0, 27.5, ...] }
          },
          "expected_cost": 1250.75,
          "expected_kpis": { "avg_pressure": 28.5 }
        }
        ```

### 设计理念

`Scheduling` 对象的核心是构建和求解一个复杂的“最优控制问题”。

1.  **声明式定义:** 用户通过 `control_variables`, `objective_function`, `constraints` 等属性，以一种声明式的方式来描述“要优化什么”、“目标是什么”以及“红线是什么”，而不需要关心底层的优化算法（如遗传算法、混合整数规划等）是如何实现的。

2.  **预测驱动:** 调度是面向未来的。它严重依赖于 `input_forecasts`。需水量预测的准确性直接决定了调度结果的质量。这种设计体现了“预测-优化”联动的思想。

3.  **模型驱动:** 调度依赖于 `target_simulation_model`。优化器在内部会成千上万次地调用这个水力模型，来评估不同控制组合的效果。模型的准确性是保证调度计划在现实世界中可行的基础。

`Scheduling` 对象是整个智慧水务系统从“感知-分析”到“决策”的关键一环。它将来自孪生、诊断、预测等模块的信息进行汇总，并最终产出可直接执行的、最优的控制策略，是实现系统运行降本增效的核心功能。
