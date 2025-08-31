# 示例: 在线辨识管道糙率

本示例是参数辨识系列的第三个，旨在演示如何在线校准 `Pipe` (管道) 模型的 `friction_factor` (达西-韦斯巴赫摩擦系数 `f`)。

## 1. 场景目标

我们继续沿用“真实”与“孪生”的模式，创建一个 `true_pipe` 和一个 `twin_pipe`。`twin_pipe` 的初始 `friction_factor` 是一个不准确的猜测值。

本示例的目标是，在仿真运行的同时，让 `ParameterIdentificationAgent` 自动学习并修正 `twin_pipe` 的 `friction_factor`，使其逼近真实值。

## 2. 核心工作流程

此示例同样使用 `run_identification.py` 脚本来编排辨识流程：

1.  **双重世界设定**: 脚本创建了两个管道实例，一个代表“真实世界”，一个代表“数字孪生”。
2.  **数据采集**:
    *   一个 `DigitalTwinAgent` 负责发布来自 `true_pipe` 的观测数据（如 `outflow`）。
    *   为了辨识管道参数，我们还需要知道管道两端的水位。这些数据由脚本直接生成或从其它模拟组件中获取，并发布到消息总线上。
3.  **在线辨识**:
    *   `ParameterIdentificationAgent` 订阅所有需要的数据主题（`upstream_levels`, `downstream_levels`, `observed_flows`）。
    *   当收集到足够的数据点后，它会调用 `twin_pipe` 模型的 `identify_parameters` 方法。
    *   `Pipe` 模型内部的辨识逻辑会利用达西-韦斯巴赫公式，反向求解出最优的 `friction_factor`。
4.  **模型在线更新**:
    *   辨识出的新 `friction_factor` 被发布出去，并由 `ModelUpdaterAgent` 接收并应用回 `twin_pipe` 模型。

## 3. 如何运行

直接在终端中执行此目录下的 `run_identification.py` 脚本：
```bash
python examples/identification/03_pipe_roughness/run_identification.py
```

## 4. 预期输出

脚本运行结束后，您会在终端看到以下输出：

*   **初始 `f`**: 打印出 `twin_pipe` 在辨识前的摩擦系数。
*   **辨识后 `f`**: 打印出经过在线校准后，`twin_pipe` 的新摩擦系数。

通过对比这两个值与 `true_pipe` 的真实 `friction_factor` 值（在 `components.yml` 中定义），您可以评估参数辨识的准确性。
