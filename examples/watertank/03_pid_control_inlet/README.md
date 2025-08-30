# 案例三：通过PID控制进水实现水位稳定

## 1. 案例目标

本案例旨在演示一个经典的水位控制问题。在一个水箱的出水流量（`Q_out`）存在外部扰动的情况下，我们如何通过控制进水水泵的流量（`Q_in`）来将水位稳定在我们期望的目标值（Setpoint）。

这个场景由两个核心智能体协作完成：
- **水泵智能体 (Pump Agent)**: 这是一个**控制器**智能体。它内部集成了一个PID控制器。它的任务是实时监测水位，并根据当前水位与目标水位的偏差，计算出需要向水箱中注入的精确流量。
- **水库孪生智能体 (WaterTank Twin Agent)**: 这是一个**被控对象**智能体。它模拟水箱的物理行为。它接收来自水泵智能体的进水，并同时承受一个预定义的、随时间变化的出水流量扰动。

## 2. 文件结构

- `main.py`: 控制仿真的主入口程序。它负责初始化水泵和水箱智能体，并编排它们之间的交互。
- `pump_agent.py`: 定义了 `PumpAgent` 类，封装了PID控制器和控制逻辑。
- `watertank_twin_agent.py`: 定义了 `WaterTankTwinAgent` 类，模拟被控制的水箱。
- `config.json`: 配置文件。在这里可以设置水箱的物理参数、PID控制器的增益（Kp, Ki, Kd）、目标水位、仿真时长以及最重要的——出水扰动模式。
- `README.md`: 本说明文档。

## 3. 控制原理

这是一个典型的反馈控制系统：

1.  **测量 (Measure)**: `PumpAgent` 测量 `WaterTankTwinAgent` 的当前水位 `h`。
2.  **比较 (Compare)**: `PumpAgent` 将当前水位 `h` 与目标水位 `h_setpoint` 进行比较，计算出误差 `error = h_setpoint - h`。
3.  **计算 (Compute)**: PID控制器根据误差 `error` 计算出控制信号，即进水流量 `Q_in`。
    -   **P (比例)**: 误差越大，控制作用越强。
    -   **I (积分)**: 消除系统的稳态误差，确保长时间稳定。
    -   **D (微分)**: 预测误差的变化趋势，防止超调和振荡。
4.  **执行 (Actuate)**: `PumpAgent` 输出的 `Q_in` 被施加到 `WaterTankTwinAgent`上。
5.  **扰动 (Disturbance)**: 与此同时，`WaterTankTwinAgent` 受到一个独立的、不确定的出水流量 `Q_out_disturbance` 的影响。
6.  **循环**: 水位在 `Q_in` 和 `Q_out_disturbance` 的共同作用下发生变化，`PumpAgent` 在下一个时间步测量到新的水位，开始新一轮的控制循环。

最终，一个性能良好的PID控制器能够快速、准确地抵消出水扰动带来的影响，使水位始终保持在目标值附近。

## 4. 如何运行

1.  在 `03_pid_control_inlet` 目录下，直接运行主程序：

    ```bash
    python main.py
    ```

2.  程序会打印仿真开始和结束的信息。
3.  仿真结果保存在 `examples/watertank/logs/03_pid_control_inlet/pid_control_log.csv` 文件中。你可以通过绘图软件（如Excel, Python Matplotlib）打开此文件，将 `time`, `setpoint`, `water_level` 这三列数据可视化，直观地看到水位是如何跟随设定值变化的，以及控制器是如何抵抗扰动的。

## 5. 如何配置

通过修改 `config.json` 文件来调整控制系统：

- `pid_params`:
  - `setpoint`: 改变你想要控制的目标水位。
  - `kp`, `ki`, `kd`: **这是PID控制的核心**。调整这三个增益参数，观察控制效果的变化。例如，增大 `kp` 会加快响应速度，但可能导致超调；引入 `ki` 可以消除静差；`kd` 则能改善系统的动态性能。
  - `output_limits`: 限制水泵的最大和最小流量。
- `disturbance_params`:
  - `outflow_pattern`: 设计不同的、更具挑战性的扰动模式，测试PID控制器的鲁棒性。
