# 3. 孪生 (Twinning) - 方法接口详解

本篇文档详细介绍 `DigitalTwin` 对象的主要方法接口。

## `start()`

*   **描述:** 启动数字孪生服务。
*   **语法:** `start() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当服务成功启动时，Promise被resolve。
*   **错误码:**
    *   `400 Bad Request`: 孪生配置不完整（如数据源连接失败）。
    *   `409 Conflict`: 孪生服务已在运行中。

## `stop()`

*   **描述:** 停止数字孪生服务。
*   **语法:** `stop() -> Promise<void>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<void>`
    *   **成功:** 当服务成功停止时，Promise被resolve。
*   **错误码:**
    *   `409 Conflict`: 孪生服务未在运行。

## `get_current_state()`

*   **描述:** 获取数字孪生在当前时刻的最新状态快照。
*   **语法:** `get_current_state() -> TwinState`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Object (TwinState)`
    *   **成功:** 返回包含了当前所有网元状态的 `TwinState` 对象。
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的孪生实例。
    *   `204 No Content`: 孪生正在初始化，暂无状态可用。

## `get_historical_state(startTime, endTime)`

*   **描述:** 查询指定时间范围内的历史状态数据。
*   **语法:** `get_historical_state(startTime: String, endTime: String) -> Promise<Array<TwinState>>`
*   **参数:**
    *   `startTime`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **格式:** ISO 8601 (e.g., `"2023-09-01T08:00:00Z"`)
    *   `endTime`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **格式:** ISO 8601 (e.g., `"2023-09-01T09:00:00Z"`)
*   **返回值:**
    *   **类型:** `Promise<Array<TwinState>>`
    *   **成功:** 返回一个 `TwinState` 对象的数组。
*   **错误码:**
    *   `400 Bad Request`: 时间格式错误或结束时间早于开始时间。

## `run_what_if_simulation(scenario)`

*   **描述:** 在数字孪生的当前状态基础上，运行一个“假设分析”仿真。
*   **语法:** `run_what_if_simulation(scenario: Simulation) -> Promise<SimulationResults>`
*   **参数:**
    *   `scenario`
        *   **类型:** `Object (Simulation)`
        *   **是否必需:** 是
        *   **描述:** 一个定义了未来场景的 `Simulation` 对象。
*   **返回值:**
    *   **类型:** `Promise<Object (SimulationResults)>`
    *   **成功:** 返回该假设分析仿真的结果 `SimulationResults`。
*   **错误码:**
    *   `400 Bad Request`: `scenario` 对象配置无效。
    *   `409 Conflict`: 当前正有另一个假设分析在运行中。

## `trigger_recalibration()`

*   **描述:** 手动触发一次模型的再校准（参数辨识）过程。
*   **语法:** `trigger_recalibration() -> Promise<Identification>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (Identification)>`
    *   **成功:** 返回一个代表已启动的 `Identification` 任务的对象。
*   **错误码:**
    *   `409 Conflict`: 已有一个再校准任务正在进行中。
