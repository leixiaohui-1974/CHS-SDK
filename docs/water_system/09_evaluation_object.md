# 5. 评价 (Evaluation) - 对象文档

## 概述

`Evaluation` 对象是水系统性能评价模块的核心。与 `Diagnosis` 专注于发现“故障”和“异常”不同，`Evaluation` 的目标是从更宏观、更长期的角度，对水系统的运行效率、服务水平、能耗、水力稳定性等多个维度进行量化评估。它通常基于数字孪生的历史数据，生成周期性的评价报告。

## `Evaluation` 对象

### 属性

`Evaluation` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 评价任务的唯一标识符。
    *   **示例:** `"eval_monthly_energy_efficiency"`

*   **`name` (String):**
    *   **描述:** 评价任务的名称。
    *   **示例:** `"月度能效评价"`

*   **`target_twin` (DigitalTwin):**
    *   **描述:** 评价所基于的数字孪生对象。评价所需的历史数据均来源于此。

*   **`evaluation_period` (Object):**
    *   **描述:** 定义了评价的时间范围和周期。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "recurring", // recurring (周期性) 或 one_time (一次性)
          "cron_expression": "0 0 1 * *", // 每月1号的0点0分执行
          "data_window_days": 30 // 每次执行时，分析过去30天的数据
        }
        ```

*   **`key_performance_indicators` (Array<KPI>):**
    *   **描述:** 定义了需要计算的关键性能指标 (KPI)。这是评价内容的核心。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "id": "kpi_avg_pressure",
            "name": "平均节点压力",
            "description": "衡量供水服务压力水平的稳定性。",
            "calculation_method": {
              "type": "average",
              "source": "twin_history.node_states.*.pressure" // * 代表所有节点
            },
            "unit": "mH2O"
          },
          {
            "id": "kpi_unaccounted_water_rate",
            "name": "产销差率",
            "description": "评估管网的漏损水平。",
            "calculation_method": {
              "type": "expression",
              // (总进水量 - 总用户用水量) / 总进水量
              "expression": "(sum(twin_history.reservoir.*.outflow) - sum(twin_history.node.*.demand)) / sum(twin_history.reservoir.*.outflow)"
            },
            "unit": "%"
          },
          {
            "id": "kpi_pump_energy_consumption",
            "name": "吨水百米电耗",
            "description": "衡量水泵运行效率的核心指标。",
            "calculation_method": {
              "type": "custom_function",
              "function_name": "calculate_pump_whc"
            },
            "unit": "kWh/t·hm"
          }
        ]
        ```

*   **`status` (String):**
    *   **描述:** 评价服务的运行状态。可以是 `running`, `stopped`。

*   **`latest_report` (EvaluationReport):**
    *   **描述:** 一个只读属性，包含了最近一次生成的评价报告。
    *   **数据结构 (示例):**
        ```json
        {
          "report_id": "report_20230901",
          "evaluation_id": "eval_monthly_energy_efficiency",
          "start_time": "2023-08-01T00:00:00Z",
          "end_time": "2023-08-31T23:59:59Z",
          "generated_at": "2023-09-01T00:05:00Z",
          "kpi_results": [
            { "kpi_id": "kpi_avg_pressure", "value": 25.4, "trend": -0.02 }, // trend 表示与上个周期的变化
            { "kpi_id": "kpi_unaccounted_water_rate", "value": 15.2, "trend": 0.01 },
            { "kpi_id": "kpi_pump_energy_consumption", "value": 2.8, "trend": 0.05 }
          ],
          "summary": "本月能效略有下降，产销差率略有上升，需关注。"
        }
        ```

### 设计理念

`Evaluation` 对象的设计目标是实现“自动化、标准化的性能度量”。

1.  **数据驱动:** 评价完全基于 `target_twin` 中沉淀的、经过验证的历史数据，保证了评价结果的客观性和准确性。

2.  **KPI驱动:** `key_performance_indicators` 的设计是该对象的核心。它将复杂的评价逻辑分解为一系列独立的、可配置的KPI。每个KPI都明确定义了其计算方法（可以是简单的统计、复杂的表达式，甚至是自定义的算法函数），使得评价体系非常灵活且易于扩展。用户可以根据自己的管理需求，组合出不同的评价方案。

3.  **周期性与自动化:** 通过 `evaluation_period` 的定义，评价任务可以像一个定时任务一样，自动、周期性地执行，无需人工干预。这使得性能跟踪和管理从被动响应变为主动监控，能够持续地为管理者提供决策支持。

`Evaluation` 对象将原始的、海量的时序数据，提炼为有价值的、可指导行动的洞察，是连接数字孪生与业务管理的桥梁。
