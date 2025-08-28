# 案例说明：多闸门河流 PID 控制

## 1. 案例概述

本案例模拟了一个带有反馈控制的河流系统。该系统由一个上游水库、一个中间河道以及两个分别位于水库下游和河道下游的闸门组成。两个闸门均由独立的PID控制器进行自动控制。

这个案例的主要目的是：
- 演示如何在一个仿真案例中配置和使用控制器（`Controller`）。
- 展示如何通过`config.json`文件定义控制器参数及其“接线”（即控制器观测哪个组件的哪个状态，并控制另一个组件）。
- 验证`SimulationHarness`仿真器对闭环控制系统的支持能力。

## 2. 拓扑结构与控制逻辑

**物理拓扑**:
`Reservoir -> Gate1 -> RiverChannel -> Gate2`

**控制逻辑**:
1.  **控制器1 (`res_level_ctrl`)**:
    - **目标**: 维持上游水库 (`reservoir_1`) 的水位在一个期望的目标值（`setpoint: 18.0`）。
    - **观测**: `reservoir_1` 的 `water_level`（水位）状态。
    - **控制**: `gate_1` 的开度。当水位低于目标值时，关小闸门；当水位高于目标值时，开大闸门。

2.  **控制器2 (`chan_vol_ctrl`)**:
    - **目标**: 维持中间河道 (`channel_1`) 的蓄水量在一个期望的目标值（`setpoint: 400000`）。
    - **观测**: `channel_1` 的 `volume`（蓄水量）状态。
    - **控制**: `gate_2` 的开度。这是一个负向控制，当蓄水量高于目标时，开大下游闸门以泄水。

## 3. 配置文件 (`config.json`) 说明

本案例的`config.json`在之前的案例基础上，新增了`controllers`部分。

- **`metadata`**, **`simulation_settings`**, **`components`**, **`connections`**: 与其他案例结构相同。
- **`controllers`**: 一个列表，定义了所有控制器。
  - `id`: 控制器的唯一标识符。
  - `type`: 控制器的类型，必须与`run_simulation.py`中`CONTROLLER_CLASS_MAP`字典里的键名相匹配（例如`PIDController`）。
  - `params`: 初始化该控制器所需的所有参数，如`Kp`, `Ki`, `Kd`和`setpoint`等。
  - `wiring`: 定义了控制器的连接方式。
    - `controlled_id`: 被该控制器所操作的组件ID。
    - `observed_id`: 为控制器提供反馈信号的组件ID。
    - `observation_key`: 所观测的状态变量的名称。

## 4. 如何运行

可以直接通过Python运行本目录下的`run_simulation.py`脚本：

```bash
python examples/multi_gate_river/run_simulation.py
```

脚本会自动加载并解析`config.json`，包括其中的控制器配置，然后运行仿真。结束后，详细的仿真结果将被保存在同目录的`output.json`文件中。
