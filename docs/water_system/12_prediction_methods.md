# 6. 预测 (Prediction) - 方法接口详解

本篇文档详细介绍 `Prediction` 对象的主要方法接口。

## `start()` / `stop()`

*   **描述:** 启动或停止周期性预测服务。
*   **语法:** `start() -> Promise<void>`, `stop() -> Promise<void>`
*   **参数:** 无
*   **返回值:** `Promise<void>`，在服务状态切换成功后resolve。

## `run_once()`

*   **描述:** 立即手动触发一次预测任务。
*   **语法:** `run_once() -> Promise<PredictionResult>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (PredictionResult)>`
    *   **成功:** 返回新生成的 `PredictionResult` 对象。
*   **错误码:**
    *   `400 Bad Request`: 模型所需的输入特征数据不完整（例如，无法获取天气预报）。
    *   `429 Too Many Requests`: 手动触发过于频繁。

## `get_latest_prediction()`

*   **描述:** 获取最近一次生成的预测结果。
*   **语法:** `get_latest_prediction() -> Promise<PredictionResult | null>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (PredictionResult) | null>`
    *   **成功:** 返回最新的 `PredictionResult` 对象，如果还没有任何预测，则返回 `null`。

## `get_prediction_history(page, pageSize)`

*   **描述:** 查询历史预测结果列表，支持分页。
*   **语法:** `get_prediction_history(page: Number, pageSize: Number) -> Promise<{predictions: Array<PredictionResult>, total: Number}>`
*   **参数:**
    *   `page` / `pageSize`
        *   **类型:** `Number`
        *   **是否必需:** 是
        *   **约束:** `page >= 1`, `1 <= pageSize <= 100`
*   **返回值:**
    *   **类型:** `Promise<Object>`
    *   **成功:** 返回一个包含 `predictions` 数组和 `total` 预测总数的对象。

## `on(eventName, callback)`

*   **描述:** 注册事件监听器，用于在新的预测结果生成时获得通知。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `'prediction_generated'`
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **回调函数签名:** `(payload: PredictionResult) => {}`
*   **返回值:** 无
