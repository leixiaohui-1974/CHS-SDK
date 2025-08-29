# 8. 测试 (Testing) - 数据模型

本篇文档详细描述了与“自动化测试”功能相关的核心数据模型。该模型用于定义测试套件、测试用例，并记录每次测试的执行结果。

## ER图 (实体关系图)

```
[test_suites] 1--* [test_cases]
[test_suites] 1--* [test_runs]
[test_runs] 1--* [test_case_results]
[test_cases] 1--* [test_case_results]
```

## 表结构定义 (SQL DDL)

### `test_suites`

存储测试套件的定义。

```sql
CREATE TABLE test_suites (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 测试运行的环境配置
    -- e.g., {"type": "staging", "endpoints": {"prediction_service": "..."}}
    execution_environment JSONB,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `test_cases`

存储组成测试套件的每个独立的测试用例。

```sql
CREATE TABLE test_cases (
    id VARCHAR(255) PRIMARY KEY,
    suite_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 测试用例的执行步骤和断言，使用JSONB存储
    -- e.g., {"steps": [...], "assertions": [...]}
    definition JSONB NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (suite_id) REFERENCES test_suites(id)
);
```

### `test_runs`

记录测试套件的每一次执行。

```sql
CREATE TABLE test_runs (
    id BIGSERIAL PRIMARY KEY,
    suite_id VARCHAR(255) NOT NULL,

    triggered_at TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER,

    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'running', 'error'

    -- 本次运行的概要信息
    -- e.g., {"total": 10, "passed": 9, "failed": 1}
    summary JSONB,

    -- 触发者信息 (e.g., 'CI/CD pipeline', 'user:jules')
    triggered_by VARCHAR(255),

    FOREIGN KEY (suite_id) REFERENCES test_suites(id)
);
```

### `test_case_results`

存储在一次测试运行中，每个测试用例的具体结果。

```sql
CREATE TABLE test_case_results (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL,
    case_id VARCHAR(255) NOT NULL,

    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'skipped'
    duration_ms INTEGER,

    -- 如果测试失败，存储失败原因和相关日志
    failure_reason TEXT,
    logs JSONB,

    FOREIGN KEY (run_id) REFERENCES test_runs(id),
    FOREIGN KEY (case_id) REFERENCES test_cases(id),
    UNIQUE (run_id, case_id)
);
```

### 设计说明

*   **定义与执行分离**: `test_suites` 和 `test_cases` 表负责存储测试的“定义”，而 `test_runs` 和 `test_case_results` 负责存储测试的“执行历史”。这种分离使得测试用例的维护和版本控制变得清晰，同时可以完整地追溯每一次运行的结果。
*   **结构化结果**: 将 `summary` 和 `logs` 存储为 `JSONB` 格式，可以在关系型数据库中方便地存储结构化的测试产出，便于后续的查询和分析，例如，可以查询“所有失败日志中包含特定错误信息的测试用例”。
