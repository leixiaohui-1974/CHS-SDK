# 1. 仿真 (Simulation) - 方法接口详解

本篇文档详细介绍 `Simulation` 对象的主要方法接口，包括详细的参数、返回值和错误码说明。

## `run()`

*   **描述:** 启动一个仿真任务。这是一个异步方法，调用后会立即返回，仿真将在后台运行。
*   **语法:** `run() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当仿真任务成功提交到执行队列时，Promise被resolve。
    *   **失败:** 当启动请求失败时，Promise被reject。
*   **错误码:**
    *   `400 Bad Request`: 仿真配置不完整或无效（例如，网络拓扑未定义）。
    *   `409 Conflict`: 仿真实例已经处于 `running` 或 `completed` 状态。
    *   `500 Internal Server Error`: 服务器内部错误，无法启动仿真任务。

## `pause()`

*   **描述:** 暂停一个正在运行的仿真。
*   **语法:** `pause() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当暂停指令被成功接收时，Promise被resolve。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的仿真实例。
    *   `409 Conflict`: 仿真状态不是 `running`，无法暂停。

## `resume()`

*   **描述:** 恢复一个已暂停的仿真。
*   **语法:** `resume() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当恢复指令被成功接收时，Promise被resolve。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的仿真实例。
    *   `409 Conflict`: 仿真状态不是 `paused`，无法恢复。

## `cancel()`

*   **描述:** 取消一个仿真任务。被取消的任务无法恢复。
*   **语法:** `cancel() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当取消指令被成功接收时，Promise被resolve。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的仿真实例。

## `get_status()`

*   **描述:** 获取仿真的当前状态。
*   **语法:** `get_status() -> String`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `String`
    *   **说明:** 返回表示当前状态的字符串。
    *   **可能的值:** `"created"`, `"running"`, `"paused"`, `"completed"`, `"failed"`。

## `get_results()`

*   **描述:** 获取仿真的结果。
*   **语法:** `get_results() -> SimulationResults | null`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Object (SimulationResults) | null`
    *   **成功:** 如果仿真状态为 `completed`，则返回一个包含详细时序结果的 `SimulationResults` 对象。
    *   **失败/未完成:** 在其他情况下返回 `null`。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的仿真实例。

## `on(eventName, callback)`

*   **描述:** 注册一个事件监听器，用于接收仿真的状态变更通知。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **描述:** 要监听的事件名称。
        *   **有效值:**
            *   `'status_change'`: 当 `status` 属性改变时触发。
            *   `'progress'`: 仿真进行中，定期触发。
            *   `'error'`: 仿真过程中发生错误时触发。
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **描述:** 事件触发时调用的回调函数。
        *   **回调函数签名:**
            *   `status_change`: `(payload: {newStatus: String, oldStatus: String}) => {}`
            *   `progress`: `(payload: {progressPercentage: Number}) => {}`
            *   `error`: `(payload: {errorCode: String, message: String}) => {}`
*   **返回值:** 无
