# 水系统物理单元清单

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.1 | 2025-08-30 |


## 1. 简介

本文档旨在为**水系统智能控制平台**的开发提供一份关于**物理单元**的权威参考。所有在系统中进行建模、仿真或控制的物理实体，都在此进行统一说明。

本文档的核心目标是：
*   **明确物理实体**：清晰定义系统中的每一个物理单元及其在现实世界中的作用和特性。
*   **关联数字代理**：将物理单元与其在软件中的数字孪生代理（Agent）进行唯一映射，方便开发者理解其软件对应物。
*   **提供开发基准**：为新功能的开发、测试和集成提供统一的物理单元参考。

## 2. 物理单元分类

根据其是否具备主动控制能力，物理单元分为两类：

*   **被控对象 (Controlled Objects)**：不具备主动控制能力的物理单元，如水库、河道。其代理的核心职责是**状态感知**。
*   **控制对象 (Control Objects)**：具备主动控制能力的物理单元，如水泵、水闸。其代理在感知状态的同时，还负责**接收并执行控制指令**。

---

## 3. 物理单元清单 (智能体)

本章节清单主要描述与物理单元关联的**智能体 (Agent)**。

### 3.1 被控对象 (Controlled Objects)

这些是系统中仅提供状态感知的物理单元，是物理世界的数字眼睛。

| 物理单元 | 功能与物理特性描述 | 对应的智能体 | 源码路径 |
| :--- | :--- | :--- | :--- |
| 水库 | 用于调蓄和存储水资源的大型人工湖泊。主要功能包括防洪、供水、灌溉和水力发电。其关键物理特性为库容、水位与库容面积的关系、大坝结构等。 | `ReservoirPerceptionAgent` | `core_lib/local_agents/perception/reservoir_perception_agent.py` |
| 有压管道 | 全封闭的、依靠压力输送流体的管状设施。广泛用于城市供水、排水和长距离输水工程。其物理特性包括管径、材质、壁厚、长度和沿程摩阻系数。 | `PipelinePerceptionAgent` | `core_lib/local_agents/perception/pipeline_perception_agent.py` |
| 无压渠道/河道 | 具有自由表面的水流通道，如天然河流、人工运河或灌溉渠。水流依靠重力驱动。关键物理特性包括断面形状、尺寸、坡度、糙率等。 | `ChannelPerceptionAgent` | `core_lib/local_agents/perception/channel_perception_agent.py` |
| 水电站 | 将水能转换为电能的综合性工程设施。通常由大坝、引水系统、厂房和水轮发电机组组成。其核心是利用水流的势能或动能驱动水轮机发电。 | `HydropowerStationPerceptionAgent` | `core_lib/local_agents/perception/hydropower_station_perception_agent.py` |
| 泵站 | 用于提升水位或增加水压的机电设施，是水系统中的动力心脏。通常包括集水池、一台或多台水泵机组及其附属的电气和控制设备。 | `PumpStationPerceptionAgent` | `core_lib/local_agents/perception/pump_station_perception_agent.py` |
| 阀门/水闸站 | 集中安装和管理多个阀门或水闸的控制节点。用于精确调控管网或渠道中的流量和压力。其物理布局和各单元的类型、尺寸是关键特征。 | `ValveStationPerceptionAgent` | `core_lib/local_agents/perception/valve_station_perception_agent.py` |
| 不规则河道 | 指断面形状、坡度和糙率等随里程不断变化的天然河流。其水力学行为复杂，是进行洪水演进和水环境模拟时的重点和难点。 | `RiverChannelPerceptionAgent` | `core_lib/local_agents/perception/river_channel_perception_agent.py` |
| 单个闸门 | 安装在渠道或水工建筑物中用于控制水流的活动挡板。通过升降或旋转来调节过流量或水位。常见的物理形式有平板闸、弧形闸等。 | `GatePerceptionAgent`| `core_lib/local_agents/perception/gate_perception_agent.py` |
| 单个水泵 | 将机械能转化为液体能量以输送液体的核心设备。关键物理特性包括其性能曲线（流量-扬程-效率曲线）、额定功率、尺寸和材料。 | `PumpPerceptionAgent`| `core_lib/local_agents/perception/pump_perception_agent.py` |
| 单个阀门 | 安装在承压管道中用于调节流量、压力或切断流路的控制元件。根据功能和结构，可分为闸阀、球阀、蝶阀等多种物理类型。 | `ValvePerceptionAgent`| `core_lib/local_agents/perception/valve_perception_agent.py` |

### 3.2 控制对象 (Control Objects)

这些是系统中具备主动控制能力的物理单元。下表中的描述同样聚焦于物理实体本身。

| 物理单元 | 功能与物理特性描述 | 对应的智能体 | 源码路径 |
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
=======
| 泵机组 | 一台或多台水泵的组合，作为泵站内的基本操作单元。通常会根据调度指令成组启停，以满足不同的流量和扬程需求。 | `PumpControlAgent` | `core_lib/local_agents/control/pump_control_agent.py` |
| 单个阀门 | (同上) 安装在承压管道中用于调节流量、压力或切断流路的控制元件。其控制形态包括远程调节开度和快速开关。 | `ValveControlAgent` | `core_lib/local_agents/control/valve_control_agent.py` |
| 单个闸门 | (同上) 安装在渠道或水工建筑物中用于控制水流的活动挡板。其控制系统能够接收指令并精确驱动闸门到达指定开度。 | `GateControlAgent` | `core_lib/local_agents/control/gate_control_agent.py` |
| 泵站 | (同上) 用于提升水位或增加水压的机电设施。作为控制对象时，其整体（而非单个水泵）被视为一个可调度的单元，能够响应总流量或压力目标。 | `PumpStationControlAgent` | `core_lib/local_agents/control/pump_station_control_agent.py` |
| 阀门站 | (同上) 集中安装和管理多个阀门或水闸的控制节点。作为控制对象时，它接收站级总目标，并自主协调内部各单元的动作。 | `ValveStationControlAgent` | `core_lib/local_agents/control/valve_station_control_agent.py` |
| 水电站 | (同上) 将水能转换为电能的综合性工程设施。作为控制对象时，其调度系统可以根据电网需求和水情，主动调整发电出力和下泄流量。 | `HydropowerStationAgent` / `HydropowerStationControlAgent` | `core_lib/local_agents/control/hydropower_station_agent.py` |
| 压力调控点 | 这是一个虚拟的物理单元，指代管网中需要精确控制压力的一个或多个关键位置。其物理实现依赖于附近的可调控物理设备（如阀门或变频泵）。| `PressureControlAgent` | `core_lib/local_agents/control/pressure_control_agent.py` |

---
## 4. 外部影响与边界条件 (External Influences & Boundary Conditions)

除了构成水利基础设施的物理单元外，仿真平台还需要定义对系统产生影响的外部物理过程或边界。这些通常作为模拟场景的输入。

| 物理过程/边界 | 功能与物理特性描述 | 对应的智能体 | 源码路径 |
| :--- | :--- | :--- | :--- |
| 入流 | 代表系统边界上游的水流来源，如河流上游来水、水库入流或管道的起始流量。在仿真中，这通常是一个随时间变化的时间序列数据。 | `CsvInflowAgent` | `core_lib/data_access/csv_inflow_agent.py` |
| 降雨 | 模拟在特定区域上发生的降雨过程。降雨是驱动径流和影响河流水位、水库蓄水量的关键气象因素。其物理特性包括降雨强度、持续时间和空间分布。 | `RainfallAgent`, `DynamicRainfallAgent` | `core_lib/disturbances/rainfall_agent.py` |
| 用水需求 | 模拟从系统中取水的行为，如城市居民用水、工业用水或农业灌溉。这在仿真中表现为系统中的一个或多个“汇”点，其需求量通常随时间变化。 | `WaterUseAgent` | `core_lib/disturbances/water_use_agent.py` |

