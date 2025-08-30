# 2. 参数辨识 (Identification)

本篇文档详细介绍 `core_lib` 中模型参数自动辨识功能的设计与实现。

## 1. 核心理念：事件驱动的在线辨识

与传统的、需要手动收集数据并离线运行的参数辨识工具不同，`core_lib` 中的辨识过程被设计为一个**在线(Online)**、**事件驱动**的持续过程。

其核心思想是：系统中的辨识智能体 (`ParameterIdentificationAgent`) 会持续监听消息总线 (`MessageBus`) 上的实时仿真数据和观测数据。当积累了足够多的新数据后，它会自动触发一次参数优化过程，并用优化后的新参数更新模型。这个过程周而复始，使得模型能够动态地自我校准，以适应物理世界中不断变化的特性。

## 2. 关键组件

### 2.1 `Identifiable` 接口

为了让一个模型（例如一个`rainfall_runoff`模型）的参数能够被辨识，它必须实现 `Identifiable` 接口，该接口定义在 `core_lib/core/interfaces.py` 中。

```python
# core_lib/core/interfaces.py (示意)
class Identifiable:
    def identify_parameters(self, data: Dict[str, np.ndarray]):
        """
        使用提供的数据来辨识和更新模型自身的参数。

        Args:
            data: 一个字典，key是数据类型（如'rainfall', 'observed_runoff'），
                  value是对应的numpy数组形式的时间序列数据。
        """
        raise NotImplementedError
```

这个方法封装了具体的参数优化算法（如`rls_estimator.py`中的递归最小二乘法）。模型自己最清楚应该如何根据输入数据来校准自己的参数。

### 2.2 `ParameterIdentificationAgent`

这是参数辨识功能的“大脑”，定义在 `core_lib/identification/identification_agent.py`。它的职责是：

1.  **订阅数据**: 在初始化时，根据配置，它会向 `MessageBus` 订阅一系列它需要的数据主题（Topics），包括模型的输入（如降雨）和模型的“真实”输出（如观测到的径流）。
2.  **收集数据**: 它有一个 `handle_data_message` 方法作为回调函数。每当其订阅的主题上有新消息时，这个方法就会被调用，并将数据存储在内部的 `data_history` 缓冲区中。
3.  **触发辨识**: 在 `run()` 方法中（由`SimulationHarness`在每个时间步调用），它会检查收集到的新数据量是否达到了预设的阈值 (`identification_interval`)。
4.  **调用接口**: 一旦达到阈值，它就会将收集到的、整理好的数据传递给其管理的 `target_model` 的 `identify_parameters()` 方法，从而启动一次实际的参数辨识计算。
5.  **清空并重复**: 调用完成后，它会清空内部的数据缓冲区，为下一个辨识周期做准备。

## 3. 工作流程示例

1.  一个 `rainfall_agent` 将实时降雨数据发布到 `topic_rainfall` 主题。
2.  一个 `csv_data_source` 将文件中记录的历史真实径流数据发布到 `topic_observed_runoff` 主题。
3.  一个 `ParameterIdentificationAgent` 实例被创建，它负责一个 `RainfallRunoffModel` 实例。
4.  该辨识智能体同时订阅 `topic_rainfall` 和 `topic_observed_runoff`。
5.  随着时间的推移，智能体不断收集降雨和径流数据。
6.  当收集到（例如）100个新的数据点后，智能体将这些数据打包，并调用 `RainfallRunoffModel.identify_parameters()`。
7.  `RainfallRunoffModel` 内部使用这些数据，通过优化算法（如最小二乘法）调整自身的产流系数、汇流时间等参数，以使得模型的模拟径流输出与观测到的径流尽可能一致。
8.  参数更新完成，模型在后续的仿真中将使用这套更精确的参数。
