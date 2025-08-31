# 示例: 在线辨识水闸流量系数

本示例是参数辨识系列的第二个，旨在演示如何在线校准 `Gate` (水闸) 模型的 `discharge_coefficient` (流量系数 `C_d`)。

## 1. 场景目标

与水库示例类似，我们设定一个“真实”水闸 (`true_gate`) 和一个待校准的“数字孪生”水闸 (`twin_gate`)。`twin_gate` 的初始 `discharge_coefficient` 是一个不准确的猜测值。

本示例的目标是，在仿真运行的同时，让 `ParameterIdentificationAgent` 自动学习并修正 `twin_gate` 的 `discharge_coefficient`，使其逼近真实值。

## 2. 核心工作流程

此示例同样使用 `run_identification.py` 脚本来编排辨识流程：

1.  **双重世界设定**: 脚本创建了两个水闸实例，一个代表“真实世界”，一个代表“数字孪生”。
2.  **数据采集**:
    *   一个 `DigitalTwinAgent` 负责发布来自 `true_gate` 的观测数据（如 `outflow`）。
    *   为了进行辨识，我们还需要知道驱动水闸运行的其它变量，如上游水位 (`upstream_level`)、下游水位 (`downstream_level`) 和水闸开度 (`opening`)。这些数据由脚本直接生成或从其它模拟组件中获取，并发布到消息总线上。
3.  **在线辨识**:
    *   `ParameterIdentificationAgent` 订阅所有需要的数据主题（`upstream_level`, `downstream_level`, `opening`, `observed_flows`）。
    *   当收集到足够的数据点后，它会调用 `twin_gate` 模型的 `identify_parameters` 方法。
    *   `Gate` 模型内部的辨识逻辑会利用这些数据，反向求解出最优的 `discharge_coefficient`。
4.  **模型在线更新**:
    *   辨识出的新 `discharge_coefficient` 被发布出去，并由 `ModelUpdaterAgent` 接收并应用回 `twin_gate` 模型。

## 3. 如何运行

直接在终端中执行此目录下的 `run_identification.py` 脚本：
```bash
python examples/identification/02_gate_discharge_coefficient/run_identification.py
```

## 4. 预期输出

脚本运行结束后，您会在终端看到以下输出：

*   **初始 `C_d`**: 打印出 `twin_gate` 在辨识前的流量系数。
*   **辨识后 `C_d`**: 打印出经过在线校准后，`twin_gate` 的新流量系数。

通过对比这两个值与 `true_gate` 的真实 `C_d` 值（在 `components.yml` 中定义），您可以评估参数辨识的准确性。
