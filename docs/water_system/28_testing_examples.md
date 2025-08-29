# 9. 测试 (Testing) - 代码示例

本篇文档提供 `Testing` 对象方法的Python代码实现示例。这是保障整个复杂系统稳定可靠的关键。

## 准备工作

我们为`WaterSystemApiClient`添加与自动化测试服务交互的方法。

```python
# a_hypothetical_api_client.py (续)
import time
import datetime
import random

class TestingClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        self._test_suites = {}
        self._run_history = {}
        print("Testing Client initialized.")

    def define_test_suite(self, suite_id, test_cases):
        print(f"Defining test suite {suite_id} with {len(test_cases)} cases.")
        self._test_suites[suite_id] = test_cases
        return {"success": True}

    def run_test_suite(self, suite_id):
        print(f"--- Running test suite: {suite_id} ---")
        if suite_id not in self._test_suites:
            return {"success": False, "error": "Test suite not found."}

        case_results = []
        summary = {"total": 0, "passed": 0, "failed": 0}

        for case in self._test_suites[suite_id]:
            time.sleep(0.1) # 模拟测试执行
            status = "passed" if random.random() > 0.2 else "failed"
            summary["total"] += 1
            if status == "passed": summary["passed"] += 1
            else: summary["failed"] += 1
            case_results.append({ "case_id": case['id'], "status": status, "duration_ms": random.randint(50, 200) })
            print(f"  - Test Case '{case['name']}': {status.upper()}")

        run_result = {
            "run_id": f"run_{int(time.time())}", "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
            "status": "failed" if summary['failed'] > 0 else "passed",
            "summary": summary, "case_results": case_results
        }

        if suite_id not in self._run_history: self._run_history[suite_id] = []
        self._run_history[suite_id].append(run_result)

        print("--- Test suite run finished. ---")
        return {"result": run_result}

    def run_single_case(self, suite_id, case_id):
        print(f"--- Running single test case '{case_id}' from suite '{suite_id}' ---")
        status = "passed" if random.random() > 0.1 else "failed"
        return {"result": {"case_id": case_id, "status": status}}

testing_client = TestingClient()
suite_id = "test_suite_full_system_v1"
```

## 1. 定义并运行测试套件

这个例子展示了如何定义一个包含多个测试用例的测试套件，并执行它。这通常是CI/CD流水线中的一个步骤。

```python
# 1. 定义测试用例
test_cases = [
    { "id": "tc_001_prediction_accuracy", "name": "测试需水量预测精度" },
    { "id": "tc_002_scheduler_leak_response", "name": "测试调度系统在爆管场景下的响应" },
    { "id": "tc_003_control_mode_switch", "name": "测试控制模式切换的安全性" }
]

testing_client.define_test_suite(suite_id, test_cases)

# 2. 运行整个测试套件
print("\n--- Starting full test suite run ---")
suite_run_data = testing_client.run_test_suite(suite_id)
suite_result = suite_run_data['result']

print("\n--- Test Run Summary ---")
print(f"Overall Status: {suite_result['status'].upper()}")
print(f"Passed: {suite_result['summary']['passed']} / {suite_result['summary']['total']}")
```

## 2. 运行单个测试用例

在修复bug或开发新功能时，只运行相关的单个测试用例会更高效。

```python
target_case_id = "tc_002_scheduler_leak_response"
print(f"\n--- Running a single test case for debugging: {target_case_id} ---")

single_run_data = testing_client.run_single_case(suite_id, target_case_id)
single_result = single_run_data['result']

print(f"Result for case '{single_result['case_id']}': {single_result['status'].upper()}")
```
