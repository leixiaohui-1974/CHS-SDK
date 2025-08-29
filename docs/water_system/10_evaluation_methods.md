# 5. 评价 (Evaluation) - 方法文档

本篇文档详细介绍 `Evaluation` 对象的主要方法。这些方法用于控制评价任务的生命周期、手动触发评价以及查询历史评价报告。

## `start()`

*   **描述:**
    启动周期性评价服务。启动后，系统会根据 `evaluation_period` 中定义的 `cron_expression`，定时自动执行评价任务。

*   **语法:**
    ```
    start() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功启动时 resolve。

## `stop()`

*   **描述:**
    停止周期性评价服务。已有的评价报告不会被删除，但系统不会再自动生成新的报告。

*   **语法:**
    ```
    stop() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功停止时 resolve。

## `run_once(startTime, endTime)`

*   **描述:**
    手动触发一次一次性的评价任务，而不是等待周期性任务执行。这对于需要对特定历史时期进行深入分析的场景非常有用。

*   **语法:**
    ```
    run_once(startTime: String, endTime: String) -> Promise<EvaluationReport>
    ```

*   **参数:**
    *   `startTime` (String): 本次评价所要分析的数据的开始时间 (ISO 8601 格式)。
    *   `endTime` (String): 结束时间 (ISO 8601 格式)。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为本次手动评价生成的 `EvaluationReport` 对象。

*   **使用示例:**
    ```javascript
    // 分析上个季度的能效情况
    myEvaluation.run_once('2023-04-01T00:00:00Z', '2023-06-30T23:59:59Z')
      .then(report => {
        console.log("上季度产销差率为:", report.kpi_results.find(k => k.kpi_id === 'kpi_unaccounted_water_rate').value);
      })
      .catch(error => {
        console.error("手动评价失败:", error);
      });
    ```

## `get_latest_report()`

*   **描述:**
    获取最近一次生成的评价报告。

*   **语法:**
    ```
    get_latest_report() -> EvaluationReport | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果至少已生成过一次报告，则返回最新的 `EvaluationReport` 对象。
    *   否则返回 `null`。

## `get_report_history(page, pageSize, filter)`

*   **描述:**
    查询历史评价报告列表，支持分页和过滤。

*   **语法:**
    ```
    get_report_history(page: Number, pageSize: Number, filter?: Object) -> Promise<{reports: Array<EvaluationReport>, total: Number}>
    ```

*   **参数:**
    *   `page` (Number): 页码，从 1 开始。
    *   `pageSize` (Number): 每页的报告数量。
    *   `filter` (Object, 可选): 用于过滤的条件，例如按时间范围过滤。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个包含报告列表和总数量的对象。

*   **使用示例:**
    ```javascript
    // 获取今年的所有月度报告
    myEvaluation.get_report_history(1, 12, { year: 2023 })
      .then(({reports, total}) => {
        console.log(`今年共生成了 ${total} 份报告。`);
        // 可以用于绘制KPI年度变化曲线
        const energyTrends = reports.map(r => r.kpi_results.find(k => k.kpi_id === 'kpi_pump_energy_consumption').value);
        plot(energyTrends);
      });
    ```

## `on(eventName, callback)`

*   **描述:**
    注册事件监听器，用于在新的评价报告生成时获得通知。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称，主要是 `'report_generated'`。
    *   `callback` (Function): 事件触发时调用的回调函数。
        *   `report_generated`: `(report) => {}`

*   **使用示例:**
    ```javascript
    // 每当新的月度报告生成时，就将其推送到管理者的仪表盘
    myEvaluation.on('report_generated', (report) => {
      pushToDashboard(report);
    });
    ```
