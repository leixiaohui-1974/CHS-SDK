# CHS-SDK: 水系统智能仿真与控制平台

欢迎使用 CHS-SDK（Water System Intelligent Simulation and Control Platform），一个专为复杂水系统设计的高级仿真与控制平台。

本平台采用**数据驱动**和**多智能体（Multi-Agent System, MAS）**的架构，允许用户通过编写配置文件来快速、灵活地构建、仿真和测试各种水系统场景，而无需编写复杂的逻辑代码。

## 核心理念

CHS-SDK 的设计基于以下三大核心概念：

1.  **物理模型 (Physical Models)**：这是对真实世界水利单元（如水库、管道、水泵、水闸）的数学抽象和模拟。平台内置了丰富的、经过验证的物理模型库。
2.  **数字智能体 (Digital Agents)**：每个物理模型都可以关联一个或多个智能体。智能体是系统的“大脑”，负责感知物理世界的状态（**感知智能体**）或执行控制决策（**控制智能体**）。
3.  **消息驱动架构 (Message-Driven Architecture)**：智能体之间通过一个中央**消息总线（Message Bus）**进行通信。感知智能体将物理状态（如水位、流量）发布为消息，控制智能体订阅这些消息并据此作出决策，然后将控制指令（如开闸、启泵）发送给物理模型。这种解耦的设计使得系统高度灵活和可扩展。

## 快速开始

在本平台中，所有仿真都通过一个统一的入口脚本 `run_scenario.py` 来启动。您无需编写任何 Python 代码，只需准备一个包含配置文件的**场景文件夹**。

**标准执行命令:**

```bash
python run_scenario.py --scenario_path <path_to_your_scenario_folder>
```

例如，要运行 `yinchuojiliao` 场景，执行：

```bash
python run_scenario.py --scenario_path mission/scenarios/yinchuojiliao
```

## 场景文件夹结构

一个标准的场景文件夹是仿真的核心，它必须包含以下四个YAML配置文件：

| 文件名 | 作用 | 描述 |
| :--- | :--- | :--- |
| `components.yml` | **定义物理世界** | 在此文件中定义仿真中包含的所有物理实体（如水库、管道、水泵）及其静态参数（如库容曲线、管道长度、摩阻系数）。 |
| `topology.yml` | **定义连接关系** | 描述物理实体之间的水力拓扑连接，即水流如何从一个组件流向下游的另一个组件。 |
| `agents.yml` | **定义系统大脑** | 定义所有智能体，包括它们的类型、参数以及它们之间的通信方式（订阅和发布哪些消息主题）。这是实现系统控制逻辑的核心。 |
| `config.yml` | **定义仿真配置** | 配置全局仿真参数，如仿真时长、时间步长，并指定上述三个配置文件的路径。同时，您可以在此配置需要记录和输出的日志变量。 |

此外，场景文件夹还可以包含：

*   `event_scenario.yml` (可选): 定义一系列按时间顺序触发的预定事件（如设备故障、突发洪水），用于模拟复杂工况。
*   `data/` (可选文件夹): 用于存放所有外部数据文件，如历史入流数据 `inflow.csv`、降雨数据 `rainfall.csv` 等。

##核心组件概览

平台提供了丰富的物理模型和智能体库，以下是部分核心组件的列表。

### 物理模型 (Physical Models)

| 模型类别 | 核心模型 | 描述 |
| :--- | :--- | :--- |
| **蓄水单元** | `Reservoir`, `Lake` | 模拟水库、湖泊、水池等，基于水量平衡方程计算水位和库容。 |
| **输水管道** | `Pipe` | 模拟有压管道，基于达西-韦史巴赫公式计算水头损失和流量。 |
| **渠道河道** | `UnifiedCanal` | **推荐使用**的统一渠道/河道模型，支持多种水流演算方法。 |
| **控制设备** | `Gate`, `Valve`, `Pump`, `WaterTurbine` | 模拟水闸、阀门、水泵、水轮机等核心调控设备。 |
| **站级单元** | `PumpStation`, `ValveStation`, `HydropowerStation` | 作为多个设备的容器，用于聚合状态和实现站级管理。 |

### 智能体 (Agents)

| 智能体类别 | 核心智能体 | 描述 |
| :--- | :--- | :--- |
| **感知智能体** | `ReservoirPerceptionAgent`, `PipelinePerceptionAgent`, `ChannelPerceptionAgent` | 作为物理世界的数字孪生，负责感知并发布物理单元的状态。 |
| **本地控制智能体** | `LocalControlAgent`, `GateControlAgent`, `PumpControlAgent` | 接收观测值并执行本地闭环或开环控制，如PID控制。 |
| **中央协调智能体** | `CentralDispatcherAgent`, `CentralPerceptionAgent` | 负责全局状态感知、优化计算和集中调度。 |
| **数据与扰动** | `CsvInflowAgent`, `RainfallAgent`, `WaterUseAgent` | 从外部文件读取数据或模拟降雨、用水等外部影响。 |

## 示例

您可以参考 `examples/` 和 `mission/scenarios/` 目录下的多个示例场景，来深入了解如何构建自己的仿真。

*   **`examples/`**: 包含针对特定功能（如PID控制、分层控制）的教学示例。
*   **`mission/scenarios/`**: 包含更完整、更复杂的综合性应用场景。

## 面向开发者

如果您希望为平台贡献新的功能，请遵循以下核心原则：

*   **继承基类**: 新的物理模型或智能体应尽可能继承自 `core_lib` 中已有的基类。
*   **保持解耦**: 遵循消息驱动的设计模式，避免在智能体之间建立硬编码的依赖关系。
*   **文档先行**: 在添加新功能前，请先更新相关的设计文档。
