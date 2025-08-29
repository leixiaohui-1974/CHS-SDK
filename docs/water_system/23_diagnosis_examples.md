# 4. 诊断 (Diagnosis) - 代码示例

本篇文档提供 `Diagnosis` 对象方法的Python代码实现示例。

## 准备工作

我们为`WaterSystemApiClient`添加与故障诊断服务交互的方法。

```python
# a_hypothetical_api_client.py (续)
import time
import datetime

class WaterSystemApiClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        # 模拟一个内存中的告警列表
        self._active_diagnoses = []
        self._diagnosis_history = []
        print("API Client initialized.")

    def start_diagnosis_service(self, service_id):
        print(f"Starting diagnosis service {service_id}...")
        # 模拟一个告警事件的发生
        self._active_diagnoses.append({
            "id": f"diag_res_{int(time.time())}",
            "rule_id": "rule_pipe_burst",
            "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
            "severity": "critical",
            "conclusion": "节点n5附近可能发生管道爆裂！",
            "status": "unacknowledged",
            "details": {"pressure_delta": -12.5}
        })
        return {"status": "running"}

    def get_active_diagnoses(self, service_id):
        print(f"Getting active diagnoses for service {service_id}...")
        return {"diagnoses": self._active_diagnoses}

    def acknowledge_diagnosis(self, diagnosis_id, user, comments):
        print(f"User '{user}' acknowledging diagnosis {diagnosis_id} with comments: '{comments}'")
        for diag in self._active_diagnoses:
            if diag['id'] == diagnosis_id and diag['status'] == 'unacknowledged':
                diag['status'] = 'acknowledged'
                diag['acknowledged_by'] = user
                diag['acknowledged_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
                print(f"Diagnosis {diagnosis_id} is now 'acknowledged'.")
                return {"success": True}
        return {"success": False, "error": "Diagnosis not found or already acknowledged."}

    def resolve_diagnosis(self, diagnosis_id, user, resolution_notes):
        print(f"User '{user}' resolving diagnosis {diagnosis_id} with notes: '{resolution_notes}'")
        diag_to_resolve = None
        for diag in self._active_diagnoses:
            if diag['id'] == diagnosis_id:
                diag_to_resolve = diag
                break

        if diag_to_resolve:
            diag_to_resolve['status'] = 'resolved'
            diag_to_resolve['resolved_by'] = user
            diag_to_resolve['resolution_notes'] = resolution_notes
            self._active_diagnoses.remove(diag_to_resolve)
            self._diagnosis_history.append(diag_to_resolve)
            print(f"Diagnosis {diagnosis_id} is now 'resolved' and moved to history.")
            return {"success": True}
        return {"success": False, "error": "Diagnosis not found."}

    def get_diagnosis_history(self, service_id, start_time, end_time):
        print(f"Getting diagnosis history for service {service_id}...")
        # 在实际应用中会根据时间过滤
        return {"history": self._diagnosis_history}


client = WaterSystemApiClient()
diagnosis_service_id = "diag_leakage_detection_main_zone"
current_user = "jules_the_operator"
```

## 1. 启动服务并检查活动告警

这个例子展示了如何启动诊断服务，并获取当前未解决的告警列表。

```python
# 1. 启动诊断服务 (在后台，这会开始监控孪生)
# 在我们的模拟中，启动时会自动产生一个告警
client.start_diagnosis_service(diagnosis_service_id)

# 2. 获取活动告警列表
active_diagnoses_data = client.get_active_diagnoses(diagnosis_service_id)
active_diagnoses = active_diagnoses_data['diagnoses']

print("\n--- Active Diagnoses ---")
if not active_diagnoses:
    print("No active diagnoses. System is healthy.")
else:
    for diag in active_diagnoses:
        print(f"ID: {diag['id']}, Status: {diag['status']}, Conclusion: {diag['conclusion']}")
```

## 2. 处理告警 (确认与解决)

这个例子展示了一个典型的告警处理工作流：一个操作员首先“确认”告警，表示他已接手处理，然后在问题解决后“解决”该告警。

```python
if active_diagnoses:
    # 假设我们处理列表中的第一个告警
    target_diagnosis_id = active_diagnoses[0]['id']

    # 3. 确认告警
    print(f"\n--- Acknowledging diagnosis {target_diagnosis_id} ---")
    client.acknowledge_diagnosis(
        diagnosis_id=target_diagnosis_id,
        user=current_user,
        comments="I am investigating this issue now."
    )

    # 再次获取活动告警，检查状态变化
    updated_diagnoses = client.get_active_diagnoses(diagnosis_service_id)['diagnoses']
    print(f"Status of {target_diagnosis_id} is now: {updated_diagnoses[0]['status']}")

    # 4. 解决告警
    # ... 假设操作员已经在线下完成了维修 ...
    print(f"\n--- Resolving diagnosis {target_diagnosis_id} ---")
    client.resolve_diagnosis(
        diagnosis_id=target_diagnosis_id,
        user=current_user,
        resolution_notes="Isolated the leaking pipe section and dispatched repair crew."
    )

    # 再次获取活动告警，列表应该为空了
    final_diagnoses = client.get_active_diagnoses(diagnosis_service_id)['diagnoses']
    print(f"\nNumber of active diagnoses now: {len(final_diagnoses)}")
```

## 3. 查询历史告警

这个例子展示了如何查询已解决的告警记录，用于审计或分析。

```python
history_data = client.get_diagnosis_history(diagnosis_service_id, "start_date", "end_date")
history = history_data['history']

print("\n--- Diagnosis History ---")
if not history:
    print("No resolved diagnoses in history.")
else:
    for diag in history:
        print(f"ID: {diag['id']}, Resolved by: {diag['resolved_by']}, Notes: {diag['resolution_notes']}")
```
