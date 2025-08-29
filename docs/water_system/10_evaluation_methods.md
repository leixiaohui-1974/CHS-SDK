# 5. 评价 (Evaluation) - 方法接口详解

本篇文档详细介绍 `Evaluation` 对象的主要方法接口。

## `start()` / `stop()`

*   **描述:** 启动或停止周期性评价服务。
*   **语法:** `start() -> Promise<void>`, `stop() -> Promise<void>`
*   **参数:** 无
*   **返回值:** `Promise<void>`，在服务状态切换成功后resolve。

## `run_once(startTime, endTime)`

*   **描述:** 手动触发一次一次性的评价任务。
*   **语法:** `run_once(startTime: String, endTime: String) -> Promise<EvaluationReport>`
*   **参数:**
    *   `startTime` / `endTime`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **格式:** ISO 8601
*   **返回值:**
    *   **类型:** `Promise<Object (EvaluationReport)>`
    *   **成功:** 返回新生成的 `EvaluationReport` 对象。
*   **错误码:**
    *   `400 Bad Request`: 时间格式错误或数据窗口过大。
    *   `429 Too Many Requests`: 短时间内手动触发过于频繁。

## `get_latest_report()`

*   **描述:** 获取最近一次生成的评价报告。
*   **语法:** `get_latest_report() -> Promise<EvaluationReport | null>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (EvaluationReport) | null>`
    *   **成功:** 返回最新的 `EvaluationReport` 对象，如果没有报告则返回 `null`。

## `get_report_history(page, pageSize, filter)`

*   **描述:** 查询历史评价报告列表，支持分页和过滤。
*   **语法:** `get_report_history(page: Number, pageSize: Number, filter?: Object) -> Promise<{reports: Array<EvaluationReport>, total: Number}>`
*   **参数:**
    *   `page` / `pageSize`
        *   **类型:** `Number`
        *   **是否必需:** 是
        *   **约束:** `page >= 1`, `1 <= pageSize <= 100`
    *   `filter`
        *   **类型:** `Object`
        *   **是否必需:** 否
        *   **描述:** 用于过滤的条件，例如按时间范围 `{ "start_time": "...", "end_time": "..." }`。
*   **返回值:**
    *   **类型:** `Promise<Object>`
    *   **成功:** 返回一个包含 `reports` 数组和 `total` 报告总数的对象。

## `on(eventName, callback)`

*   **描述:** 注册事件监听器，用于在新的评价报告生成时获得通知。
*   **语法:** `on(eventName: String, callback: Function) -> void`
*   **参数:**
    *   `eventName`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **有效值:** `'report_generated'`
    *   `callback`
        *   **类型:** `Function`
        *   **是否必需:** 是
        *   **回调函数签名:** `(payload: EvaluationReport) => {}`
*   **返回值:** 无
