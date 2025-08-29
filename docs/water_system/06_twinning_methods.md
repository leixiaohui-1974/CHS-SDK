# 3. 孪生 (Twinning) - 方法文档

本篇文档详细介绍 `DigitalTwin` 对象的主要方法。这些方法提供了启动、停止和与数字孪生体进行交互的接口。

## `start()`

*   **描述:**
    启动数字孪生服务。调用此方法后，数字孪生将根据其 `synchronization_policy` 开始周期性地从 `data_source_connections` 定义的数据源拉取数据，更新其内部状态，并与仿真模型进行同步。

*   **语法:**
    ```
    start() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象。当服务成功启动时，`Promise` 会被 resolve。

*   **使用示例:**
    ```javascript
    const myTwin = new DigitalTwin({ ... });
    myTwin.start()
      .then(() => console.log("数字孪生服务已启动。"))
      .catch(err => console.error("启动失败:", err));
    ```

## `stop()`

*   **描述:**
    停止数字孪生服务。停止后，所有与数据源的连接将断开，状态同步将暂停。

*   **语法:**
    ```
    stop() -> Promise<void>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，当服务成功停止时，该 `Promise` 会被 resolve。

## `get_current_state()`

*   **描述:**
    获取数字孪生在当前时刻的最新状态快照。

*   **语法:**
    ```
    get_current_state() -> TwinState
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `TwinState` 对象，包含了当前时刻所有网元（节点、管道等）的详细状态信息。

*   **使用示例:**
    ```javascript
    const currentState = myTwin.get_current_state();
    console.log(`当前时刻 ${currentState.timestamp}，节点n1的压力为:`, currentState.node_states.n1.pressure);
    ```

## `get_historical_state(startTime, endTime)`

*   **描述:**
    查询指定时间范围内的历史状态数据。数字孪生系统会记录其状态的每一次变化，形成历史时序数据库。

*   **语法:**
    ```
    get_historical_state(startTime: String, endTime: String) -> Promise<Array<TwinState>>
    ```

*   **参数:**
    *   `startTime` (String): 查询的开始时间 (ISO 8601 格式)。
    *   `endTime` (String): 查询的结束时间 (ISO 8601 格式)。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个 `TwinState` 对象的数组，按时间顺序排列。

*   **使用示例:**
    ```javascript
    myTwin.get_historical_state("2023-09-01T08:00:00Z", "2023-09-01T09:00:00Z")
      .then(history => {
        history.forEach(state => {
          console.log(state.timestamp, state.node_states.n1.pressure);
        });
      });
    ```

## `run_what_if_simulation(scenario)`

*   **描述:**
    在数字孪生的当前状态基础上，运行一个“假设分析” (What-if) 仿真。这是数字孪生的核心价值之一：能够在不干扰物理世界的情况下，推演未来可能发生的情况。

*   **语法:**
    ```
    run_what_if_simulation(scenario: Simulation) -> Promise<SimulationResults>
    ```

*   **参数:**
    *   `scenario` (Simulation): 一个 `Simulation` 对象，定义了要模拟的未来场景。例如，可以修改其中的需水量、开关泵状态等。**重要的是**，此 `Simulation` 对象的初始状态将自动设置为数字孪生的 `current_state`，而不是从头开始计算。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为该假设分析仿真的 `SimulationResults`。

*   **使用示例:**
    ```javascript
    // 场景：假设未来两小时，n5节点处的管道突然爆裂 (通过增加一个极大的需水量来模拟)
    const whatIfScenario = new Simulation({
      time_settings: { start_time: "now", duration_hours: 2, time_step_seconds: 300 },
      network_modifications: [
        {
          element_type: 'node',
          element_id: 'n5',
          parameter_name: 'demand',
          value: 10.0 // 一个非常大的需量
        }
      ]
    });

    myTwin.run_what_if_simulation(whatIfScenario)
      .then(results => {
        // 分析爆管对周围节点压力的影响
        console.log("爆管后n4节点的压力变化:", results.node_pressures['n4']);
      });
    ```

## `trigger_recalibration()`

*   **描述:**
    手动触发一次模型的再校准（参数辨识）过程。通常，此过程由 `synchronization_policy` 自动触发，但此方法提供了手动干预的能力。

*   **语法:**
    ```
    trigger_recalibration() -> Promise<Identification>
    ```

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个正在运行的 `Identification` 任务实例。你可以用这个实例来监控校准过程。
