# CHS-SDK: 水系统智能仿真与控制平台

欢迎使用 CHS-SDK（Water System Intelligent Simulation and Control Platform），一个专为复杂水系统设计的高级仿真与控制平台。

本平台采用**数据驱动**和**多智能体（Multi-Agent System, MAS）**的架构，允许用户通过编写配置文件来快速、灵活地构建、仿真和测试各种水系统场景，而无需编写复杂的逻辑代码。

## 核心理念

CHS-SDK 的设计基于以下三大核心概念：

1. **物理模型 (Physical Models)**：这是对真实世界水利单元（如水库、管道、水泵、水闸）的数学抽象和模拟。平台内置了丰富的、经过验证的物理模型库。
2. **数字智能体 (Digital Agents)**：每个物理模型都可以关联一个或多个智能体。智能体是系统的"大脑"，负责感知物理世界的状态（**感知智能体**）或执行控制决策（**控制智能体**）。
3. **消息驱动架构 (Message-Driven Architecture)**：智能体之间通过一个中央**消息总线（Message Bus）**进行通信。感知智能体将物理状态（如水位、流量）发布为消息，控制智能体订阅这些消息并据此作出决策，然后将控制指令（如开闸、启泵）发送给物理模型。这种解耦的设计使得系统高度灵活和可扩展。

## 快速开始

### 示例运行方式

本平台提供两种类型的示例，每种都有不同的运行方式：

#### 1. YAML配置示例（声明式）

这类示例通过YAML文件完全定义仿真场景，使用统一的运行脚本。这些示例包含完整的四个YAML配置文件，无需编写Python代码。

**特征标识：**
- 包含 `.scenario_config` 标识文件
- 包含完整的 `config.yml`、`components.yml`、`topology.yml`、`agents.yml` 文件
- 目录中没有独立的 `run_*.py` 脚本

**运行命令：**
```bash
python run_scenario.py <示例目录路径>
```

**示例：**
```bash
# 运行集中式紧急防洪调度示例
python run_scenario.py examples/agent_based/06_centralized_emergency_override

# 运行分层分布式控制示例
python run_scenario.py examples/canal_model/hierarchical_distributed_control_example
```

#### 2. Python脚本示例（编程式）

这类示例包含自定义的Python逻辑和算法实现，需要直接运行对应的Python脚本。

**特征标识：**
- 包含独立的运行脚本（如 `run_identification.py`、`run_simulation.py` 等）
- 可能包含YAML配置文件，但主要逻辑在Python脚本中
- 通常用于演示特定算法或复杂控制逻辑

**运行命令：**
```bash
cd <示例目录>
python <示例脚本名称>.py
```

**示例：**
```bash
# 运行水库参数辨识示例
cd examples/identification/01_reservoir_storage_curve
python run_identification.py

# 运行多组件系统仿真示例
cd examples/non_agent_based/02_multi_component_systems
python run_multi_component_simulation.py
```

### 自动检测示例类型

平台提供了自动检测工具来识别示例类型：

```python
from core_lib.utils.example_detector import detect_example_type, get_run_command

# 检测示例类型
example_type = detect_example_type("examples/agent_based/06_centralized_emergency_override")
print(example_type)  # 输出: "run_scenario.py"

# 获取运行命令
command = get_run_command("examples/identification/01_reservoir_storage_curve")
print(command)  # 输出: "cd examples/identification/01_reservoir_storage_curve && python run_identification.py"
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

- `event_scenario.yml` (可选): 定义一系列按时间顺序触发的预定事件（如设备故障、突发洪水），用于模拟复杂工况。
- `data/` (可选文件夹): 用于存放所有外部数据文件，如历史入流数据 `inflow.csv`、降雨数据 `rainfall.csv` 等。

## 核心组件概览

平台提供了丰富的物理模型和智能体库，以下是部分核心组件的列表。

### 物理模型 (Physical Models)

| 模型类别 | 核心模型 | 描述 |
| :--- | :--- | :--- |
| **蓄水单元** | `Reservoir`, `Lake` | 模拟水库、湖泊、水池等，基于水量平衡方程计算水位和库容。 |
| **输水管道** | `Pipe` | 模拟有压管道，基于达西-韦史巴赫公式计算水头损失和流量。 |
| **渠道河道** | `UnifiedCanal` | **推荐使用**的统一渠道/河道模型，支持多种水流演算方法。 |
| **控制设备** | `Gate`, `Valve`, `Pump`, `WaterTurbine` | 模拟水闸、阀门、水泵、水轮机等核心调控设备。 |
| **站级单元** | `PumpStation`, `ValveStation`, `HydropowerStation` | 作为多个设备（如水泵、阀门、水轮机）的逻辑容器，用于聚合状态和实现站级管理。 |

### 智能体 (Agents)

| 智能体类别 | 核心智能体 | 描述 |
| :--- | :--- | :--- |
| **感知智能体** | `ReservoirPerceptionAgent`, `PipelinePerceptionAgent`, `ChannelPerceptionAgent` | 作为物理世界的数字孪生，负责感知并发布物理单元的状态。 |
| **本地控制智能体** | `LocalControlAgent`, `GateControlAgent`, `PumpControlAgent` | 接收观测值并执行本地闭环或开环控制，如PID控制。 |
| **中央协调智能体** | `CentralDispatcherAgent`, `CentralPerceptionAgent` | 负责全局状态感知、优化计算和集中调度。 |
| **数据与扰动** | `CsvInflowAgent`, `RainfallAgent`, `WaterUseAgent` | 从外部文件读取数据或模拟降雨、用水等外部影响。 |

## 示例

您可以参考 `examples/` 和 `mission/scenarios/` 目录下的多个示例场景，来深入了解如何构建自己的仿真。

- **`examples/`**: 包含针对特定功能（如PID控制、分层控制）的教学示例。
- **`mission/scenarios/`**: 包含更完整、更复杂的综合性应用场景。

## 面向开发者

如果您希望为平台贡献新的功能，请遵循以下核心原则：

- **继承基类**: 新的物理模型或智能体应尽可能继承自 `core_lib` 中已有的基类。
- **保持解耦**: 遵循消息驱动的设计模式，避免在智能体之间建立硬编码的依赖关系。
- **文档先行**: 在添加新功能前，请先更新相关的设计文档。

---

## 仿真平台操作指南：模式与入口

### 简介

本平台为复杂水利系统提供了一个高度灵活的仿真与控制环境。为了满足从简单的物理过程模拟到复杂的智能调度系统测试等不同需求，平台设计了多种仿真模式和运行入口。理解这些模式与入口的差异，将帮助您更高效地进行系统建模与分析。

本文档分为三个核心部分：

- **核心概念关系**: 宏观介绍各模块如何协同工作
- **仿真模式详解**: 深入介绍系统支持的几种核心仿真范式，即"仿真什么"
- **入口程序详解**: 详细介绍启动和配置仿真的不同方法，即"如何运行"

### 第一部分：核心概念关系

为了更好地理解平台架构，我们可以将其想象成一个层次化的结构：

- **物理层 (Physical Layer)**: 这是最底层，包含了所有水利设施的数学模型（如水库、管道）。这是仿真的"世界"。

- **仿真引擎层 (Engine Layer)**: 该层负责驱动物理层的模型按时间步进，实现状态式仿真。这是仿真的"物理定律"。

- **智能层 (Intelligence Layer)**: 在引擎层之上，引入了智能体（Agent）和消息总线（Message Bus），构成了代理式仿真的核心。这是系统拥有"大脑"和"神经系统"的地方。

- **策略层 (Strategy Layer)**: 在智能层内部，通过设计特殊的中央智能体，可以实现集中式仿真的顶层设计和分层控制。这是"大脑"进行高级思考的方式。

- **执行入口 (Execution Entry Point)**: 这一系列启动脚本和配置方法（硬编码、配置文件、智能生成等）是与整个仿真平台交互的"接口"，决定了如何启动和定义一个仿真任务。

> **注意**: 上层构建于下层之上

### 第二部分：仿真模式详解

#### 2.1 概述

本平台支持多种仿真范式，它们并非相互排斥，而是代表了不同层次的系统复杂度和控制策略。

- **状态式仿真 (State-Based Simulation)**: 纯物理过程模拟，是所有仿真的基础核心
- **代理式仿真 (Agent-Based Simulation)**: 分布式、事件驱动的智能系统，是平台的主要架构
- **集中式仿真 (Centralized Simulation)**: 在代理式架构下实现的一种分层、目标驱动的控制策略

#### 2.2 状态式仿真 (State-Based Simulation): 物理核心

**概念 (Concept)**:

这是最基础的仿真层次，仅模拟系统中各个物理组件（如水库、管道、闸门）的行为，完全遵循预设的物理和水力学规律。此模式下不涉及任何智能决策或主动控制（例如，闸门的开度是按预设时间表变化的，而不是响应水位），旨在观察系统在给定输入和边界条件下的自然演化过程。

**关键特性**:

- **确定性**: 给定相同的初始条件和输入，结果完全相同
- **无智能**: 系统行为完全由物理模型和预设输入驱动
- **核心基础**: 是所有更高级仿真模式的物理世界基础

**代码实现 (Code Implementation)**:

- **物理模型**: 所有物理组件的数学模型都定义在 `core_lib/physical_objects/` 目录下（例如 `Reservoir`, `UnifiedCanal(model_type='integral')`, `Gate`）。这些类都实现了 `Simulatable` 接口。

- **拓扑与加载**: `SimulationLoader` 根据 `components.yml` 和 `topology.yml` 文件实例化物理组件，并构建它们之间的连接关系图。

- **仿真引擎**: 核心驱动逻辑位于 `SimulationHarness._step_physical_models()` 方法中。该方法会按照拓扑排序（保证水流方向的计算正确性）依次调用每个物理组件的 `.step()` 方法，更新其状态。

**如何运行 (How to Run)**:

在你的场景配置中，提供一个空的 `agents.yml` 文件，或者文件中不包含任何控制或感知类的智能体。当 `run_scenario.py` 执行时，`SimulationHarness.run_mas_simulation()` 的主循环中，智能体执行阶段将无事可做，只有物理模型演化阶段 `_step_physical_models()` 会被有效执行，从而实现纯粹的状态式仿真。

#### 2.3 代理式仿真 (Agent-Based Simulation): 分布式智能

**概念 (Concept)**:

这是平台设计的核心架构，即一个多智能体系统 (Multi-Agent System, MAS)。在此模式下，多个拥有自主行为的智能体（Agent）通过一个中央消息总线进行通信，形成一个分布式的感知-决策-行动系统。每个智能体通常只负责一个局部任务，系统的宏观智能行为由所有智能体的交互涌现而出。

**关键特性**:

- **分布式**: 决策逻辑分散在各个智能体中
- **事件驱动**: 智能体响应消息总线上的事件（消息）来触发行为
- **异步通信**: 智能体之间通过消息总线解耦，实现异步交互

**代码实现 (Code Implementation)**:

- **仿真引擎**: `SimulationHarness.run_mas_simulation()` 方法是此模式的专用执行器。其主循环在每个时间步分为两个阶段：
  - 智能体行动: 循环调用所有已加载智能体的 `.run()` 方法
  - 物理世界演化: 调用 `_step_physical_models()` 更新物理状态

- **感知 (Perception)**: 以 `DigitalTwinAgent` 为代表的感知智能体是物理世界到信息世界的桥梁。在它的 `.run()` 方法中，它会调用 `self.model.get_state()` 从其关联的物理模型获取状态，然后通过 `self.bus.publish('some_topic', state_data)` 将状态发布到 `MessageBus` 的指定主题上。

- **通信 (Communication)**: `core_lib/central_coordination/collaboration/message_bus.py` 中定义的 `MessageBus` 是所有智能体异步通信的中枢。智能体通过 `subscribe` 订阅感兴趣的主题，通过 `publish` 发布消息。

- **行动 (Action)**: 控制类智能体（如 `LocalControlAgent` 的子类）订阅 `MessageBus` 上的相关主题以获取状态或指令。在做出决策后，它们可以直接调用其持有的物理组件实例的方法（例如 `gate.set_opening()`），或发布新的指令消息到总线，供其他智能体使用。

**如何运行 (How to Run)**:

在 `agents.yml` 文件中定义所有你需要的感知、控制、扰动等智能体。`SimulationLoader` 会负责将它们实例化，并注入 `MessageBus` 和其他依赖，最终"装配"出一个完整的多智能体系统。

#### 2.4 集中式仿真 (Centralized Simulation): 分层控制策略

**概念 (Concept)**:

集中式仿真并非一个与代理式并列的独立模式，而是在代理式仿真架构下实现的一种高级控制策略。它通过引入一个或多个拥有全局视野的"中央"智能体，来实现对下层"地方"智能体的协调和调度，构成一个分层控制系统。

**关键特性**:

- **分层结构**: 存在中央决策层和地方执行层
- **全局优化**: 中央智能体可以基于全局信息做出最优决策
- **指令驱动**: 地方智能体响应中央智能体的指令

**代码实现 (Code Implementation)**:

- **中央智能体**: 以 `CentralDispatcherAgent` 为例，这类智能体被设计用来监控全局的关键绩效指标（KPI）或系统状态。

- **全局决策**: 中央智能体在其 `.run()` 逻辑中，会评估全局状态。例如，`CentralDispatcherAgent` 会检查水库的全局水位。

- **顶层指令**: 当满足某个全局条件时（如水位超过防洪限制），中央智能体便会向 `MessageBus` 发布一个高优先级的指令消息。这个消息的目标通常是某个或某些地方智能体。

- **分层执行**: 地方智能体（如某个闸门的控制智能体）除了执行自己的本地控制逻辑外，也订阅来自中央智能体的指令主题。当收到顶层指令时，它会服从该指令，覆盖掉自己原来的决策。这就实现了一个清晰的"中央调度-地方执行"的分层控制链路。

**如何运行 (How to Run)**:

在你的 `agents.yml` 配置文件中，除了定义所有地方智能体外，再加入一个或多个中央协调类的智能体（如 `CentralDispatcherAgent`）。只要这个智能体被加载到系统中，整个代理式仿真就自动具备了集中式、分层控制的特性。

#### 2.5 (附录) 简单集中控制模式 (Appendix: Simple Centralized Control Mode)

**概念 (Concept)**:

这是一个为简化测试而存在的、同步的仿真模式。它完全绕过了智能体和 `MessageBus` 架构，允许控制器（Controller）直接与物理模型交互。

**使用场景 (Use Case)**:

此模式非常适合用来快速验证一个独立的、简单的反馈控制器（如PID控制器）的性能，而无需配置和运行一整套复杂的智能体系统。注意，标准的 `run_scenario.py` 脚本调用的是 `run_mas_simulation()`，因此该模式主要用于代码内部的编程式调用和单元测试。

**代码实现 (Code Implementation)**:

- **仿真引擎**: 此模式由 `SimulationHarness.run_simulation()` 方法实现。

- **同步循环**: 在每个仿真步，该方法会：
  - 直接遍历所有注册的 `Controller` 对象
  - 从每个控制器所观察的物理模型中获取状态
  - 调用 `controller.compute_control_action()` 计算出控制信号
  - 将所有控制信号统一传递给 `_step_physical_models()` 方法，作用于物理模型

### 第三部分：入口程序详解

#### 3.1 概述

除了选择不同的仿真模式，本平台还提供了多种启动和配置仿真的"入口"方式。这些方式从完全在代码中定义到使用高度集成的配置文件，再到由大语言模型驱动，提供了极大的灵活性。

#### 3.2 硬编码方式 (Hardcoded Approach)

**概念**: 这是最直接的方式，所有仿真元素——包括物理组件、智能体、拓扑结构和仿真参数——都直接在Python脚本中通过代码进行实例化和配置。

**适用场景**: 适用于快速原型开发、单元测试、或者非常固定且无需频繁修改的简单场景。

**优点**: 直观，易于调试，无需管理外部配置文件。

**缺点**: 灵活性差，每次修改都需要改动代码，不利于场景的复用和分享。

**示例脚本**: `examples/run_hardcoded.py`

#### 3.3 传统多配置文件方式 (Traditional Multi-Config File Approach)

**概念**: 这是平台早期采用的模块化配置方式。一个完整的仿真场景被拆分到多个独立的YAML文件中：

- `components.yml`: 定义物理组件及其参数
- `topology.yml`: 定义物理组件之间的连接关系
- `agents.yml`: 定义所有智能体及其参数
- `config.yml`: 定义仿真器的全局设置（如仿真时长、步长等）

**适用场景**: 适用于需要清晰分离物理模型、智能体和仿真设置的场景，有助于理解系统的模块化构成。

**优点**: 关注点分离，结构清晰。

**缺点**: 配置文件数量较多，管理略显繁琐。

**示例脚本**: `examples/run_scenario.py`

#### 3.4 单一整合配置文件方式 (Unified Config File Approach)

**概念**: 为了简化配置，这种方式将传统多配置文件方式中的所有内容合并到一个名为 `unified_config.yml` 的单一文件中。该文件内部通过不同的顶层关键字（如 `components`, `topology`, `agents`）来组织内容。

**适用场景**: 当一个仿真场景相对固定，希望在一个文件中查看和管理所有配置时，这种方式非常方便。

**优点**: 简化了文件管理，所有配置一目了然。

**缺点**: 对于非常复杂的系统，单个文件可能变得庞大，不利于模块化管理。

**示例脚本**: `examples/run_unified_scenario.py`

#### 3.5 通用配置文件方式 (Universal Config File Approach)

**概念**: 这是目前推荐的最佳实践。它采用一个名为 `universal_config.yml` 的高度结构化单一配置文件。该文件具有更严谨和全面的 schema，支持模板、引用、变量等高级功能，使得配置更加规范、可复用和易于扩展。

**适用场景**: 适用于构建复杂、标准化、可复用的仿真场景，是企业级应用和复杂研究的首选。

**优点**: 功能强大，结构规范，高度可复用，是未来平台功能扩展的基础。

**缺点**: 初次学习时需要理解其更复杂的 schema 结构。

**示例脚本**: `examples/run_universal_config.py`

#### 3.6 智能运行方式 (Intelligent/Smart Run Approach)

**概念**: 这是最具前瞻性的运行方式。它利用大语言模型（LLM）来理解自然语言描述的仿真需求，并自动生成所需的配置文件（通常是 `universal_config.yml`），甚至可以在仿真过程中根据高级指令动态调整策略。

**工作流**: 用户提供自然语言提示 → LLM生成 `universal_config.yml` → `run_universal_config.py` 加载并执行仿真。

**适用场景**:

- **快速原型构建**: 通过自然语言快速搭建一个仿真场景的雏形
- **非技术人员使用**: 允许领域专家通过自然语言与仿真系统交互
- **构建AI驱动的决策系统**: 将LLM作为顶层的"中央决策大脑"

**优点**: 极大地降低了使用门槛，提高了仿真实验的效率和创造力。

**缺点**: 依赖于LLM的能力，对结果的精确控制有时需要通过精心设计的提示（Prompt）来实现。

**示例脚本**: `examples/run_smart.py`, `examples/llm_integration/run_llm_demonstration.py`

### 第四部分：如何选择

#### 4.1 推荐路径

| 目标 | 推荐仿真模式 | 推荐入口程序 | 理由 |
| :--- | :--- | :--- | :--- |
| 开发/测试新的物理模型 | 状态式 | 硬编码方式 | 在隔离环境中验证物理行为，无需控制逻辑干扰。 |
| 对物理模型进行参数标定 | 状态式 | 通用配置文件 | 方便通过修改变量来运行多组参数对比实验。 |
| 测试单个简单的控制器 (如PID) | 简单集中控制 | 硬编码方式 | 快速、直接地测试控制算法，无需配置完整的智能体系统。 |
| 模拟含多个交互控制单元的系统 | 代理式 | 通用配置文件 | 最能体现平台核心优势，适合构建模块化、分布式的智能系统。 |
| 模拟有顶层协调的大型系统 | 集中式 (构建于代理式之上) | 通用配置文件 | 可同时模拟地方自主控制和中央的宏观调度。 |
| 根据自然语言描述快速构建原型 | 任何模式 | 智能运行方式 | 利用大语言模型的能力，从需求直接生成可运行的仿真场景。 |

#### 4.2 总结

本平台通过仿真模式和入口程序两个维度的组合，提供了极高的灵活性。

- 对于初学者，建议从硬编码或传统多配置文件方式入手，以理解平台的基本构成。
- 对于常规应用和标准化项目，强烈推荐使用通用配置文件 (`universal_config.yml`) 的方式。
- 对于探索性研究和构建高级智能应用，智能运行方式提供了强大的助力。

无论选择何种入口，底层的仿真核心都可以是状态式、代理式或集中式的，您可以根据具体需求灵活组合。