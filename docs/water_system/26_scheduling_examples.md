# 7. 调度 (Scheduling) - 代码示例

本篇文档提供 `Scheduling` 对象方法的Python代码实现示例。

## 准备工作

我们为`WaterSystemApiClient`添加与优化调度服务交互的方法。同时，我们需要一个`Prediction`服务的客户端来获取输入。

```python
# a_hypothetical_api_client.py (续)
import datetime
import random
import time

# --- Prediction Client (from previous example) ---
class PredictionClient:
    def _generate_fake_prediction(self):
        base_demand = 100
        start_time = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        timestamps = [(start_time + datetime.timedelta(hours=i)).isoformat() + 'Z' for i in range(24)]
        values = [base_demand + random.uniform(-10, 10) + i * 2 for i in range(24)]
        return { "prediction_id": f"pred_res_{int(start_time.timestamp())}", "generated_at": datetime.datetime.utcnow().isoformat() + 'Z', "prediction_start_time": timestamps[0], "time_series": { "timestamps": timestamps, "predicted_values": values } }
    def __init__(self): self._latest_prediction = self._generate_fake_prediction()
    def get_latest_demand_prediction(self, prediction_id): return {"prediction": self._latest_prediction}

# --- Scheduling Client ---
class SchedulingClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        self._latest_schedule = None
        print("Scheduling Client initialized.")

    def run_pump_optimization(self, scheduler_id, demand_forecast):
        print(f"Running optimization for {scheduler_id}...")
        print(f"Using demand forecast starting at: {demand_forecast['prediction_start_time']}")
        time.sleep(1) # 模拟计算耗时
        schedule = {
            "schedule_id": f"cs_{int(datetime.datetime.utcnow().timestamp())}", "generated_at": datetime.datetime.utcnow().isoformat() + 'Z', "start_time": demand_forecast['prediction_start_time'],
            "control_plan": {
                "pump_A1": {"status": [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0]},
                "pump_A2": {"status": [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1]}
            },
            "expected_cost": 1250.75, "expected_kpis": {"avg_pressure": 28.5}
        }
        self._latest_schedule = schedule
        return {"schedule": schedule}

    def get_latest_schedule(self, scheduler_id):
        print(f"Getting latest schedule for {scheduler_id}...")
        return {"schedule": self._latest_schedule}

    def simulate_schedule(self, schedule):
        print(f"Simulating schedule {schedule['schedule_id']} for verification...")
        min_pressure = 22.5 - random.uniform(0, 5) # 模拟可能存在的风险
        return { "simulation_results": {"constraints_violated": min_pressure < 22.0, "min_pressure": min_pressure} }

prediction_client = PredictionClient()
scheduling_client = SchedulingClient()
scheduler_service_id = "sched_pump_station_A_24h"
```

## 1. 运行优化调度

调度任务的核心是接收需水量预测，并计算出最优的水泵运行计划。

```python
# 首先，从预测服务获取最新的需水量预测
print("--- Step 1: Get latest demand forecast ---")
demand_forecast_data = prediction_client.get_latest_demand_prediction("pred_zonal_demand_24h")
demand_forecast = demand_forecast_data['prediction']
print(f"Obtained forecast {demand_forecast['prediction_id']}")

# 然后，以该预测为输入，运行优化调度
print("\n--- Step 2: Run pump optimization ---")
schedule_data = scheduling_client.run_pump_optimization(scheduler_service_id, demand_forecast)
latest_schedule = schedule_data['schedule']

print("\n--- Generated Control Schedule ---")
print(f"Schedule ID: {latest_schedule['schedule_id']}")
print(f"Expected Cost: ${latest_schedule['expected_cost']:.2f}")
print("Pump A1 planned status for next 24 hours:")
print(latest_schedule['control_plan']['pump_A1']['status'])
```

## 2. 验证调度计划 (沙盘推演)

在将调度计划下发到物理设备执行之前，进行一次仿真验证是一个非常好的安全实践。这可以确保生成的计划在实际执行时不会违反任何关键约束（如最低压力）。

```python
print("\n--- Step 3: Simulate the generated schedule for safety check ---")
if latest_schedule:
    simulation_result_data = scheduling_client.simulate_schedule(latest_schedule)
    sim_results = simulation_result_data['simulation_results']

    print(f"Simulation check complete. Minimum pressure found: {sim_results['min_pressure']:.2f} mH2O")

    if sim_results['constraints_violated']:
        print("\nWARNING: This schedule may violate system constraints!")
        print("Action: Do not deploy. Trigger a re-optimization with tighter constraints.")
    else:
        print("\nSUCCESS: Schedule is safe to deploy.")
        print("Action: Load schedule into the Control service for execution.")
else:
    print("No schedule to simulate.")
```
