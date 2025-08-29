# 4. 诊断 (Diagnosis) - 对象文档

## 概述

`Diagnosis` 对象是水系统故障诊断与健康状态监测模块的核心。它的主要职责是持续分析来自数字孪生或实时传感器的数据，依据预设的诊断规则，识别系统中可能发生的异常事件，如管道泄漏、水泵故障、水质污染等，并生成诊断报告或告警。

## `Diagnosis` 对象

### 属性

`Diagnosis` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 诊断任务的唯一标识符。
    *   **示例:** `"diag_leakage_detection_main_zone"`

*   **`name` (String):**
    *   **描述:** 诊断任务的名称。
    *   **示例:** `"主供水分区泄漏诊断"`

*   **`target_twin` (DigitalTwin):**
    *   **描述:** 诊断任务所监控的数字孪生对象。诊断分析所需的数据主要来源于此数字孪生的实时状态和历史状态。
    *   **关联:** `Diagnosis` 对象会作为 `target_twin` 的一个监听者，实时获取状态更新。

*   **`diagnosis_rules` (Array<DiagnosisRule>):**
    *   **描述:** 一组用于定义异常或故障模式的规则。这是诊断逻辑的核心。每条规则定义了触发条件、严重等级、诊断结论等。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "id": "rule_pipe_burst",
            "name": "管道爆裂检测",
            "description": "通过检测节点压力突然下降和相邻流量剧增来判断是否发生爆管。",
            "trigger_condition": {
              "type": "expression",
              // 表达式语言，可以引用孪生状态
              "expression": "delta(node.n5.pressure, 5min) < -10 && delta(pipe.p3.flow, 5min) > 0.5"
            },
            "severity": "critical", // 严重等级: critical, warning, info
            "diagnosis_conclusion": "节点n5附近可能发生管道爆裂！",
            "suggested_actions": ["立即关闭相关阀门", "派遣巡检人员"]
          },
          {
            "id": "rule_water_quality_anomaly",
            "name": "水质异常检测",
            "trigger_condition": {
              "type": "ml_model", // 也可以基于机器学习模型
              "model_id": "chlorine_anomaly_detector_v1",
              "input_features": ["node.n10.chlorine_residual", "node.n10.turbidity"]
            },
            "severity": "warning",
            "diagnosis_conclusion": "节点n10监测到余氯或浊度异常。",
            "suggested_actions": ["增加水质采样频率", "检查上游加氯站"]
          }
        ]
        ```

*   **`status` (String):**
    *   **描述:** 诊断服务的运行状态。可以是 `running`, `stopped`。
    *   **默认值:** `stopped`

*   **`active_diagnoses` (Array<DiagnosisResult>):**
    *   **描述:** 一个只读属性，包含了当前所有处于“活动”状态的诊断结果（即已触发且未解决的异常事件）。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "id": "diag_res_1678886400",
            "rule_id": "rule_pipe_burst",
            "timestamp": "2023-09-01T12:00:00Z",
            "severity": "critical",
            "conclusion": "节点n5附近可能发生管道爆裂！",
            "status": "unacknowledged", // unacknowledged, acknowledged, resolved
            "details": {
              "triggering_values": {
                "node.n5.pressure_delta": -12.5,
                "pipe.p3.flow_delta": 0.6
              }
            }
          }
        ]
        ```

### 设计理念

`Diagnosis` 对象的设计基于“规则驱动的事件处理”模式。

1.  **数据源:** 它不直接与物理设备交互，而是以高层次的 `DigitalTwin` 对象作为其输入。这使得诊断逻辑可以利用到经过孪生系统融合、校正和补全的高质量数据，而不仅仅是原始、可能有噪声的传感器数据。

2.  **规则引擎:** `diagnosis_rules` 是一个灵活的规则引擎。它将诊断的业务逻辑（什么情况算作异常）与系统的其他部分解耦。这意味着领域专家（如水务工程师）可以方便地通过修改JSON配置来添加或更新诊断规则，而无需改动核心代码。规则可以基于简单的阈值表达式，也可以集成复杂的机器学习模型，具有很好的可扩展性。

3.  **状态管理:** `active_diagnoses` 属性提供了对当前系统健康状况的即时快照。通过管理诊断结果的状态（`unacknowledged`, `acknowledged`, `resolved`），它可以支持一个完整的故障处理工作流（发现问题 -> 响应问题 -> 解决问题）。

`Diagnosis` 对象充当了数字孪生的“大脑”或“免疫系统”，它赋予了孪生系统理解自身状态并对异常做出反应的能力。
