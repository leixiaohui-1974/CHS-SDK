# 6. 预测 (Prediction) - 数据模型

本篇文档详细描述了与“预测”功能相关的核心数据模型。与数字孪生类似，预测功能的数据也分为两部分：
1.  **配置数据**: 存储预测任务的定义，适合用关系型数据库。
2.  **结果数据**: 存储预测生成的时序结果，适合用时序数据库。

---

## 第一部分: 配置数据 (关系型模型)

### `prediction_tasks`

存储预测任务的元数据和配置。

```sql
CREATE TABLE prediction_tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,

    -- 预测的目标变量, e.g., {"type": "demand", "scope": "zonal", "zone_id": "zone_A"}
    target_variable JSONB NOT NULL,

    -- 使用的预测模型信息, e.g., {"type": "ml_model", "model_id": "demand_lstm_model_v2"}
    prediction_model JSONB NOT NULL,

    -- 预测的执行计划, e.g., {"type": "recurring", "cron_expression": "0 * * * *"}
    prediction_schedule JSONB NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `prediction_runs`

记录每一次预测任务的执行。

```sql
CREATE TABLE prediction_runs (
    id VARCHAR(255) PRIMARY KEY, -- 预测结果的唯一ID
    task_id VARCHAR(255) NOT NULL,

    generated_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed'

    -- 预测覆盖的时间范围
    prediction_start_time TIMESTAMPTZ NOT NULL,
    prediction_end_time TIMESTAMPTZ NOT NULL,

    -- 相关的元数据，例如本次预测使用的模型版本、输入特征摘要等
    metadata JSONB,

    FOREIGN KEY (task_id) REFERENCES prediction_tasks(id)
);
```

---

## 第二部分: 结果数据 (时序模型)

预测结果本身是时序数据，强烈建议使用时序数据库（TSDB）存储。

### `prediction_values` (预测值)

*   **Measurement:** `prediction_values`
*   **Tags:**
    *   `run_id`: 预测执行的ID，关联到`prediction_runs`表。
    *   `task_id`: 预测任务的ID。
*   **Fields:**
    *   `value`: 预测值 (Float)。
    *   `upper_bound`: 置信区间的上界 (Float, 可选)。
    *   `lower_bound`: 置信区间的下界 (Float, 可选)。
*   **Timestamp:** 预测点对应的时间戳。
*   **示例 (Line Protocol):**
    ```
    # 第一行数据
    prediction_values,run_id=pred_res_1678886400,task_id=pred_zonal_demand_24h value=120.5,upper_bound=128.0,lower_bound=113.0 1678890000000000000
    # 第二行数据 (1小时后)
    prediction_values,run_id=pred_res_1678886400,task_id=pred_zonal_demand_24h value=125.8,upper_bound=133.2,lower_bound=118.4 1678893600000000000
    ```

### 设计说明

*   **配置与实例分离**: `prediction_tasks` 表定义了一个预测“应该如何”运行，而 `prediction_runs` 表记录了每一次实际的运行实例。这种设计清晰地分离了配置与历史记录。
*   **元数据与数据分离**: 关系型的 `prediction_runs` 表存储了每次预测的元数据（何时运行、是否成功、覆盖范围等），而海量的时序数据点则交由更适合的TSDB来存储。通过 `run_id` 可以将两者关联起来，实现高效的查询。例如，可以先在关系型数据库中查询“过去一周所有成功的预测运行”，获得它们的 `run_id` 列表，然后再到TSDB中查询这些 `run_id` 对应的具体时序数据。
