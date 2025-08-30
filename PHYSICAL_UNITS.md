# 水系统物理单元清单

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.1 | 2025-08-30 |

## 1. 简介

本文档旨在为**水系统智能控制平台**的开发提供一份关于**物理单元**的权威参考。所有在系统中进行建模、仿真或控制的物理实体，都在此进行统一说明。

本文档的核心目标是：
*   **明确物理实体**：清晰定义系统中的每一个物理单元。
*   **关联数字代理**：将物理单元与其在软件中的数字孪生代理（Agent）进行唯一映射。
*   **提供开发基准**：为新功能的开发、测试和集成提供统一的物理单元参考，加速开发进程。

## 2. 物理单元分类

根据其是否具备主动控制能力，物理单元分为两类：

*   **被控对象 (Controlled Objects)**：不具备主动控制能力的物理单元，如水库、河道。其代理的核心职责是**状态感知**。
*   **控制对象 (Control Objects)**：具备主动控制能力的物理单元，如水泵、水闸。其代理在感知状态的同时，还负责**接收并执行控制指令**。

---

## 3. 物理单元清单 (智能体)

本章节清单主要描述与物理单元关联的**智能体 (Agent)**。

### 3.1 被控对象 (Controlled Objects)

这些是系统中仅提供状态感知的物理单元。

| 物理单元 | 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- | :--- |
| 水库 | `ReservoirPerceptionAgent` | 水库感知，提供水位、库容等状态 | `core_lib/local_agents/perception/reservoir_perception_agent.py` |
| 有压管道 | `PipelinePerceptionAgent` | 有压管道感知，提供流量、压力等状态 | `core_lib/local_agents/perception/pipeline_perception_agent.py` |
| 无压渠道/河道 | `ChannelPerceptionAgent` | 无压渠道/河道感知，提供水位、流量等状态 | `core_lib/local_agents/perception/channel_perception_agent.py` |
| 水电站（感知） | `HydropowerStationPerceptionAgent` | 水电站感知，提供上下游水位、总发电量等状态 | `core_lib/local_agents/perception/hydropower_station_perception_agent.py` |
| 泵站（感知） | `PumpStationPerceptionAgent` | 泵站感知，提供集水池水位、总流量等站级状态 | `core_lib/local_agents/perception/pump_station_perception_agent.py` |
| 阀门/水闸站（感知）| `ValveStationPerceptionAgent` | 阀门/水闸站感知，提供上下游水位、总流量等站级状态 | `core_lib/local_agents/perception/valve_station_perception_agent.py` |
| 不规则河道 | `RiverChannelPerceptionAgent` | 专注于不规则断面河道的感知，处理更复杂的河道水力学模型。 | `core_lib/local_agents/perception/river_channel_perception_agent.py` |
| 单个闸门（感知） | `GatePerceptionAgent`| 针对单个闸门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/gate_perception_agent.py` |
| 单个水泵（感知） | `PumpPerceptionAgent`| 针对单个水泵的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/pump_perception_agent.py` |
| 单个阀门（感知） | `ValvePerceptionAgent`| 针对单个阀门的感知，实现更细粒度的数字孪生和故障诊断。 | `core_lib/local_agents/perception/valve_perception_agent.py` |

### 3.2 控制对象 (Control Objects)

这些是系统中具备主动控制能力的物理单元。

| 物理单元 | 智能体名称 | 功能描述 | 源码路径 |
| :--- | :--- | :--- | :--- |
| **通用控制器** | `LocalControlAgent` | **本地控制通用基类**，封装了控制器，并通过消息总线处理观测和动作。是实现大多数本地控制任务的核心。 | `core_lib/local_agents/control/local_control_agent.py` |
| 泵机组 | `PumpControlAgent` | 控制一个**泵站**（PumpStation），根据流量需求决定开启或关闭站内**多个离散水泵**。(*注意: 该代理直接继承自 Agent，而非 LocalControlAgent*) | `core_lib/local_agents/control/pump_control_agent.py` |
| 单个阀门（控制） | `ValveControlAgent` | 控制单个阀门。它本身是 `LocalControlAgent` 的一个轻量级实现，需在初始化时配置具体的控制器（如PID）。 | `core_lib/local_agents/control/valve_control_agent.py` |
| 单个闸门（控制） | `GateControlAgent` | 控制单个闸门，与 `ValveControlAgent` 类似，是 `LocalControlAgent` 的轻量级实现。 | `core_lib/local_agents/control/gate_control_agent.py` |
| 泵站（控制） | `PumpStationControlAgent` | 泵站控制的**站级代理**，负责站级总调度（如决定总流量），并将指令下发给机组级代理（如 `PumpControlAgent`）。 | `core_lib/local_agents/control/pump_station_control_agent.py` |
| 阀门站（控制） | `ValveStationControlAgent` | 阀门站控制的**站级代理**，负责实现站级流量或水位目标，并将计算出的开度指令下发给站内每个阀门。 | `core_lib/local_agents/control/valve_station_control_agent.py` |
| 水电站（控制） | `HydropowerStationAgent` | 水电站控制，负责制定站级策略，并向下游发布针对单个水轮机或水闸的控制指令。 | `core_lib/local_agents/control/hydropower_station_agent.py` |
| 水电站（控制） | `HydropowerStationControlAgent` | 水电站控制，同上。 | `core_lib/local_agents/control/hydropower_station_control_agent.py` |
| 压力控制器 | `PressureControlAgent` | 压力控制，一个 `LocalControlAgent` 的应用实例，专用于需要维持特定压力的控制场景。 | `core_lib/local_agents/control/pressure_control_agent.py` |

---

## 4. 物理模型清单 (Physical Model Inventory)

本章节清单详细描述了仿真平台中的**物理模型**，它们是物理单元在数字世界中的数学表达。

### 4.1 水库、湖泊与水池 (Reservoirs, Lakes & Ponds)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `Reservoir` | **通用蓄水池**。基于水量平衡方程，模拟蓄水单元的水位和体积变化。适用于水库、调节池等。 | `volume`, `water_level`, `outflow` | `surface_area` | 基础的蓄水模型。 |
| `Lake` | **考虑蒸发的湖泊**。在 `Reservoir` 模型基础上增加了蒸发损失计算。适用于模拟地表开阔的湖泊或水库。 | `volume`, `water_level`, `outflow` | `surface_area`, `max_volume`, `evaporation_rate_m_per_s` | 可用于模拟任何有显著蒸发损失的水体，例如**水池**。 |

### 4.2 管道 (Pipes)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `Pipe` | **有压管道**。使用达西-韦史巴赫公式计算流量。可工作在两种模式下：1. 由上游水泵等提供强制灌输流量。2. 根据上下游压差（水头）计算自由流。 | `outflow`, `head_loss` | `diameter`, `friction_factor`, `length` | 核心的有压输水模型。 |

### 4.3 渠道与河道 (Canals & Rivers)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `UnifiedCanal` | **统一渠道模型**。一个灵活的渠道/河道模型，通过 `model_type` 参数支持多种不同的水流演算方法。 | `water_level`, `inflow`, `outflow` | `model_type` (e.g., 'integral', 'integral_delay'), 及各类型对应参数 | **推荐使用**。这是当前所有无压渠道和河道模拟的核心。 |
| `Canal` | (已弃用) 梯形断面渠道。 | `volume`, `water_level`, `outflow` | `bottom_width`, `length`, `slope`, `side_slope_z`, `manning_n` | **已弃用**。请使用 `UnifiedCanal` 代替。 |
| `RiverChannel` | (已弃用) 线性水库河道。 | `volume`, `outflow` | `k` | **已弃用**。请使用 `UnifiedCanal(model_type='linear_reservoir')` 代替。 |

#### `UnifiedCanal` 模型类型

| `model_type` | 描述 | 所需额外参数 |
| :--- | :--- | :--- |
| `integral` | 积分模型，类似一个简单的水库。 | `surface_area`, `outlet_coefficient` |
| `integral_delay` | 积分延迟模型，考虑水流传播的纯时间延迟。 | `gain`, `delay` |
| `integral_delay_zero` | 积分零点延迟模型，更复杂的延迟模型，包含导数项。 | `gain`, `delay`, `zero_time_constant` |
| `linear_reservoir` | 线性水库模型，类似马斯京根法。 | `storage_constant`, `level_storage_ratio` |

### 4.4 水闸 (Gates)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `Gate` | **可控闸门**。基于孔口出流公式 (`Q = C*A*sqrt(2gh)`) 计算流量。闸门开度变化受最大变动速率限制。 | `opening`, `outflow` | `discharge_coefficient`, `width`, `max_opening`, `max_rate_of_change` | 核心的水量控制设备模型。 |

### 4.5 水泵 (Pumps)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `Pump` | **离心泵**。一个简化的开关模型。当开启且扬程在允许范围内时，提供恒定的流量。 | `status` (0/1), `outflow`, `power_draw_kw` | `max_head`, `max_flow_rate`, `power_consumption_kw` | 用于模拟单个的、定速的水泵。 |
| `PumpStation` | **泵站**。作为多个 `Pump` 对象的容器，聚合其总流量和总功耗。 | `total_outflow`, `active_pumps`, `total_power_draw_kw` | (无) | 自身无水力学逻辑，仅作为管理和状态聚合单元。 |

### 4.6 阀门 (Valves)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `Valve` | **可控阀门**。基于修正的孔口出流公式计算流量，其有效出流系数与开度百分比相关。 | `opening` (%), `outflow` | `discharge_coefficient`, `diameter` | 核心的压力和流量控制设备模型。 |
| `ValveStation` | **阀门站**。作为多个 `Valve` 对象的容器，聚合其总流量。 | `total_outflow`, `valve_count` | (无) | 自身无水力学逻辑，仅作为管理和状态聚合单元。 |

### 4.7 水电站 (Hydropower Stations)

| 模型/类名称 | 功能描述 | 状态变量 | 模型参数 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `HydropowerStation` | **水电站**。作为 `WaterTurbine` 和 `Gate` 对象的容器，聚合其总出流量和总发电功率。 | `total_outflow`, `total_power_generation`, `turbine_outflow`, `spillway_outflow` | (无) | 自身无水力学和发电逻辑，仅作为管理和状态聚合单元。 |
| `WaterTurbine` | **水轮机**。基于水电方程 (`P = η*ρ*g*Q*H`) 计算发电功率。出流量受可用水量和最大流量限制。 | `outflow`, `power` | `efficiency`, `max_flow_rate` | 核心的发电单元模型。 |
