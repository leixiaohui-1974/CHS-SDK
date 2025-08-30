# 7. 调度 (Scheduling) - 数据模型

本篇文档详细描述了与“优化调度”功能相关的核心数据模型。该模型主要用于存储调度任务的配置，以及每次优化运行后生成的控制计划。

## ER图 (实体关系图)

```
[scheduling_tasks] 1--* [control_schedules]
```

## 表结构定义 (SQL DDL)

### `scheduling_tasks`

存储优化调度任务的配置信息。

```sql
CREATE TABLE scheduling_tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_simulation_model_id VARCHAR(255) NOT NULL,

    -- 可被控制的设备列表
    control_variables JSONB NOT NULL,
    -- e.g., [{"element_type": "pump", "element_id": "pump_A1", "control_type": "status"}]

    -- 优化的目标函数
    objective_function JSONB NOT NULL,
    -- e.g., {"type": "minimize_cost", "cost_components": ["energy_cost", "maintenance_cost"]}

    -- 必须满足的约束条件
    constraints JSONB NOT NULL,
    -- e.g., [{"type": "node_pressure", "node_id": "n_critical", "min_pressure": 22.0}]

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_simulation_model_id) REFERENCES simulations(id)
);
```

### `control_schedules`

存储优化调度任务的执行结果，即具体的控制计划。

```sql
CREATE TABLE control_schedules (
    id VARCHAR(255) PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,

    generated_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed_no_solution'

    -- 该计划所基于的输入预测ID
    based_on_prediction_run_id VARCHAR(255),

    -- 计划覆盖的时间范围
    schedule_start_time TIMESTAMPTZ NOT NULL,
    schedule_end_time TIMESTAMPTZ NOT NULL,

    -- 详细的控制计划，使用JSONB存储
    -- 结构: {"pump_station_1": {"flow_rate": [...]}, "g1": {"opening_height": [...]}, "hydro1": {"turbine_flow": [...]}}
    control_plan JSONB,

    -- 预期的成本和KPI
    expected_cost NUMERIC,
    expected_kpis JSONB,

    FOREIGN KEY (task_id) REFERENCES scheduling_tasks(id),
    FOREIGN KEY (based_on_prediction_run_id) REFERENCES prediction_runs(id)
);

-- 为了快速查找某个任务的历史调度计划，创建索引
CREATE INDEX idx_schedules_task_id ON control_schedules (task_id);
```

### 设计说明

*   **JSONB的广泛使用**: 在 `scheduling_tasks` 表中，`control_variables`, `objective_function`, 和 `constraints` 都是半结构化的复杂数据。使用 `JSONB` 类型可以非常方便地存储这些灵活的配置，而无需创建大量关联表，大大简化了模型。
*   **结果的完整性**: `control_schedules` 表不仅存储了最终的 `control_plan`，还记录了它是基于哪个预测 (`based_on_prediction_run_id`) 生成的，以及预期的成本和KPI。这为后续的“计划-实际”对比分析提供了完整的数据链条。
*   **关系型模型的适用性**: 与时序数据不同，调度计划是离散的、结构化的，其生成频率不高（例如，每小时或每天一次）。因此，使用传统的关系型数据库来存储是完全合适的，并且便于进行复杂的查询和关联。
