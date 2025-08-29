# 1. 仿真 (Simulation) - 代码示例

本篇文档提供 `Simulation` 对象方法的Python代码实现示例。这些示例假设我们通过一个API客户端与智慧水务平台进行交互。

## 准备工作

首先，假设我们有一个API客户端，已经配置好了认证信息。

```python
# a_hypothetical_api_client.py
import time

class WaterSystemApiClient:
    def __init__(self, api_key):
        self.api_key = api_key
        print("API Client initialized.")

    def create_simulation(self, config):
        print(f"Creating simulation with config: {config['name']}")
        # 实际应用中，这里会发送一个HTTP POST请求
        # 返回一个模拟的仿真ID
        return {"id": f"sim_{int(time.time())}"}

    def run_simulation(self, sim_id):
        print(f"Sending command to run simulation {sim_id}...")
        # 实际应用中，这里会发送一个HTTP POST请求
        return {"status": "running"}

    def get_simulation_status(self, sim_id):
        print(f"Checking status for simulation {sim_id}...")
        # 实际应用中，这里会发送一个HTTP GET请求
        # 这里我们模拟一个会随时间变化的状态
        if not hasattr(self, '_sim_status') or not self._sim_status:
            self._sim_status = ['running', 'running', 'running', 'completed']

        status = self._sim_status.pop(0)
        return {"id": sim_id, "status": status}

    def get_simulation_results(self, sim_id):
        print(f"Fetching results for simulation {sim_id}...")
        # 实际应用中，这里会发送一个HTTP GET请求
        # 只有在状态为 'completed' 时才返回结果
        # 为了示例，我们直接返回结果
        return {
            "results": {
                "timestamps": ["..."],
                "node_pressures": {"n1": [15.2, 15.1], "n2": [14.8, 14.7]},
                "pipe_flows": {"p1": [0.5, 0.51]}
            }
        }

# 初始化客户端
client = WaterSystemApiClient(api_key="YOUR_API_KEY")
```

## 1. 创建并运行一个仿真

这个例子展示了如何定义一个仿真配置，创建一个仿真实例，然后运行它。

```python
# a_hypothetical_api_client.py (续)

# 1. 定义仿真配置
simulation_config = {
    "name": "城市主干管网压力仿真",
    "network": {
        "nodes": [{"id": "n1", "elevation": 10.5, "demand": 0.1}],
        "pipes": [{"id": "p1", "from_node": "n1", "to_node": "n2"}]
    },
    "time_settings": {
        "start_time": "2023-09-01T00:00:00Z",
        "end_time": "2023-09-01T23:59:59Z",
        "time_step_seconds": 600
    }
}

# 2. 创建仿真实例
simulation_instance = client.create_simulation(simulation_config)
sim_id = simulation_instance['id']
print(f"Simulation created with ID: {sim_id}")

# 3. 运行仿真
client.run_simulation(sim_id)
print(f"Simulation {sim_id} is now running in the background.")
```

## 2. 监控仿真状态并获取结果

这个例子展示了如何轮询一个正在运行的仿真的状态，并在其完成后获取结果。

```python
# a_hypothetical_api_client.py (续)

def monitor_and_get_results(sim_id):
    while True:
        status_response = client.get_simulation_status(sim_id)
        current_status = status_response['status']
        print(f"Current status of {sim_id}: {current_status}")

        if current_status == 'completed':
            print("Simulation completed. Fetching results...")
            results_data = client.get_simulation_results(sim_id)
            if results_data:
                print("Results received:")
                print(results_data['results'])
            break
        elif current_status == 'failed':
            print(f"Simulation {sim_id} failed.")
            break

        # 等待一段时间再查询，避免过于频繁的API调用
        time.sleep(2)

# 执行监控
monitor_and_get_results(sim_id)
```

## 3. 使用事件监听器 (更高级的方式)

在实际应用中，使用事件监听器（如WebSockets或回调URL）比轮询更高效。下面的代码是一个概念性的示例。

```python
# a_hypothetical_event_handler.py

class SimulationEventHandler:
    def __init__(self, api_client):
        self.client = api_client
        # 实际应用中，这里会初始化WebSocket连接
        print("Event handler initialized.")

    def subscribe_to_simulation(self, sim_id):
        print(f"Subscribing to events for simulation {sim_id}")

    def on_status_change(self, event):
        sim_id = event['sim_id']
        new_status = event['new_status']
        print(f"Event received: Simulation {sim_id} status changed to {new_status}")

        if new_status == 'completed':
            # 当收到完成事件时，自动去获取结果
            results = self.client.get_simulation_results(sim_id)
            print("Automatically fetched results upon completion event:", results)

# 概念性使用
# event_handler = SimulationEventHandler(client)
# event_handler.subscribe_to_simulation(sim_id)

# 模拟平台推送一个事件
# event_handler.on_status_change({
#     "sim_id": sim_id,
#     "new_status": "completed"
# })
```
