# 4. 诊断 (Diagnosis) - 方法接口详解

本篇文档详细介绍 `Diagnosis` 对象的主要方法接口，包括告警处理工作流。

## `start()` / `stop()`

*   **描述:** 启动或停止诊断服务。
*   **语法:** `start() -> Promise<void>`, `stop() -> Promise<void>`
*   **参数:** 无
*   **返回值:** `Promise<void>`，在服务状态切换成功后resolve。

## `get_active_diagnoses()`

*   **描述:** 获取当前所有活动的（即`unacknowledged`或`acknowledged`状态的）诊断结果列表。
*   **语法:** `get_active_diagnoses() -> Promise<Array<DiagnosisResult>>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Array<DiagnosisResult>>`
    *   **成功:** 返回 `DiagnosisResult` 对象的数组。如果无活动告警，则数组为空。

## `get_diagnosis_history(startTime, endTime, filter)`

*   **描述:** 查询历史诊断记录。
*   **语法:** `get_diagnosis_history(startTime: String, endTime: String, filter?: Object) -> Promise<Array<DiagnosisResult>>`
*   **参数:**
    *   `startTime` / `endTime`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **格式:** ISO 8601
    *   `filter`
        *   **类型:** `Object`
        *   **是否必需:** 否
        *   **描述:** 用于过滤结果的条件，例如 `{ "severity": "critical", "rule_id": "rule_pipe_burst" }`。
*   **返回值:**
    *   **类型:** `Promise<Array<DiagnosisResult>>`
    *   **成功:** 返回符合条件的 `DiagnosisResult` 对象数组。

## `acknowledge_diagnosis(diagnosisId, user, comments)`

*   **描述:** 确认一个诊断结果（告警），表示问题已被认知并开始处理。状态将从 `unacknowledged` -> `acknowledged`。
*   **语法:** `acknowledge_diagnosis(diagnosisId: String, user: String, comments?: String) -> Promise<void>`
*   **参数:**
    *   `diagnosisId`
        *   **类型:** `String`
        *   **是否必需:** 是
    *   `user`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **描述:** 执行此操作的用户名或ID。
    *   `comments`
        *   **类型:** `String`
        *   **是否必需:** 否
*   **返回值:** `Promise<void>`
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的告警。
    *   `409 Conflict`: 告警状态不是 `unacknowledged`。

## `resolve_diagnosis(diagnosisId, user, resolutionNotes)`

*   **描述:** 将一个诊断结果标记为已解决。状态将变为 `resolved`，并从活动列表中移除。
*   **语法:** `resolve_diagnosis(diagnosisId: String, user: String, resolutionNotes: String) -> Promise<void>`
*   **参数:**
    *   `diagnosisId`
        *   **类型:** `String`
        *   **是否必需:** 是
    *   `user`
        *   **类型:** `String`
        *   **是否必需:** 是
    *   `resolutionNotes`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **描述:** 问题如何被解决的说明，用于归档。
*   **返回值:** `Promise<void>`
*   **错误码:**
    *   `404 Not Found`: 找不到指定ID的告警。

## `on(eventName, callback)`

*   **描述:** 注册事件监听器，用于在新的诊断事件发生时接收实时通知。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `'new_diagnosis'`
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **回调函数签名:** `(payload: DiagnosisResult) => {}`
*   **返回值:** 无
