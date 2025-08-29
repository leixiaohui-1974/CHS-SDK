# 2. 辨识 (Identification) - 方法文档

本篇文档详细介绍 `Identification` 对象的主要方法。这些方法用于启动、控制和查询参数辨识任务。

## `run()`

*   **描述:**
    启动参数辨识任务。这是一个计算密集型操作，通常是异步的。调用后，系统会根据 `optimizer_options` 的配置，在后台运行优化算法，不断调整 `parameters_to_identify` 中指定的参数，并调用 `simulation_model` 进行仿真，以最小化仿真结果与 `observation_data` 之间的差距。

*   **语法:**
    ```
    run() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象。当辨识任务成功启动时，`Promise` 会被 resolve。如果配置不正确（例如，未提供观测数据），`Promise` 会被 reject。

*   **使用示例:**
    ```javascript
    const myIdentification = new Identification({ ... });

    myIdentification.run()
      .then(() => {
        console.log("参数辨识任务已启动。");
      })
      .catch(error => {
        console.error("任务启动失败:", error);
      });
    ```

## `cancel()`

*   **描述:**
    取消一个正在运行的参数辨识任务。所有中间计算结果将被丢弃。

*   **语法:**
    ```
    cancel() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当任务成功取消时，该 `Promise` 会被 resolve。

## `get_status()`

*   **描述:**
    获取辨识任务的当前状态。

*   **语法:**
    ```
    get_status() -> String
    ```

*   **参数:**
    无

*   **返回值:**
    一个表示当前状态的字符串，例如 `"created"`, `"running"`, `"completed"`, `"failed"`。

## `get_results()`

*   **描述:**
    获取参数辨识的结果。

*   **语法:**
    ```
    get_results() -> IdentificationResults | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果辨识任务成功完成 (`status` 为 `completed`)，则返回一个 `IdentificationResults` 对象，其中包含了参数的最优解。
    *   否则，返回 `null`。

*   **使用示例:**
    ```javascript
    const results = myIdentification.get_results();
    if (results) {
      console.log("辨识得到的管道p1粗糙度为:", results.identified_parameters[0].optimal_value);
    }
    ```

## `get_calibrated_model()`

*   **描述:**
    在辨识任务成功完成后，获取一个已经用辨识结果校准过的新的 `Simulation` 对象实例。这个新的仿真模型可以直接用于后续的、更精确的仿真分析。

*   **语法:**
    ```
    get_calibrated_model() -> Simulation | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果辨识任务成功完成，返回一个新的 `Simulation` 对象实例，其网络参数已被更新为辨识出的最优值。
    *   否则，返回 `null`。

*   **使用示例:**
    ```javascript
    const calibratedSim = myIdentification.get_calibrated_model();
    if (calibratedSim) {
      // 使用校准后的模型进行一次新的仿真
      calibratedSim.run();
    }
    ```

## `on(eventName, callback)`

*   **描述:**
    注册事件监听器，以接收辨识任务的状态更新。

*   **语法:**
    ```
    on(eventName: String, callback: Function) -> void
    ```

*   **参数:**
    *   `eventName` (String): 事件名称。支持的事件包括:
        *   `'status_change'`: 当 `status` 属性改变时触发。
        *   `'progress'`: 辨识过程中，定期触发，可用于报告优化进程。
        *   `'error'`: 辨识过程中发生错误时触发。
    *   `callback` (Function): 事件触发时调用的回调函数。
        *   `status_change`: `(newStatus, oldStatus) => {}`
        *   `progress`: `(currentIteration, objectiveValue) => {}`
        *   `error`: `(errorObject) => {}`

*   **使用示例:**
    ```javascript
    myIdentification.on('progress', (generation, fitness) => {
      console.log(`第 ${generation} 代: 最小误差 = ${fitness}`);
    });

    myIdentification.on('status_change', (newStatus) => {
      if (newStatus === 'completed') {
        console.log("辨识完成！");
        const calibratedModel = myIdentification.get_calibrated_model();
        // ...
      }
    });
    ```
