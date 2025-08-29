# 8. 控制 (Control) - 方法接口详解

本篇文档详细介绍 `Control` 对象的主要方法接口。

## `load_schedule(schedule)`

*   **描述:** 将一个 `ControlSchedule` 加载到控制器中，作为 `active_schedule`。
*   **语法:** `load_schedule(schedule: ControlSchedule) -> Promise<void>`
*   **参数:**
    *   `schedule`
        *   **类型:** `Object (ControlSchedule)`
        *   **是否必需:** 是
*   **返回值:** `Promise<void>`
*   **错误码:**
    *   `400 Bad Request`: 计划格式无效或包含不受此控制器管理的设备。
    *   `409 Conflict`: 当前控制器正忙或处于无法加载新计划的状态。

## `set_mode(mode)`

*   **描述:** 设置控制器的执行模式。
*   **语法:** `set_mode(mode: String) -> Promise<void>`
*   **参数:**
    *   `mode`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `"automatic"`, `"manual"`, `"advisory"`
*   **返回值:** `Promise<void>`
*   **错误码:**
    *   `400 Bad Request`: 无效的模式字符串。

## `manual_override(action, targetId, value)`

*   **描述:** 在 `manual` 模式下，手动下发一个单独的控制指令。
*   **语法:** `manual_override(action: String, targetId: String, value?: any) -> Promise<{success: boolean, message: string}>`
*   **参数:**
    *   `action`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `"start"`, `"stop"`, `"set_speed"`, `"set_setting"`
    *   `targetId`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **描述:** 目标设备的逻辑ID (e.g., `"pump_A1"`)。
    *   `value`
        *   **类型:** `any`
        *   **是否必需:** 否
        *   **描述:** 控制设定值，仅用于`set_speed`, `set_setting`等动作。
*   **返回值:**
    *   **类型:** `Promise<Object>`
    *   **成功:** 返回 `{"success": true, "message": "Command executed and feedback confirmed."}`
    *   **失败:** 返回 `{"success": false, "message": "Execution failed. See log for details."}`
*   **错误码:**
    *   `403 Forbidden`: 当前模式不是 `manual`。
    *   `404 Not Found`: 目标设备 `targetId` 不存在。
    *   `504 Gateway Timeout`: 指令已下发，但在超时时间内未收到设备反馈。

## `get_control_log(startTime, endTime)`

*   **描述:** 查询在指定时间范围内的控制执行日志。
*   **语法:** `get_control_log(startTime: String, endTime: String) -> Promise<Array<LogEntry>>`
*   **参数:**
    *   `startTime` / `endTime`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **格式:** ISO 8601
*   **返回值:** `Promise<Array<LogEntry>>`

## `on(eventName, callback)`

*   **描述:** 注册事件监听器，用于接收关于控制执行的关键事件通知。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `'command_executed'`, `'command_failed'`, `'communication_error'`
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **回调函数签名:**
            *   `command_executed`: `(logEntry: LogEntry) => {}`
            *   `command_failed`: `(logEntry: LogEntry, error: Object) => {}`
            *   `communication_error`: `(payload: {deviceId: String, status: String}) => {}`
*   **返回值:** 无
