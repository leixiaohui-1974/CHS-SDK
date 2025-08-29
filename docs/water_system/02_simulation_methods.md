# 1. 仿真 (Simulation) - 方法文档

本篇文档详细介绍 `Simulation` 对象的主要方法。这些方法提供了与仿真任务进行交互的接口，包括运行、监控和获取结果。

## `run()`

*   **描述:**
    启动一个仿真任务。这是一个异步方法，调用后会立即返回，仿真将在后台运行。你可以通过查询 `status` 属性或监听事件来获取仿真状态。

*   **语法:**
    ```
    run() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当仿真成功启动时，该 `Promise` 会被 resolve。如果启动失败（例如，配置不完整），`Promise` 会被 reject 并返回一个错误信息。

*   **使用示例:**
    ```javascript
    const mySimulation = new Simulation({ ... }); // 初始化配置

    mySimulation.run()
      .then(() => {
        console.log("仿真已成功启动。");
      })
      .catch(error => {
        console.error("仿真启动失败:", error);
      });
    ```

## `pause()`

*   **描述:**
    暂停一个正在运行的仿真。这个功能对于需要手动干预或进行分步调试的场景非常有用。

*   **语法:**
    ```
    pause() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当仿真成功暂停时，该 `Promise` 会被 resolve。

*   **注意:**
    只有当 `status` 为 `running` 时，此方法才有效。

## `resume()`

*   **描述:**
    恢复一个已暂停的仿真。

*   **语法:**
    ```
    resume() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当仿真成功恢复时，该 `Promise` 会被 resolve。

*   **注意:**
    只有当 `status` 为 `paused` 时，此方法才有效。

## `cancel()`

*   **描述:**
    取消一个仿真任务。被取消的任务无法恢复，其所有中间结果都将被清除。

*   **语法:**
    ```
    cancel() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当仿真成功取消时，该 `Promise` 会被 resolve。

## `get_status()`

*   **描述:**
    获取仿真的当前状态。

*   **语法:**
    ```
    get_status() -> String
    ```

*   **参数:**
    无

*   **返回值:**
    一个表示当前状态的字符串，例如 `"created"`, `"running"`, `"paused"`, `"completed"`, `"failed"`。

*   **使用示例:**
    ```javascript
    if (mySimulation.get_status() === 'completed') {
      const results = mySimulation.get_results();
      // ... 处理结果
    }
    ```

## `get_results()`

*   **描述:**
    获取仿真的结果。

*   **语法:**
    ```
    get_results() -> SimulationResults | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果仿真成功完成 (`status` 为 `completed`)，则返回一个 `SimulationResults` 对象。
    *   在其他情况下，返回 `null`。

*   **使用示例:**
    ```javascript
    const results = mySimulation.get_results();
    if (results) {
      console.log("节点n1的压力时间序列:", results.node_pressures['n1']);
    } else {
      console.log("仿真尚未完成或已失败。");
    }
    ```

## `on(eventName, callback)`

*   **描述:**
    注册一个事件监听器，用于接收仿真的状态变更通知。这是一种比轮询 `get_status()` 更高效的方式。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称。支持的事件包括:
        *   `'status_change'`: 当 `status` 属性改变时触发。
        *   `'progress'`: 仿真进行中，定期触发，可用于显示进度条。
        *   `'error'`: 仿真过程中发生错误时触发。
    *   `callback` (Function): 事件触发时调用的回调函数。回调函数的参数根据事件类型而定。
        *   `status_change`: `(newStatus, oldStatus) => {}`
        *   `progress`: `(progressPercentage) => {}`
        *   `error`: `(errorObject) => {}`

*   **使用示例:**
    ```javascript
    mySimulation.on('status_change', (newStatus) => {
      console.log(`仿真状态变更为: ${newStatus}`);
      if (newStatus === 'completed') {
        // ...
      }
    });

    mySimulation.on('progress', (percentage) => {
      updateProgressBar(percentage);
    });
    ```
