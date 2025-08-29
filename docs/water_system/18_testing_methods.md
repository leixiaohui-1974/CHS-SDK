# 9. 测试 (Testing) - 方法文档

本篇文档详细介绍 `Testing` 对象的主要方法。这些方法用于执行测试套件和查询测试结果。

## `run()`

*   **描述:**
    执行整个测试套件中定义的所有 `test_cases`。这是一个可能会长时间运行的异步操作。它会按照顺序或并行地执行每个测试用例，收集结果，并最终生成一个总的 `TestRunResult`。

*   **语法:**
    ```
    run() -> Promise<TestRunResult>
    ```

*   **参数:**
    无

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为本次测试运行的最终 `TestRunResult` 对象。

*   **使用示例:**
    ```javascript
    const myTestSuite = new Testing({ ... });

    // 通常在CI/CD流水线中被调用
    console.log("开始运行全系统冒烟测试...");
    myTestSuite.run()
      .then(result => {
        if (result.status === 'failed') {
          console.error("测试未通过！详情:", result.summary);
          // 可以将结果发送到团队聊天工具
          postToSlackChannel(`测试失败: ${result.summary.failed} / ${result.summary.total} 个用例失败。`);
          // 在CI/CD中，这通常会导致构建失败
          process.exit(1);
        } else {
          console.log("所有测试用例均已通过。");
        }
      })
      .catch(error => {
        console.error("测试执行过程中发生严重错误:", error);
        process.exit(1);
      });
    ```

## `run_case(caseId)`

*   **描述:**
    只执行测试套件中的某一个特定的测试用例。这在开发和调试单个测试用例时非常有用。

*   **语法:**
    ```
    run_case(caseId: String) -> Promise<TestCaseResult>
    ```

*   **参数:**
    *   `caseId` (String): 要执行的测试用例的ID。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为该单个测试用例的 `TestCaseResult` 对象。

*   **使用示例:**
    ```javascript
    // 正在调试一个新的测试用例，只运行这一个
    myTestSuite.run_case('tc_003_new_feature_test')
      .then(result => {
        console.log(`测试用例 ${result.case_id} 的执行结果: ${result.status}`);
        if (result.status === 'failed') {
          console.log("失败原因:", result.failure_reason);
        }
      });
    ```

## `get_last_run_result()`

*   **描述:**
    获取最近一次运行整个测试套件的结果。

*   **语法:**
    ```
    get_last_run_result() -> TestRunResult | null
    ```

*   **参数:**
    无

*   **返回值:**
    *   如果至少已运行过一次，则返回最新的 `TestRunResult` 对象。
    *   否则返回 `null`。

## `get_run_history(page, pageSize)`

*   **描述:**
    查询历史测试运行的记录，支持分页。

*   **语法:**
    ```
    get_run_history(page: Number, pageSize: Number) -> Promise<{runs: Array<TestRunResult>, total: Number}>
    ```

*   **参数:**
    *   `page` (Number): 页码，从 1 开始。
    *   `pageSize` (Number): 每页的数量。

*   **返回值:**
    一个 `Promise` 对象，它会 resolve 为一个包含测试运行历史列表和总数量的对象。

*   **使用示例:**
    ```javascript
    // 获取最近10次测试运行的结果，以观察系统质量的变化趋势
    myTestSuite.get_run_history(1, 10)
      .then(({runs}) => {
        const passRates = runs.map(r => (r.summary.passed / r.summary.total));
        console.log("最近10次测试的通过率:", passRates);
      });
    ```
