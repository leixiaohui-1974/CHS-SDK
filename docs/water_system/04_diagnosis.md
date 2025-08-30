# 4. 诊断 (Diagnosis)

本篇文档详细介绍 `core_lib` 中异常诊断功能的设计与实现。

## 1. 核心理念：中心化的多源数据分析

系统的诊断功能被设计为一个**中心化的服务**，其核心思想是：通过汇集来自系统中**多个不同部分**的实时状态数据，进行综合分析，从而发现单一组件无法察觉的系统级异常。

例如，一个孤立的管道压力传感器可能无法判断其读数是否异常。但如果一个中心化的诊断服务同时观测到：
1.  上游水库水位正在下降。
2.  连接的管道压力**没有**相应升高。
3.  下游流量计读数也**没有**变化。

它就可以推断出，这三者之间存在矛盾，可能表示有未知的泄漏或传感器故障。

## 2. 关键组件

### 2.1 `IsolationForestAnomalyDetector` (算法层)

*   **位置**: `core_lib/data_processing/anomaly_detector.py`
*   **职责**: 提供一个具体的、可重用的异常检测算法。
*   **实现**: 该文件封装了来自 `scikit-learn` 库的 **Isolation Forest (孤立森林)** 算法。这是一个成熟的、无需标签的异常检测算法，尤其适用于检测多维数据中的异常点。它提供了一个标准的 `fit_predict()` 接口，输入一个数据帧(DataFrame)，输出每个数据点是否为异常的标签。

### 2.2 `CentralAnomalyDetectionAgent` (业务流程层)

*   **位置**: `core_lib/central_coordination/dispatch/central_anomaly_detection_agent.py`
*   **职责**: 作为诊断功能的业务流程编排者。
*   **工作流程**:
    1.  **订阅**: 在初始化时，该智能体根据配置，向 `MessageBus` 订阅它需要监控的多个状态主题（例如，来自不同`DigitalTwinAgent`的`state_topic`）。
    2.  **汇集**: 通过 `handle_message` 回调函数，它持续接收并更新来自这些主题的最新数据，在内存中形成一个关于系统当前状态的“快照”。
    3.  **分析 (设计意图)**: 在 `run()` 或 `detect_anomalies()` 方法中，它应该将汇集的多维数据传递给一个像 `IsolationForestAnomalyDetector` 这样的算法实例进行分析。
    4.  **发布告警**: 如果算法返回了异常结果，该智能体将构建一条标准的告警消息，并将其发布到一个指定的告警主题 (`alert_topic`) 上。

### 3. 实现说明

需要注意的是，根据当前 `core_lib` 中的代码，`CentralAnomalyDetectionAgent` 的 `run()` 和 `detect_anomalies()` 方法中的核心分析逻辑仍是**占位符 (Placeholder)**。它已经完整地实现了数据的订阅和汇集功能，但尚未完成调用 `IsolationForestAnomalyDetector` 并发布告警的最后一步。

因此，当前的诊断模块为未来的功能实现搭建了完整的基础架构，但核心的诊断逻辑有待填充。
