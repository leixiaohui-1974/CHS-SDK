# 水系统物理单元清单

| **文档状态** | **版本号** | **最后更新日期** |
| :--- | :--- | :--- |
| 正式发布 | 1.2 | 2023-10-27 |

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

## 3. 物理单元清单

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
