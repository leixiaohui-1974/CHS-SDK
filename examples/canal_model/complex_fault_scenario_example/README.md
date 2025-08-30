# 复杂故障场景示例

本示例旨在模拟一个包含传感器、执行器故障以及各种水力条件变化的复杂运河系统。我们引入了 `physicalio` 和 `scenario` 智能体来管理这些动态事件，并测试PID控制算法在这些干扰下的鲁棒性。

## 系统描述

该系统在 `structured_control_example` 的基础上进行了扩展，主要增加了沿线分水口和故障模拟功能。

- **拓扑结构**: `水库 -> 分水口1 -> 闸门1 -> 渠道1 -> 分水口2 -> 闸门2 -> 渠道2 -> 终端用户`
- **物理组件**:
    - `upstream_reservoir`: 上游水库
    - `gate_1`, `gate_2`: 两个控制闸门
    - `canal_1`, `canal_2`: 两个渠道段
    - `turnout_1`, `turnout_2`: 两个分水口，用于模拟沿线用水
    - `terminal_user`: 渠道末端的集中用水户

## 核心功能

1.  **`PhysicalIOAgent`**:
    - 模拟传感器（如水位计）和执行器（如闸门控制器）的物理特性。
    - 可配置传感器噪声、执行器延迟或完全故障，以模拟真实世界的硬件问题。

2.  **`ScenarioAgent`**:
    - 根据预定义的脚本（`event_scenario.yml`）动态改变模拟条件。
    - 能够模拟以下类型的故障和事件：
        - **来水变化**: `upstream_reservoir` 的入流突然增加或减少。
        - **分水口用水**: `turnout_1` 和 `turnout_2` 的流量需求变化。
        - **末端用户用水**: `terminal_user` 的流量需求变化。
        - **传感器故障**: 模拟水位计读数错误或完全失效。
        - **执行器故障**: 模拟闸门卡住或响应迟钝。

3.  **`StructuredControlAgent` (PID控制器)**:
    - 与 `structured_control_example` 类似，我们使用PID控制器来自动调节闸门。
    - 本示例的目的是测试PID控制器在上述多种故障和干扰下的适应性和稳定性。

## 如何运行示例

请从代码库的根目录执行以下命令：

```bash
python run_scenario.py examples/canal_model/complex_fault_scenario_example/
```

## 预期结果

模拟运行后，将在 `examples/canal_model/complex_fault_scenario_example/` 目录下生成一个 `output.yml` 文件。您可以分析此文件，观察在各种故障条件下，系统的水位、流量和闸门开度等是如何响应的，从而评估PID控制算法的效果。
