# 8. 控制 (Control) - 方法文档

本篇文档详细介绍 `Control` 对象的主要方法。这些方法用于加载调度计划、管理控制模式以及执行手动控制。

## `load_schedule(schedule)`

*   **描述:**
    将一个由 `Scheduling` 模块生成的 `ControlSchedule` 加载到控制器中，作为 `active_schedule`。加载后，如果控制器处于 `automatic` 模式，它将开始根据这个计划执行控制。

*   **语法:**
    ```
    load_schedule(schedule: ControlSchedule) -> Promise<void>
    ```

*   **参数:**
    *   `schedule` (ControlSchedule): 要执行的控制调度计划。

*   **返回值:**
    一个 `Promise` 对象，当计划成功加载并验证通过后 resolve。如果计划中的控制点与控制器配置的 `target_devices` 不匹配，则会 reject。

*   **使用示例:**
    ```javascript
    const latestSchedule = myScheduler.get_latest_schedule();
    if (latestSchedule) {
      myController.load_schedule(latestSchedule)
        .then(() => console.log("新调度计划已加载。"))
        .catch(err => console.error("计划加载失败:", err));
    }
    ```

## `set_mode(mode)`

*   **描述:**
    设置控制器的执行模式。

*   **语法:**
    ```
    set_mode(mode: String) -> Promise<void>
    ```

*   **参数:**
    *   `mode` (String): 目标模式。必须是 `"automatic"`, `"manual"`, 或 `"advisory"`之一。

*   **返回值:**
    一个 `Promise` 对象，当模式切换成功后 resolve。

*   **使用示例:**
    ```javascript
    // 在进行设备维护前，切换到手动模式
    myController.set_mode('manual')
      .then(() => console.log("控制器已切换到手动模式。"));
    ```

## `manual_override(action, targetId, value)`

*   **描述:**
    在 `manual` 模式下，手动下发一个单独的控制指令。此操作会绕过 `active_schedule`。这是为操作员提供紧急干预或手动操作能力的接口。

*   **语法:**
    ```
    manual_override(action: String, targetId: String, value?: any) -> Promise<boolean>
    ```

*   **参数:**
    *   `action` (String): 控制动作，如 `"start"`, `"stop"`, `"set_speed"`, `"set_pressure"`。
    *   `targetId` (String): 目标设备的逻辑ID，如 `"pump_A1"`。
    *   `value` (any, 可选): 控制设定值，例如水泵转速或阀门开度。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个布尔值，表示指令是否下发成功并收到了正确的反馈。

*   **使用示例:**
    ```javascript
    // 手动紧急停止1号泵
    myController.manual_override('stop', 'pump_A1')
      .then(success => {
        if (success) {
          console.log("泵P1已成功停止。");
        } else {
          console.error("停止泵P1的指令执行失败！");
        }
      });
    ```

## `get_control_log(startTime, endTime)`

*   **描述:**
    查询在指定时间范围内的控制执行日志。

*   **语法:**
    ```
    get_control_log(startTime: String, endTime: String) -> Promise<Array<LogEntry>>
    ```

*   **参数:**
    *   `startTime` (String): 查询的开始时间 (ISO 8601 格式)。
    *   `endTime` (String): 查询的结束时间 (ISO 8601 格式)。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个 `LogEntry` 对象的数组。

## `on(eventName, callback)`

*   **描述:**
    注册事件监听器，用于接收关于控制执行的关键事件通知。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称。
        *   `'command_executed'`: 每当一个控制指令（无论是自动还是手动）执行后触发。
        *   `'command_failed'`: 当一个指令执行失败时触发。
        *   `'communication_error'`: 当与物理设备的通信中断或恢复时触发。
    *   `callback` (Function): 事件触发时调用的回调函数。
        *   `command_executed`: `(logEntry) => {}`
        *   `command_failed`: `(logEntry, error) => {}`
        *   `communication_error`: `(device_id, status) => {}`

*   **使用示例:**
    ```javascript
    // 监听所有失败的指令并发出高优先级告警
    myController.on('command_failed', (logEntry, error) => {
      createHighPriorityAlarm(`控制指令失败: ${logEntry.command}`, { log: logEntry, error: error });
    });

    // 监听通信状态变化
    myController.on('communication_error', (deviceId, status) => {
      console.log(`设备 ${deviceId} 的通信状态变更为: ${status}`);
    });
    ```
