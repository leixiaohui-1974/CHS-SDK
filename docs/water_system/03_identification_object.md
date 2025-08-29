# 2. 辨识 (Identification) - 对象文档

## 概述

`Identification` 对象是水系统模型参数辨识模块的核心。在水务系统中，许多模型的参数（如管道的粗糙系数、需水模式的系数等）是未知或不确定的。参数辨识的目的就是利用实际的观测数据（如传感器测量的压力、流量），来反向推断和校准这些模型参数，使模型的输出尽可能地接近真实世界的观测值。

## `Identification` 对象

### 属性

`Identification` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 参数辨识任务的唯一标识符。
    *   **示例:** `"ident_pipe_roughness_20230829"`

*   **`name` (String):**
    *   **描述:** 辨识任务的名称。
    *   **示例:** `"主干管网管道粗糙度辨识"`

*   **`simulation_model` (Simulation):**
    *   **描述:** 关联的仿真模型。参数辨识需要在该模型的基础上进行。辨识的目标就是调整此模型中的某些参数。
    *   **重要:** 该 `Simulation` 对象应包含一个已定义的 `network`。

*   **`parameters_to_identify` (Array<ParameterSpec>):**
    *   **描述:** 一个数组，定义了需要辨识哪些参数。每个元素都是一个 `ParameterSpec` 对象，指明了参数的位置、类型、初始猜测值以及取值范围。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "element_type": "pipe",
            "element_id": "p1",
            "parameter_name": "roughness",
            "initial_guess": 130,
            "lower_bound": 100,
            "upper_bound": 150
          },
          {
            "element_type": "node",
            "element_id": "n2",
            "parameter_name": "demand_multiplier",
            "initial_guess": 1.0,
            "lower_bound": 0.5,
            "upper_bound": 1.5
          }
        ]
        ```

*   **`observation_data` (ObservationData):**
    *   **描述:** 用于参数辨识的实际观测数据。这些数据是连接模型与现实的桥梁。
    *   **数据结构 (示例):**
        ```json
        {
          "time_series": {
            "node_pressures": {
              "n2": {
                "timestamps": ["2023-09-01T08:00:00Z", "2023-09-01T09:00:00Z"],
                "values": [14.5, 14.2]
              }
            },
            "pipe_flows": {
              "p1": {
                "timestamps": ["2023-09-01T08:00:00Z", "2023-09-01T09:00:00Z"],
                "values": [0.55, 0.58]
              }
            }
          }
        }
        ```

*   **`optimizer_options` (OptimizerOptions):**
    *   **描述:** 优化算法的配置选项，例如选择哪种优化算法（如遗传算法、粒子群算法）、最大迭代次数、收敛判据等。
    *   **数据结构 (示例):**
        ```json
        {
          "algorithm": "genetic_algorithm",
          "population_size": 50,
          "max_generations": 100,
          "convergence_tolerance": 1e-4
        }
        ```

*   **`status` (String):**
    *   **描述:** 辨识任务的当前状态。可以是 `created`, `running`, `completed`, `failed`。
    *   **默认值:** `created`

*   **`results` (IdentificationResults):**
    *   **描述:** 辨识任务完成后的结果。在任务完成前为 `null`。
    *   **数据结构 (示例):**
        ```json
        {
          "identified_parameters": [
            {
              "element_type": "pipe",
              "element_id": "p1",
              "parameter_name": "roughness",
              "optimal_value": 125.8
            },
            {
              "element_type": "node",
              "element_id": "n2",
              "parameter_name": "demand_multiplier",
              "optimal_value": 1.12
            }
          ],
          "final_objective_value": 0.05, // 目标函数最终值，表示模型输出与观测数据的拟合优度
          "convergence_history": [0.8, 0.5, 0.2, ...] // 目标函数值的收敛过程
        }
        ```

### 设计理念

`Identification` 对象的核心思想是定义一个优化问题。其目标函数是“仿真模型的输出”与“实际观测数据”之间的差异（或误差）。优化的变量是 `parameters_to_identify` 中指定的模型参数。通过调用 `run()` 方法，底层的优化器会不断地调整这些参数，并反复运行仿真，直到找到一组能使目标函数最小化的参数值。

这种设计将问题定义（需要辨识什么、依据什么数据）与求解过程（如何辨识）清晰地分离开来，具有很好的灵活性和可扩展性。
