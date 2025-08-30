# 案例四：通过PID控制出水实现水位稳定

## 1. 案例目标

本案例与案例三互为镜像，旨在演示另一种常见的水位控制策略。在一个水箱的**进水流量（`Q_in`）** 存在外部扰动的情况下，我们通过控制**出水阀门的流量（`Q_out`）** 来将水位稳定在期望的目标值（Setpoint）。

此场景同样由两个核心智能体协作完成：
- **阀门智能体 (Valve Agent)**: 这是一个**控制器**智能体，内部集成PID控制器。它的任务是监测水位，并根据水位与目标值的偏差，计算出需要从水箱中排出的精确流量。
- **水库孪生智能体 (WaterTank Twin Agent)**: 这是**被控对象**智能体，模拟水箱。它接收来自外部的、不确定的进水流量扰动，同时其出水量由阀门智能体精确控制。

## 2. 文件结构

- `main.py`: 控制仿真的主入口程序。
- `valve_agent.py`: 定义了 `ValveAgent` 类，封装了PID控制器和相应的控制逻辑。
- `watertank_twin_agent.py`: 定义了 `WaterTankTwinAgent` 类，模拟被控制的水箱。
- `config.json`: 配置文件。可设置水箱参数、PID增益、目标水位、以及**进水扰动模式**。
- `README.md`: 本说明文档。

## 3. 控制原理

控制逻辑与案例三类似，但作用方向相反：

1.  **测量 (Measure)**: `ValveAgent` 测量 `WaterTankTwinAgent` 的当前水位 `h`。
2.  **比较 (Compare)**: `ValveAgent` 将当前水位 `h` 与目标水位 `h_setpoint` 进行比较。
3.  **计算 (Compute)**: PID控制器根据误差计算出控制信号，即出水流量 `Q_out`。这里的关键在于误差的定义：
    -   为了实现正确的控制方向，我们定义的误差是 `error = h - h_setpoint`。
    -   当水位**高于**目标 (`h > h_setpoint`)，`error` 为正，PID输出一个**正的** `Q_out`，增加排水。
    -   当水位**低于**目标 (`h < h_setpoint`)，`error` 为负，PID输出一个**接近零的** `Q_out`（受输出下限限制），减少排水。
4.  **执行 (Actuate)**: `ValveAgent` 输出的 `Q_out` 被施加到 `WaterTankTwinAgent`上。
5.  **扰动 (Disturbance)**: 与此同时，`WaterTankTwinAgent` 受到一个独立的进水流量 `Q_in_disturbance` 的影响。
6.  **循环**: 水位在 `Q_in_disturbance` 和 `Q_out` 的共同作用下发生变化，开启新一轮的控制循环。

最终，`ValveAgent` 能够有效抵消不确定的进水扰动，将水位维持在目标值。

## 4. 如何运行

1.  在 `04_pid_control_outlet` 目录下，直接运行主程序：

    ```bash
    python main.py
    ```

2.  程序会打印仿真开始和结束的信息。
3.  仿真结果保存在 `examples/watertank/logs/04_pid_control_outlet/pid_control_log.csv` 文件中。同样，你可以通过可视化 `time`, `setpoint`, `water_level` 列来观察控制效果。

## 5. 如何配置

通过修改 `config.json` 文件来调整控制系统：

- `pid_params`:
  - `setpoint`: 设定目标水位。
  - `kp`, `ki`, `kd`: 调整PID增益以优化控制性能。可以尝试从一个较高的初始水位（如 `initial_level: 12.0`）控制到一个较低的目标水位（如 `setpoint: 10.0`），观察系统的响应。
  - `output_limits`: 限制阀门的最大和最小排水流量。
- `disturbance_params`:
  - `inflow_pattern`: 设计不同的进水扰动模式，测试阀门控制器的性能。
