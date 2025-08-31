## 01 - 简单开环仿真 (Simple Open-Loop Simulation)

### 问题描述 (Problem Description)

本案例旨在模拟一个最基础的水库系统。在此场景中，我们为一个具有初始水量的水库提供一个持续、恒定的入流量，并观察在没有出流控制的情况下，水库水位随时间如何自然演变。这是一个典型的开环仿真，用于验证核心物理模型的正确性并为后续更复杂的控制场景提供基线。

### 实现思路 (Implementation)

该场景通过三个核心配置文件搭建：`components.yml` 定义物理实体，`topology.yml` 定义连接关系（在本例中为空），`agents.yml` 定义驱动仿真的智能体。

*   **物理拓扑 (topology.yml):**
    此案例中只有一个独立的 `Reservoir` (水库) 组件，因此 `topology.yml` 文件为空，没有组件间的连接。

*   **物理组件 (components.yml):**
    ```yaml
    components:
      - id: reservoir_1
        class: core_lib.physical_objects.reservoir.Reservoir
        inflow_topic: inflow_topic
        name: "simple_tank"
        initial_state:
          water_level: 2.0
        parameters:
          surface_area: 10.0
    ```
    该文件定义了一个名为 `simple_tank` 的水库，设定了其初始水位为2.0米，水库表面积为10.0平方米。

*   **智能体配置 (agents.yml):**
    ```yaml
    agents:
      - id: inflow_agent_1
        class: core_lib.data_access.csv_inflow_agent.CsvInflowAgent
        config:
          csv_file: inflow.csv
          time_column: time
          data_column: inflow_rate
          inflow_topic: inflow_topic
          data_id: inflow_1
    ```
    配置了一个 `CsvInflowAgent`，其职责是从 `inflow.csv` 文件中读取预定义的流量数据，并将其发布到 `inflow_topic` 主题上。水库组件 (`reservoir_1`) 订阅了此主题，从而接收到入流量。

### 关键技术 (Key Technologies)

本案例重点展示了CHS-SDK中的几个核心类：

*   **`Reservoir`**: 核心的水库物理模型，能够根据输入流量和自身参数（如表面积）计算水位的变化。
*   **`CsvInflowAgent`**: 一个数据驱动的智能体，用于将外部时间序列数据（如历史流量）注入仿真环境中，是连接真实世界数据与仿真的桥梁。
*   **`SimulationHarness`**: 整个仿真的运行器，负责根据配置加载组件和智能体，并按时间步推进仿真。

### 仿真结果与分析 (Simulation Results & Analysis)

#### 动态过程展示 (Dynamic Process)
![Simulation Results](simulation_results.gif)

#### 关键指标总结 (Key Performance Indicators)
| 指标 (Metric) | 数值 (Value) |
|---|---|
| 水库最高水位 (m) | 32.00 |
| 水库最低水位 (m) | 2.15 |
| 水库平均水位 (m) | 17.08 |
| 总供水量 (m³) | 300.00 |
| 总耗电量 (kWh) | N/A |
| 水位控制均方根误差 (RMSE) | N/A |

#### 结果分析与讨论 (Analysis & Discussion)
从上面的动态图和关键指标可以看出，仿真开始后，由于 `CsvInflowAgent` 持续提供1.5 m³/s的恒定入流，而水库没有设置任何出流，水库水位从初始的2.0米开始稳定线性上升。在200秒的仿真时长内，水位最终达到了32.0米。总供水量为 300 m³ (1.5 m³/s * 200 s)，与仿真结果完全一致。

该结果符合物理预期，验证了 `Reservoir` 模型和 `CsvInflowAgent` 的基本功能是正确可靠的。

### 建议与展望 (Suggestions & Outlook)

这个简单的开环系统为我们提供了一个理想的起点。基于此案例，可以进行以下扩展实验：

*   **增加出流**: 可以为水库模型增加一个出口，例如连接一个 `Valve` (阀门) 或 `Pipe` (管道) 组件，观察在有出流情况下的水位变化。
*   **引入控制**: 在具备出流或可控入流（如 `Pump`）的基础上，可以引入PID控制器，尝试将水库水位维持在一个目标水平，搭建一个闭环控制系统。
*   **改变入流模式**: 可以修改 `inflow.csv` 文件，使用变化的、更接近真实场景的入流数据，观察系统的动态响应。
