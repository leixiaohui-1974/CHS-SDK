# 4. 诊断 (Diagnosis) - 方法文档

本篇文档详细介绍 `Diagnosis` 对象的主要方法。这些方法用于控制诊断服务的生命周期，并管理诊断结果。

## `start()`

*   **描述:**
    启动诊断服务。一旦启动，`Diagnosis` 对象会开始监听其 `target_twin` 的状态更新，并根据 `diagnosis_rules` 持续评估系统状态。当有规则的触发条件被满足时，会生成新的 `DiagnosisResult` 并添加到 `active_diagnoses` 列表中。

*   **语法:**
    ```
    start() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功启动时，该 `Promise` 会被 resolve。

## `stop()`

*   **描述:**
    停止诊断服务。服务停止后，将不再对 `target_twin` 的状态进行监控和评估。

*   **语法:**
    ```
    stop() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功停止时，该 `Promise` 会被 resolve。

## `get_active_diagnoses()`

*   **描述:**
    获取当前所有活动的（即未解决的）诊断结果列表。

*   **语法:**
    ```
    get_active_diagnoses() -> Array<DiagnosisResult>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `DiagnosisResult` 对象的数组。如果当前没有活动的诊断，则返回一个空数组。

*   **使用示例:**
    ```javascript
    const activeIssues = myDiagnosis.get_active_diagnoses();
    if (activeIssues.length > 0) {
      console.log(`当前有 ${activeIssues.length} 个活动告警。`);
      displayAlarms(activeIssues);
    }
    ```

## `get_diagnosis_history(startTime, endTime, filter)`

*   **描述:**
    查询历史诊断记录。系统会存储所有触发过的诊断事件，无论其后续是否被解决。

*   **语法:**
    ```
    get_diagnosis_history(startTime: String, endTime: String, filter?: Object) -> Promise<Array<DiagnosisResult>>
    ```

*   **参数:**
    *   `startTime` (String): 查询的开始时间 (ISO 8601 格式)。
    *   `endTime` (String): 查询的结束时间 (ISO 8601 格式)。
    *   `filter` (Object, 可选): 用于过滤结果的条件。
        *   `severity` (String | Array<String>): 按严重等级过滤。
        *   `rule_id` (String | Array<String>): 按规则ID过滤。
        *   `status` (String): 按 'resolved' 或 'unresolved' 过滤。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个符合条件的 `DiagnosisResult` 对象的数组。

*   **使用示例:**
    ```javascript
    // 查询上周所有“严重”等级的告警
    myDiagnosis.get_diagnosis_history('2023-08-21T00:00:00Z', '2023-08-28T00:00:00Z', { severity: 'critical' })
      .then(history => {
        console.log(`上周共发生 ${history.length} 次严重告警。`);
      });
    ```

## `acknowledge_diagnosis(diagnosisId, user, comments)`

*   **描述:**
    确认一个诊断结果（告警）。这通常意味着运维人员已经注意到这个问题，并准备开始处理。此操作会将 `DiagnosisResult` 的状态从 `unacknowledged` 变为 `acknowledged`。

*   **语法:**
    ```
    acknowledge_diagnosis(diagnosisId: String, user: String, comments?: String) -> Promise<void>
    ```

*   **参数:**
    *   `diagnosisId` (String): 要确认的诊断结果的ID。
    *   `user` (String): 执行此操作的用户名。
    *   `comments` (String, 可选): 相关的备注信息。

*   **返回值:**
    一个 `Promise` 对象，当操作成功时 resolve。

## `resolve_diagnosis(diagnosisId, user, resolutionNotes)`

*   **描述:**
    将一个诊断结果标记为已解决。这表示相关的异常事件已经处理完毕。此操作会将 `DiagnosisResult` 的状态更新为 `resolved`，并将其从 `active_diagnoses` 列表中移除。

*   **语法:**
    ```
    resolve_diagnosis(diagnosisId: String, user: String, resolutionNotes: String) -> Promise<void>
    ```

*   **参数:**
    *   `diagnosisId` (String): 要解决的诊断结果的ID。
    *   `user` (String): 执行此操作的用户名。
    *   `resolutionNotes` (String): 问题如何被解决的说明。

*   **返回值:**
    一个 `Promise` 对象，当操作成功时 resolve。

## `on(eventName, callback)`

*   **描述:**
    注册事件监听器，用于在新的诊断事件发生时接收实时通知。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称。核心事件是 `'new_diagnosis'`。
    *   `callback` (Function): 事件触发时调用的回调函数。
        *   `new_diagnosis`: `(diagnosisResult) => {}`

*   **使用示例:**
    ```javascript
    // 当有新的告警产生时，立即发送邮件通知
    myDiagnosis.on('new_diagnosis', (result) => {
      console.log(`新告警: ${result.conclusion}`);
      sendEmailNotification(result);
    });
    ```
