# 核心概念: 消息总线 (Message Bus)

本篇文档详细介绍 `core_lib` 中实现智能体之间通信的核心组件：`MessageBus`。

## 1. 核心理念：发布/订阅模式

*   **位置**: `core_lib/central_coordination/collaboration/message_bus.py`

为了实现智能体之间的**松耦合 (Loose Coupling)**，系统中的智能体不直接相互调用。相反，它们通过一个中央的“信息中介”——消息总线——来通信。

`MessageBus` 实现的是经典的**发布/订阅 (Publish/Subscribe, Pub/Sub)** 设计模式。

*   **发布 (Publish)**: 任何智能体都可以向一个指定**主题 (Topic)** 的通道发布一条**消息 (Message)**。它不需要知道谁会接收这条消息。
*   **订阅 (Subscribe)**: 任何智能体都可以声明它对某个或某些主题感兴趣。当有消息被发布到这些主题时，消息总线会自动将消息转发给所有订阅了该主题的智能体。

这种模式的巨大优势在于，消息的发送方和接收方被完全解耦。一个发布者可以有零个、一个或多个订阅者，而它自己完全无需关心。同样，一个订阅者可以接收来自多个发布者的消息。这使得系统非常灵活和易于扩展。

## 2. `MessageBus` 的实现

`MessageBus` 类提供两个核心方法：

### `subscribe(topic: str, callback: Callable)`

*   **作用**: 将一个回调函数注册为某个主题的订阅者。
*   **参数**:
    *   `topic`: 一个字符串，代表主题的名称。主题是分层的，通常使用类似路径的格式，例如 `state/reservoir/main` 或 `command/gate/flood`。
    *   `callback`: 一个函数或方法。当有消息发布到 `topic` 时，这个函数将被调用。消息本身会作为参数传递给该回调函数。

### `publish(topic: str, message: Message)`

*   **作用**: 向指定主题发布一条消息。
*   **参数**:
    *   `topic`: 要发布到的主题。
    *   `message`: 要发布的消息。在 `core_lib` 中，消息通常是一个字典 (`Dict`)。

## 3. 工作流程示例

1.  `DigitalTwinAgent` (孪生体A) 调用 `self.bus.subscribe('command/A', self.handle_command)`，订阅自己的命令主题。
2.  `LocalControlAgent` (控制器B) 调用 `self.bus.subscribe('state/A', self.handle_observation)`，订阅孪生体A的状态主题。
3.  `CentralDispatcher` (调度器C) 想要给孪生体A发送一个指令。它调用 `self.bus.publish('command/A', {'setpoint': 5.0})`。
4.  `MessageBus` 查找所有订阅了 `command/A` 的回调，找到了孪生体A的 `handle_command` 方法，并用 `{'setpoint': 5.0}` 作为参数调用它。控制器B则完全收不到这条消息。
5.  孪生体A在接收到指令并更新其内部模型后，调用 `self.bus.publish('state/A', {'current_level': 4.9})` 来发布自己的新状态。
6.  `MessageBus` 查找所有订阅了 `state/A` 的回调，找到了控制器B的 `handle_observation` 方法，并调用它。调度器C则收不到这条消息。

通过这种方式，三个智能体在完全不知道彼此存在的情况下，实现了精确的信息交换。
