# 9. 测试 (Testing) - 对象文档

## 概述

`Testing` 对象是为整个智慧水务系统提供自动化测试能力的框架。在一个复杂的、由多个模块（仿真、预测、调度、控制等）组成的系统中，确保每个模块的正确性以及它们之间交互的可靠性至关重要。`Testing` 对象不是用于测试水务硬件，而是用于测试软件系统本身。它允许开发和运维人员定义和执行一系列测试用例，以验证系统在各种场景下的行为是否符合预期。

## `Testing` 对象

### 属性

`Testing` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 测试套件的唯一标识符。
    *   **示例:** `"test_suite_full_system_v1"`

*   **`name` (String):**
    *   **描述:** 测试套件的名称。
    *   **示例:** `"全系统冒烟测试套件"`

*   **`test_cases` (Array<TestCase>):**
    *   **描述:** 组成测试套件的一系列测试用例。每个测试用例定义了一个具体的测试场景、执行步骤和期望结果。
    *   **数据结构 (示例):**
        ```json
        [
          {
            "id": "tc_001_prediction_accuracy",
            "name": "测试需水量预测精度",
            "description": "使用历史数据回测预测模型，验证其MAPE是否在可接受范围内。",
            "steps": [
              {
                "service": "Prediction",
                "method": "run_backtest",
                "params": { "model_id": "demand_lstm_model_v2", "test_data_range": ["2023-07-01", "2023-07-31"] }
              }
            ],
            "assertions": [
              {
                "source": "step[0].result.mean_absolute_percentage_error",
                "operator": "less_than",
                "expected_value": 0.10 // MAPE应小于10%
              }
            ]
          },
          {
            "id": "tc_002_scheduler_leak_response",
            "name": "测试调度系统在爆管场景下的响应",
            "description": "模拟一个突发爆管事件，验证调度系统是否能生成合理的应急调度计划。",
            "steps": [
              { "service": "DigitalTwin", "method": "inject_mock_data", "params": { ... } }, // 模拟爆管数据
              { "service": "Diagnosis", "method": "run_once", "params": {} },
              { "service": "Scheduling", "method": "run_emergency_optimization", "params": { "trigger_event": "step[1].result" } }
            ],
            "assertions": [
              {
                "source": "step[1].result.conclusion", // 验证诊断模块是否正确识别爆管
                "operator": "contains",
                "expected_value": "爆裂"
              },
              {
                "source": "step[2].result.control_plan.valve_V5.status[0]", // 验证调度是否关闭了爆管点附近阀门
                "operator": "equals",
                "expected_value": 0
              }
            ]
          }
        ]
        ```

*   **`execution_environment` (Object):**
    *   **描述:** 定义测试运行的环境。例如，是指向生产环境、预发环境，还是一个完全隔离的、使用模拟数据的测试环境。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "staging", // production, staging, mock
          "endpoints": {
            "prediction_service": "https://staging.api.water.com/prediction",
            "scheduling_service": "https://staging.api.water.com/scheduling"
          }
        }
        ```

*   **`last_run_result` (TestRunResult):**
    *   **描述:** 一个只读属性，包含了最近一次运行整个测试套件的结果。
    *   **数据结构 (示例):**
        ```json
        {
          "run_id": "run_12345",
          "timestamp": "2023-09-02T10:00:00Z",
          "status": "failed", // passed, failed
          "summary": { "total": 2, "passed": 1, "failed": 1 },
          "case_results": [
            { "case_id": "tc_001_prediction_accuracy", "status": "passed", "duration_ms": 12000 },
            { "case_id": "tc_002_scheduler_leak_response", "status": "failed", "duration_ms": 5000, "failure_reason": "Assertion failed: step[2].result.control_plan.valve_V5.status[0] expected 0 but got 1." }
          ]
        }
        ```

### 设计理念

`Testing` 对象的设计借鉴了现代软件测试框架（如 Jest, Pytest）的思想，并将其应用于整个智慧水务业务系统。

1.  **声明式测试用例:** `test_cases` 的定义是声明式的。用户通过描述 `steps`（做什么）和 `assertions`（期望得到什么）来定义一个测试，而无需编写复杂的脚本代码。这种方式降低了编写和维护测试用例的门槛。

2.  **端到端测试能力:** `Testing` 框架不仅仅是单元测试。如 `tc_002_scheduler_leak_response` 所示，它可以定义一个跨越多个服务（孪生、诊断、调度）的端到端（E2E）测试场景。这对于验证复杂业务流程的正确性至关重要。

3.  **环境隔离:** `execution_environment` 的设计使得同一套测试用例可以在不同的环境中运行。这对于持续集成/持续部署（CI/CD）流程至关重要。例如，每次代码提交后，可以在 `mock` 环境中快速运行一遍核心测试；每天晚上，在 `staging` 环境中运行完整的回归测试。

4.  **结果导向:** `TestRunResult` 提供了清晰、结构化的测试结果，可以方便地集成到仪表盘或告警系统中，使得团队能够快速了解系统的健康状况。

`Testing` 对象是保障整个系统质量和稳定性的基石。在一个持续迭代和演进的复杂系统中，一个强大的自动化测试框架是不可或缺的。
