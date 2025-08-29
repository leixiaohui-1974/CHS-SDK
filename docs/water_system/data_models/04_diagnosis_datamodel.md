# 4. 诊断 (Diagnosis) - 数据模型

本篇文档详细描述了与“故障诊断”功能相关的核心数据模型。该模型主要围绕“诊断规则”的定义和“告警事件”的记录与管理。

## ER图 (实体关系图)

```
[diagnosis_services] 1--* [diagnosis_rules]
[diagnosis_rules] 1--* [diagnosis_alarms]
```
*(注: `diagnosis_services` 表用于管理不同的诊断任务，为简化起见，我们在此关注规则和告警本身)。*

## 表结构定义 (SQL DDL)

### `diagnosis_rules`

存储用于定义异常或故障模式的规则。

```sql
CREATE TABLE diagnosis_rules (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    severity VARCHAR(50) NOT NULL, -- 'critical', 'warning', 'info'

    -- 规则的触发条件可以有多种形式，使用JSONB可以灵活存储
    -- 示例1: 表达式类型
    -- {"type": "expression", "expression": "delta(node.n5.pressure, 5min) < -10"}
    -- 示例2: 机器学习模型类型
    -- {"type": "ml_model", "model_id": "chlorine_anomaly_detector_v1"}
    trigger_condition JSONB NOT NULL,

    -- 建议的应对措施
    suggested_actions TEXT[],

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `diagnosis_alarms`

记录所有由诊断规则触发的告警事件。这张表同时包含了活动告警和历史告警。

```sql
CREATE TABLE diagnosis_alarms (
    id BIGSERIAL PRIMARY KEY,
    rule_id VARCHAR(255) NOT NULL,

    -- 告警状态 (Lifecycle of an alarm)
    -- unacknowledged -> acknowledged -> resolved
    status VARCHAR(50) NOT NULL DEFAULT 'unacknowledged',

    -- 触发信息
    triggered_at TIMESTAMPTZ NOT NULL,
    severity_at_trigger VARCHAR(50) NOT NULL,
    conclusion_at_trigger TEXT NOT NULL,
    triggering_details JSONB, -- 存储触发时相关的具体数值

    -- 确认信息 (Acknowledgement)
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(255), -- User ID or name
    acknowledgement_comments TEXT,

    -- 解决信息 (Resolution)
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(255), -- User ID or name
    resolution_notes TEXT,

    FOREIGN KEY (rule_id) REFERENCES diagnosis_rules(id)
);

-- 为了高效查询活动告警和历史告警，创建索引
CREATE INDEX idx_alarms_status ON diagnosis_alarms (status);
CREATE INDEX idx_alarms_triggered_at ON diagnosis_alarms (triggered_at);
```

### 设计说明

*   **规则的灵活性**: 在 `diagnosis_rules` 表中，`trigger_condition` 字段使用 `JSONB` 类型，这提供了极大的灵活性。无论是简单的阈值规则、复杂的布尔逻辑表达式，还是调用外部机器学习模型的指令，都可以被结构化地存储。
*   **告警生命周期**: `diagnosis_alarms` 表通过 `status` 字段清晰地管理了每个告警从发生 (`unacknowledged`)、被响应 (`acknowledged`) 到被关闭 (`resolved`) 的完整生命周期。所有的时间戳和用户信息都被记录下来，便于审计和责任追溯。
*   **性能**: 对 `status` 和 `triggered_at` 字段建立索引，可以极大地提高查询效率。例如，查询“所有活动的严重告警”或“上周发生的所有告警”等常见操作，都会因此受益。
