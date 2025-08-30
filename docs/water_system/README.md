# 智慧水务平台 - `core_lib` 文档

欢迎来到 `core_lib` 的技术文档中心。本系列文档详细介绍了 `core_lib` 的核心架构、组件和工作流程。

## 建议阅读顺序

为了最好地理解本系统的设计哲学，建议您按照以下顺序进行阅读：

1.  **[./00_overview.md](./00_overview.md)**
    *   首先阅读**架构总览**，理解系统基于“智能体”和“消息总线”的事件驱动设计。

2.  **核心概念 (`01_concepts/`)**
    *   **[./01_concepts/01_simulation_harness.md](./01_concepts/01_simulation_harness.md)**: 了解驱动所有仿真的“世界引擎”。
    *   **[./01_concepts/02_message_bus.md](./01_concepts/02_message_bus.md)**: 理解智能体之间解耦通信的关键。

3.  **物理模型 (`02_physical_models/`)**
    *   接下来，浏览此目录下的文档，了解系统中可用的各种水力对象的数学模型。
    *   例如: **[./02_physical_models/01_pipe.md](./02_physical_models/01_pipe.md)**, **[./02_physical_models/02_river_channel.md](./02_physical_models/02_river_channel.md)**

4.  **核心智能体 (`03_agents/`)**
    *   然后，深入了解各类智能体的职责和设计。
    *   例如: **[./03_agents/01_digital_twin_agent.md](./03_agents/01_digital_twin_agent.md)**, **[./03_agents/02_local_control_agent.md](./03_agents/02_local_control_agent.md)**

5.  **场景定义与执行**
    *   **[./04_scenarios.md](./04_scenarios.md)**: 最后，学习如何通过YAML配置文件将以上所有组件和智能体组合起来，定义并运行一个完整的仿真任务。

## 文档结构

*   `00_overview.md`: 系统最高层次的架构介绍。
*   `01_concepts/`: 存放核心架构概念的文档。
    *   `01_simulation_harness.md`
    *   `02_message_bus.md`
*   `02_physical_models/`: 存放各类物理实体模型的详细说明。
    *   `01_pipe.md`
    *   `02_river_channel.md`
    *   `03_gate.md`
    *   `04_reservoir.md`
    *   `05_pump.md`
    *   `06_st_venant_reach.md`
*   `03_agents/`: 存放各类核心智能体的详细说明。
    *   `01_digital_twin_agent.md`
    *   `02_local_control_agent.md`
    *   `03_central_mpc_agent.md`
    *   `04_parameter_identification_agent.md`
*   `04_scenarios.md`: 介绍如何通过YAML配置文件定义和运行仿真。
*   `README.md`: 本目录文件。
