# 案例一：基础水箱仿真

## 1. 案例目标

本案例旨在演示一个基础的水箱物理仿真过程。我们使用一个**本体仿真智能体（Ontology Simulation Agent）** 来模拟水箱的动态行为。该智能体的核心是水箱的数学模型，它根据输入的流量来计算水位的变化。

## 2. 文件结构

- `main.py`: 仿真的主入口程序。它负责加载配置、初始化智能体和数据记录器，并执行仿真循环。
- `ontology_agent.py`: 定义了 `OntologySimulationAgent` 类，该类封装了水箱的物理模型。
- `config.json`: 配置文件，用于定义水箱的物理参数（如横截面积、出口系数）、仿真参数（如时长、步长）以及日志记录设置。
- `README.md`: 本说明文档。

## 3. 模型原理

水箱模型基于质量守恒定律：

```
dV/dt = Q_in - Q_out
```

其中：
- `V` 是水箱中的水量
- `t` 是时间
- `Q_in` 是进水流量
- `Q_out` 是出水流量

水位 `h` 的变化率可以表示为：

```
dh/dt = (Q_in - Q_out) / A
```

其中 `A` 是水箱的横截面积。

出水流量 `Q_out` 根据托里拆利定律计算，与水位的平方根成正比：

```
Q_out = k * sqrt(h)
```

其中 `k` 是出口系数，它综合了出口面积、重力加速度等因素。

## 4. 如何运行

1. 确保已安装所需的库（如 `numpy`）。
2. 在 `01_simulation` 目录下，直接运行主程序：

   ```bash
   python main.py
   ```

3. 仿真开始后，程序会打印启动和结束信息。
4. 仿真结束后，结果将保存在 `examples/watertank/logs/01_simulation/simulation_log.csv` 文件中。该文件记录了每个时间步的水位、进水流量和出水流量。

## 5. 如何配置

你可以通过修改 `config.json` 文件来调整仿真参数：

- `tank_params`: 设置水箱的物理属性。
  - `area`: 水箱横截面积 (m²)。
  - `initial_level`: 初始水位 (m)。
  - `outlet_coeff`: 出口流量系数。
- `simulation_params`: 设置仿真的运行参数。
  - `total_time`: 仿真总时长 (s)。
  - `time_step`: 每个仿真步的时间间隔 (s)。
  - `inflow_rate`: 恒定的进水流量 (m³/s)。
- `logging_params`: 设置数据记录。
  - `log_dir`: 日志文件存放的目录。
  - `log_file`: 日志文件的名称。
  - `log_headers`: CSV 文件中的列标题。
