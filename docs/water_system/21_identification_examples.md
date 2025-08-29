# 2. 辨识 (Identification) - 代码示例

本篇文档提供 `Identification` 对象方法的Python代码实现示例。这些示例将沿用之前定义的`WaterSystemApiClient`概念。

## 准备工作

我们将为`WaterSystemApiClient`添加与参数辨识相关的方法。

```python
# a_hypothetical_api_client.py (续)
import time

# 为了示例清晰，我们创建一个包含新方法的类
class WaterSystemApiClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        print("API Client initialized.")

    def create_identification_task(self, config):
        print(f"Creating identification task: {config['name']}")
        self._ident_status = ['running', 'running', 'running', 'completed'] # 重置状态
        return {"id": f"ident_{int(time.time())}"}

    def run_identification_task(self, task_id):
        print(f"Sending command to run identification task {task_id}...")
        return {"status": "running"}

    def get_identification_status(self, task_id):
        print(f"Checking status for identification task {task_id}...")
        if not hasattr(self, '_ident_status') or not self._ident_status:
            return {"id": task_id, "status": "completed"}
        status = self._ident_status.pop(0)
        return {"id": task_id, "status": status}

    def get_identification_results(self, task_id):
        print(f"Fetching results for identification task {task_id}...")
        return {
            "results": {
                "identified_parameters": [
                    {"element_id": "p1", "parameter_name": "roughness", "optimal_value": 125.8}
                ],
                "final_objective_value": 0.05
            }
        }

    def get_calibrated_model_from_task(self, task_id):
        print(f"Fetching calibrated model from task {task_id}...")
        return {
            "calibrated_model": {
                "id": f"sim_calibrated_{int(time.time())}",
                "name": "Calibrated Simulation Model",
                "network": {
                    "pipes": [{"id": "p1", "roughness": 125.8}] # 参数已被更新
                }
            }
        }

client = WaterSystemApiClient()
```

## 1. 定义并运行参数辨识任务

这个例子展示了如何定义一个参数辨识任务，包括要辨识的参数、观测数据等，然后启动任务。

```python
# 1. 定义参数辨识任务配置
identification_config = {
    "name": "主干管网管道粗糙度辨识",
    "simulation_model_id": "sim_base_model_v1",
    "parameters_to_identify": [
        {
            "element_type": "pipe",
            "element_id": "p1",
            "parameter_name": "roughness",
            "initial_guess": 130,
            "lower_bound": 100,
            "upper_bound": 150
        }
    ],
    "observation_data": {
        "node_pressures": {
            "n2": {"timestamps": ["..."], "values": [14.5, 14.2]}
        }
    },
    "optimizer_options": {
        "algorithm": "genetic_algorithm"
    }
}

# 2. 创建辨识任务
ident_task = client.create_identification_task(identification_config)
task_id = ident_task['id']
print(f"Identification task created with ID: {task_id}")

# 3. 运行辨识任务
client.run_identification_task(task_id)
print(f"Identification task {task_id} is now running.")
```

## 2. 获取辨识结果和校准后的模型

这个例子展示了在任务完成后，如何获取辨识出的最优参数，以及一个用这些参数更新过的新仿真模型。

```python
def check_identification_and_get_model(task_id):
    # 假设我们已经通过轮询或事件监听确认任务已完成
    while True:
        status_response = client.get_identification_status(task_id)
        current_status = status_response['status']
        print(f"Task status: {current_status}. Waiting...")
        if current_status == 'completed':
            break
        time.sleep(1)

    print("Identification task completed.")

    # 1. 获取辨识结果
    results_data = client.get_identification_results(task_id)
    print("Identification results:")
    print(results_data['results'])

    optimal_roughness = results_data['results']['identified_parameters'][0]['optimal_value']
    print(f"Identified optimal roughness for pipe p1 is: {optimal_roughness}")

    # 2. 获取校准后的模型
    model_data = client.get_calibrated_model_from_task(task_id)
    calibrated_model = model_data['calibrated_model']
    print("\nReceived new calibrated model:")
    print(calibrated_model)

    # 现在可以使用这个校准后的模型进行更精确的仿真
    # client.run_simulation(calibrated_model['id'])

# 执行
check_identification_and_get_model(task_id)
```
