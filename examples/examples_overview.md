# 智能水务平台仿真示例教程

欢迎来到智能水务平台的仿真示例系列。这个系列旨在通过一系列逐步复杂的场景，引导您从一个最简单的单体仿真，过渡到完整的多智能体、分层控制的复杂网络仿真。

## 教程路径

这些示例被设计为循序渐进的教程，每个教程都在前一个的基础上引入新的概念和功能。

### 主题一：仿真的基本构成 (Python脚本)

本主题涵盖了仿真平台的核心概念，所有示例均通过直接执行其对应的Python脚本来运行（例如，`python3 docs/examples/01_getting_started/run_simulation.py`）。

- **[教程 1: 您的第一个仿真](./non_agent_based/01_getting_started/README.md)**
  - **目标**: 学习如何配置和运行一个最基础的、由 `SimulationHarness` 直接编排的仿真。
  - **核心概念**: 物理组件（水库、闸门）和控制逻辑（PID控制器）的实例化与组合。
  - **场景**: 一个单一水库，通过PID控制器调节下游闸门来控制水位。

- **[教程 2: 构建一个多组件系统](./non_agent_based/02_multi_component_systems/README.md)**
  - **目标**: 学习如何模拟一个包含多个相互连接的组件和多个独立控制器的系统。
  - **核心概念**: 组件的拓扑连接和多控制器管理。
  - **场景**: 一个由水库、河道和两个独立控制的闸门组成的串联系统。

### 主题二：迈向多智能体系统 (MAS) (Python脚本)

本主题介绍了平台架构的一次重大飞跃：从中央编排转向事件驱动的、解耦的多智能体系统。

- **[教程 3: 事件驱动的代理与消息总线](./agent_based/03_event_driven_agents/README.md)**
  - **目标**: 理解多智能体系统（MAS）的架构，其中智能体通过中央 `MessageBus` 进行通信。
  - **核心概念**: 发布/订阅模式、数字孪生代理（DigitalTwinAgent）和本地控制代理（LocalControlAgent）的职责分离。
  - **场景**: 重构教程1的场景，使用独立的代理来感知状态和执行控制。

- **[教程 4: 使用中央调度器的分层控制](./agent_based/04_hierarchical_control/README.md)**
  - **目标**: 学习如何构建一个两级分层控制系统，其中一个高层代理管理低层代理的目标。
  - **核心概念**: 监督控制、远程设定点调整、命令与状态的闭环。
  - **场景**: 一个中央调度器根据全局水位情况，动态调整本地闸门控制代理的PID设定点。

### 主题三：构建复杂的物理世界 (Python脚本)

本主题的核心是平台处理复杂水利网络和多样化物理过程的能力。

- **[教程 5: 模拟复杂网络](./agent_based/05_complex_networks/README.md)**
  - **目标**: 学习如何使用平台基于图的拓扑结构来模拟非线性的、分支的复杂水网。
  - **核心概念**: 基于图的拓扑定义 (`add_connection`) 和拓扑排序。
  - **场景**: 一个包含两个水库、多条河道和汇流点的分支网络，并由一个分层控制系统进行管理。

- **[教程 6: 处理扰动](./agent_based/06_handling_disturbances/README.md)**
  - **目标**: 演示系统如何响应外部扰动（如降雨），并展示控制系统的弹性。
  - **核心概念**: 扰动代理（`RainfallAgent`）和能感知消息的物理模型。
  - **场景**: 在一个分层控制系统中引入突发的降雨事件，观察本地和中央控制器如何协同工作以减轻其影响。

- **[教程 7: 有压管网仿真](./non_agent_based/07_pipe_and_valve/README.md)**
  - **目标**: 演示如何模拟有压管道（Pipe）和阀门（Valve）的动态行为。
  - **核心概念**: 达西-韦斯巴赫水头损失计算和阀门流量控制。

- **[教程 8: 泵站协同控制](./agent_based/08_pump_station_control/README.md)**
  - **目标**: 演示如何通过一个智能体协同控制一个泵站内的多个水泵机组。
  - **核心概念**: 多设备协同控制，将离散的启停动作映射到连续的流量目标。

- **[教程 9: 水电站仿真](./agent_based/09_hydropower_plant/README.md)**
  - **目标**: 演示如何模拟一个简单的水电站发电过程。
  - **核心概念**: 水轮机（WaterTurbine）模型，根据流量和水头差计算发电量。

### 主题四：基于配置文件的仿真 (设计模式)

这一部分展示了如何使用YAML配置文件来定义和运行仿真场景。这些示例旨在作为**设计模式**，说明了平台的声明式配置能力。

**运行方式**:
```bash
python3 run_scenario.py <path_to_scenario_directory>
```
例如: `python3 run_scenario.py docs/examples/non_agent_based/08_non_agent_simulation/`

**注意**: 这些基于YAML的示例在当前版本中可能无法按预期工作，因为它们依赖于一些尚在开发中的、可从配置动态加载的控制代理。它们主要用于展示配置结构和设计思想。

- **[教程 8 (配置版): 非代理式（状态式）仿真](./non_agent_based/08_non_agent_simulation/README.md)**
  - **目标**: 演示一个纯物理仿真，其行为完全由初始状态和物理定律决定。
  - **核心**: `agents.yml` 文件为空，无任何智能体干预。

- **[教程 6 (配置版): 集中式紧急防洪调度](./agent_based/06_centralized_emergency_override/README.md)**
- **[教程 7 (配置版): 集中式设定点协同优化](./notebooks/07_centralized_setpoint_optimization/README.md)**
- **[教程 9 (配置版): 代理式（分布式）仿真](./agent_based/09_agent_based_distributed_control/README.md)**
  - **目标**: 展示如何通过配置文件定义包含感知、决策和控制的完整智能体回路。

### 主题五：组件文档

以下目录不包含可运行的仿真脚本，而是提供了对核心物理和逻辑组件的详细文档和Jupyter Notebook。这些是深入理解平台各部分能力的重要参考资料。

- **[运河与河流组件](./notebooks/10_canal_system/README.md)**
- **[控制与智能体组件](./notebooks/11_control_and_agents/README.md)**
