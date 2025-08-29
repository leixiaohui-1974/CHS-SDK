# 6. 预测 (Prediction) - 方法文档

本篇文档详细介绍 `Prediction` 对象的主要方法。这些方法用于控制预测服务的生命周期，并获取预测结果。

## `start()`

*   **描述:**
    启动周期性预测服务。启动后，系统会根据 `prediction_schedule` 中定义的 `cron_expression`，定时自动执行预测任务。

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
    停止周期性预测服务。已有的预测结果不会被删除，但系统不会再自动生成新的预测。

*   **语法:**
    ```
    stop() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功停止时 resolve。

## `run_once()`

*   **描述:**
    立即手动触发一次预测任务，而不是等待下一个调度周期。这在需要紧急更新预测或测试模型时非常有用。

*   **语法:**
    ```
    run_once() -> Promise<PredictionResult>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为本次手动预测生成的 `PredictionResult` 对象。

*   **使用示例:**
    ```javascript
    // 在一次突发天气事件后，立即重新运行需水量预测
    myPrediction.run_once()
      .then(result => {
        console.log("最新的需水量预测结果已生成。");
        // 将新结果推送给调度系统
        dispatchSystem.update_demand_forecast(result);
      })
      .catch(error => {
        console.error("手动预测失败:", error);
      });
    ```

## `get_latest_prediction()`

*   **描述:**
    获取最近一次生成的预测结果。

*   **语法:**
    ```
    get_latest_prediction() -> PredictionResult | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果至少已生成过一次预测，则返回最新的 `PredictionResult` 对象。
    *   否则返回 `null`。

*   **使用示例:**
    ```javascript
    const latestDemand = myPrediction.get_latest_prediction();
    if (latestDemand) {
      const nextHourDemand = latestDemand.time_series.predicted_values[0];
      console.log(`预测下一个小时的需水量为: ${nextHourDemand}`);
    }
    ```

## `get_prediction_history(page, pageSize)`

*   **描述:**
    查询历史预测结果列表，支持分页。这对于分析预测模型的长期性能（例如，将历史预测与实际发生值进行比较）非常重要。

*   **语法:**
    ```
    get_prediction_history(page: Number, pageSize: Number) -> Promise<{predictions: Array<PredictionResult>, total: Number}>
    ```

*   **参数:**
    *   `page` (Number): 页码，从 1 开始。
    *   `pageSize` (Number): 每页的数量。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个包含预测结果列表和总数量的对象。

## `on(eventName, callback)`

*   **描述:**
    注册事件监听器，用于在新的预测结果生成时获得通知。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称，主要是 `'prediction_generated'`。
    *   `callback` (Function): 事件触发时调用的回调函数。
        *   `prediction_generated`: `(predictionResult) => {}`

*   **使用示例:**
    ```javascript
    // 每当新的需水量预测生成时，自动触发一次优化调度计算
    myPrediction.on('prediction_generated', (result) => {
      console.log("接收到新的预测，触发优化调度...");
      myScheduler.run_optimization(result);
    });
    ```
