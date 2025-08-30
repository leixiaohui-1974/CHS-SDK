# 参数辨识功能示例

该目录包含了演示不同数字孪生模型参数辨识功能的示例。每个子目录都专注于一个特定模型的一个特定参数的辨识过程，展示了系统如何基于模拟的“观测”数据进行自校准。

## 示例工作原理

每个示例都遵循相似的设计模式：

1.  **“真实”模型 vs. “孪生”模型**: 我们会创建两个版本的模型。
    *   一个 **“真实” (true)** 模型，其拥有一个我们已知的、正确的参数（例如，已知的管道糙率）。该模型用于生成仿真的“观测数据”。
    *   一个 **“孪生” (twin)** 模型，即我们希望校准的数字孪生。它使用一个不正确的、初始猜测的参数开始运行。
2.  **感知 (Perception)**: 一组 `DigitalTwinAgent` 智能体负责观测“真实”系统的状态（例如水位、流量、闸门开度等），并将这些数据发布到消息总线（Message Bus）上。
3.  **辨识 (Identification)**: 一个 `ParameterIdentificationAgent` 智能体被配置为监听这些“观测”数据。同时，它也监测“孪生”模型的输入和输出。
4.  **优化 (Optimization)**: 当收集到足够的数据后，`ParameterIdentificationAgent` 会调用孪生模型上的 `.identify_parameters()` 方法。该方法内部使用一个优化算法（`scipy.optimize.minimize`）来寻找能够最好地解释观测数据的参数值。
5.  **更新 (Update)**: 一个 `ModelUpdaterAgent` 智能体负责监听辨识的结果，并自动地将新的、校正后的参数应用到孪生模型上。

## 示例列表

### 1. 水库库容曲线 (`01_reservoir_storage_curve`)
*   **目标**: 辨识水库的非线性库容曲线（库容 vs. 水位）。
*   **状态**: **正常工作**。
*   **运行方式**:
    ```bash
    python examples/identification/01_reservoir_storage_curve/run_identification.py
    ```
*   **预期结果**: 脚本将打印一个表格，对比真实的、初始的、以及最终辨识出的三条库容曲线。最终曲线应明显比初始猜测更接近真实曲线。同时，脚本也会生成一张对比图 (`identification_results.png`)。

### 2. 闸门流量系数 (`02_gate_discharge_coefficient`)
*   **目标**: 辨识闸门的流量系数 (`C`)。
*   **状态**: **正常工作**。
*   **运行方式**:
    ```bash
    python examples/identification/02_gate_discharge_coefficient/run_identification.py
    ```
*   **预期结果**: 脚本将打印出真实的、初始的、以及最终辨识出的流量系数值。最终值应非常接近真实值 0.8。

### 3. 管道糙率 (`03_pipe_roughness`)
*   **目标**: 辨识管道的曼宁糙率系数 (`n`)。
*   **状态**: **部分工作（存在已知问题）**。
*   **运行方式**:
    ```bash
    python examples/identification/03_pipe_roughness/run_identification.py
    ```
*   **已知问题**: 该示例可以无错误地运行，完整的智能体辨识流程也能被触发。然而，优化算法目前无法找到正确的曼宁 `n` 值，而是收敛到了其搜索范围的上界。这表明优化器与管道水力学方程之间的相互作用存在一个微妙的问题，需要进一步深入研究。尽管如此，该示例对于展示辨识场景的整体架构和数据流仍然具有价值。
