# 场景代理（ScenarioAgent）

`ScenarioAgent` 是一个专门的代理，负责在模拟环境中管理和执行预定义的测试场景。一个场景由一系列事件的时间轴组成，这些事件被注入到系统中，以测试其对各种情况的响应。这些事件可以包括干扰（如突然降雨或设备故障），也可以是在特定模拟时间发布的高级命令。

该代理对于确保供水系统中实施的控制策略的稳健性和可靠性至关重要。通过模拟各种场景，我们可以评估系统在正常和异常情况下的行为。

## 工作原理

`ScenarioAgent` 基于一个 `scenario_script`（场景脚本）运行，该脚本是一个按时间安排的事件列表。代理会持续将当前的模拟时间与事件时间轴进行核对。当模拟时间与事件的预定时间匹配时，`ScenarioAgent` 会将事件的消息发布到 `MessageBus` 上的指定主题。

## 初始化

`ScenarioAgent` 的初始化需要以下参数：

- `agent_id` (str): 代理的唯一标识符。
- `message_bus` (MessageBus): 用于通信的系统 `MessageBus` 实例。
- `scenario_script` (List[Dict[str, Any]]): 定义场景的定时事件列表。

`scenario_script` 中的每个事件都是一个包含三个键的字典：
- `time` (float): 事件应执行的模拟时间。
- `topic` (str): 事件消息将在 `MessageBus` 上发布的主题。
- `message` (Any): 要发布的消息内容。

脚本在初始化时会按时间排序，以确保事件按正确顺序执行。

## 使用示例

以下是如何定义 `scenario_script` 并用它来初始化 `ScenarioAgent` 的示例。

### 场景脚本定义

首先，为您的场景定义事件序列。例如，您可能希望模拟用水需求突然增加，随后发生管道破裂。

```python
scenario_script = [
    {
        'time': 100.0,
        'topic': 'water.demand.update',
        'message': {'zone': 'A', 'demand_increase': 0.5}
    },
    {
        'time': 250.0,
        'topic': 'infrastructure.failure',
        'message': {'type': 'pipe_burst', 'location': 'pipe_12', 'severity': 'high'}
    },
    {
        'time': 300.0,
        'topic': 'water.demand.update',
        'message': {'zone': 'A', 'demand_increase': 0.2}
    }
]
```

### 代理初始化与执行

接下来，使用此脚本创建 `ScenarioAgent` 的实例，并将其集成到主模拟循环中。

```python
from core_lib.mission.scenario_agent import ScenarioAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# 假设 message_bus 是 MessageBus 的一个现有实例
message_bus = MessageBus()

# 初始化 ScenarioAgent
scenario_agent = ScenarioAgent(
    agent_id='scenario_agent_1',
    message_bus=message_bus,
    scenario_script=scenario_script
)

# 在主模拟循环中
current_simulation_time = 0.0
time_step = 1.0

while current_simulation_time <= 500.0:
    # 其他模拟逻辑...

    # 运行 ScenarioAgent
    scenario_agent.run(current_time=current_simulation_time)

    # 其他模拟逻辑...

    current_simulation_time += time_step
```

在此示例中，`ScenarioAgent` 将在指定的模拟时间发布需求更新和管道破裂的消息，使您能够观察和验证系统的响应。
