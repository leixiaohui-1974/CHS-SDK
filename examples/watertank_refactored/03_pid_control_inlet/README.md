## 03 - PID入口控制 (PID Inlet Control)

### 问题描述 (Problem Description)

本案例在“简单开环仿真”的基础上，引入了反馈控制。目标是设计一个PID控制器，通过调节水库的入口流量，使得水库水位能够稳定在预设的目标值（10.0米），即使用户侧的需水量（作为一种外部扰动）在仿真过程中发生变化。

这是水务系统中最经典的控制问题之一，旨在检验PID控制智能体的基本性能和系统在闭环控制下的动态响应。

### 实现思路 (Implementation)

该场景的实现依赖于多个智能体之间的协作，通过消息总线进行通信。

*   **物理拓扑 (topology.yml):**
    此案例中依然只有一个独立的 `Reservoir` (水库) 组件，没有物理连接。其入口流量完全由智能体通过消息总线控制。

*   **智能体配置 (agents.yml):**
    1.  `DigitalTwinAgent`: 作为“感知”智能体，负责读取水库的物理状态（尤其是 `water_level`），并将其发布到 `tank_water_level_topic` 主题上。
    2.  `CsvInflowAgent`: 作为“扰动”智能体，从 `disturbance.csv` 文件中读取一个变化的、代表负流量（即出水）的时间序列，并将其发布到 `disturbance_signal_topic`。
    3.  `LocalControlAgent`: 这是PID控制的核心。它内部封装了一个 `PIDController` 实例。该智能体订阅 `tank_water_level_topic` 来获取当前水位，将其与设定的目标值（10.0米）进行比较，然后计算出所需的控制动作（入口流量），并发布到 `control_signal_topic`。
    4.  `SignalAggregatorAgent`: 该智能体订阅PID控制器的输出 (`control_signal_topic`) 和扰动信号 (`disturbance_signal_topic`)，将两者相加得到净入口流量，并发布到水库订阅的 `aggregated_inflow_topic`。
    5.  `TopicLoggerAgent`: 我们额外配置了两个该类型的智能体，用于专门记录 `control_signal_topic` 和 `disturbance_signal_topic` 上的消息，以便后续进行可视化分析。

### 关键技术 (Key Technologies)

*   **`PIDController`**: 经典的比例-积分-微分控制器，是实现反馈控制的基础。
*   **`LocalControlAgent`**: 将通用的控制算法（如PID）封装为标准化的智能体，处理了消息订阅和发布的细节，使得控制器本身可以专注于核心算法。
*   **`SignalAggregatorAgent`**: 一个实用的工具型智能体，展示了如何将多个独立的控制或扰动信号组合成一个对物理组件的最终输入。
*   **`TopicLoggerAgent`**: 一个我们为便于分析而新增的调试工具，展示了如何通过订阅消息总线上的任意主题来记录和捕获系统内部的中间数据。

### 仿真结果与分析 (Simulation Results & Analysis)

#### 动态过程展示 (Dynamic Process)
![Simulation Results](simulation_results.gif)

#### 关键指标总结 (Key Performance Indicators)
| 指标 (Metric) | 数值 (Value) |
|---|---|
| 水库最高水位 (m) | 12.00 |
| 水库最低水位 (m) | 8.95 |
| 水库平均水位 (m) | 9.95 |
| 水位控制均方根误差 (RMSE) | 0.2708 |

#### 结果分析与讨论 (Analysis & Discussion)
从动图和指标可以看出PID控制器的有效性：
1.  **水位控制 (上图)**: 仿真开始时，水位为5.0米，远低于10.0米的目标值。PID控制器迅速响应，将入口流量（绿线）开到最大（5.0 m³/s）以快速提升水位。水位在约20秒时出现超调，达到了12.0米的峰值。之后，控制器逐渐减小入口流量，使水位最终在 `t=100s` 左右稳定在目标值10.0米附近。
2.  **扰动响应 (下图)**: 在 `t=50s` 和 `t=200s` 时，系统受到了两次出流量扰动（紫线）。从图中可以看出，每次扰动发生后，水位都会出现偏离，但PID控制器都能在几十秒内调整入口流量，有效地抑制扰动，将水位重新拉回到目标值附近。

总体而言，当前PID参数（Kp=1.2, Ki=0.1, Kd=0.05）能够实现有效控制，但响应略带振荡且超调较大。

### 建议与展望 (Suggestions & Outlook)

*   **PID参数整定**: 当前的P、I、D参数是手动设置的，存在优化空间。可以尝试使用Ziegler-Nichols等经典的整定方法，或通过实验来寻找一组能实现更快响应、更小超调的参数组合。
*   **增加物理约束**: 当前仿真没有考虑入口水泵的物理约束（如功率限制、响应延迟）。在更真实的仿真中，需要将这些因素建模，并测试控制器在存在执行器约束时的性能。
*   **对比其他控制器**: 可以在此场景基础上，替换PID控制器为更先进的控制算法（如MPC模型预测控制），并比较不同控制器在响应速度、稳定性和抗扰动能力上的差异。
