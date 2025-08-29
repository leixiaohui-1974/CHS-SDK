# 9. 测试 (Testing) - 方法接口详解

本篇文档详细介绍 `Testing` 对象的主要方法接口。

## `run()`

*   **描述:** 异步执行整个测试套件。
*   **语法:** `run() -> Promise<TestRunResult>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (TestRunResult)>`
    *   **成功:** 返回本次测试运行的最终 `TestRunResult` 对象。
*   **错误码:**
    *   `400 Bad Request`: 测试套件配置无效或测试环境无法连接。
    *   `409 Conflict`: 同一个测试套件已在运行中。

## `run_case(caseId)`

*   **描述:** 只执行测试套件中的某一个特定的测试用例。
*   **语法:** `run_case(caseId: String) -> Promise<TestCaseResult>`
*   **参数:**
    *   `caseId`
        *   **类型:** `String`
        *   **是否必需:** 是
        *   **描述:** 要执行的测试用例的ID。
*   **返回值:**
    *   **类型:** `Promise<Object (TestCaseResult)>`
    *   **成功:** 返回该单个测试用例的 `TestCaseResult` 对象。
*   **错误码:**
    *   `404 Not Found`: 在测试套件中找不到指定的 `caseId`。

## `get_last_run_result()`

*   **描述:** 获取最近一次运行整个测试套件的结果。
*   **语法:** `get_last_run_result() -> Promise<TestRunResult | null>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (TestRunResult) | null>`
    *   **成功:** 返回最新的 `TestRunResult` 对象，若无则返回 `null`。

## `get_run_history(page, pageSize)`

*   **描述:** 查询历史测试运行的记录，支持分页。
*   **语法:** `get_run_history(page: Number, pageSize: Number) -> Promise<{runs: Array<TestRunResult>, total: Number}>`
*   **参数:**
    *   `page` / `pageSize`
        *   **类型:** `Number`
        *   **是否必需:** 是
        *   **约束:** `page >= 1`, `1 <= pageSize <= 50`
*   **返回值:**
    *   **类型:** `Promise<Object>`
    *   **成功:** 返回一个包含 `runs` 数组和 `total` 运行总数的对象。
