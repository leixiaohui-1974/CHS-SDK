# 示例: 在线辨识水库库容曲线

本示例演示了 `CHS-SDK` 中一个非常强大的高级功能：**在线参数辨识**。我们将展示如何使用 `ParameterIdentificationAgent` 和 `ModelUpdaterAgent` 来自动校准一个水库模型的关键参数——库容曲线 (`storage_curve`)。

## 1. 场景目标

想象一个场景：我们有一个物理世界中的真实水库 (`true_reservoir`)，但我们对其物理特性（库容曲线）的了解并不完全。我们有一个该水库的数字孪生模型 (`twin_reservoir`)，但它的库容曲线是基于一个不准确的初始猜测。

本示例的目标是，在仿真运行的同时，让系统**自动学习**并**修正**这个数字孪生模型的库容曲线，使其越来越接近真实水库的特性。

## 2. 核心工作流程

这个示例不使用标准的 `run_scenario.py`，而是通过一个自定义的 `run_identification.py` 脚本来精心编排整个辨识流程：

1.  **双重世界设定**: 脚本创建了两个水库实例：
    *   `true_reservoir`: 模拟物理世界中的真实水库，拥有我们想要辨识出的“正确”库容曲线。
    *   `twin_reservoir`: 模拟我们正在维护的数字孪生，其库容曲线是一个不准确的初始猜测。

2.  **数据采集**:
    *   一个 `CsvInflowAgent` 为 `true_reservoir` 提供入流，模拟真实的来水过程。
    *   一个 `DigitalTwinAgent` (`observation_agent`) 负责观察 `true_reservoir` 的状态（特别是水位），模拟从真实世界采集到的观测数据。

3.  **在线辨识**:
    *   `ParameterIdentificationAgent` 订阅来自 `observation_agent` 的观测数据，以及来自 `twin_reservoir` 自身的模拟输出数据。
    *   在后台，它持续收集这些数据。当收集到足够的数据点后（由 `identification_interval` 参数定义），它会触发其内部的优化算法，计算出一个新的、更优的库容曲线。

4.  **模型在线更新**:
    *   辨识出的新库容曲线被发布到一个专门的主题上。
    *   `ModelUpdaterAgent` 订阅了这个主题。在接收到新参数后，它会立即将新的库容曲线应用到 `twin_reservoir` 模型上。

这个过程在整个仿真期间会周期性地重复，使得数字孪生模型不断地“自我完善”。

## 3. 如何运行

直接在终端中执行此目录下的 `run_identification.py` 脚本：
```bash
python examples/identification/01_reservoir_storage_curve/run_identification.py
```
**注意**: 此示例需要 `matplotlib` 库来生成结果图。如果尚未安装，请运行 `pip install matplotlib`。

## 4. 预期输出

脚本运行结束后，您会看到：

1.  **终端输出**:
    *   一个详细的表格，逐行对比“真实水位”、“初始猜测水位”和“辨识后水位”，让您可以精确地看到参数优化的效果。
2.  **图像文件**:
    *   在项目根目录下会生成一个名为 `identification_results.png` 的图像文件。该图表会可视化地展示三条库容曲线（真实的、初始的、辨识后的），让您对辨识结果有一个直观的认识。

通过这个示例，您可以看到 `CHS-SDK` 是如何通过组合不同的智能体，来实现复杂的、自适应的数字孪生系统的。
