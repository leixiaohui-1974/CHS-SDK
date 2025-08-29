# 2. 辨识 (Identification) - 数据模型

本篇文档详细描述了与“参数辨识”功能相关的核心数据模型。

## ER图 (实体关系图)

```
[identification_tasks] 1--* [identification_parameters]
[identification_tasks] 1--* [observation_data_points]
[identification_tasks] 1--1 [identification_results]
```

## 表结构定义 (SQL DDL)

### `identification_tasks`

存储辨识任务的基本信息和配置。

```sql
CREATE TABLE identification_tasks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    simulation_model_id VARCHAR(255) NOT NULL, -- 关联的基础仿真模型
    optimizer_options JSONB, -- e.g., {"algorithm": "genetic_algorithm", "population_size": 50}
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (simulation_model_id) REFERENCES simulations(id)
);
```

### `identification_parameters`

定义了在一个辨识任务中，具体要调整哪些参数。

```sql
CREATE TABLE identification_parameters (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    element_type VARCHAR(50) NOT NULL, -- e.g., 'pipe', 'node'
    element_id VARCHAR(255) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL, -- e.g., 'roughness', 'demand_multiplier'
    initial_guess NUMERIC,
    lower_bound NUMERIC,
    upper_bound NUMERIC,
    FOREIGN KEY (task_id) REFERENCES identification_tasks(id)
);
```

### `observation_data_points`

存储用于辨识的观测数据。对于大规模或高频率的观测，可考虑使用时序数据库。此处的模型适用于批处理辨识任务。

```sql
CREATE TABLE observation_data_points (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    element_type VARCHAR(50) NOT NULL, -- e.g., 'node', 'pipe'
    element_id VARCHAR(255) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL, -- e.g., 'pressure', 'flow'
    observed_value NUMERIC NOT NULL,
    FOREIGN KEY (task_id) REFERENCES identification_tasks(id)
);

-- 为了提高查询效率，建议在(task_id, observation_time)上创建索引
CREATE INDEX idx_obs_data_task_time ON observation_data_points (task_id, observation_time);
```

### `identification_results`

存储辨识任务完成后的结果。

```sql
CREATE TABLE identification_results (
    task_id VARCHAR(255) PRIMARY KEY,
    status VARCHAR(50) NOT NULL, -- 'completed' or 'failed'
    completed_at TIMESTAMPTZ,
    final_objective_value NUMERIC, -- 最终的目标函数值，表示拟合优度
    identified_parameters JSONB, -- 存储最终辨识出的参数值, e.g., [{"element_id": "p1", "parameter_name": "roughness", "optimal_value": 125.8}]
    convergence_history JSONB, -- 存储收敛过程，可选
    FOREIGN KEY (task_id) REFERENCES identification_tasks(id)
);
```
