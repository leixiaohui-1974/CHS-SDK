# 6. 预测 (Prediction) - 代码示例

本篇文档提供 `Prediction` 对象方法的Python代码实现示例。

## 准备工作

我们为`WaterSystemApiClient`添加与需水量预测服务交互的方法。

```python
# a_hypothetical_api_client.py (续)
import datetime
import random
import time

class WaterSystemApiClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        self._latest_prediction = self._generate_fake_prediction()
        self._prediction_history = [self._latest_prediction]
        print("API Client initialized.")

    def _generate_fake_prediction(self):
        """Helper to generate a plausible-looking prediction result."""
        base_demand = 100
        start_time = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        timestamps = [(start_time + datetime.timedelta(hours=i)).isoformat() + 'Z' for i in range(24)]
        values = [base_demand + random.uniform(-10, 10) + i * 2 for i in range(24)]
        return {
            "prediction_id": f"pred_res_{int(start_time.timestamp())}",
            "generated_at": datetime.datetime.utcnow().isoformat() + 'Z',
            "prediction_start_time": timestamps[0],
            "time_series": {
                "timestamps": timestamps,
                "predicted_values": values
            }
        }

    def get_latest_demand_prediction(self, prediction_id):
        print(f"Getting latest prediction for {prediction_id}...")
        return {"prediction": self._latest_prediction}

    def run_prediction_once(self, prediction_id):
        print(f"Manually triggering a new prediction run for {prediction_id}...")
        # 模拟计算耗时
        time.sleep(1)
        new_prediction = self._generate_fake_prediction()
        self._latest_prediction = new_prediction
        self._prediction_history.append(new_prediction)
        return {"prediction": new_prediction}

    def get_prediction_history(self, prediction_id, page, page_size):
        print(f"Getting prediction history for {prediction_id}...")
        return {"predictions": self._prediction_history, "total": len(self._prediction_history)}

client = WaterSystemApiClient()
prediction_service_id = "pred_zonal_demand_24h"
```

## 1. 获取最新的需水量预测

这是最常见的用例，调度系统需要获取最新的需水量预测来制定优化计划。

```python
print("--- Getting the latest demand forecast ---")
prediction_data = client.get_latest_demand_prediction(prediction_service_id)
latest_prediction = prediction_data['prediction']

print(f"Prediction ID: {latest_prediction['prediction_id']}")
print(f"Generated at: {latest_prediction['generated_at']}")

# 查看未来几个小时的预测值
timestamps = latest_prediction['time_series']['timestamps']
values = latest_prediction['time_series']['predicted_values']

print("\n--- Forecast for the next 5 hours ---")
for i in range(5):
    print(f"  - Time: {timestamps[i]}, Predicted Demand: {values[i]:.2f} m³/h")
```

## 2. 手动触发一次新的预测

在某些情况下（例如，天气预报有重大更新），可能需要立即重新生成预测，而不是等待下一个周期。

```python
print("\n--- Manually triggering a new prediction run ---")
run_data = client.run_prediction_once(prediction_service_id)
new_prediction = run_data['prediction']

print("New prediction generated.")
print(f"New Prediction ID: {new_prediction['prediction_id']}")

# 比较新旧预测的第一个值
old_first_value = latest_prediction['time_series']['predicted_values'][0]
new_first_value = new_prediction['time_series']['predicted_values'][0]

print(f"Old forecast for next hour: {old_first_value:.2f}")
print(f"New forecast for next hour: {new_first_value:.2f}")
```

## 3. 获取历史预测用于评估

为了评估预测模型的准确性，我们需要将历史预测值与实际发生的需量值进行比较。这里我们只演示如何获取历史预测。

```python
print("\n--- Retrieving prediction history ---")
history_data = client.get_prediction_history(prediction_service_id, page=1, page_size=10)
history = history_data['predictions']

print(f"Found {len(history)} historical prediction runs.")
# 打印每个历史预测的ID和生成时间
for p in history:
    print(f"  - ID: {p['prediction_id']}, Generated at: {p['generated_at']}")

# 在实际应用中，你会将这些预测值与存储在数字孪生中的历史需量值进行对比
```
