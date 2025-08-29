# 5. 评价 (Evaluation) - 代码示例

本篇文档提供 `Evaluation` 对象方法的Python代码实现示例。

## 准备工作

我们为`WaterSystemApiClient`添加与性能评价服务交互的方法。

```python
# a_hypothetical_api_client.py (续)
import time
import datetime

class WaterSystemApiClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        # 模拟一个内存中的报告列表
        self._reports = [
            {
                "report_id": "report_20230801",
                "evaluation_id": "eval_monthly_energy_efficiency",
                "start_time": "2023-07-01T00:00:00Z",
                "end_time": "2023-07-31T23:59:59Z",
                "generated_at": "2023-08-01T00:05:00Z",
                "kpi_results": [
                    {"kpi_id": "kpi_unaccounted_water_rate", "value": 15.8, "trend": 0.03},
                    {"kpi_id": "kpi_pump_energy_consumption", "value": 2.9, "trend": 0.08}
                ],
                "summary": "7月能效有所下降，产销差率略有上升。"
            }
        ]
        print("API Client initialized.")

    def run_one_time_evaluation(self, eval_id, start_time, end_time):
        print(f"Running one-time evaluation for {eval_id} from {start_time} to {end_time}...")
        # 模拟生成一个新报告
        new_report = {
            "report_id": f"report_manual_{int(time.time())}",
            "evaluation_id": eval_id,
            "start_time": start_time,
            "end_time": end_time,
            "generated_at": datetime.datetime.utcnow().isoformat() + 'Z',
            "kpi_results": [
                {"kpi_id": "kpi_unaccounted_water_rate", "value": 14.5, "trend": -0.05},
                {"kpi_id": "kpi_pump_energy_consumption", "value": 2.6, "trend": -0.04}
            ],
            "summary": "手动评估期间：能效和产销差率均有改善。"
        }
        self._reports.append(new_report)
        return {"report": new_report}

    def get_latest_evaluation_report(self, eval_id):
        print(f"Getting latest report for {eval_id}...")
        if not self._reports:
            return None
        # 返回按生成时间最新的报告
        latest_report = sorted(self._reports, key=lambda r: r['generated_at'], reverse=True)[0]
        return {"report": latest_report}

    def get_evaluation_report_history(self, eval_id, page, page_size):
        print(f"Getting report history for {eval_id}...")
        # 实际应用会处理分页
        return {"reports": self._reports, "total": len(self._reports)}

client = WaterSystemApiClient()
evaluation_service_id = "eval_monthly_energy_efficiency"
```

## 1. 手动执行一次性评价

这个例子展示了如何对一个特定的历史时期（例如，上个季度）手动触发一次性能评价。

```python
start_date = "2023-04-01T00:00:00Z"
end_date = "2023-06-30T23:59:59Z"

print("--- Running a one-time evaluation for Q2 2023 ---")
manual_run_data = client.run_one_time_evaluation(evaluation_service_id, start_date, end_date)
manual_report = manual_run_data['report']

print("\n--- Manual Evaluation Report ---")
print(f"Report ID: {manual_report['report_id']}")
print(f"Summary: {manual_report['summary']}")
for kpi in manual_report['kpi_results']:
    print(f"  - KPI '{kpi['kpi_id']}': {kpi['value']}")
```

## 2. 获取最新的周期性报告

这个例子展示了如何获取由系统自动周期性生成的最新一份评价报告。

```python
print("\n--- Getting the latest periodic report ---")
latest_report_data = client.get_latest_evaluation_report(evaluation_service_id)
if latest_report_data:
    latest_report = latest_report_data['report']
    print(f"Latest Report ID: {latest_report['report_id']} (for period ending {latest_report['end_time']})")
    print(f"Summary: {latest_report['summary']}")
else:
    print("No reports found.")
```

## 3. 查询历史报告以分析趋势

这个例子展示了如何获取所有历史报告，以便对关键指标（KPI）的长期变化趋势进行分析。

```python
print("\n--- Analyzing KPI trends from report history ---")
history_data = client.get_evaluation_report_history(evaluation_service_id, page=1, page_size=10)
history = history_data['reports']

if history:
    # 按时间排序报告
    sorted_history = sorted(history, key=lambda r: r['end_time'])

    print("Unaccounted Water Rate (%) over time:")
    for report in sorted_history:
        kpi_value = next((kpi['value'] for kpi in report['kpi_results'] if kpi['kpi_id'] == 'kpi_unaccounted_water_rate'), 'N/A')
        print(f"  - Period ending {report['end_time'][:10]}: {kpi_value}")
else:
    print("No history found to analyze.")
```
