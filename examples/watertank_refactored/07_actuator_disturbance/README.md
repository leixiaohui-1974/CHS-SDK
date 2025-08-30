# 示例 7: 执行器扰动下的 PID 控制 (重构版 v2)

## 1. 场景目标

本示例旨在演示**执行器故障**对闭环控制系统稳定性的影响。执行器（如此处的进水泵）是有物理局限的，它可能无法完美地执行上层控制器发来的指令。

我们复用了“示例3：进水泵PID控制”的基本场景，但这次我们假设：
-   感知是完美的，控制器能获取到最真实的水位。
-   控制器发出的指令是理想的。
-   但负责执行指令的**水泵是不精确的**，它存在**系统性偏差**（比如，指令流量为100，实际只能达到95），以及**随机噪声**。

这将导致系统状态的演变与控制器的预期产生偏差，影响控制效果。

## 2. 架构设计 (核心库增强)

根据用户的指示，本场景的实现依赖于对核心库 `PhysicalIOAgent` 的一项重要增强：**为其增加了内置的执行器噪声模拟功能**。

这使得本场景的架构变得非常清晰和标准：

### 组件 (`components.yml`)
-   `DisturbanceAwareReservoir`: 一个自定义的 `Reservoir` 子类 (定义于本目录的 `agents.py`)。它被扩展以能够订阅一个外部的扰动出流主题，因为标准 `Reservoir` 不支持数据驱动的出流。

### 智能体 (`agents.yml`)

1.  **`perception_agent` (`DigitalTwinAgent`)**: 标准的感知智能体，提供**完美的**水位观测值。
2.  **`pump_pid_controller_agent` (`LocalControlAgent`)**: 标准的PID控制器，根据完美观测值，发布一个**干净、理想**的流量指令到 `clean_pump_command_topic`。
3.  **`disturbance_agent` (`CsvInflowAgent`)**: 标准的数据输入智能体，提供不可控的扰动出流。
4.  **`noisy_actuator_agent` (`PhysicalIOAgent`)**:
    -   **核心**: 这是本场景的关键。我们现在使用的是**核心库中标准**的 `PhysicalIOAgent`。
    -   **订阅**: 它订阅控制器发出的 `clean_pump_command_topic`。
    -   **加噪**: 在其配置中，我们直接定义了 `noise_params` (包含 `bias` 和 `std_dev`)。`PhysicalIOAgent` 的新逻辑会读取这些参数，并将接收到的理想指令“腐化”为一个带偏差和噪声的实际指令。
    -   **行动**: 它将这个“被污染”的实际流量值，直接设置到 `DisturbanceAwareReservoir` 组件的 `data_inflow` 属性上。

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/07_actuator_disturbance
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。您可以对比 `clean_pump_command_topic` (理想指令) 和 `actual_inflow_topic` (实际执行的指令) 的数据，会发现后者在前者的基础上增加了偏差和噪声。最终，`water_level_topic` 的数据会显示，由于执行器不精确，真实水位很难完全稳定在目标值 10.0m，会产生持续的误差和波动。
