# 3. 孪生 (Twinning) - 数据模型

本篇文档详细描述了与“数字孪生”功能相关的核心数据模型。数字孪生的数据模型是整个系统的核心，它分为两部分：
1.  **配置数据**: 存储孪生本身的定义和策略，适合用关系型数据库。
2.  **状态数据**: 存储孪生在每个时间点的状态快照，数据量巨大，是典型的时序数据，适合用时序数据库。

---

## 第一部分: 配置数据 (关系型模型)

### `digital_twins`

存储数字孪生服务实例的元数据和配置。

```sql
CREATE TABLE digital_twins (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    base_simulation_model_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'stopped', -- 'running', 'stopped', 'degraded'
    synchronization_policy JSONB, -- 存储同步策略, e.g., {"sync_interval_seconds": 60, ...}
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_simulation_model_id) REFERENCES simulations(id)
);
```

### `data_source_connections`

存储孪生体与外部数据源（如SCADA）的连接信息。

```sql
CREATE TABLE data_source_connections (
    id VARCHAR(255) PRIMARY KEY,
    twin_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL, -- 'opc_ua', 'modbus_tcp', 'mqtt'
    endpoint_url VARCHAR(1024) NOT NULL,
    credentials JSONB, -- 存储认证信息
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (twin_id) REFERENCES digital_twins(id)
);
```

### `data_point_mappings`

定义了外部数据源中的具体测点如何映射到管网模型中的元素和属性。

```sql
CREATE TABLE data_point_mappings (
    id SERIAL PRIMARY KEY,
    connection_id VARCHAR(255) NOT NULL,
    source_tag VARCHAR(255) NOT NULL, -- SCADA中的点位名, e.g., "SCADA.Node.Pressure.N5"
    element_type VARCHAR(50) NOT NULL, -- 'node', 'pipe', etc.
    element_id VARCHAR(255) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL, -- 'pressure', 'flow', etc.
    UNIQUE (connection_id, source_tag),
    FOREIGN KEY (connection_id) REFERENCES data_source_connections(id)
);
```

---

## 第二部分: 状态数据 (时序模型)

这部分数据强烈建议使用专门的时序数据库（Time-Series Database, TSDB）如 InfluxDB, TimescaleDB, 或 Prometheus 进行存储。下面以 **InfluxDB** 的数据模型为例。

在InfluxDB中，我们会为每一种类型的测量值创建一个`measurement`。

### `state_pressure` (节点压力)

*   **Measurement:** `state_pressure`
*   **Tags:**
    *   `twin_id`: 孪生实例的ID。
    *   `node_id`: 节点的ID。
*   **Fields:**
    *   `value`: 压力值 (Float)。
    *   `quality_score`: 数据质量评分 (Float, 0-1)。
*   **示例 (Line Protocol):**
    ```
    state_pressure,twin_id=twin_main,node_id=n5 value=25.3,quality_score=0.98 1678886400000000000
    ```

### `state_flow` (管道流量)

*   **Measurement:** `state_flow`
*   **Tags:**
    *   `twin_id`: 孪生实例的ID。
    *   `pipe_id`: 管道的ID。
*   **Fields:**
    *   `value`: 流量值 (Float)。
    *   `quality_score`: 数据质量评分 (Float, 0-1)。
*   **示例 (Line Protocol):**
    ```
    state_flow,twin_id=twin_main,pipe_id=p3 value=0.45,quality_score=0.95 1678886400000000000
    ```

### `state_quality` (水质)

*   **Measurement:** `state_quality`
*   **Tags:**
    *   `twin_id`: 孪生实例的ID。
    *   `node_id`: 节点的ID。
    *   `pollutant`: 污染物名称 (e.g., "chlorine", "turbidity")。
*   **Fields:**
    *   `value`: 浓度或值 (Float)。
    *   `quality_score`: 数据质量评分 (Float, 0-1)。
*   **示例 (Line Protocol):**
    ```
    state_quality,twin_id=twin_main,node_id=n10,pollutant=chlorine value=0.85,quality_score=0.99 1678886400000000000
    ```
