# 7. 调度 (Scheduling) - 方法接口详解

本篇文档详细介绍 `Scheduling` 对象的主要方法接口。

## `run_optimization()`

*   **描述:** 启动一次优化调度计算。这是一个计算密集型的异步任务。
*   **语法:** `run_optimization() -> Promise<ControlSchedule>`
*   **参数:** 无 (方法会自动从关联的预测服务获取最新输入)
*   **返回值:**
    *   **类型:** `Promise<Object (ControlSchedule)>`
    *   **成功:** 返回计算出的最优 `ControlSchedule` 对象。
*   **错误码:**
    *   `400 Bad Request`: 缺少输入数据（如无法获取最新的需水量预测）。
    *   `422 Unprocessable Entity`: 优化问题无解（例如，在当前约束下找不到满足所有条件的调度方案）。
    *   `500 Internal Server Error`: 优化求解器发生内部错误。

## `get_latest_schedule()`

*   **描述:** 获取最近一次成功生成的优化调度计划。
*   **语法:** `get_latest_schedule() -> Promise<ControlSchedule | null>`
*   **参数:** 无
*   **返回值:**
    *   **类型:** `Promise<Object (ControlSchedule) | null>`
    *   **成功:** 返回最新的 `ControlSchedule` 对象，若无则返回 `null`。

## `get_schedule_history(page, pageSize)`

*   **描述:** 查询历史生成的调度计划，支持分页。
*   **语法:** `get_schedule_history(page: Number, pageSize: Number) -> Promise<{schedules: Array<ControlSchedule>, total: Number}>`
*   **参数:**
    *   `page` / `pageSize`
        *   **类型:** `Number`
        *   **是否必需:** 是
        *   **约束:** `page >= 1`, `1 <= pageSize <= 100`
*   **返回值:**
    *   **类型:** `Promise<Object>`
    *   **成功:** 返回一个包含 `schedules` 数组和 `total` 调度总数的对象。

## `simulate_schedule(schedule)`

*   **描述:** 对一个给定的 `ControlSchedule` 进行更精细、更全面的“沙盘推演”仿真。
*   **语法:** `simulate_schedule(schedule: ControlSchedule) -> Promise<SimulationResults>`
*   **参数:**
    *   `schedule`
        *   **类型:** `Object (ControlSchedule)`
        *   **是否必需:** 是
        *   **描述:** 需要进行仿真推演的调度计划。
*   **返回值:**
    *   **类型:** `Promise<Object (SimulationResults)>`
    *   **成功:** 返回详细的仿真结果 `SimulationResults` 对象。
*   **错误码:**
    *   `400 Bad Request`: 传入的 `schedule` 对象格式不正确。
