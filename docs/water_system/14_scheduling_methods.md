# 7. 调度 (Scheduling) - 方法文档

本篇文档详细介绍 `Scheduling` 对象的主要方法。这些方法用于触发和管理优化调度计算任务。

## `run_optimization()`

*   **描述:**
    启动一次优化调度计算。这是一个计算密集型任务，通常异步执行。它会从 `Prediction` 模块获取最新的输入预测（如需水量），然后运行优化算法，求解在满足所有 `constraints` 的前提下，能够使 `objective_function` 最优的 `control_variables` 的时序控制计划。

*   **语法:**
    ```
    run_optimization() -> Promise<ControlSchedule>
    ```

*   **参数:**
    无。方法会自动从关联的预测服务中获取最新输入。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为计算出的最优 `ControlSchedule` 对象。

*   **使用示例:**
    ```javascript
    // 通常由预测模块在新预测生成后触发
    myPrediction.on('prediction_generated', (newForecast) => {
      console.log("接收到新预测，开始优化调度...");
      myScheduler.run_optimization()
        .then(schedule => {
          console.log("优化调度计划已生成，预期成本:", schedule.expected_cost);
          // 可以将计划发送给控制模块执行
          myController.load_schedule(schedule);
        })
        .catch(error => {
          console.error("优化调度失败:", error);
        });
    });
    ```

## `get_latest_schedule()`

*   **描述:**
    获取最近一次成功生成的优化调度计划。

*   **语法:**
    ```
    get_latest_schedule() -> ControlSchedule | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果至少已成功计算过一次，则返回最新的 `ControlSchedule` 对象。
    *   否则返回 `null`。

## `get_schedule_history(page, pageSize)`

*   **描述:**
    查询历史生成的调度计划，支持分页。这对于审计、回溯和分析调度性能非常有用。

*   **语法:**
    ```
    get_schedule_history(page: Number, pageSize: Number) -> Promise<{schedules: Array<ControlSchedule>, total: Number}>
    ```

*   **参数:**
    *   `page` (Number): 页码，从 1 开始。
    *   `pageSize` (Number): 每页的数量。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个包含调度计划列表和总数量的对象。

## `simulate_schedule(schedule)`

*   **描述:**
    在将一个调度计划付诸实践之前，用仿真模型来详细模拟执行该计划后，系统的完整响应。`run_optimization` 在内部也会做仿真，但通常是简化的。此方法提供了一个工具，可以对一个给定的 `ControlSchedule` 进行更精细、更全面的“沙盘推演”。

*   **语法:**
    ```
    simulate_schedule(schedule: ControlSchedule) -> Promise<SimulationResults>
    ```

*   **参数:**
    *   `schedule` (ControlSchedule): 需要进行仿真推演的调度计划。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为详细的 `SimulationResults` 对象，包含了在执行该调度计划下，所有节点、管段在所有时间步的详细状态。

*   <strong>使用示例:</strong>
    ```javascript
    const latestSchedule = myScheduler.get_latest_schedule();
    if (latestSchedule) {
      myScheduler.simulate_schedule(latestSchedule)
        .then(results => {
          // 检查在该调度计划下，关键节点的压力是否始终在安全范围内
          const criticalNodePressure = results.node_pressures['node_critical_1'];
          if (Math.min(...criticalNodePressure) < 22.0) {
            console.warn("警告：该调度计划可能导致关键点压力过低！");
          }
        });
    }
    ```
