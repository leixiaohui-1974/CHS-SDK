# 示例 7: 执行器扰动下的 PID 控制 (重构版)

## 1. 场景目标

本示例旨在演示**执行器故障**对闭环控制系统的影响。执行器（如此处的进水泵）是有物理局限的，它可能无法完美地执行上层控制器发来的指令。

我们复用了“示例3：进水泵PID控制”的基本场景，但这次我们假设：
-   感知是完美的，控制器能获取到最真实的水位。
-   控制器发出的指令是理想的。
-   但负责执行指令的**水泵是不精确的**，它存在**系统性偏差**（比如，指令流量为100，实际只能达到95），以及**随机噪声**。

这将导致系统状态的演变与控制器的预期产生偏差，影响控制效果。

## 2. 架构设计 (继承与扩展)

为了满足用户“**必须使用 `PhysicalIOAgent`**”的指令，同时解决标准库中该智能体与消息驱动组件的设计不兼容问题，本场景采用了**继承与扩展**的策略，是所有示例中技术上最复杂的。

我们在本目录的 `agents.py` 文件中创建了两个自定义子类：

1.  **`DisturbanceAwareReservoir`**:
    -   它继承自核心库的 `Reservoir` 类。
    -   它增加了新的功能：可以订阅一个 `disturbance_outflow_topic` 主题来接收一个额外的、不可控的扰动出流。

2.  **`NoisyPhysicalIOAgent`**:
    -   它继承自核心库的 `PhysicalIOAgent`。
    -   它重写了 `_handle_action` 方法。在原有的“接收指令 -> 执行动作”的逻辑中，加入了**增加偏差和噪声**的核心步骤。
    -   它还增加了将“被污染后的实际指令”发布到日志主题的功能，方便我们对比分析。

### 数据流

1.  `LocalControlAgent` 发出一个**干净、理想**的流量指令到 `clean_pump_command_topic`。
2.  `NoisyPhysicalIOAgent` 监听到该指令，对其进行“污染”（乘以0.95的偏差并加上随机噪声），得到一个**真实的、带噪声的**流量值。
3.  `NoisyPhysicalIOAgent` 将这个真实流量值：
    -   发布到 `actual_inflow_topic` (用于日志记录)。
    -   直接设置到 `DisturbanceAwareReservoir` 组件的 `data_inflow` 属性上，完成“行动”。
4.  `DisturbanceAwareReservoir` 在自身的 `step` 方法中，使用这个带噪声的入流和来自另一主题的扰动出流，来计算真实的水位变化。

## 3. 如何运行

在项目根目录下执行以下命令：

```bash
python run_scenario.py examples/watertank_refactored/07_actuator_disturbance
```

## 4. 预期结果

仿真结束后，将在本目录下生成 `output.yml` 文件。

您可以重点观察和对比以下两个主题的数据：

-   `clean_pump_command_topic`: PID控制器发出的理想指令。
-   `actual_inflow_topic`: 执行器加噪后，真正进入水库的流量。
-   `water_level_topic`: 最终的真实水位。

您会发现，即使PID控制器的指令是平滑的，但由于执行器的不精确性，真实水位很难完全稳定在目标值 10.0m，会产生持续的误差和波动。
