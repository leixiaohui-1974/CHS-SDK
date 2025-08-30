# 案例六：传感器扰动下的控制

## 1. 案例目标

本案例旨在演示在**传感器测量不精确**的情况下，PID控制器的性能表现。在真实世界中，传感器（如水位计）的读数总会包含一定的随机噪声。本案例将模拟这种噪声，并观察其对水箱水位控制稳定性的影响。

## 2. 架构设计

本案例的架构基于案例三（进水PID控制），核心区别在于感知智能体：

- **物理对象 (`Reservoir`)**: 同样用于模拟水箱的真实物理过程。
- **带噪声的感知智能体 (`NoisyDigitalTwinAgent`)**: 这是本案例的关键。它继承自`DigitalTwinAgent`，但在发布状态到消息总线之前，它会为真实的“水位”数据叠加上一个可配置的**高斯白噪声**。
- **控制智能体 (`LocalControlAgent`)**: 它接收的是带有噪声的水位数据，并基于这些不精确的信息进行PID计算和决策。
- **主程序 (`main.py`)**: 负责组装和运行整个系统。为了进行对比，它会同时记录**真实水位**和带噪声的**观测水位**。

通过对比日志中的`true_water_level`和`noisy_water_level`，以及观察`inflow_control`的波动，可以清晰地看到传感器噪声是如何影响控制过程的。

## 3. 文件结构

- `main.py`: 仿真的主入口。
- `noisy_digital_twin_agent.py`: 定义了`NoisyDigitalTwinAgent`，它在标准数字孪生的基础上增加了噪声注入功能。
- `config.json`: 配置文件，除了案例三的参数外，还增加了`noise_params`部分，用于定义噪声的均值和标准差。
- `README.md`: 本说明文档。

## 4. 如何运行

在 `06_sensor_disturbance` 目录下，直接运行主程序：

```bash
python main.py
```

仿真结束后，结果将保存在 `examples/watertank/logs/06_sensor_disturbance/sensor_disturbance_log.csv` 文件中。通过绘制该文件中的数据，可以直观地分析噪声对控制效果的影响。
