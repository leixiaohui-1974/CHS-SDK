# 5. 评价 (Evaluation) - 数据模型

本篇文档详细描述了与“性能评价”功能相关的核心数据模型。该模型的核心是围绕可复用的“KPI定义”和周期性生成的“评价报告”。

## ER图 (实体关系图)

```
[evaluation_tasks] 1--* [evaluation_reports]
[evaluation_reports] 1--* [evaluation_report_kpis]
[kpi_definitions] 1--* [evaluation_report_kpis]
```

## 表结构定义 (SQL DDL)

### `evaluation_tasks`

存储周期性评价任务的配置信息。

```sql
CREATE TABLE evaluation_tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_twin_id VARCHAR(255) NOT NULL,

    -- e.g., {"type": "recurring", "cron_expression": "0 0 1 * *"}
    evaluation_period JSONB NOT NULL,

    -- 该评价任务包含的KPI列表
    kpi_ids VARCHAR(255)[], -- Array of kpi_definition IDs

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_twin_id) REFERENCES digital_twins(id)
);
```

### `kpi_definitions`

定义了系统中的关键性能指标 (KPI)。这使得KPI的定义标准化、可复用。

```sql
CREATE TABLE kpi_definitions (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit VARCHAR(50), -- e.g., '%', 'mH2O', 'kWh/t·hm'

    -- KPI的计算方法，使用JSONB可以非常灵活
    -- e.g., {"type": "average", "source": "twin_history.node_states.*.pressure"}
    -- e.g., {"type": "expression", "expression": "(sum(inflow) - sum(outflow))/sum(inflow)"}
    -- e.g., {"type": "custom_function", "function_name": "calculate_pump_whc"}
    calculation_method JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `evaluation_reports`

存储每一次评价任务执行后生成的报告。

```sql
CREATE TABLE evaluation_reports (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,

    -- 本次报告所评估的数据时间范围
    data_start_time TIMESTAMPTZ NOT NULL,
    data_end_time TIMESTAMPTZ NOT NULL,

    -- 报告生成信息
    generated_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed'
    summary TEXT, -- 报告的文字总结

    FOREIGN KEY (task_id) REFERENCES evaluation_tasks(id)
);
```

### `evaluation_report_kpis`

存储在每份报告中，每个KPI的具体计算结果。

```sql
CREATE TABLE evaluation_report_kpis (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL,
    kpi_id VARCHAR(255) NOT NULL,

    calculated_value NUMERIC,

    -- 与上一个周期的对比值，可以是差值或百分比
    trend_from_previous NUMERIC,

    -- 其他相关的元数据
    metadata JSONB,

    FOREIGN KEY (report_id) REFERENCES evaluation_reports(id),
    FOREIGN KEY (kpi_id) REFERENCES kpi_definitions(id),
    UNIQUE (report_id, kpi_id)
);
```
