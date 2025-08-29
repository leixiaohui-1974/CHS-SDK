# 1. 仿真 (Simulation) - 数据模型

本篇文档详细描述了与“仿真”功能相关的核心数据模型。我们采用关系型数据库模型来存储仿真的配置和管网拓扑结构。

## ER图 (实体关系图)

```
[simulations] 1--1 [networks]
[networks] 1--* [nodes]
[networks] 1--* [pipes]
[networks] 1--* [pumps]
[networks] 1--* [valves]
[networks] 1--* [reservoirs]
```

## 表结构定义 (SQL DDL)

### `simulations`

存储仿真任务的基本信息和配置。

```sql
CREATE TABLE simulations (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    network_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    time_step_seconds INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'created',
    solver_options JSONB, -- 存储求解器配置, e.g., {"tolerance": 1e-6}
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (network_id) REFERENCES networks(id)
);
```

### `networks`

存储管网的元数据。

```sql
CREATE TABLE networks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_file_path VARCHAR(1024), -- 可选，如果从INP等文件导入
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `nodes` (节点)

存储管网中的节点信息，如接点、需用水户。

```sql
CREATE TABLE nodes (
    id VARCHAR(255) PRIMARY KEY,
    network_id VARCHAR(255) NOT NULL,
    base_demand_m3_per_sec NUMERIC,
    elevation_m NUMERIC,
    initial_quality NUMERIC,
    demand_pattern_id VARCHAR(255), -- 关联到需用水量模式
    coordinates JSONB, -- e.g., {"x": 123.45, "y": 678.90}
    FOREIGN KEY (network_id) REFERENCES networks(id)
);
```

### `pipes` (管道)

```sql
CREATE TABLE pipes (
    id VARCHAR(255) PRIMARY KEY,
    network_id VARCHAR(255) NOT NULL,
    from_node_id VARCHAR(255) NOT NULL,
    to_node_id VARCHAR(255) NOT NULL,
    length_m NUMERIC NOT NULL,
    diameter_m NUMERIC NOT NULL,
    roughness NUMERIC NOT NULL, -- e.g., Hazen-Williams C-factor
    status VARCHAR(50) DEFAULT 'Open', -- Open, Closed, CV
    FOREIGN KEY (network_id) REFERENCES networks(id),
    FOREIGN KEY (from_node_id) REFERENCES nodes(id),
    FOREIGN KEY (to_node_id) REFERENCES nodes(id)
);
```

### `pumps` (水泵)

```sql
CREATE TABLE pumps (
    id VARCHAR(255) PRIMARY KEY, -- 注意: 水泵也是一个管段，其ID应与pipes表中的ID对应
    network_id VARCHAR(255) NOT NULL,
    pump_curve_id VARCHAR(255), -- 关联到水泵特性曲线
    initial_status VARCHAR(50) DEFAULT 'Open',
    initial_speed NUMERIC DEFAULT 1.0,
    power_kw NUMERIC,
    FOREIGN KEY (id) REFERENCES pipes(id),
    FOREIGN KEY (network_id) REFERENCES networks(id)
);
```

### `valves` (阀门)

```sql
CREATE TABLE valves (
    id VARCHAR(255) PRIMARY KEY, -- 阀门也是一个管段
    network_id VARCHAR(255) NOT NULL,
    valve_type VARCHAR(50) NOT NULL, -- e.g., PRV, PSV, FCV
    diameter_m NUMERIC NOT NULL,
    initial_setting NUMERIC,
    initial_status VARCHAR(50) DEFAULT 'Open',
    FOREIGN KEY (id) REFERENCES pipes(id),
    FOREIGN KEY (network_id) REFERENCES networks(id)
);
```

### `reservoirs` (水库/水池)

```sql
CREATE TABLE reservoirs (
    id VARCHAR(255) PRIMARY KEY, -- 水库是一个特殊的节点
    network_id VARCHAR(255) NOT NULL,
    initial_level_m NUMERIC,
    min_level_m NUMERIC,
    max_level_m NUMERIC,
    diameter_m NUMERIC,
    FOREIGN KEY (id) REFERENCES nodes(id),
    FOREIGN KEY (network_id) REFERENCES networks(id)
);
```

### 仿真结果 (非关系型存储)

仿真结果是大量的时序数据，通常不适合存储在关系型数据库中。推荐使用 **时序数据库 (Time-Series Database)**，如 InfluxDB 或 TimescaleDB。

数据模型示例如下 (以InfluxDB Line Protocol为例):

```
# Measurement: pressure
# Tags: simulation_id, node_id
# Fields: value
pressure,simulation_id=sim_abc,node_id=n1 value=25.3 1678886400000000000
pressure,simulation_id=sim_abc,node_id=n2 value=24.9 1678886400000000000

# Measurement: flow
# Tags: simulation_id, pipe_id
# Fields: value
flow,simulation_id=sim_abc,pipe_id=p1 value=105.7 1678886400000000000
```
