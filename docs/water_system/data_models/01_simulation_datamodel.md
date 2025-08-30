# 1. 仿真 (Simulation) - 通用数据模型

本篇文档详细描述了与“仿真”功能相关的、经过通用化设计的核心数据模型。该模型现在可以同时支持承压管网和开放式河道/渠系。

## ER图 (实体关系图)

```
[simulations] 1--1 [system_topologies]

[system_topologies] 1--* [nodes]
[system_topologies] 1--* [links]

-- links表是所有连接件的父表 --
[links] <|-- [pipes]
[links] <|-- [pumps]
[links] <|-- [valves]
[links] <|-- [reaches]
[links] <|-- [gates]
```

## 表结构定义 (SQL DDL)

### `simulations`

存储仿真任务的基本信息和配置。

```sql
CREATE TABLE simulations (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    topology_id VARCHAR(255) NOT NULL, -- 引用通用的拓扑结构
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    time_step_seconds INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'created',
    solver_options JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topology_id) REFERENCES system_topologies(id)
);
```

### `system_topologies`

存储水力系统拓扑的元数据，取代了原先的`networks`表。

```sql
CREATE TABLE system_topologies (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- 坐标系信息, e.g., 'EPSG:4326'
    coordinate_system VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### `nodes` (节点)

经过通用化设计，可以代表管网接点、河道断面、湖泊等。

```sql
CREATE TABLE nodes (
    id VARCHAR(255) PRIMARY KEY,
    topology_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL, -- 'junction', 'storage', 'outfall', 'confluence'
    elevation_m NUMERIC, -- 地面或河床高程
    initial_depth_m NUMERIC, -- 初始水深
    max_depth_m NUMERIC,
    -- 对于存储节点(湖、库)，定义其面积与水深关系
    storage_curve JSONB,
    coordinates JSONB,
    FOREIGN KEY (topology_id) REFERENCES system_topologies(id)
);
```

### `links` (连接件)

这是一个抽象的父表，用于统一所有连接两个节点的元素。

```sql
CREATE TABLE links (
    id VARCHAR(255) PRIMARY KEY,
    topology_id VARCHAR(255) NOT NULL,
    link_type VARCHAR(50) NOT NULL, -- 'pipe', 'pump', 'reach', 'gate'
    from_node_id VARCHAR(255) NOT NULL,
    to_node_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (topology_id) REFERENCES system_topologies(id),
    FOREIGN KEY (from_node_id) REFERENCES nodes(id),
    FOREIGN KEY (to_node_id) REFERENCES nodes(id)
);
```

### `pipes` (管道)
继承自`links`。
```sql
CREATE TABLE pipes (
    link_id VARCHAR(255) PRIMARY KEY,
    length_m NUMERIC NOT NULL,
    diameter_m NUMERIC NOT NULL,
    roughness NUMERIC NOT NULL,
    FOREIGN KEY (link_id) REFERENCES links(id)
);
```

### `reaches` (河道/渠系)
继承自`links`。
```sql
CREATE TABLE reaches (
    link_id VARCHAR(255) PRIMARY KEY,
    length_m NUMERIC NOT NULL,
    manning_n NUMERIC NOT NULL, -- 曼宁糙率系数
    -- 断面形状信息
    cross_section JSONB NOT NULL, -- e.g., {"type": "trapezoidal", "bottom_width": 20}
    FOREIGN KEY (link_id) REFERENCES links(id)
);
```

### `gates` (闸门)
继承自`links`。
```sql
CREATE TABLE gates (
    link_id VARCHAR(255) PRIMARY KEY,
    gate_type VARCHAR(50) NOT NULL, -- 'sluice', 'radial'
    height_m NUMERIC,
    width_m NUMERIC,
    discharge_coeff NUMERIC, -- 流量系数
    FOREIGN KEY (link_id) REFERENCES links(id)
);
```

### `hydropower_stations` (水电站)
水电站通常与一个`node`（代表大坝）关联。
```sql
CREATE TABLE hydropower_stations (
    id VARCHAR(255) PRIMARY KEY,
    node_id VARCHAR(255) NOT NULL,
    station_type VARCHAR(50), -- 'dam_toe', 'diversion'
    max_flow_m3_per_sec NUMERIC,
    efficiency_curve JSONB,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
```

### 仿真结果 (非关系型存储)
时序数据的存储模型保持不变，但`tags`可以更丰富，例如可以增加`element_type`标签来区分不同类型的流量或水位。
```
# Measurement: water_level
# Tags: simulation_id, node_id, node_type
# Fields: value
water_level,simulation_id=sim_xyz,node_id=n_lake,node_type=storage value=150.7 1678886400000000000
```
