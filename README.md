# 智能水务平台 (SWP) - 数字孪生与多代理系统框架

本代码库包含一个前瞻性的“智慧水务系统数字孪生与协同控制平台”的基础框架。该项目被构想为一个“母体机器”——一个用于模拟、生成、测试和管理复杂水务系统的元平台，其核心采用了多代理系统（MAS）的方法。

整个架构被设计为模块化、可插拔和可扩展的，其灵感来源于Simulink的基于模块的建模范式。每一个组件都被设计成一个可组合的后端算法和引擎。

## 宏观愿景 (High-Level Vision)

- **数字孪生平台 (Digital Twin Platform)**: 通过整合实时监测数据，构建物理水务系统的实时数字映像。
- **智能体工厂 (Agent Factory)**: 从仿真模型中自动生成并配置多代理系统。
- **在环测试沙盒 (In-the-Loop Sandbox)**: 作为其自身的测试环境，对生成的代理进行严格、自动化的测试。
- **全生命周期管理 (Lifecycle Management)**: 管理代理的版本控制、性能评估和自适应更新。

## 技术架构 (Technical Architecture)

该平台建立在一个分层的、模块化的架构之上，分为四个主要的产品类别：

1.  **`swp.simulation_identification`**:
    - **水系统仿真与辨识**: 包含所有的水动力学仿真模型。
2.  **`swp.local_agents`**:
    - **本地代理与控制**: 包括感知代理（数字孪生）和本地控制模块（实现如PID、MPC等算法）。
3.  **`swp.central_coordination`**:
    - **中央协调与调度**: 包含中央调度“大脑”和多代理协作库（例如，消息总线）。
4.  **`swp.core_engine`**:
    - **核心平台引擎**: “母体机器”本身。包含代理工厂、生命周期管理器和在环测试平台。

一个中心的 `swp.core` 包定义了确保所有组件“可插拔”的抽象接口。

## 示例 (Examples)

本项目包含一系列配置驱动的示例，展示了平台从基础组件到复杂系统的各项功能。所有示例都位于 `/examples` 目录中。

### 运行示例的方法

所有示例都通过一个运行器脚本和一个JSON配置文件来执行。您可以通过修改JSON文件来调整仿真的参数、拓扑结构或场景。

例如，要运行一个示例，请使用以下命令格式：
```bash
python3 examples/<runner_script_name>.py examples/<mission_config_name>.json
```

---

### 1. 智能体与控制系统示例

这些示例使用 `run_harness_from_config.py` 运行器，展示了基于多智能体系统（MAS）的监控和控制应用。

- **引绰济辽工程全系统仿真 (Yin Chuo Ji Liao Project Simulation)**
  - **配置**: [`mission_yinchuojiliao.json`](./examples/mission_yinchuojiliao.json)
  - **命令**: `python3 examples/run_harness_from_config.py examples/mission_yinchuojiliao.json`

- **分层分布式控制 (Hierarchical Control)**
  - **描述**: 演示一个由中央MPC智能体和本地PID智能体组成的多层控制系统，以应对预报的洪水事件。
  - **配置**: [`mission_2_2_hierarchical_control.json`](./examples/mission_2_2_hierarchical_control.json)
  - **命令**: `python3 examples/run_harness_from_config.py examples/mission_2_2_hierarchical_control.json`

- **流域联合调度 (Joint Watershed Dispatch)**
  - **描述**: 演示一个基于规则的中央调度器，用于协调水电站和下游用户以应对洪水。
  - **配置**: [`mission_2_3_joint_dispatch.json`](./examples/mission_2_3_joint_dispatch.json)
  - **命令**: `python3 examples/run_harness_from_config.py examples/mission_2_3_joint_dispatch.json`

- **多机协调与电网交互 (Multi-Turbine Coordination)**
  - **描述**: 演示一个本地控制智能体如何协调6台水轮机以满足发电目标，并响应电网的限制事件。
  - **配置**: [`mission_5_2_multi_turbine_grid.json`](./examples/mission_5_2_multi_turbine_grid.json)
  - **命令**: `python3 examples/run_harness_from_config.py examples/mission_5_2_multi_turbine_grid.json`

- **现地闭环控制 (Local Closed-Loop Control)**
  - **描述**: 一个完整的本地PID闭环控制系统，用于将渠池水位稳定在设定点。
  - **配置**: [`mission_2_1_local_closed_loop.json`](./examples/mission_2_1_local_closed_loop.json)
  - **命令**: `python3 examples/run_harness_from_config.py examples/mission_2_1_local_closed_loop.json`

---

### 2. 独立智能体功能示例

这些示例使用 `run_mission_from_config.py` 运行器（一个简化的、手动步进的仿真器），用于独立测试单个智能体的行为。

- **中央MPC调度智能体 (Central MPC Agent)**
  - **配置**: [`mission_1_5_central_dispatcher.json`](./examples/mission_1_5_central_dispatcher.json)
  - **命令**: `python3 examples/run_mission_from_config.py examples/mission_1_5_central_dispatcher.json`

- **数字孪生智能体 (Digital Twin Agent)**
  - **配置**: [`mission_1_4_digital_twin_agent.json`](./examples/mission_1_4_digital_twin_agent.json)
  - **命令**: `python3 examples/run_mission_from_config.py examples/mission_1_4_digital_twin_agent.json`

- **闸站控制智能体 (Gate Control Agent)**
  - **配置**: [`mission_1_3_gate_control_agent.json`](./examples/mission_1_3_gate_control_agent.json)
  - **命令**: `python3 examples/run_mission_from_config.py examples/mission_1_3_gate_control_agent.json`

- **传感器与执行器仿真智能体 (Physical I/O Agent)**
  - **配置**: [`mission_1_2_physical_io_agent.json`](./examples/mission_1_2_physical_io_agent.json)
  - **命令**: `python3 examples/run_mission_from_config.py examples/mission_1_2_physical_io_agent.json`

---

### 3. 物理模型与数据生成示例

#### 物理网络仿真

这个示例使用 `run_network_solver_from_config.py` 运行器，展示了基于 `NetworkSolver` 的纯物理网络仿真。

- **水轮机与闸门的物理行为 (Turbine & Gate Physics)**
  - **描述**: 演示水轮机和闸门在尾水水位抬高（顶托）影响下的物理行为。
  - **配置**: [`mission_5_1_turbine_gate.json`](./examples/mission_5_1_turbine_gate.json)
  - **命令**: `python3 examples/run_network_solver_from_config.py examples/mission_5_1_turbine_gate.json`

#### 数据表生成

这些脚本用于生成可供控制智能体使用的查找表（Lookup Tables）。

- **水轮机经济调度表 (Turbine Economic Dispatch Table)**
  - **描述**: 通过优化计算，生成在不同工况下6台不同特性的水轮机的最优功率分配方案。
  - **配置**: [`mission_5_3_compute_turbine_table.json`](./examples/mission_5_3_compute_turbine_table.json)
  - **命令**: `python3 examples/run_table_computation.py examples/mission_5_3_compute_turbine_table.json`

- **闸门流量分配表 (Gate Flow Allocation Table)**
  - **描述**: 根据一系列运行规则，计算5个溢洪道闸门在不同工況下的联合开启方式。
  - **配置**: [`mission_5_4_compute_gate_table.json`](./examples/mission_5_4_compute_gate_table.json)
  - **命令**: `python3 examples/run_table_computation.py examples/mission_5_4_compute_gate_table.json`
