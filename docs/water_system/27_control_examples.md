# 8. 控制 (Control) - 代码示例

本篇文档提供 `Control` 对象方法的Python代码实现示例。这是连接决策与物理执行的关键环节。

## 准备工作

我们为`WaterSystemApiClient`添加与自动控制服务交互的方法。

```python
# a_hypothetical_api_client.py (续)
import datetime
import time
import random

# --- Prerequisite Clients (from previous examples) ---
class PredictionClient:
    def _generate_fake_prediction(self):
        base_demand = 100
        start_time = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        timestamps = [(start_time + datetime.timedelta(hours=i)).isoformat() + 'Z' for i in range(24)]
        values = [base_demand + random.uniform(-10, 10) + i * 2 for i in range(24)]
        return { "prediction_id": f"pred_res_{int(start_time.timestamp())}", "generated_at": datetime.datetime.utcnow().isoformat() + 'Z', "prediction_start_time": timestamps[0], "time_series": { "timestamps": timestamps, "predicted_values": values } }
    def __init__(self): self._latest_prediction = self._generate_fake_prediction()
    def get_latest_demand_prediction(self, prediction_id): return {"prediction": self._latest_prediction}

class SchedulingClient:
    def __init__(self): self._latest_schedule = None
    def run_pump_optimization(self, scheduler_id, demand_forecast):
        schedule = { "schedule_id": f"cs_{int(datetime.datetime.utcnow().timestamp())}", "generated_at": datetime.datetime.utcnow().isoformat() + 'Z', "start_time": demand_forecast['prediction_start_time'], "control_plan": { "pump_A1": {"status": [1]*12 + [0]*12}, "pump_A2": {"status": [0]*6 + [1]*12 + [0]*6} }, "expected_cost": 1250.75 }
        self._latest_schedule = schedule
        return {"schedule": schedule}

# --- Control Client ---
class ControlClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        self._mode = "manual"
        self._log = []
        self._active_schedule_id = None
        print("Control Client initialized.")

    def load_schedule(self, controller_id, schedule):
        print(f"Loading schedule {schedule['schedule_id']} into controller {controller_id}...")
        if "pump_A1" in schedule['control_plan']:
            self._active_schedule_id = schedule['schedule_id']
            self._log.append(f"{datetime.datetime.utcnow().isoformat()} - INFO - Schedule {self._active_schedule_id} loaded by user.")
            print("Schedule loaded successfully.")
            return {"success": True}
        return {"success": False, "error": "Schedule contains devices not managed by this controller."}

    def set_mode(self, controller_id, mode):
        if mode not in ["automatic", "manual", "advisory"]: return {"success": False, "error": "Invalid mode."}
        self._mode = mode
        self._log.append(f"{datetime.datetime.utcnow().isoformat()} - INFO - Mode changed to {mode.upper()}.")
        print(f"Controller {controller_id} mode set to {mode.upper()}.")
        if mode == "automatic":
            print("Controller is now executing schedule automatically.")
            self._log.append(f"{datetime.datetime.utcnow().isoformat()} - EXEC - Automatic execution of schedule {self._active_schedule_id} started.")
        return {"success": True}

    def manual_override(self, controller_id, target_id, action):
        print(f"Attempting to manually '{action}' device '{target_id}'...")
        if self._mode != "manual": return {"success": False, "error": "Manual override is only allowed in MANUAL mode."}
        log_msg = f"{datetime.datetime.utcnow().isoformat()} - MANUAL - User commanded '{action}' on '{target_id}'."
        print(log_msg)
        self._log.append(log_msg)
        return {"success": True}

    def get_control_log(self, controller_id):
        return {"log": self._log}

prediction_client = PredictionClient()
scheduling_client = SchedulingClient()
control_client = ControlClient()
controller_id = "ctrl_service_main_pumps"
```

## 1. 加载并自动执行调度计划

这个例子展示了标准的“自动驾驶”工作流程：将优化好的调度计划加载到控制器，然后切换到自动模式开始执行。

```python
# 首先，获取预测和调度计划
demand_forecast = prediction_client.get_latest_demand_prediction("pred")['prediction']
optimal_schedule = scheduling_client.run_pump_optimization("sched", demand_forecast)['schedule']
print(f"Obtained schedule {optimal_schedule['schedule_id']}")

# 第二步：将计划加载到控制器
print("\n--- Step 2: Load schedule into controller ---")
control_client.load_schedule(controller_id, optimal_schedule)

# 第三步：切换到自动模式开始执行
print("\n--- Step 3: Set mode to AUTOMATIC ---")
control_client.set_mode(controller_id, "automatic")
print("\nController is now running on autopilot, executing the plan...")
```

## 2. 紧急手动干预

这个例子展示了在突发情况下，操作员如何夺回控制权，并手动执行操作。

```python
print("\n--- EMERGENCY SCENARIO ---")

# 第一步：立即切换到手动模式，暂停自动执行
print("\n--- Step 1: Switch to MANUAL mode to pause automation ---")
control_client.set_mode(controller_id, "manual")

# 第二步：执行手动指令（例如，紧急停止所有泵）
print("\n--- Step 2: Issue manual override commands ---")
control_client.manual_override(controller_id, "pump_A1", "stop")
control_client.manual_override(controller_id, "pump_A2", "stop")

# ... 手动操作解决紧急情况 ...

# 第三步：恢复自动控制
# 实际应用中，可能需要重新运行优化调度，获得新的计划
print("\n--- Step 3: Resume automatic control (hypothetical) ---")
# control_client.load_schedule(controller_id, new_emergency_schedule)
# control_client.set_mode(controller_id, "automatic")
```

## 3. 查看控制日志

为了审计和追溯，可以随时查看详细的控制日志。

```python
print("\n--- Retrieving Control Log ---")
log_data = control_client.get_control_log(controller_id)
log_entries = log_data['log']

for entry in log_entries:
    print(entry)
```
