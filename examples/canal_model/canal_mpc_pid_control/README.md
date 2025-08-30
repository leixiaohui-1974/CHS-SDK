# 渠道系统MIMO MPC + PID 级联控制示例

本示例实现了一个**多输入多输出（MIMO）**的MPC控制器，用于对整个渠道系统进行全局优化和协调控制。

## 系统描述

系统拓扑结构包含扰动节点，核心目的是在存在多种扰动的情况下，精确、稳定地控制`canal_1`的水位。

`reservoir` -> `diversion_1` -> `gate_1` -> `canal_1` -> `diversion_2` -> `gate_2` -> `tail_user`

## 控制架构：MPC-PID级联控制

本示例采用了一种先进的**级联控制（Cascaded Control）**架构。

1.  **外环：中央MIMO MPC控制器 (`central_mpc_agent`)**
    -   **角色**: 战略决策层。
    -   **目标**: 维持`canal_1`的水位在理想的目标值。
    -   **控制变量**: 计算通过`gate_1`和`gate_2`的**最优流量**（`q1`和`q2`）。
    -   **输出**: 计算出的最优流量作为**设定点**，发送给内环的PID控制器。

2.  **内环：现地PID流量控制器 (`gate_1_flow_pid_agent`, `gate_2_flow_pid_agent`)**
    -   **角色**: 战术执行层。
    -   **目标**: 精确执行MPC下发的**流量指令**。
    -   **工作原理**: 接收来自MPC的流量设定点, 比较闸门的“实际流量”与“目标流量”，并自动调整闸门开度。

## 感知与扰动

- **感知**: 为`gate_1`和`gate_2`新增了`DigitalTwinAgent`，专门用于发布它们各自的实时状态（包括`outflow`），供PID控制器观测。
- **扰动**: 系统扰动由一个中央的`ScenarioAgent`统一管理，它在`agents.yml`中根据预设的脚本，在特定时间注入流量扰动。

## 如何运行

```bash
python run_scenario.py examples/canal_model/canal_mpc_pid_control
```

## 预期结果
脚本将执行模拟，并将所有组件和智能体的详细历史记录保存到 `output.yml` 文件中。
