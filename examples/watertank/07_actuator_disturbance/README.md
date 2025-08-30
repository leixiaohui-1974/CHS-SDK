# 案例七：执行器扰动下的控制

## 1. 案例目标

本案例旨在演示在**控制执行器不精确**的情况下，PID控制器的性能表现。在真实世界中，执行器（如水泵、阀门）可能因为机械磨损、电压不稳或校准问题，导致其无法完美执行上层控制器发出的指令。例如，指令要求水泵提供2.0 m³/s的流量，但它实际可能只提供了1.9 m³/s。

本案例将模拟这种执行器层面的**系统性偏差（bias）**和**随机噪声（noise）**，并观察其对水箱水位控制稳定性的影响。

## 2. 架构设计

本案例的架构与案例三（进水PID控制）非常相似，核心区别在于物理对象本身：

- **带噪声执行器的物理对象 (`NoisyActuatorReservoir`)**: 这是本案例的关键。它继承自标准的`Reservoir`类，但重写了`set_inflow`方法。当这个方法被调用时，它不会直接使用传入的`commanded_inflow`，而是会先对其进行处理（例如 `actual_inflow = commanded_inflow * bias + noise`），然后再将这个“不精确”的流量作为真实的物理入流。
- **感知智能体 (`DigitalTwinAgent`)**: 在这个例子中，我们假设传感器是完美的。它直接读取并发布由`NoisyActuatorReservoir`产生的真实水位。
- **控制智能体 (`LocalControlAgent`)**: 它基于完美的水位读数进行决策，但它发出的控制指令在物理层面没有被完美执行。
- **主程序 (`main.py`)**: 负责组装和运行整个系统。为了进行对比，它会同时记录**指令流量**和由物理对象反馈的**实际流量**。

通过对比日志中的`commanded_inflow`和`actual_inflow`，可以清晰地看到执行器扰动是如何影响系统状态并导致控制误差的。

## 3. 文件结构

- `main.py`: 仿真的主入口。
- `noisy_actuator_reservoir.py`: 定义了`NoisyActuatorReservoir`，它在标准`Reservoir`的基础上增加了执行器噪声。
- `config.json`: 配置文件，增加了`actuator_noise_params`部分，用于定义执行器噪声的偏差和标准差。
- `README.md`: 本说明文档。

## 4. 如何运行

在 `07_actuator_disturbance` 目录下，直接运行主程序：

```bash
python main.py
```

仿真结束后，结果将保存在 `examples/watertank/logs/07_actuator_disturbance/actuator_disturbance_log.csv` 文件中。
