# 6. 预测 (Prediction) - 对象文档

## 概述

`Prediction` 对象是水系统预测模块的核心。它的主要任务是利用历史数据和外部信息（如天气预报），对未来的关键变量进行预测。最常见的预测任务是需水量预测，它是后续进行优化调度和控制的基础。除了需水量，也可以预测未来的原水水质、电价等。

## `Prediction` 对象

### 属性

`Prediction` 对象包含以下主要属性：

*   **`id` (String):**
    *   **描述:** 预测任务的唯一标识符。
    *   **示例:** `"pred_zonal_demand_24h"`

*   **`name` (String):**
    *   **描述:** 预测任务的名称。
    *   **示例:** `"分区未来24小时需水量预测"`

*   **`target_variable` (Object):**
    *   **描述:** 定义了需要预测的目标变量。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "demand", // 预测类型: demand, quality, price, etc.
          "scope": "zonal", // 预测范围: nodal (节点), zonal (分区), system (全系统)
          "zone_id": "zone_A" // 如果是分区预测，需要指定分区ID
        }
        ```

*   **`prediction_model` (Object):**
    *   **描述:** 定义了用于预测的机器学习或统计模型。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "ml_model", // model_type: ml_model, statistical (e.g. ARIMA), hybrid
          "model_id": "demand_lstm_model_v2", // 预先训练好的模型的ID
          "input_features": [ // 模型需要的输入特征
            "historical_demand",
            "day_of_week",
            "hour_of_day",
            "is_holiday",
            "weather_forecast.temperature",
            "weather_forecast.precipitation"
          ]
        }
        ```

*   **`data_sources` (Object):**
    *   **描述:** 定义了获取模型输入特征所需的数据源。
    *   **数据结构 (示例):**
        ```json
        {
          "historical_demand": { "source": "twin_history", "variable": "demand", "zone_id": "zone_A" },
          "weather_forecast": { "source": "external_api", "api_endpoint": "https://api.weather.com/v1/forecast" }
        }
        ```

*   **`prediction_schedule` (Object):**
    *   **描述:** 定义了预测任务的执行计划。
    *   **数据结构 (示例):**
        ```json
        {
          "type": "recurring",
          "cron_expression": "0 * * * *", // 每小时的0分执行一次
          "prediction_horizon_hours": 24, // 每次预测未来24小时
          "prediction_interval_minutes": 60 // 预测结果的时间粒度为60分钟
        }
        ```

*   **`status` (String):**
    *   **描述:** 预测服务的运行状态。可以是 `running`, `stopped`。

*   **`latest_prediction` (PredictionResult):**
    *   **描述:** 一个只读属性，包含了最近一次生成的预测结果。
    *   **数据结构 (示例):**
        ```json
        {
          "prediction_id": "pred_res_202309011400",
          "generated_at": "2023-09-01T14:00:05Z",
          "prediction_start_time": "2023-09-01T15:00:00Z",
          "time_series": {
            "timestamps": ["2023-09-01T15:00:00Z", "2023-09-01T16:00:00Z", ...],
            "predicted_values": [120.5, 125.8, ...],
            "confidence_upper_bound": [128.0, 133.2, ...], // 可选的置信区间
            "confidence_lower_bound": [113.0, 118.4, ...]
          }
        }
        ```

### 设计理念

`Prediction` 对象的设计体现了现代时间序列预测应用的典型架构。

1.  **特征工程与数据源分离:** `prediction_model` 中明确定义了模型所需的 `input_features`，而 `data_sources` 则负责说明如何获取这些特征。这种解耦使得我们可以方便地为同一个模型更换不同的数据源（例如，从一个天气API切换到另一个），或者为同一个数据源尝试不同的预测模型。

2.  **模型即服务 (Model as a Service):** `prediction_model` 的定义中只包含了模型的ID和元数据，而不是模型本身。这假设存在一个独立的模型仓库或服务，负责管理和提供预先训练好的模型。这种设计使得模型的更新、版本控制和部署可以独立于预测应用本身，更加灵活和可维护。

3.  **调度与执行分离:** `prediction_schedule` 定义了“何时”以及“预测多远”的业务逻辑，而具体的预测计算则由底层的模型服务来完成。这使得预测任务的调度和管理变得非常清晰。

`Prediction` 对象是连接历史与未来的桥梁。它将数字孪生中积累的历史数据转化为对未来的洞察，为前瞻性的决策（如优化调度）提供了最关键的输入。
