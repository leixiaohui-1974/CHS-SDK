# 2. 辨识 (Identification) - 方法接口详解

本篇文档详细介绍 `Identification` 对象的主要方法接口，包括详细的参数、返回值和错误码说明。

## `run()`

*   **描述:** 启动参数辨识任务。这是一个计算密集型的异步操作。
*   **语法:** `run() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当辨识任务成功启动时，Promise被resolve。
*   **错误码:**
    *   `400 Bad Request`: 任务配置不完整（如未指定`parameters_to_identify`或`observation_data`）。
    *   `409 Conflict`: 该辨识任务实例已在运行中。

## `cancel()`

*   **描述:** 取消一个正在运行的参数辨识任务。
*   **语法:** `cancel() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当取消指令成功发出时，Promise被resolve。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的辨识任务。
    *   `409 Conflict`: 任务未在运行状态，无法取消。

## `get_status()`

*   **描述:** 获取辨识任务的当前状态。
*   **语法:** `get_status() -> String`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `String`
    *   **说明:** 返回表示当前状态的字符串。
    *   **可能的值:** `"created"`, `"running"`, `"completed"`, `"failed"`。

## `get_results()`

*   **描述:** 获取参数辨识的结果。
*   **语法:** `get_results() -> IdentificationResults | null`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Object (IdentificationResults) | null`
    *   **成功:** 如果任务状态为 `completed`，返回包含最优参数值和拟合优度的 `IdentificationResults` 对象。
    *   **失败/未完成:** 在其他情况下返回 `null`。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的辨识任务。
    *   `409 Conflict`: 任务尚未完成。

## `get_calibrated_model()`

*   **描述:** 获取一个用辨识结果校准过的新的 `Simulation` 对象实例。
*   **语法:** `get_calibrated_model() -> Simulation | null`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Object (Simulation) | null`
    *   **成功:** 如果任务状态为 `completed`，返回一个全新的、参数已更新的 `Simulation` 对象。
    *   **失败/未完成:** 在其他情况下返回 `null`。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的辨识任务。
    *   `409 Conflict`: 任务尚未完成，无法生成校准模型。

## `on(eventName, callback)`

*   **描述:** 注册事件监听器，以接收辨识任务的状态更新。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `'status_change'`, `'progress'`, `'error'`。
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **描述:** 事件触发时调用的回调函数。
        *   **回调函数签名:**
            *   `status_change`: `(payload: {newStatus: String, oldStatus: String}) => {}`
            *   `progress`: `(payload: {currentIteration: Number, totalIterations: Number, objectiveValue: Number}) => {}`
            *   `error`: `(payload: {errorCode: String, message: String}) => {}`
*   **返回值:** 无
