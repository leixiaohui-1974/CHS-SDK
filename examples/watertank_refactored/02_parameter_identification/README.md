# 示例 2: 阀门流量系数辨识 (标准库版)

## 1. 场景目标

本示例旨在演示如何使用本仿真框架的**标准参数辨识智能体** (`ParameterIdentificationAgent`)，在线辨识一个**标准物理组件** (`Valve`) 的内部参数。

具体来说，我们想要辨识出水阀的 **`discharge_coefficient` (流量系数)**。这是一个关键的物理参数，决定了在一定的水头差和开度下，阀门的过流能力。

## 2. 架构设计 (核心库增强)

根据用户的指示，本场景的实现依赖于对核心库 (`core_lib`) 的两项重要增强：
1.  为 `core_lib/physical_objects/valve.py` 中的 `Valve` 类增加了参数辨识能力。
2.  改进了 `core_lib/identification/identification_agent.py` 中的 `ParameterIdentificationAgent`，使其能够从复杂消息中提取数据。

基于此，本场景的架构非常标准和清晰：

### 物理系统 (`components.yml` & `topology.yml`)
我们搭建了两套并行的“水库->阀门”系统：
-   **真实系统**: `real_reservoir` -> `real_valve`。其中 `real_valve` 的流量系数被设为我们想要辨识的“真实值”（如 0.8）。
-   **孪生系统**: `twin_reservoir` -> `twin_valve`。其中 `twin_valve` 的流量系数被设为一个错误的“初始猜测值”（如 0.2）。

### 智能体 (`agents.yml`)

1.  **数据输入智能体**:
    -   `CsvInflowAgent`: 为两个水库提供完全相同的入流，保证了输入条件的一致性。
    -   `ConstantValueAgent`: 提供一个恒为0的下游水位，作为阀门出流计算的基准。

2.  **感知智能体 (`DigitalTwinAgent`)**:
    -   我们用了三个独立的感知智能体，分别用于发布“真实阀门”的状态（观测流量）、“孪生阀门”的状态（开度）和“孪生水库”的状态（上游水位）。

3.  **辨识智能体 (`ParameterIdentificationAgent`)**:
    -   **核心**: 这是本场景的大脑。
    -   **目标**: 它的辨识目标被配置为 `twin_valve` 组件。
    -   **数据**: 它订阅上述所有感知智能体发布的主题，以收集辨识所需的所有数据（观测流量、开度、上下游水位）。
    -   **动作**: 每隔50个时间步，它会调用 `twin_valve` 自身新增的 `identify_parameters` 方法，来更新其内部的 `discharge_coefficient` 参数。

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/02_parameter_identification
```

## 4. 预期结果

仿真结束后，`twin_valve` 组件的 `discharge_coefficient` 参数会从初始的 0.2 逐步收敛到 `real_valve` 的真实值 0.8。您可以通过以下方式验证：
-   检查仿真过程中打印的日志，其中会包含类似 `Identification complete. New discharge_coefficient: 0.xxx` 的信息。
-   分析 `output.yml` 文件中 `twin_valve_state_topic` 的数据，查看其 `discharge_coefficient` 随时间的变化。
