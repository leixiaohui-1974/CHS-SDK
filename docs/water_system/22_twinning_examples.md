# 3. 孪生 (Twinning) - 代码示例

本篇文档提供 `DigitalTwin` 对象方法的Python代码实现示例。

## 准备工作

我们继续扩展`WaterSystemApiClient`，为其添加与数字孪生交互的方法。

```python
# a_hypothetical_api_client.py (续)
import time
import datetime

class WaterSystemApiClient:
    def __init__(self, api_key="YOUR_API_KEY"):
        self.api_key = api_key
        print("API Client initialized.")

    def start_twin(self, twin_id):
        print(f"Starting digital twin service {twin_id}...")
        return {"status": "running"}

    def stop_twin(self, twin_id):
        print(f"Stopping digital twin service {twin_id}...")
        return {"status": "stopped"}

    def get_twin_current_state(self, twin_id):
        print(f"Getting current state for twin {twin_id}...")
        return {
            "state": {
                "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
                "node_states": {
                    "n1": {"pressure": 15.1, "quality": 0.98},
                    "n5": {"pressure": 25.3, "quality": 0.95}
                },
                "pipe_states": {
                    "p3": {"flow": 0.45, "velocity": 1.2}
                },
                "sync_status": {"last_sync_error": 0.05}
            }
        }

    def get_twin_historical_state(self, twin_id, start_time, end_time):
        print(f"Getting historical state for twin {twin_id} from {start_time} to {end_time}...")
        # 返回模拟的历史数据
        return {
            "history": [
                {"timestamp": start_time, "node_states": {"n1": {"pressure": 15.5}}},
                {"timestamp": end_time, "node_states": {"n1": {"pressure": 15.4}}}
            ]
        }

    def run_what_if_simulation_on_twin(self, twin_id, scenario_config):
        print(f"Running what-if scenario '{scenario_config['name']}' on twin {twin_id}...")
        # 模拟“爆管”场景的结果
        return {
            "results": {
                "timestamps": ["..."],
                "node_pressures": {
                    "n4": [25.0, 15.0, 10.0], # 压力急剧下降
                    "n5": [25.3, 12.0, 8.0]
                }
            }
        }

client = WaterSystemApiClient()
twin_id = "twin_main_city_pipeline"
```

## 1. 启动并获取孪生实时状态

这个例子展示了如何启动数字孪生服务，并查询其反映的当前物理世界状态。

```python
# 1. 启动孪生服务
client.start_twin(twin_id)

# 2. 获取当前状态
current_state_data = client.get_twin_current_state(twin_id)
current_state = current_state_data['state']
print("\n--- Current Twin State ---")
print(f"Timestamp: {current_state['timestamp']}")
print(f"Pressure at Node n5: {current_state['node_states']['n5']['pressure']} mH2O")
print(f"Flow in Pipe p3: {current_state['pipe_states']['p3']['flow']} m³/s")
```

## 2. 查询历史状态

这个例子展示了如何查询孪生体记录的某个时间段的历史数据。

```python
start = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat() + 'Z'
end = datetime.datetime.utcnow().isoformat() + 'Z'

historical_data = client.get_twin_historical_state(twin_id, start, end)
print("\n--- Historical State for Node n1 ---")
for record in historical_data['history']:
    print(f"At {record['timestamp']}, pressure was {record['node_states']['n1']['pressure']}")

```

## 3. 运行 "What-if" 假设分析

这是数字孪生的核心价值之一。下面的例子模拟了一个“爆管”场景，并观察其对系统压力的影响，而这一切都在虚拟世界中进行，不会影响物理系统。

```python
# 1. 定义假设分析场景
# 场景：假设未来两小时，n5节点处的管道突然爆裂 (通过增加一个极大的需水量来模拟)
what_if_scenario_config = {
    "name": "Pipe burst simulation at Node n5",
    "time_settings": {"duration_hours": 2},
    "network_modifications": [
        {
            "element_type": 'node',
            "element_id": 'n5',
            "parameter_name": 'demand',
            "value": 10.0 # 一个非常大的需量
        }
    ]
}

# 2. 在孪生体上运行此场景
what_if_results_data = client.run_what_if_simulation_on_twin(twin_id, what_if_scenario_config)
what_if_results = what_if_results_data['results']

print("\n--- What-if Scenario Results ---")
print("Simulated pressure drop at neighboring node n4:")
print(what_if_results['node_pressures']['n4'])
print("This allows us to predict the impact of a pipe burst without any real-world consequences.")
```
